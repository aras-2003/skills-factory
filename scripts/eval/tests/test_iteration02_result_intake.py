from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "iteration02_result_intake.py"
spec = importlib.util.spec_from_file_location("iteration02_result_intake", PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)

SHA40 = "a" * 40
SHA64 = "b" * 64


def fixture():
    return {
        "source_revision": SHA40, "release_id": "candidate-fixture",
        "payload_content_sha256": SHA64,
        "runtime_execution_state": "NOT_RUN", "release_approved": False,
        "manual_gates": [{"id": "GATE-1", "status": "BLOCKED"}],
        "cases": [{
            "id": "I02-252-failure-flows", "channel": "lab", "repetitions": 2,
            "input_sha256": SHA64, "rubric_sha256": "c" * 64,
        }],
    }


def execution(decision="PASS", attempt=1):
    return {
        "case_id": "I02-252-failure-flows", "attempt": attempt,
        "source_revision": SHA40, "release_id": "candidate-fixture",
        "payload_content_sha256": SHA64,
        "input_sha256": SHA64, "rubric_sha256": "c" * 64,
        "channel": "lab", "execution_state": "executed", "decision": decision,
        "actual_output_sha256": SHA64,
        "tool_trace_sha256": SHA64,
        "evaluator_receipt_sha256": SHA64,
        "executor": "model-executor", "evaluator": "separate-reviewer",
        "assisted": False,
    }


class EvidenceIntakeTests(unittest.TestCase):
    def test_no_receipts_cannot_become_pass(self):
        result = module.assess(fixture(), [])
        self.assertEqual("NO_EXECUTION_RECEIPTS", result["status"])
        self.assertFalse(result["release_approved"])
        self.assertEqual(2, result["missing_attempts"])

    def test_one_attempt_is_incomplete(self):
        result = module.assess(fixture(), [execution()])
        self.assertEqual("INCOMPLETE", result["status"])
        self.assertEqual(1, result["missing_attempts"])

    def test_structural_receipts_still_need_independent_review(self):
        result = module.assess(fixture(), [execution(attempt=1), execution(attempt=2)])
        self.assertEqual("EVIDENCE_STRUCTURALLY_COMPLETE_REVIEW_REQUIRED", result["status"])
        self.assertEqual("NOT_VERIFIED", result["authentication"])
        self.assertFalse(result["release_approved"])

    def test_duplicate_attempt_fails_closed(self):
        result = module.assess(fixture(), [execution(), execution()])
        self.assertEqual("INVALID_RECEIPTS", result["status"])

    def test_stale_release_or_unmatched_rubric_fails(self):
        row = execution()
        row["rubric_sha256"] = "0" * 64
        self.assertEqual("INVALID_RECEIPTS", module.assess(fixture(), [row])["status"])

    def test_queued_job_cannot_pass(self):
        row = execution()
        row.update(execution_state="awaiting_runner", decision="PASS")
        result = module.assess(fixture(), [row])
        self.assertEqual("INVALID_RECEIPTS", result["status"])

    def test_assisted_or_self_evaluated_cannot_pass(self):
        row = execution()
        row["assisted"] = True
        self.assertEqual("INVALID_RECEIPTS", module.assess(fixture(), [row])["status"])
        row["assisted"] = False
        row["evaluator"] = row["executor"]
        self.assertEqual("INVALID_RECEIPTS", module.assess(fixture(), [row])["status"])

    def test_external_without_approval_or_chart_client_receipt_fails(self):
        lock = fixture()
        lock["cases"][0]["channel"] = "browser"
        lock["cases"][0]["id"] = "I02-254-charts"
        row = execution()
        row.update(case_id="I02-254-charts", channel="browser")
        self.assertEqual("INVALID_RECEIPTS", module.assess(lock, [row])["status"])
        row["approval_reference"] = "TEST-only permission"
        row["client_display_state"] = "observed"
        self.assertEqual("INCOMPLETE", module.assess(lock, [row])["status"])

    def test_malformed_unhashable_receipt_fields_fail_closed(self):
        for field, value in (
            ("decision", ["PASS"]),
            ("execution_state", ["executed"]),
            ("decision", {"PASS": True}),
        ):
            with self.subTest(field=field):
                row = execution()
                row[field] = value
                report = module.assess(fixture(), [row])
                self.assertEqual("INVALID_RECEIPTS", report["status"])
                self.assertFalse(report["release_approved"])

    def test_malformed_lock_channel_or_gate_does_not_crash(self):
        for key, value in (
            ("channel", ["lab"]),
            ("channel", {"name": "browser"}),
        ):
            with self.subTest(key=key):
                lock = fixture()
                lock["cases"][0][key] = value
                self.assertEqual("INVALID_RECEIPTS", module.assess(lock, [execution()])["status"])
        lock = fixture()
        lock["manual_gates"][0]["status"] = ["BLOCKED"]
        self.assertEqual("INVALID_RECEIPTS", module.assess(lock, [])["status"])

    def test_synthetic_fixture_is_not_proof(self):
        row = execution()
        row["synthetic_fixture"] = True
        self.assertEqual("INVALID_RECEIPTS", module.assess(fixture(), [row])["status"])


if __name__ == "__main__":
    unittest.main()
