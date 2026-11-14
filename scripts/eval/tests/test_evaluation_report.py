"""Contract tests for Evaluation Report v1; all examples are synthetic."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/eval"))
import evaluation_report as report


class EvaluationReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads((ROOT / "scripts/eval/examples/evaluation-report-v1.json").read_text())

    def test_synthetic_example_is_valid_but_provisional(self):
        self.assertEqual([], report.validate_report(self.example))
        self.assertEqual("PROVISIONAL", self.example["score"]["status"])
        self.assertEqual("ITERATE", self.example["decision"]["status"])

    def test_schema_rejects_missing_required_and_unknown_properties(self):
        missing = copy.deepcopy(self.example)
        del missing["skill_id"]
        self.assertTrue(any("skill_id" in error for error in report.validate_report(missing)))
        invalid_path = ROOT / "scripts/eval/tests/fixtures/evaluation-report-invalid-unknown-field-v1.json"
        invalid = json.loads(invalid_path.read_text())
        self.assertTrue(report.validate_report(invalid))

    def test_weighted_assertions_and_half_up_rounding_are_deterministic(self):
        profile = {"profile_id":"p", "version":"1", "calibration_status":"VALIDATED",
                   "dimensions":[{"name":"quality","weight":100,"critical":True}],
                   "thresholds":{"pass_minimum":8.5,"critical_dimension_minimum":7,"reject_below":5}}
        assertions = [
            {"id":"a","dimension":"quality","case_id":"c","required":True,"importance":1,"execution_state":"executed","grade":1,"evidence_refs":["e"],"blocking_gate":False},
            {"id":"b","dimension":"quality","case_id":"c","required":True,"importance":1,"execution_state":"executed","grade":0.5,"evidence_refs":["e"],"blocking_gate":False},
        ]
        first = report.calculate_score(profile, assertions)
        second = report.calculate_score(profile, assertions)
        self.assertEqual(first, second)
        self.assertEqual(7.5, first["value"])
        self.assertEqual("ITERATE", first["decision"]["status"])

    def test_profile_weights_must_total_one_hundred(self):
        profile = copy.deepcopy(self.example["evaluation_profile"])
        profile["dimensions"][0]["weight"] -= 1
        with self.assertRaisesRegex(ValueError, "sum to 100"):
            report.calculate_score(profile, self.example["assertions"])

    def test_unexecuted_required_assertion_is_not_scorable(self):
        profile = copy.deepcopy(self.example["evaluation_profile"])
        assertions = copy.deepcopy(self.example["assertions"])
        assertions[0]["execution_state"] = "blocked"
        assertions[0]["grade"] = None
        score = report.calculate_score(profile, assertions)
        self.assertIsNone(score["value"])
        self.assertEqual("NOT_SCORABLE", score["status"])
        self.assertNotEqual("PASS", score["decision"]["status"])

    def test_failed_blocking_assertion_cannot_pass_high_score(self):
        profile = copy.deepcopy(self.example["evaluation_profile"])
        profile["calibration_status"] = "VALIDATED"
        assertions = copy.deepcopy(self.example["assertions"])
        assertions[0]["grade"] = 0
        assertions[0]["blocking_gate"] = True
        score = report.calculate_score(profile, assertions)
        self.assertEqual("REJECT", score["decision"]["status"])
        self.assertTrue(score["decision"]["blocking_gates"])

    def test_evidence_hash_mismatch_is_rejected(self):
        changed = copy.deepcopy(self.example)
        changed["evidence_receipts"][0]["sha256"] = "0" * 64
        self.assertTrue(any("SHA-256" in error for error in report.validate_report(changed)))

    def test_comparator_requires_matching_runtime_profile_evalset_and_final_score(self):
        candidate = copy.deepcopy(self.example)
        candidate["evaluation_profile"]["calibration_status"] = "VALIDATED"
        candidate["comparator"] = {
            "id":"base","version":"1","source_sha":"b"*40,"score":8.0,
            "profile_id":candidate["evaluation_profile"]["profile_id"],
            "profile_version":candidate["evaluation_profile"]["version"],
            "evalset_id":candidate["evalset"]["id"],"evalset_version":candidate["evalset"]["version"],
            "case_ids":[case["case_id"] for case in candidate["cases"]],
            "assertion_ids":[assertion["id"] for assertion in candidate["assertions"]],
            "runtime_identity":copy.deepcopy(candidate["runtime"]),"not_applicable_reason":None}
        candidate.update(report.calculate_report(candidate))
        self.assertEqual(2.0, candidate["comparison_delta"]["value"])
        candidate["comparator"]["runtime_identity"]["model_id"] = "different"
        candidate.update(report.calculate_report(candidate))
        self.assertIsNone(candidate["comparison_delta"]["value"])
        self.assertIn("Runtime/model/tool identity differs", candidate["comparison_delta"]["reason"])
        candidate["comparator"]["runtime_identity"] = copy.deepcopy(candidate["runtime"])
        candidate["comparator"]["assertion_ids"].pop()
        candidate.update(report.calculate_report(candidate))
        self.assertIsNone(candidate["comparison_delta"]["value"])
        self.assertIn("assertion identities differ", candidate["comparison_delta"]["reason"])


if __name__ == "__main__":
    unittest.main()
