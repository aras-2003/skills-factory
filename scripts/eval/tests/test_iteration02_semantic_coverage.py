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

    def test_cov_08_ci_packages_the_generated_crosswalk_with_candidate_evidence(self):
        workflow = (ROOT / ".github/workflows/ci-validate.yml").read_text(encoding="utf-8")
        generation = workflow.index(
            "python scripts/eval/iteration02_semantic_coverage.py --output .tmp/sdlc/semantic-coverage.json")
        packaging = workflow.index("python scripts/eval/artifact_bundle.py pack --directory .tmp/sdlc")
        upload = workflow.index("name: sf-evidence-${{ env.SOURCE_REVISION }}")
        self.assertLess(generation, packaging)
        self.assertLess(packaging, upload)
        self.assertIn("path: .tmp/sdlc/", workflow[upload:])

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

    def test_cov_10_crosswalk_carries_safe_receipt_age_without_promotion(self):
        name = self.skills["skills"][0]["name"]
        receipt = {"component": name, "case_id": "case-1", "receipt_path": "evals/results/x.json",
                   "receipt_sha256": "a" * 64, "receipt_validation": "PASS",
                   "recorded_status": "NOT_RUN", "component_identity_matches": True,
                   "compatibility": "NOT_VERIFIED", "evaluation_timestamp_utc": "2026-11-20T12:00:00Z",
                   "age_days": 3.0, "age_state": "KNOWN", "age_as_of_utc": "2026-11-23T12:00:00Z",
                   "age_basis": "git_commit_committer_timestamp", "source_revision": "a" * 40,
                   "source_revision_state": "MISMATCH", "evidence_scope": "historical"}
        with patch.object(mod, "_receipt_rows", return_value=[receipt]):
            report = self.check()
        row = next(item for item in report["components"] if item["name"] == name)
        indexed = row["evaluation_receipts"][0]
        self.assertEqual(3.0, indexed["age_days"])
        self.assertEqual("MISMATCH", indexed["source_revision_state"])
        self.assertEqual("historical", indexed["evidence_scope"])
        self.assertEqual("NOT_VERIFIED", row["runtime_status"])
        self.assertEqual("NOT_RUN", row["behavior_status"])
        self.assertEqual("NOT_RUN", row["integration_status"])
        self.assertEqual("NOT_VERIFIABLE_FROM_PUBLIC_INDEX", row["evidence_freshness"])

    def test_cov_11_missing_receipt_keeps_unknown_evidence_and_not_run_states(self):
        with patch.object(mod, "_receipt_rows", return_value=[]):
            report = self.check()
        row = report["components"][0]
        self.assertEqual([], row["evaluation_receipts"])
        self.assertEqual("NO_RECEIPT", row["evidence_freshness"])
        self.assertEqual("NOT_VERIFIED", row["runtime_status"])
        self.assertEqual("NOT_RUN", row["behavior_status"])
        self.assertEqual("NOT_RUN", row["integration_status"])

    def test_cov_12_identity_mismatch_does_not_become_current_evidence(self):
        name = self.skills["skills"][0]["name"]
        receipt = {"component": name, "case_id": "case-1", "receipt_path": "evals/results/x.json",
                   "receipt_sha256": "b" * 64, "receipt_validation": "PASS",
                   "recorded_status": "PASS", "component_identity_matches": False,
                   "compatibility": "NOT_VERIFIED", "age_days": None,
                   "age_state": "AS_OF_UNAVAILABLE", "age_as_of_utc": None,
                   "age_basis": "CANDIDATE_COMMIT_TIME_UNAVAILABLE", "source_revision_state": "MISMATCH"}
        with patch.object(mod, "_receipt_rows", return_value=[receipt]):
            report = self.check()
        row = next(item for item in report["components"] if item["name"] == name)
        self.assertEqual("STALE_COMPONENT_IDENTITY", row["evidence_freshness"])
        self.assertEqual("NOT_VERIFIED", row["runtime_status"])
        self.assertIsNone(row["evaluation_receipts"][0]["age_days"])

    def test_cov_03_reconciles_missing_workflows_with_versioned_cases(self):
        report = self.check()
        rows = report["workflow_fixture_reconciliation"]
        self.assertEqual(9, len(rows))
        self.assertEqual([], report["errors"])
        self.assertEqual({"commerce-opportunity-review", "commerce-product-deep-dive",
                          "investment-portfolio-review", "investment-theme-discovery",
                          "oaf-enterprise-architecture-review", "oaf-enterprise-change-review",
                          "oaf-governance-redesign", "oaf-operating-model-redesign",
                          "oaf-transformation-design"}, {row["workflow_id"] for row in rows})
        self.assertTrue(all(row["local_cases_yaml"] == "PRESENT" for row in rows))
        self.assertTrue(all(row["follow_up_state"] == "RECONCILED_CASE_DESIGNED" for row in rows))
        self.assertTrue(all(row["new_design_case_ids"] for row in rows))
        self.assertTrue(all(len(row["local_case_ids"]) == 2 and len(row["negative_case_ids"]) == 1
                            for row in rows))
        self.assertTrue(all(row["owner"] != "UNKNOWN" and len(row["workflow_source_sha256"]) == 64
                            for row in rows))
        self.assertTrue(all(row["execution_state"] == "NOT_RUN" for row in rows))
        self.assertTrue(all(row["runtime_pass"] is False for row in rows))

    def test_cov_03_reconciliation_campaign_binds_exact_source_case_input_and_rubric(self):
        report = self.check()
        campaign = report["workflow_reconciliation_campaign"]
        self.assertEqual("TEST_DESIGN", campaign["kind"])
        self.assertEqual("NOT_RUN", campaign["runtime_execution"])
        self.assertEqual("d8498e8a7e9140971b67f3567b5094b97b751ff9", campaign["design_base_sha"])
        self.assertEqual(9, len(campaign["cases"]))
        self.assertEqual("NOT_RUN", report["independent_evaluation"])
        for case in campaign["cases"]:
            self.assertEqual("NOT_RUN", case["execution_state"])
            self.assertFalse(case["runtime_pass"])
            for digest_key in ("workflow_source_sha256", "case_file_sha256", "input_sha256", "rubric_sha256"):
                self.assertRegex(case[digest_key], r"^[0-9a-f]{64}$")

        by_workflow = {case["workflow_id"]: case for case in campaign["cases"]}
        governance = mod._read_yaml(ROOT / by_workflow["oaf-governance-redesign"]["rubric"])
        product = mod._read_yaml(ROOT / by_workflow["commerce-product-deep-dive"]["rubric"])
        architecture = mod._read_yaml(ROOT / by_workflow["oaf-enterprise-architecture-review"]["rubric"])
        governance_text = " ".join(governance["assertions"]["must"])
        product_text = " ".join(product["assertions"]["must"])
        architecture_text = " ".join(architecture["assertions"]["must"])
        self.assertIn("not authorize enterprise rollout before a bounded pilot", governance_text)
        self.assertIn("user-supplied 300 PLN cap", product_text)
        self.assertIn("KILL if the supplied differentiation failure condition occurs", product_text)
        self.assertIn("states the relevant route and why", architecture_text)
        self.assertIn("states portfolio implications", architecture_text)
        self.assertIn("names a specific next gate", architecture_text)

    def test_cov_03_reconciliation_campaign_rejects_malformed_design_base_pin(self):
        original_read_yaml = mod._read_yaml
        campaign_path = ROOT / "evals/campaigns/workflow-case-reconciliation-2026-11/campaign.yaml"

        def malformed_pin(path):
            data = original_read_yaml(path)
            if Path(path) == campaign_path:
                data["design_base_sha"] = "not-a-commit"
            return data

        with patch.object(mod, "_read_yaml", side_effect=malformed_pin):
            report = self.check()
        self.assertEqual("BLOCKED_SOURCE", report["status"])
        self.assertIn(
            "workflow reconciliation campaign must pin a full lowercase 40-character design_base_sha",
            report["errors"],
        )

    def test_cov_06_frequency_exposes_historical_receipt_lower_bound_without_ranking(self):
        report = self.check()
        components = report["components"]
        self.assertTrue(all(isinstance(row["historical_receipt_count_lower_bound"], int)
                            and row["historical_receipt_count_lower_bound"] >= 0 for row in components))
        self.assertTrue(all(row["execution_frequency"] == "UNKNOWN" and
                            row["priority"] == "UNRANKED_FREQUENCY_UNKNOWN" for row in components))

    def test_cov_03_component_task_owner_uses_existing_metadata(self):
        report = self.check()
        by_id = {row["stable_id"]: row for row in report["components"]}
        registry = mod._read_yaml(ROOT / "workflows/runtime-registry.yaml")
        workflow_metadata = {row["name"]: row.get("metadata", {})
                             for row in registry.get("workflows", []) if isinstance(row, dict)}

        for row in report["components"]:
            if row["kind"] == "skill":
                metadata = mod._source_metadata(ROOT, row["source_path"], "skill")["metadata"]
            else:
                metadata = workflow_metadata.get(row["name"], {})
            owner = metadata.get("owner") if isinstance(metadata, dict) else None
            expected = owner if isinstance(owner, str) and owner.strip() else "UNKNOWN"
            with self.subTest(stable_id=row["stable_id"]):
                self.assertEqual(expected, by_id[row["stable_id"]]["task_owner"])

    def test_cov_03_missing_workflow_cases_get_bounded_owner_pinned_request(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = "workflows/sample-flow/WORKFLOW.md"
            workflow = root / source
            workflow.parent.mkdir(parents=True)
            workflow.write_text("# Sample\n", encoding="utf-8")
            (root / "skills").mkdir()
            (root / "workflows/runtime-registry.yaml").write_text(
                "workflows:\n  - name: sample-flow\n    workflow: workflows/sample-flow/WORKFLOW.md\n"
                "    metadata:\n      owner: team-workflows\n"
                "    dependencies:\n      required: []\n      optional: []\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs/catalog.json").write_text(json.dumps({"skills": [], "workflows": [
                {"name": "sample-flow", "source": source}]}), encoding="utf-8")
            (root / "evals").mkdir()
            (root / "evals/runtime-fixtures.yaml").write_text("targets: {}\n", encoding="utf-8")

            with patch.object(mod, "_receipt_rows", return_value=[]):
                report = mod.assess({"total_skills": 0, "skills": []}, {
                    "total": 1, "workflows": [{"name": "sample-flow", "source": source,
                        "status": "REVIEW_REQUIRED", "local_test_suite_present": False,
                        "central_eval_case_count": 0}]}, root)

        row = report["workflow_fixture_reconciliation"][0]
        request = row["case_design_request"]
        self.assertEqual("team-workflows", row["owner"])
        self.assertEqual("team-workflows", request["owner"])
        self.assertEqual(source, request["workflow_source"])
        self.assertEqual(row["workflow_source_sha256"], request["workflow_source_sha256"])
        self.assertEqual("workflows/sample-flow/tests/cases.yaml", request["case_file"])
        self.assertEqual(3, request["max_case_ids"])
        self.assertEqual([], request["case_ids"])
        self.assertEqual(["PRIMARY_PATH", "HIGHEST_RISK_NEGATIVE_OR_MISSING_EVIDENCE"],
                         request["required_scenarios"])
        self.assertEqual("NOT_RUN", request["execution_state"])
        self.assertTrue(request["defined_cases_are_not_executed"])

    def test_cov_03_missing_or_non_text_owner_is_unknown(self):
        self.assertEqual("UNKNOWN", mod._task_owner({}))
        self.assertEqual("UNKNOWN", mod._task_owner({"owner": "  "}))
        self.assertEqual("UNKNOWN", mod._task_owner({"owner": 42}))

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

    def test_cov_04_workflow_skill_mentions_are_unverified_consumer_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "skills" / "sample-skill" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: sample-skill\ndescription: test\n---\n", encoding="utf-8")
            workflow = root / "workflows" / "sample-flow" / "WORKFLOW.md"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(
                "Use `sample-skill` when the request meets its trigger.\n", encoding="utf-8")
            (root / "workflows" / "runtime-registry.yaml").write_text(
                "workflows:\n  - name: sample-flow\n    workflow: workflows/sample-flow/WORKFLOW.md\n"
                "    dependencies:\n      required: []\n      optional: []\n", encoding="utf-8")

            graph, _ = mod._declared_graph(root)
            edge = graph["workflow:sample-flow"][0]
            self.assertIsNone(edge["target"])
            self.assertEqual("sample-skill", edge["target_name"])
            self.assertEqual("UNVERIFIED_SOURCE_REFERENCE", edge["edge_status"])
            self.assertEqual("workflows/sample-flow/WORKFLOW.md#L1", edge["evidence"])

            report = {"components": [
                {"stable_id": "skill:sample-skill", "dependency_edges": [],
                 "direct_consumers": [], "transitive_consumers": []},
                {"stable_id": "workflow:sample-flow", "dependency_edges": [edge],
                 "direct_consumers": [], "transitive_consumers": []},
            ], "source_revision": "a" * 40, "crosswalk_sha256": "b" * 64,
                "worktree_state": "CLEAN_CHECKOUT"}
            query = mod._affected_query(report, "skill:sample-skill")
            self.assertEqual("BLOCKED_UNKNOWN_EDGES", query["status"])
            self.assertEqual("a" * 40, query["source_revision"])
            self.assertEqual("b" * 64, query["crosswalk_sha256"])
            self.assertEqual("CLEAN_CHECKOUT", query["worktree_state"])
            self.assertEqual(["workflow:sample-flow"],
                             [item["stable_id"] for item in query["unverified_consumer_candidates"]])
            self.assertEqual([edge], [item["edge"] for item in query["unresolved_edges"]])

    def test_cov_04_plain_text_skill_reference_is_unverified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "skills" / "position-sizing-review" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: position-sizing-review\ndescription: test\n---\n", encoding="utf-8")
            workflow = root / "workflows" / "sample-flow" / "WORKFLOW.md"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(
                "For sizing, consult position-sizing-review when applicable.\n", encoding="utf-8")
            (root / "workflows" / "runtime-registry.yaml").write_text(
                "workflows:\n  - name: sample-flow\n    workflow: workflows/sample-flow/WORKFLOW.md\n"
                "    dependencies:\n      required: []\n      optional: []\n", encoding="utf-8")
            graph, _ = mod._declared_graph(root)
            edge = graph["workflow:sample-flow"][0]
            self.assertEqual("position-sizing-review", edge["target_name"])
            self.assertEqual("UNVERIFIED_SOURCE_REFERENCE", edge["edge_status"])
            self.assertEqual("workflows/sample-flow/WORKFLOW.md#L1", edge["evidence"])

    def test_cov_04_malformed_dependency_buckets_are_preserved_as_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflow = root / "workflows" / "sample" / "WORKFLOW.md"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("# Sample\n", encoding="utf-8")
            (root / "workflows" / "runtime-registry.yaml").write_text(
                "workflows:\n  - name: sample\n    workflow: workflows/sample/WORKFLOW.md\n"
                "    dependencies:\n      required: malformed\n      optional: {}\n", encoding="utf-8")
            graph, _ = mod._declared_graph(root)
            edges = graph["workflow:sample"]
            self.assertEqual({"required", "optional"}, {edge["dependency"] for edge in edges})
            self.assertTrue(all(edge["edge_status"] == "MALFORMED_BUCKET" for edge in edges))

    def test_cov_04_mixed_malformed_and_unknown_refs_sort_safely(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflow = root / "workflows" / "sample" / "WORKFLOW.md"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("# Sample\n", encoding="utf-8")
            (root / "workflows" / "runtime-registry.yaml").write_text(
                "workflows:\n  - name: sample\n    workflow: workflows/sample/WORKFLOW.md\n"
                "    dependencies:\n      required: [9, missing-producer]\n      optional: []\n",
                encoding="utf-8",
            )
            graph, _ = mod._declared_graph(root)
            edges = graph["workflow:sample"]
            self.assertEqual(["MALFORMED_REFERENCE", "UNKNOWN_TARGET"],
                             [edge["edge_status"] for edge in edges])
            self.assertTrue(all(edge["evidence"].startswith("workflows/runtime-registry.yaml#/") for edge in edges))

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
        ], "worktree_state": "CLEAN_CHECKOUT", "source_revision": "c" * 40,
            "crosswalk_sha256": "d" * 64}
        result = mod._affected_query(report, "skill:producer")
        self.assertEqual("QUERY_COMPLETE", result["status"])
        self.assertEqual("CLEAN_CHECKOUT", result["worktree_state"])
        self.assertEqual({"workflow:middle", "workflow:outer"},
                         {row["stable_id"] for row in result["regression_neighbors"]})
        middle = next(row for row in result["regression_neighbors"] if row["stable_id"] == "workflow:middle")
        self.assertEqual(["middle-001"], middle["fixture_case_ids"])
        self.assertEqual(["runtime gap"], middle["evidence_gap"])

    def test_cov_06_affected_query_fails_closed_for_unknown_id_or_edge(self):
        self.assertEqual("BLOCKED_UNKNOWN_COMPONENT", mod._affected_query(
            {"components": [], "worktree_state": "CLEAN_CHECKOUT"}, "skill:missing")["status"])
        report = {"components": [
            {"stable_id": "workflow:sample", "source_path": "workflows/sample/WORKFLOW.md",
             "source_sha256": "b" * 64, "fixture_case_ids": [], "evidence_gap": [],
             "direct_consumers": [], "transitive_consumers": [],
             "dependency_edges": [{"target": None, "target_name": "unknown", "edge_status": "UNKNOWN_TARGET",
                                    "evidence": "workflows/runtime-registry.yaml#/dependencies/required"}]},
        ], "worktree_state": "CLEAN_CHECKOUT"}
        result = mod._affected_query(report, "workflow:sample")
        self.assertEqual("BLOCKED_UNKNOWN_EDGES", result["status"])
        self.assertEqual("unknown", result["unresolved_edges"][0]["edge"]["target_name"])

    def test_cov_06_affected_query_fails_closed_for_blocked_source_or_errors(self):
        partial = {"status": "BLOCKED_SOURCE", "errors": ["incomplete inventory"], "components": [
            {"stable_id": "skill:producer", "direct_consumers": [{"consumer": "workflow:known"}],
             "transitive_consumers": ["workflow:known"], "dependency_edges": []},
            {"stable_id": "workflow:known", "fixture_case_ids": ["case-1"], "dependency_edges": []},
        ]}
        by_status = mod._affected_query(partial, "skill:producer")
        self.assertEqual("BLOCKED_SOURCE", by_status["status"])
        self.assertEqual([], by_status["regression_neighbors"])
        partial["status"] = "SOURCE_INVENTORY_REVIEW_REQUIRED"
        by_errors = mod._affected_query(partial, "skill:producer")
        self.assertEqual("BLOCKED_SOURCE", by_errors["status"])
        self.assertEqual(["incomplete inventory"], by_errors["source_errors"])

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
        ], "worktree_state": "CLEAN_CHECKOUT"}
        result = mod._affected_query(report, "skill:producer")
        self.assertEqual("BLOCKED_UNKNOWN_EDGES", result["status"])
        self.assertEqual("workflow:unrelated", result["unresolved_edges"][0]["consumer"])
        self.assertEqual("GLOBAL_GRAPH", result["unresolved_edges"][0]["scope"])
        self.assertEqual("producer", result["unresolved_edges"][0]["edge"]["target_name"])

    def test_cov_06_affected_query_blocks_dirty_or_unattested_worktree(self):
        report = {"status": "SOURCE_INVENTORY_REVIEW_REQUIRED", "errors": [],
                  "source_revision": "e" * 40, "crosswalk_sha256": "f" * 64,
                  "components": [{"stable_id": "skill:producer", "name": "producer",
                                  "direct_consumers": [], "transitive_consumers": [],
                                  "dependency_edges": []}]}
        for worktree_state in ("WORKTREE_DIRTY", "LOCAL_CHECKOUT_UNATTESTED", "REVISION_UNAVAILABLE", None):
            with self.subTest(worktree_state=worktree_state):
                candidate = {**report, "worktree_state": worktree_state}
                result = mod._affected_query(candidate, "skill:producer")
                self.assertEqual("BLOCKED_WORKTREE_STATE", result["status"])
                self.assertEqual(worktree_state, result["worktree_state"])
                self.assertEqual([], result["regression_neighbors"])

    def test_cov_06_frequency_is_explicit_residual_blocker_without_numeric_score(self):
        report = self.check()
        self.assertEqual("EXECUTION_FREQUENCY_TELEMETRY_UNAVAILABLE",
                         report["gap_prioritization"]["residual_blocker"])
        self.assertTrue(all(row["execution_frequency"] == "UNKNOWN" and
                            row["priority"] == "UNRANKED_FREQUENCY_UNKNOWN"
                            for row in report["components"]))


if __name__ == "__main__":
    unittest.main()
