from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("iteration02_browser_evidence", HERE / "iteration02_browser_evidence.py")
checker = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(checker)

SRC = "a" * 40
PAYLOAD = "b" * 64
INPUT = "c" * 64
RUBRIC = "d" * 64
CHART = "e" * 64
DATA = "f" * 64
OUTPUT = "1" * 64
CASE = "I02-254-charts"
PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic-bitmap-fixture-no-real-client-UI"


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class BrowserEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.lock = {
            "kind": "external_test_inputs_only",
            "source_revision": SRC, "release_id": "fixture-1",
            "payload_content_sha256": PAYLOAD,
            "provider_calls_executed": False, "runtime_evidence": "NOT_RUN",
            "cases": [{
                "case_id": CASE, "channel": "browser", "repetitions": 3,
                "input_sha256": INPUT, "rubric_sha256": RUBRIC,
            }],
        }
        self.observation = {
            "case_id": CASE, "attempt": 1, "channel": "browser",
            "source_revision": SRC, "release_id": "fixture-1",
            "payload_content_sha256": PAYLOAD,
            "input_sha256": INPUT, "rubric_sha256": RUBRIC,
            "execution_state": "executed", "decision": "REVIEW_REQUIRED",
            "observation_source": "synthetic reference ONLY - not verified provider",
            "approval_reference": "synthetic TEST-only fixture",
            "executor": "simulated-executor", "evaluator": "separate-simulated-reviewer",
            "observed_at": "2026-10-13T12:30:00+02:00",
            "correlation_id": "fixture-corr-123",
        }
        self.trace = {
            "case_id": CASE, "attempt": 1,
            "source_revision": SRC, "release_id": "fixture-1",
            "payload_content_sha256": PAYLOAD, "input_sha256": INPUT,
            "correlation_id": "fixture-corr-123",
            "tool_calls": [{
                "id": "call-1", "tool_name": "render_line_chart",
                "execution_state": "executed", "output_sha256": OUTPUT,
                "chart_payload_sha256": CHART, "normalized_data_sha256": DATA,
            }],
        }
        self.client = {
            "case_id": CASE, "attempt": 1,
            "source_revision": SRC, "release_id": "fixture-1",
            "payload_content_sha256": PAYLOAD, "input_sha256": INPUT,
            "correlation_id": "fixture-corr-123",
            "observed_tool_call_id": "call-1", "client_display_state": "observed",
            "accessible_text": "fixture title, negative zero positive values",
            "chart_payload_sha256": CHART, "normalized_data_sha256": DATA,
        }
        self.write_evidence()

    def store(self, rel, contents, *, raw=False):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        data = contents if raw else json.dumps(contents, sort_keys=True).encode("utf-8")
        path.write_bytes(data)
        return {"path": rel, "sha256": sha(data)}

    def write_evidence(self):
        self.observation["trace"] = self.store("trace.json", self.trace)
        self.observation["client"] = self.store("client.json", self.client)
        self.observation["capture"] = self.store("screen.png", PNG, raw=True)

    def check(self):
        return checker.validate(self.lock, [self.observation], self.root)

    def test_synthetic_consistent_receipt_remains_unverified(self):
        result = self.check()
        self.assertEqual("STRUCTURAL_EVIDENCE_REVIEW_REQUIRED", result["status"], result["errors"])
        self.assertEqual("NOT_VERIFIED", result["provider_authenticity"])
        self.assertEqual("NOT_PERFORMED", result["pixel_accessibility_inspection"])
        self.assertFalse(result["release_approved"])
        self.assertEqual("NOT_PERFORMED_BY_VALIDATOR", result["runtime_execution"])

    def test_empty_receipts_not_pass(self):
        result = checker.validate(self.lock, [], self.root)
        self.assertEqual("NO_EXECUTION_EVIDENCE", result["status"])

    def test_stale_site_source_or_release_fails(self):
        for field, value in [("source_revision", "0" * 40), ("release_id", "other")]:
            with self.subTest(field=field):
                self.observation[field] = value
                self.assertEqual("INVALID_EVIDENCE", self.check()["status"])
                self.observation[field] = self.lock[field]

    def test_wrong_tool_call_id_or_correlation_blocks(self):
        self.client["observed_tool_call_id"] = "unknown"
        self.write_evidence()
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])
        self.client["observed_tool_call_id"] = "call-1"
        self.client["correlation_id"] = "another-session"
        self.write_evidence()
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])

    def test_chart_data_mismatch_blocks(self):
        self.client["normalized_data_sha256"] = "0" * 64
        self.write_evidence()
        result = self.check()
        self.assertEqual("INVALID_EVIDENCE", result["status"])
        self.assertTrue(any("normalized data" in x for x in result["errors"]))

    def test_claimed_execution_without_steps_blocks(self):
        self.trace["tool_calls"] = []
        self.write_evidence()
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])

    def test_no_client_screenshot_or_bad_hash_blocks(self):
        os.unlink(self.root / "screen.png")
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])
        self.observation["capture"] = self.store("screen.png", b"not an image", raw=True)
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])
        self.write_evidence()
        self.observation["capture"]["sha256"] = "0" * 64
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])

    def test_symlink_and_outside_evidence_are_rejected(self):
        (self.root / "screen.png").unlink()
        other = self.root / "other.png"
        other.write_bytes(PNG)
        (self.root / "screen.png").symlink_to(other)
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])
        self.observation["capture"] = {"path": "../elsewhere.png", "sha256": sha(PNG)}
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])

    def test_queued_or_false_behavioral_pass_blocks(self):
        self.observation["execution_state"] = "awaiting_runner"
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])
        self.observation["execution_state"] = "executed"
        self.observation["decision"] = "PASS"
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])

    def test_approval_and_independent_evaluator_are_required(self):
        self.observation["approval_reference"] = ""
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])
        self.observation["approval_reference"] = "synthetic TEST fixture"
        self.observation["evaluator"] = self.observation["executor"]
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])

    def test_nonbrowser_lane_or_duplicate_attempt_blocks(self):
        self.lock["cases"][0]["channel"] = "desktop"
        self.observation["channel"] = "desktop"
        self.assertEqual("INVALID_EVIDENCE", self.check()["status"])
        self.lock["cases"][0]["channel"] = "browser"
        self.observation["channel"] = "browser"
        self.assertEqual("INVALID_EVIDENCE",
                         checker.validate(self.lock, [self.observation, copy.deepcopy(self.observation)], self.root)["status"])

    def test_route_only_site_may_have_no_chart_but_needs_screen_and_tool(self):
        self.lock["cases"][0].update(case_id="I02-149-cloud-e2e", channel="site")
        self.observation.update(case_id="I02-149-cloud-e2e", channel="site")
        self.trace["case_id"] = "I02-149-cloud-e2e"
        self.trace["tool_calls"][0].pop("chart_payload_sha256")
        self.trace["tool_calls"][0].pop("normalized_data_sha256")
        self.client["case_id"] = "I02-149-cloud-e2e"
        self.client.pop("chart_payload_sha256")
        self.client.pop("normalized_data_sha256")
        self.write_evidence()
        self.assertEqual("STRUCTURAL_EVIDENCE_REVIEW_REQUIRED", self.check()["status"])


if __name__ == "__main__":
    unittest.main()
