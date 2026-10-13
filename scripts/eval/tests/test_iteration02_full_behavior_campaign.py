from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

MODULE = Path(__file__).resolve().parents[1] / "iteration02_full_behavior_campaign.py"
spec = importlib.util.spec_from_file_location("iteration02_full_behavior_campaign", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

REV = "a" * 40


class FullBehaviorCampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "skills/career/example"
        self.workflow = self.root / "workflows/workflow-one"
        self.skill.mkdir(parents=True)
        self.workflow.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("# skill fixture\n", encoding="utf-8")
        (self.workflow / "WORKFLOW.md").write_text("# workflow fixture\n", encoding="utf-8")
        (self.skill / "tests").mkdir()
        self.skill_cases = [
            {"id": f"positive-{n}", "input": f"Positive synthetic {n}", "expected": {"should_trigger": True, "must": ["respond without writing"]}}
            for n in range(2)
        ] + [
            {"id": f"negative-{n}", "input": f"Wrong skill synthetic {n}", "expected": {"should_trigger": False, "must_not": ["execute wrong skill"]}}
            for n in range(2)
        ]
        self.save_skill()
        (self.root / "evals/test").mkdir(parents=True)
        (self.root / "evals/test/flow.input.md").write_text("Synthetic workflow request, read-only", encoding="utf-8")
        (self.root / "evals/test/flow.rubric.yaml").write_text(
            yaml.safe_dump({"must": ["honor workflow boundary"]}), encoding="utf-8")
        (self.root / "evals/runtime-fixtures.yaml").write_text(yaml.safe_dump({
            "targets": {"workflow-one": [{
                "id": "flow-central-positive", "input": "evals/test/flow.input.md",
                "rubric": "evals/test/flow.rubric.yaml",
            }]},
        }), encoding="utf-8")
        (self.root / "workflows/runtime-registry.yaml").write_text(yaml.safe_dump({
            "workflows": [{"name": "workflow-one", "workflow": "workflows/workflow-one/WORKFLOW.md"}],
        }), encoding="utf-8")
        self.audit_s = {"skills": [{"name": "example", "source": "skills/career/example/SKILL.md"}]}
        self.audit_w = {"workflows": [{"name": "workflow-one", "source": "workflows/workflow-one/WORKFLOW.md"}]}

    def save_skill(self):
        (self.skill / "tests/cases.yaml").write_text(
            yaml.safe_dump({"cases": self.skill_cases}, allow_unicode=True), encoding="utf-8")

    def build(self):
        with patch.object(mod, "audit_skills", return_value=self.audit_s), patch.object(
            mod, "audit_workflows", return_value=self.audit_w,
        ):
            return mod.build(self.root, REV)

    def test_full_source_campaign_reuses_real_prompts_and_separates_rubrics(self):
        report, executor, evaluator = self.build()
        self.assertEqual("INPUTS_READY_RUNTIME_NOT_RUN", report["status"], report["errors"])
        self.assertEqual(1, report["skill_count"])
        self.assertEqual(1, report["registered_workflow_count"])
        self.assertEqual(5, report["case_count"])
        self.assertEqual({x["key"] for x in executor}, {x["key"] for x in evaluator})
        self.assertTrue(all("expected" not in e for e in executor))
        self.assertTrue(all(e["execution_state"] == "NOT_RUN" for e in executor))
        self.assertTrue(all(e["evaluator_result"] == "NOT_RUN" for e in evaluator))
        self.assertFalse(report["release_approved"])

    def test_source_cases_are_rubric_pinned_not_contained_in_executor(self):
        report, executor, evaluator = self.build()
        keyed = {e["key"]: e for e in evaluator}
        for item in executor:
            rub = keyed[item["key"]]
            self.assertEqual(mod.digest(mod.canonical(rub["expected"])), item["rubric_sha256"])
            self.assertEqual(hashlib.sha256(item["input"].encode()).hexdigest(), item["input_sha256"])
            self.assertNotIn("expected", item)
            self.assertNotIn("rubric_source", item)

    def test_missing_workflow_fixture_fails_closed_instead_of_inventing_prompt(self):
        p = self.root / "evals/runtime-fixtures.yaml"
        p.write_text("targets: {}\n", encoding="utf-8")
        result, executor, _ = self.build()
        self.assertEqual("BLOCKED_SOURCE", result["status"])
        self.assertTrue(any("workflow/workflow-one" in e for e in result["errors"]))
        self.assertEqual(4, len(executor))

    def test_insufficient_routing_polarity_blocks(self):
        self.skill_cases = self.skill_cases[:2]
        self.save_skill()
        report, _, _ = self.build()
        self.assertEqual("BLOCKED_SOURCE", report["status"])
        self.assertTrue(any("polarity" in e for e in report["errors"]))

    def test_bad_or_duplicate_id_blocks(self):
        self.skill_cases.append(dict(self.skill_cases[0]))
        self.save_skill()
        report, _, _ = self.build()
        self.assertEqual("BLOCKED_SOURCE", report["status"])
        self.assertTrue(any("duplicate" in e for e in report["errors"]))

    def test_central_path_traversal_blocks(self):
        p = self.root / "evals/runtime-fixtures.yaml"
        p.write_text(yaml.safe_dump({"targets": {"workflow-one": [{
            "id": "wrong-path", "input": "../private.txt",
            "rubric": "evals/test/flow.rubric.yaml"}]}}), encoding="utf-8")
        report, _, _ = self.build()
        self.assertEqual("BLOCKED_SOURCE", report["status"])
        self.assertTrue(any("unsafe" in e for e in report["errors"]))

    def test_no_write_on_existing_archive(self):
        with patch.object(mod, "audit_skills", return_value=self.audit_s), patch.object(
            mod, "audit_workflows", return_value=self.audit_w,
        ):
            path = self.root / "result"
            report = mod.write_outputs(self.root, REV, path)
            self.assertEqual("INPUTS_READY_RUNTIME_NOT_RUN", report["status"])
            self.assertIn("executor-inputs.json", [x.name for x in path.iterdir()])
            raw = (path / "executor-inputs.json").read_text(encoding="utf-8")
            self.assertNotIn("respond without writing", raw.replace("Positive synthetic", ""))
            queue = json.loads((path / "executor-queue.json").read_text(encoding="utf-8"))
            self.assertEqual(report["case_count"], queue["case_count"])
            self.assertFalse(queue["writes_authorized"])
            self.assertEqual("NOT_RUN", queue["provider_execution"])
            for item in queue["cases"]:
                bytes_ = (path / item["input_path"]).read_bytes()
                self.assertEqual(hashlib.sha256(bytes_).hexdigest(), item["input_sha256"])
                self.assertFalse(item["provider_call_allowed"])
                self.assertFalse(item["writes_authorized"])
            self.assertEqual(len(list((path / "executor-cases").glob("*.input.md"))), report["case_count"])
            with self.assertRaisesRegex(ValueError, "exists"):
                mod.write_outputs(self.root, REV, path)

    def test_invalid_source_sha_fails(self):
        with self.assertRaisesRegex(ValueError, "40-hex"):
            mod.build(self.root, "main")


if __name__ == "__main__":
    unittest.main()
