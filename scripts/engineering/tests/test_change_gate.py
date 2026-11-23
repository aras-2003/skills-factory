from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
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
        for impact, reviewed in [("UNKNOWN", True), ("A1", False), ("A3", True)]:
            with self.subTest(impact=impact, reviewed=reviewed):
                report = module.plan("RESOURCE", ["a.py"], architecture_impact=impact, graph_reviewed=reviewed)
                self.assertIn("full_affected_channel_baseline", report["required_checks"])
                self.assertEqual("UNKNOWN", report["dependency_graph_status"])
                self.assertFalse(report["dependency_graph_reviewed"])
                self.assertEqual(reviewed, report["dependency_graph_review_claimed"])

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

    def test_test_design_is_scoped_to_versioned_campaigns_and_not_runtime(self):
        report = module.plan("TEST_DESIGN", [
            "evals/campaigns/es08-integrated-validation-2026-11/acceptance-matrix.md"
        ], architecture_impact="A0")
        self.assertEqual("PLAN_READY", report["status"])
        self.assertEqual([
            "case_ids_and_expected_results_review",
            "coverage_and_channel_mapping_review",
            "evidence_identity_and_state_review",
        ], report["required_checks"])
        self.assertEqual("NOT_RUN", report["runtime_case_execution"])
        self.assertFalse(report["runtime_pass_claim"])
        self.assertFalse(report["release_authorized"])
        self.assertNotIn("full_affected_channel_baseline", report["required_checks"])

    def test_test_design_cannot_hide_product_changes_or_executable_test_files(self):
        for path in (
            "skills/meta/skill-test-design/SKILL.md",
            "evals/campaigns/new-campaign/runner.py",
            "docs/governance/SDLC-OPERATING-PROCESS.md",
        ):
            with self.subTest(path=path):
                report = module.plan("TEST_DESIGN", [path], architecture_impact="A0")
                self.assertEqual("BLOCKED", report["status"])
                self.assertTrue(report["blockers"])

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


class ChangeGateRevisionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
        self.git("init", "--quiet", "--template=")
        (self.root / "old-consumer.md").write_text("old", encoding="utf-8")
        self.base = self.commit("base")
        (self.root / "old-consumer.md").unlink()
        (self.root / "new-consumer.md").write_text("new", encoding="utf-8")
        self.source = self.commit("candidate")
        (self.root / "untracked.md").write_text("untracked", encoding="utf-8")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, env=self.env, text=True).strip()

    def commit(self, message):
        self.git("add", "-A")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.test", "commit", "--quiet", "-m", message)
        return self.git("rev-parse", "HEAD")

    def report(self, *args, expected_exit=0):
        result = subprocess.run(
            [sys.executable, str(TARGET), "--change-class", "RESOURCE", "--architecture-impact", "A3", *args],
            cwd=self.root, env=self.env, capture_output=True, text=True, check=False,
        )
        self.assertEqual(expected_exit, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_consumer_evidence_uses_the_selected_commit(self):
        report = self.report("--path", "changed.py", "--source-revision", self.base[:12], "--consumer", "old-consumer.md")
        self.assertEqual(self.base, report["source_revision"])
        self.assertEqual({
            "status": "PRESENT",
            "git_object_id": self.git("rev-parse", f"{self.base}:old-consumer.md"),
            "git_object_type": "blob",
            "git_mode": "100644",
        }, report["consumer_path_evidence"]["old-consumer.md"])

    def test_missing_or_untracked_consumer_cannot_claim_graph_completeness(self):
        report = self.report("--path", "changed.py", "--consumer", "missing.md", "--consumer", "untracked.md",
                             "--graph-reviewed", expected_exit=1)
        self.assertEqual("BLOCKED", report["status"])
        self.assertEqual(self.source, report["source_revision"])
        for path in ("missing.md", "untracked.md"):
            self.assertEqual({"status": "MISSING"}, report["consumer_path_evidence"][path])
            self.assertTrue(any(path in blocker for blocker in report["blockers"]))
        self.assertIn("full_affected_channel_baseline", report["required_checks"])

    def test_current_worktree_presence_does_not_validate_a_stale_source(self):
        report = self.report("--path", "changed.py", "--source-revision", self.base, "--consumer", "new-consumer.md",
                             expected_exit=1)
        self.assertEqual("BLOCKED", report["status"])
        self.assertEqual(self.base, report["source_revision"])
        self.assertEqual({"status": "MISSING"}, report["consumer_path_evidence"]["new-consumer.md"])

    def test_unresolvable_source_or_base_is_blocked(self):
        for label, args in (("source", ["--source-revision", "0" * 40, "--path", "changed.py"]),
                            ("base", ["--base-revision", "0" * 40])):
            with self.subTest(label=label):
                report = self.report(*args, expected_exit=1)
                self.assertEqual("BLOCKED", report["status"])
                self.assertEqual(None if label == "source" else self.source, report["source_revision"])
                self.assertTrue(any(f"{label} revision" in blocker for blocker in report["blockers"]))

    def test_matching_revision_aliases_use_the_exact_tree_for_full_source_plan(self):
        self.git("add", "untracked.md")
        report = self.report("--base-revision", self.source, "--source-revision", "HEAD", "--consumer", "new-consumer.md",
                             "--graph-reviewed")
        self.assertEqual(self.source, report["source_revision"])
        self.assertEqual(["new-consumer.md"], report["changed_files"])
        self.assertIn("full_affected_channel_baseline", report["required_checks"])

    def test_distinct_revisions_compute_the_diff_and_bind_consumer_evidence_to_source(self):
        report = self.report("--base-revision", "HEAD^", "--source-revision", self.source, "--consumer", "new-consumer.md")
        self.assertEqual(self.base, report["base_revision"])
        self.assertEqual(self.source, report["source_revision"])
        self.assertEqual(["new-consumer.md", "old-consumer.md"], report["changed_files"])
        self.assertEqual("PRESENT", report["consumer_path_evidence"]["new-consumer.md"]["status"])


if __name__ == "__main__":
    unittest.main()
