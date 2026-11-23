from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from unittest.mock import patch
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

    def test_cov_01_rows_have_unique_stable_ids_and_source_hashes(self):
        report = self.check()
        ids = [row["stable_id"] for row in report["components"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(self.skills["total_skills"] + len(self.workflows["workflows"]), len(ids))
        self.assertTrue(all(row["source_sha256"] and row["fixture_case_ids"] is not None for row in report["components"]))

    def test_cov_02_duplicate_identity_blocks(self):
        data = copy.deepcopy(self.skills)
        data["skills"][1]["name"] = data["skills"][0]["name"]
        result = self.check(skills=data)
        self.assertEqual("BLOCKED_SOURCE", result["status"])
        self.assertTrue(any("duplicate" in error for error in result["errors"]))

    def test_cov_03_missing_workflow_fixture_is_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "workflows" / "sample" / "WORKFLOW.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Sample\n", encoding="utf-8")
            summary = mod._fixture_summary(root, "workflows/sample/WORKFLOW.md", "workflow", {})
            self.assertFalse(summary["declared"])
            self.assertEqual([], summary["case_ids"])

    def test_cov_04_recorded_pass_never_becomes_runtime_pass(self):
        name = self.skills["skills"][0]["name"]
        receipt = {"component": name, "case_id": "case-1", "receipt_path": "evals/results/x.json",
                   "receipt_sha256": "a" * 64, "receipt_validation": "PASS",
                   "recorded_status": "PASS", "component_identity_matches": True,
                   "compatibility": "NOT_VERIFIED"}
        with patch.object(mod, "_receipt_rows", return_value=[receipt]):
            report = self.check()
        row = next(item for item in report["components"] if item["name"] == name)
        self.assertEqual("NOT_VERIFIED", row["runtime_status"])
        self.assertEqual("PASS", row["evaluation_receipts"][0]["recorded_status"])
        self.assertEqual("NOT_VERIFIABLE_FROM_PUBLIC_INDEX", row["evidence_freshness"])

    def test_cov_05_old_source_identity_is_not_current_evidence(self):
        name = self.skills["skills"][0]["name"]
        receipt = {"component": name, "case_id": "case-1", "receipt_path": "evals/results/x.json",
                   "receipt_sha256": "b" * 64, "receipt_validation": "PASS",
                   "recorded_status": "PASS", "component_identity_matches": False,
                   "compatibility": "NOT_VERIFIED"}
        with patch.object(mod, "_receipt_rows", return_value=[receipt]):
            report = self.check()
        row = next(item for item in report["components"] if item["name"] == name)
        self.assertEqual("STALE_COMPONENT_IDENTITY", row["evidence_freshness"])
        self.assertEqual("NOT_VERIFIED", row["runtime_status"])

    def test_cov_06_dependency_graph_returns_transitive_consumers(self):
        graph = {"workflow:a": [{"target": "workflow:b", "evidence": "registry", "dependency": "required"}],
                 "workflow:b": [{"target": "skill:c", "evidence": "registry", "dependency": "required"}],
                 "skill:c": []}
        _, transitive = mod._consumer_maps(graph)
        self.assertEqual(["workflow:a", "workflow:b"], transitive["skill:c"])

    def test_cov_07_crosswalk_excludes_fixture_prompt_bodies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "skills" / "private" / "SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("---\nname: private\ndescription: private\n---\n", encoding="utf-8")
            (source.parent / "tests").mkdir()
            secret = "PRIVATE_PROMPT_SENTINEL_93812"
            (source.parent / "tests" / "cases.yaml").write_text(
                "cases:\n  - id: safe-id\n    input: " + secret + "\n    expected:\n      should_trigger: true\n", encoding="utf-8")
            summary = mod._fixture_summary(root, "skills/private/SKILL.md", "skill", {})
            self.assertEqual(["safe-id"], summary["case_ids"])
            self.assertNotIn(secret, json.dumps(summary))

    def test_cov_08_regeneration_is_deterministic(self):
        first, second = self.check(), self.check()
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_cov_09_count_drift_blocks_against_current_source_inventory(self):
        data = copy.deepcopy(self.skills)
        data["total_skills"] += 1
        result = self.check(skills=data)
        self.assertEqual("BLOCKED_SOURCE", result["status"])
        self.assertTrue(any("counts disagree" in error for error in result["errors"]))

    def test_cov_09_catalog_source_drift_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs" / "catalog.json").write_text(json.dumps({
                "skills": [{"name": "old", "source": "skills/old/SKILL.md"}],
                "workflows": [],
            }), encoding="utf-8")
            result = mod._catalog_drift(root,
                [{"name": "current", "source": "skills/current/SKILL.md"}],
                [{"name": "flow", "source": "workflows/flow/WORKFLOW.md"}])
            self.assertEqual("DRIFT", result["status"])
            self.assertEqual(["current:skills/current/SKILL.md"], result["inventories"]["skill"]["missing"])
            self.assertEqual(["old:skills/old/SKILL.md"], result["inventories"]["skill"]["extra"])

    def test_cov_03_reconciles_each_workflow_without_local_cases(self):
        report = self.check()
        rows = report["workflow_fixture_reconciliation"]
        self.assertEqual(9, len(rows))
        self.assertTrue(all(row["local_cases_yaml"] == "MISSING" for row in rows))
        self.assertTrue(all(row["follow_up_state"] in {"RECONCILIATION_REQUIRED", "CASE_DESIGN_REQUIRED"}
                            for row in rows))
        self.assertTrue(all(row["follow_up_action"] for row in rows))
        self.assertTrue(all(item.get("verification") == "UNVERIFIED_LEXICAL_CANDIDATE"
                            for row in rows for item in row["alternative_campaign_candidates"]))

    def test_cov_04_unresolved_dependency_edge_is_source_anchored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "skills").mkdir()
            workflow = root / "workflows" / "sample" / "WORKFLOW.md"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("# Sample\n", encoding="utf-8")
            (root / "workflows" / "runtime-registry.yaml").write_text(
                "workflows:\n  - name: sample\n    workflow: workflows/sample/WORKFLOW.md\n"
                "    dependencies:\n      required:\n        - name: missing-producer\n      optional: []\n", encoding="utf-8")
            graph, _ = mod._declared_graph(root)
            edge = graph["workflow:sample"][0]
            self.assertIsNone(edge["target"])
            self.assertEqual("missing-producer", edge["target_name"])
            self.assertEqual("UNKNOWN_TARGET", edge["edge_status"])
            self.assertTrue(edge["evidence"].startswith("workflows/runtime-registry.yaml#/"))

    def test_cov_04_unresolved_edge_marks_workflow_dependency_status_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflow_path = "workflows/sample/WORKFLOW.md"
            workflow = root / workflow_path
            workflow.parent.mkdir(parents=True)
            workflow.write_text("# Sample\n", encoding="utf-8")
            registry = root / "workflows/runtime-registry.yaml"
            registry.write_text(
                "workflows:\n  - name: sample\n    workflow: workflows/sample/WORKFLOW.md\n"
                "    dependencies:\n      required:\n        - name: missing-producer\n      optional: []\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs/catalog.json").write_text(json.dumps({"skills": [], "workflows": [
                {"name": "sample", "source": workflow_path}]}), encoding="utf-8")
            with patch.object(mod, "_receipt_rows", return_value=[]):
                report = mod.assess({"total_skills": 0, "skills": []}, {
                    "total": 1, "workflows": [{"name": "sample", "source": workflow_path,
                        "status": "REVIEW_REQUIRED", "local_test_suite_present": False,
                        "central_eval_case_count": 0}]}, root)
            row = next(item for item in report["components"] if item["stable_id"] == "workflow:sample")
            self.assertEqual("UNKNOWN", row["dependency_status"])
            self.assertIn("DEPENDENCY_TARGET_UNRESOLVED", row["evidence_gap"])

    def test_cov_06_affected_query_returns_regression_neighbors(self):
        report = {"components": [
            {"stable_id": "skill:producer", "source_path": "skills/producer/SKILL.md",
             "source_sha256": "a" * 64, "fixture_case_ids": ["producer-001"], "evidence_gap": [],
             "direct_consumers": [{"consumer": "workflow:middle"}],
             "transitive_consumers": ["workflow:middle", "workflow:outer"], "dependency_edges": []},
            {"stable_id": "workflow:middle", "fixture_case_ids": ["middle-001"], "evidence_gap": ["runtime gap"],
             "dependency_edges": []},
            {"stable_id": "workflow:outer", "fixture_case_ids": ["outer-001"], "evidence_gap": [],
             "dependency_edges": []},
        ]}
        result = mod._affected_query(report, "skill:producer")
        self.assertEqual("QUERY_COMPLETE", result["status"])
        self.assertEqual({"workflow:middle", "workflow:outer"},
                         {row["stable_id"] for row in result["regression_neighbors"]})
        middle = next(row for row in result["regression_neighbors"] if row["stable_id"] == "workflow:middle")
        self.assertEqual(["middle-001"], middle["fixture_case_ids"])
        self.assertEqual(["runtime gap"], middle["evidence_gap"])

    def test_cov_06_affected_query_fails_closed_for_unknown_id_or_edge(self):
        self.assertEqual("BLOCKED_UNKNOWN_COMPONENT", mod._affected_query({"components": []}, "skill:missing")["status"])
        report = {"components": [
            {"stable_id": "workflow:sample", "source_path": "workflows/sample/WORKFLOW.md",
             "source_sha256": "b" * 64, "fixture_case_ids": [], "evidence_gap": [],
             "direct_consumers": [], "transitive_consumers": [],
             "dependency_edges": [{"target": None, "target_name": "unknown", "edge_status": "UNKNOWN_TARGET",
                                    "evidence": "workflows/runtime-registry.yaml#/dependencies/required"}]},
        ]}
        result = mod._affected_query(report, "workflow:sample")
        self.assertEqual("BLOCKED_UNKNOWN_EDGES", result["status"])
        self.assertEqual("unknown", result["unresolved_edges"][0]["edge"]["target_name"])

    def test_cov_06_affected_query_blocks_global_unknown_edge_naming_changed_component(self):
        report = {"components": [
            {"stable_id": "skill:producer", "name": "producer", "source_path": "skills/producer/SKILL.md",
             "source_sha256": "c" * 64, "fixture_case_ids": [], "evidence_gap": [],
             "direct_consumers": [], "transitive_consumers": [], "dependency_edges": []},
            {"stable_id": "workflow:unrelated", "name": "unrelated", "fixture_case_ids": [],
             "evidence_gap": ["DEPENDENCY_TARGET_UNRESOLVED"], "direct_consumers": [],
             "transitive_consumers": [], "dependency_edges": [
                 {"target": None, "target_name": "producer", "edge_status": "UNKNOWN_TARGET",
                  "evidence": "workflows/runtime-registry.yaml#/workflows/dependencies/required"}]},
        ]}
        result = mod._affected_query(report, "skill:producer")
        self.assertEqual("BLOCKED_UNKNOWN_EDGES", result["status"])
        self.assertEqual("workflow:unrelated", result["unresolved_edges"][0]["consumer"])
        self.assertEqual("GLOBAL_GRAPH", result["unresolved_edges"][0]["scope"])
        self.assertEqual("producer", result["unresolved_edges"][0]["edge"]["target_name"])

    def test_cov_06_frequency_is_explicit_residual_blocker_without_numeric_score(self):
        report = self.check()
        self.assertEqual("EXECUTION_FREQUENCY_TELEMETRY_UNAVAILABLE",
                         report["gap_prioritization"]["residual_blocker"])
        self.assertTrue(all(row["execution_frequency"] == "UNKNOWN" and
                            row["priority"] == "UNRANKED_FREQUENCY_UNKNOWN"
                            for row in report["components"]))


if __name__ == "__main__":
    unittest.main()
