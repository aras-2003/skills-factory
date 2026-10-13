from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "iteration02_site_route_evidence.py"
spec = importlib.util.spec_from_file_location("iteration02_site_route_evidence", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

SRC = "a" * 40
PAYLOAD = "b" * 64
PROMPT = "c" * 64
RUBRIC = "d" * 64
CASE = "I02-149-cloud-e2e"
PNG = b"\x89PNG\r\n\x1a\nsynthetic-not-real-screenshot"


class SiteRouteEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lock = {
            "kind": "external_test_inputs_only",
            "source_revision": SRC, "release_id": "fixture-site-release",
            "payload_content_sha256": PAYLOAD,
            "runtime_evidence": "NOT_RUN", "provider_calls_executed": False,
            "cases": [{
                "case_id": CASE, "channel": "site", "repetitions": 3,
                "input_sha256": PROMPT, "rubric_sha256": RUBRIC,
            }],
        }
        common = {
            "case_id": CASE, "attempt": 1, "source_revision": SRC,
            "release_id": self.lock["release_id"],
            "payload_content_sha256": PAYLOAD,
            "input_sha256": PROMPT,
            "correlation_id": "synthetic-correlation",
        }
        self.capture = {
            **common,
            "channel": "site", "rubric_sha256": RUBRIC,
            "execution_state": "executed", "decision": "REVIEW_REQUIRED",
            "approval_reference": "synthetic TEST fixture only",
            "observation_source": "synthetic NOT provider-authenticated",
            "executor": "synthetic-executor",
            "evaluator": "distinct-synthetic-reviewer",
            "observed_at": "2026-10-13T12:00:00+02:00",
        }
        self.output = {
            **common,
            "selected_child": "synthetic-child",
            "child_execution": {"state": "not_executed", "steps": []},
        }
        self.client = {
            **common,
            "observed_tool_call_id": "call-123",
            "selected_child": "synthetic-child",
            "client_display_state": "observed",
            "accessible_text": "Synthetic route to child, not executed",
        }
        self.receipt = {
            **common,
            "tool_call_id": "call-123",
            "tool_call": {
                "id": "call-123", "tool_name": "route_synthetic_request",
                "execution_state": "executed", "output_sha256": "",
            },
        }
        self.write_artifacts()

    def bind(self, label: str, blob: bytes):
        p = self.root / (label + (".png" if label == "screenshot" else ".json"))
        p.write_bytes(blob)
        self.capture[label] = {
            "path": p.name, "sha256": hashlib.sha256(blob).hexdigest(),
        }

    def write_artifacts(self):
        self.bind("tool_output", json.dumps(self.output, sort_keys=True).encode())
        self.receipt["tool_call"]["output_sha256"] = self.capture["tool_output"]["sha256"]
        self.bind("tool_receipt", json.dumps(self.receipt, sort_keys=True).encode())
        self.bind("client_observation", json.dumps(self.client, sort_keys=True).encode())
        self.bind("screenshot", PNG)

    def evaluate(self):
        return mod.assess(self.lock, self.capture, self.root)

    def test_valid_synthetic_receipt_is_not_runtime_pass(self):
        report = self.evaluate()
        self.assertEqual("STRUCTURAL_REVIEW_REQUIRED", report["status"], report["errors"])
        self.assertEqual("NOT_AUTHENTICATED", report["provider_attestation"])
        self.assertEqual("NOT_EVALUATED", report["model_behavior_verdict"])
        self.assertFalse(report["release_approved"])

    def test_child_execution_must_be_explicitly_absent(self):
        self.output["child_execution"] = {"state": "executed", "steps": [{"tool": "write"}]}
        self.write_artifacts()
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])
        self.output.pop("child_execution")
        self.write_artifacts()
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])

    def test_changed_route_selection_blocks(self):
        self.client["selected_child"] = "other-workflow"
        self.write_artifacts()
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])

    def test_forged_call_correlation_blocks(self):
        self.client["observed_tool_call_id"] = "not-the-tool-call"
        self.write_artifacts()
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])
        self.client["observed_tool_call_id"] = "call-123"
        self.receipt["tool_call"]["id"] = "wrong"
        self.write_artifacts()
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])

    def test_missing_or_tampered_artifact_blocks(self):
        self.capture["tool_output"]["sha256"] = "f" * 64
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])
        self.write_artifacts()
        (self.root / "screenshot.png").unlink()
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])

    def test_no_approval_or_independent_evaluator_blocks(self):
        self.capture["approval_reference"] = ""
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])
        self.capture["approval_reference"] = "synthetic fixture"
        self.capture["evaluator"] = self.capture["executor"]
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])

    def test_stale_installed_identity_or_wrong_channel_blocks(self):
        self.capture["source_revision"] = "f" * 40
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])
        self.capture["source_revision"] = SRC
        self.lock["cases"][0]["channel"] = "production"
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])

    def test_nonexecuted_or_behavior_pass_cannot_be_claimed(self):
        self.capture["execution_state"] = "awaiting_runner"
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])
        self.capture["execution_state"] = "executed"
        self.capture["decision"] = "PASS"
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])

    def test_symlink_and_outside_evidence_block(self):
        self.capture["screenshot"]["path"] = "../outside.png"
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])
        self.write_artifacts()
        p = self.root / "screenshot.png"
        p.unlink()
        p.symlink_to(self.root / "tool_receipt.json")
        self.assertEqual("BLOCKED_EVIDENCE", self.evaluate()["status"])


if __name__ == "__main__":
    unittest.main()
