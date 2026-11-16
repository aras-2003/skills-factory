from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "change_gate.py"
spec = importlib.util.spec_from_file_location("change_gate", TARGET)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class ChangeGateTests(unittest.TestCase):
    def test_architecture_level_expands_consumer_and_migration_checks(self):
        report = module.plan("RESOURCE", ["scripts/example.py"], architecture_impact="A3",
                             consumers=["workflows/example/WORKFLOW.md"], graph_reviewed=True)
        self.assertIn("architecture_approval", report["required_checks"])
        self.assertIn("consumer_contract_regressions", report["required_checks"])
        self.assertIn("migration_rollback_review", report["required_checks"])
        self.assertEqual(["workflows/example/WORKFLOW.md"], report["consumer_paths"])

    def test_unknown_impact_or_missing_dependency_review_never_narrows_baseline(self):
        for impact, reviewed in [("UNKNOWN", True), ("A1", False)]:
            report = module.plan("RESOURCE", ["a.py"], architecture_impact=impact, graph_reviewed=reviewed)
            self.assertIn("full_affected_channel_baseline", report["required_checks"])

    def test_low_architecture_level_does_not_bypass_security(self):
        report = module.plan("RESOURCE", ["a.py"], architecture_impact="A1", security_sensitive=True)
        self.assertIn("negative_authorization_and_data_safety_tests", report["required_checks"])
        self.assertIn("reviewer_other_than_author", report["required_checks"])
        self.assertFalse(report["release_authorized"])

    def test_a0_cannot_mask_runtime_and_unknown_levels_are_blocked(self):
        self.assertEqual("BLOCKED", module.plan("BEHAVIOR", ["a.py"], architecture_impact="A0")["status"])
        self.assertEqual("BLOCKED", module.plan("DOCS", ["README.md"], architecture_impact="LOW")["status"])

    def test_docs_only_requires_only_editorial_and_static_checks(self):
        report = module.plan("DOCS", ["README.md", "docs/roadmap/README.md"], architecture_impact="A0")
        self.assertEqual("PLAN_READY", report["status"])
        self.assertEqual(["documentation_diff_review", "static_document_validation"], report["required_checks"])
        self.assertEqual("NOT_RUN", report["runtime_case_execution"])
        self.assertFalse(report["runtime_pass_claim"])
        self.assertFalse(report["release_authorized"])

    def test_docs_class_cannot_hide_skill_or_workflow_contract_changes(self):
        for path in (
            "skills/meta/skill-test-design/SKILL.md",
            "skills/meta/skill-test-design/references/contracts.md",
            "workflows/skill-development/WORKFLOW.md",
            "scripts/eval/receipt.py",
            "release/capability-contract.yaml",
            "evals/routing/registry.yaml",
            "docs/catalog.json",
            "docs/governance/SDLC-OPERATING-PROCESS.md",
            "docs/TESTING.md",
            ".github/workflows/ci-validate.yml",
        ):
            with self.subTest(path=path):
                report = module.plan("DOCS", [path])
                self.assertEqual("BLOCKED", report["status"])
                self.assertTrue(report["blockers"])

    def test_docs_unknown_or_absent_path_is_not_assumed_safe(self):
        self.assertEqual("BLOCKED", module.plan("DOCS", [])["status"])
        for value in ("../README.md", "/tmp/x.md", "docs/../README.md", "docs\\README.md"):
            with self.subTest(path=value):
                self.assertEqual("BLOCKED", module.plan("DOCS", [value])["status"])

    def test_routing_requires_positive_near_miss_and_competitor(self):
        report = module.plan("ROUTING", ["skills/career/job-discovery/SKILL.md"])
        self.assertEqual("PLAN_READY", report["status"])
        self.assertIn("positive_indirect_near_miss_competing_routing", report["required_checks"])
        self.assertNotIn("behavioral_evals_and_regressions", report["required_checks"])

    def test_new_design_comes_before_new_skill_evaluation(self):
        report = module.plan("NEW", ["skills/meta/example/SKILL.md"])
        self.assertTrue(report["early_test_design_required"])
        self.assertLess(report["required_checks"].index("early_test_design"),
                        report["required_checks"].index("behavioral_evals_and_regressions"))

    def test_behavior_and_resource_are_not_routed_to_docs_only(self):
        for kind, check in (("BEHAVIOR", "behavioral_evals_and_regressions"),
                            ("RESOURCE", "resource_helper_unit_tests")):
            with self.subTest(kind=kind):
                report = module.plan(kind, ["skills/foo/SKILL.md"])
                self.assertEqual("PLAN_READY", report["status"])
                self.assertIn(check, report["required_checks"])
                self.assertEqual("NOT_RUN", report["runtime_case_execution"])

    def test_missing_architecture_impact_fails_closed(self):
        report = module.plan("RESOURCE", ["scripts/example.py"], architecture_impact=None)
        self.assertEqual("BLOCKED", report["status"])
        self.assertIn("Architecture Impact is required", report["blockers"][0])

    def test_deterministic_and_unknown_class_fails_closed(self):
        self.assertEqual(module.plan("RESOURCE", ["a", "b"]), module.plan("RESOURCE", ["a", "b"]))
        with self.assertRaises(ValueError):
            module.plan("PUBLISH", ["README.md"])


if __name__ == "__main__":
    unittest.main()
