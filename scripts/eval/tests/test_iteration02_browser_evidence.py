from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "iteration02_browser_evidence.py"
spec = importlib.util.spec_from_file_location("iteration02_browser_evidence", FILE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

SOURCE = "a" * 40
DIGEST = "b" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic-fixture-not-a-real-screenshot"


class BrowserEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.now = dt.datetime(2026, 10, 13, 12, 0, tzinfo=dt.timezone.utc)
        self.case_id = "I02-254-charts"
        self.lock = {
            "source_revision": SOURCE, "release_id": "synthetic-release",
            "payload_content_sha256": DIGEST, "runtime_evidence": "NOT_RUN",
            "release_approved": False,
            "cases": [{
                "case_id": self.case_id, "channel": "browser",
                "input_sha256": DIGEST, "repetitions": 1,
            }],
        }
        self.capture = {
            "case_id": self.case_id,
            "source_revision": SOURCE, "release_id": "synthetic-release",
            "payload_content_sha256": DIGEST,
            "input_sha256": DIGEST,
            "installed_attestation": "verified",
            "installed_observation_reference": "synthetic identity receipt",
            "capture_source": "synthetic browser test harness only",
            "chat_reference": "test://fixture/not-real-chat-url",
            "captured_at": "2026-10-13T12:00:00Z",
            "chart_checks": [],
        }
        self.create_check("bar", {
            "title": "Signed bar fixture",
            "labels": ["negative", "zero", "positive"],
            "values": [-5, 0, 3],
        })
        self.create_check("line", {
            "title": "Signed line fixture",
            "x_labels": ["before", "after"],
            "series_names": ["synthetic"],
            "series_values": [[-2, 0]],
        })

    def create_check(self, kind, expected):
        tool = self.root / f"{kind}.tool.json"
        accessible = self.root / f"{kind}.accessibility.json"
        screenshot = self.root / f"{kind}.png"
        tool.write_text(json.dumps({
            "tool_receipt": {
                "tool_name": mod.TOOLS[kind],
                "execution_state": "executed", "status": "SUCCESS",
                "artifact_state": "rendered",
                "client_display_state": "not_observable",
                "source_revision": SOURCE,
            },
        }), encoding="utf-8")
        accessible.write_text(json.dumps(expected), encoding="utf-8")
        screenshot.write_bytes(PNG)
        corr = f"{kind}-fixture-call"
        self.capture["chart_checks"].append({
            "kind": kind, "correlation_id": corr,
            "tool_call_correlation_id": corr,
            "client_capture_correlation_id": corr,
            "client_display_state": "observed",
            "tool_receipt_path": tool.name,
            "tool_receipt_sha256": hashlib.sha256(tool.read_bytes()).hexdigest(),
            "screenshot_path": screenshot.name,
            "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
            "accessibility_path": accessible.name,
            "accessibility_sha256": hashlib.sha256(accessible.read_bytes()).hexdigest(),
            "expected_data": expected,
        })

    def assess(self):
        return mod.assess(self.lock, self.capture, self.root, now=self.now)

    def test_synthetic_complete_is_not_authenticity_or_runtime_pass(self):
        report = self.assess()
        self.assertEqual("STRUCTURALLY_CORRELATED_INDEPENDENT_REVIEW_REQUIRED", report["status"], report["issues"])
        self.assertEqual("NOT_EVALUATED", report["model_behavior_verdict"])
        self.assertEqual("NOT_VERIFIED", report["screenshot_visual_authenticity"])
        self.assertFalse(report["release_approved"])
        self.assertEqual(2, len(report["bound_files"]))

    def test_missing_one_chart_blocks(self):
        self.capture["chart_checks"].pop()
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])

    def test_wrong_client_label_or_signed_value_blocks(self):
        for field, wrong in (("values", [5, 0, 3]), ("labels", ["a", "b", "c"])):
            with self.subTest(field=field):
                data = {"title": "Signed bar fixture", "labels": ["negative", "zero", "positive"],
                        "values": [-5, 0, 3]}
                data[field] = wrong
                (self.root / "bar.accessibility.json").write_text(json.dumps(data), encoding="utf-8")
                # Rebind correct accessibility hash: data mismatch, not hash mismatch.
                self.capture["chart_checks"][0]["accessibility_sha256"] = hashlib.sha256(
                    (self.root / "bar.accessibility.json").read_bytes()).hexdigest()
                self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])

    def test_mismatched_digest_or_tool_source_blocks(self):
        self.capture["chart_checks"][0]["screenshot_sha256"] = "f" * 64
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])
        self.capture["chart_checks"][0]["screenshot_sha256"] = hashlib.sha256(PNG).hexdigest()
        self.capture["source_revision"] = "c" * 40
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])

    def test_fabricated_client_display_in_tool_receipt_blocks(self):
        path = self.root / "bar.tool.json"
        raw = json.loads(path.read_text())
        raw["tool_receipt"]["client_display_state"] = "observed"
        path.write_text(json.dumps(raw), encoding="utf-8")
        self.capture["chart_checks"][0]["tool_receipt_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])

    def test_missing_correlated_client_screenshot_blocks(self):
        self.capture["chart_checks"][0]["client_capture_correlation_id"] = "different"
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])
        self.capture["chart_checks"][0]["client_capture_correlation_id"] = "bar-fixture-call"
        (self.root / "bar.png").unlink()
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])

    def test_path_traversal_and_symlink_block(self):
        self.capture["chart_checks"][0]["screenshot_path"] = "../outside.png"
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])
        original = self.root / "bar.png"
        self.capture["chart_checks"][0]["screenshot_path"] = "bar.png"
        original.unlink()
        original.symlink_to(self.root / "line.png")
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])

    def test_stale_capture_and_missing_chat_reference_block(self):
        self.capture["captured_at"] = "2026-10-09T12:00:00Z"
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])
        self.capture["captured_at"] = "2026-10-13T12:00:00Z"
        self.capture["chat_reference"] = ""
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])

    def test_bad_nested_input_blocks_instead_of_crashing(self):
        self.capture["chart_checks"][0]["kind"] = ["bar"]
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])
        self.capture["chart_checks"][0]["kind"] = "bar"
        self.capture["chart_checks"][0]["expected_data"] = None
        self.assertEqual("BLOCKED_EVIDENCE", self.assess()["status"])


if __name__ == "__main__":
    unittest.main()
