from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FILE = ROOT / "scripts/eval/iteration02_semantic_coverage.py"
spec = importlib.util.spec_from_file_location("iteration02_semantic_coverage", FILE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


class SemanticCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skills = mod.audit_skills(ROOT)
        cls.workflows = mod.audit_workflows(ROOT)

    def check(self, skills=None, workflows=None):
        return mod.assess(
            skills if skills is not None else copy.deepcopy(self.skills),
            workflows if workflows is not None else copy.deepcopy(self.workflows),
            ROOT,
        )

    def test_ledger_covers_current_skill_and_workflow_source_inventory(self):
        report = self.check()
        self.assertEqual("SOURCE_INVENTORY_REVIEW_REQUIRED", report["status"], report["errors"])
        self.assertEqual(self.skills["total_skills"], report["skill_count"])
        self.assertEqual(len(self.workflows["workflows"]), report["registered_workflow_count"])
        self.assertEqual(report["skill_count"] + report["registered_workflow_count"], len(report["components"]))
        self.assertEqual("NOT_RUN", report["runtime_execution"])
        self.assertFalse(report["model_behavior_verified"])
        self.assertFalse(report["release_approved"])
        self.assertEqual("NOT_RUN", report["independent_evaluation"])
        self.assertTrue(all(x["model_execution"] == "NOT_RUN" for x in report["components"]))
        self.assertTrue(all(x["source_sha256"] and len(x["source_sha256"]) == 64
                            for x in report["components"]))

    def test_missing_skill_source_blocks_not_silent_exclusion(self):
        report = copy.deepcopy(self.skills)
        report["skills"].pop()
        report["total_skills"] = len(report["skills"])
        result = self.check(skills=report)
        self.assertEqual("BLOCKED_SOURCE", result["status"])
        self.assertTrue(any("inventory incomplete" in x for x in result["errors"]))

    def test_duplicate_skill_identity_blocks(self):
        report = copy.deepcopy(self.skills)
        report["skills"][1]["name"] = report["skills"][0]["name"]
        result = self.check(skills=report)
        self.assertEqual("BLOCKED_SOURCE", result["status"])
        self.assertTrue(any("duplicate" in x for x in result["errors"]))

    def test_unsafe_path_never_read_and_blocks(self):
        report = copy.deepcopy(self.skills)
        report["skills"][0]["source"] = "/etc/passwd"
        result = self.check(skills=report)
        self.assertEqual("BLOCKED_SOURCE", result["status"])
        self.assertTrue(any("untrusted" in x for x in result["errors"]))
        self.assertIsNone(next(x for x in result["components"] if x["name"] ==
                               report["skills"][0]["name"])["source_sha256"])

    def test_missing_negative_routing_signalled_without_fake_fail(self):
        report = copy.deepcopy(self.skills)
        report["skills"][0]["negative_cases"] = 0
        result = self.check(skills=report)
        row = next(x for x in result["components"] if x["name"] == report["skills"][0]["name"])
        self.assertIn("NO_NEGATIVE_ROUTING_FIXTURE", row["review_signals"])
        self.assertEqual("NOT_VERIFIED", row["runtime_behavioral_acceptance"])

    def test_workflow_without_local_or_central_suite_is_review_signal(self):
        report = copy.deepcopy(self.workflows)
        report["workflows"][0]["local_test_suite_present"] = False
        report["workflows"][0]["central_eval_case_count"] = 0
        result = self.check(workflows=report)
        row = next(x for x in result["components"] if x["kind"] == "workflow" and
                   x["name"] == report["workflows"][0]["name"])
        self.assertIn("WORKFLOW_TEST_COVERAGE_NOT_LOCATED", row["review_signals"])
        self.assertEqual("NOT_RUN", row["model_execution"])

    def test_malformed_counts_fail_closed(self):
        report = copy.deepcopy(self.skills)
        report["skills"][0]["negative_cases"] = ["two"]
        self.assertEqual("BLOCKED_SOURCE", self.check(skills=report)["status"])

    def test_source_static_checks_ok_not_behavior_pass(self):
        report = copy.deepcopy(self.skills)
        report["skills"][0]["status"] = "STATIC_CHECKS_OK"
        result = self.check(skills=report)
        first = next(x for x in result["components"] if x["name"] == report["skills"][0]["name"])
        self.assertEqual("NOT_RUN", first["model_execution"])
        self.assertEqual("NOT_VERIFIED", first["runtime_behavioral_acceptance"])


if __name__ == "__main__":
    unittest.main()
