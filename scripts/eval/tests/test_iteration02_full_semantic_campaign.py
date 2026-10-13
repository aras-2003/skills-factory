from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

FILE = Path(__file__).resolve().parents[1] / "iteration02_full_semantic_campaign.py"
spec = importlib.util.spec_from_file_location("iteration02_full_semantic_campaign", FILE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)
SHA = "a" * 40


class FullSemanticCampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / "source"
        self.executor = self.home / "executor"
        self.evaluator = self.home / "evaluator"
        skill = self.root / "skills" / "sample"
        workflow = self.root / "workflows" / "sample-workflow"
        skill.mkdir(parents=True)
        workflow.mkdir(parents=True)
        (skill / "SKILL.md").write_text("# Fixture skill\n", encoding="utf-8")
        (workflow / "WORKFLOW.md").write_text("# Fixture workflow\n", encoding="utf-8")
        (self.root / "workflows" / "runtime-registry.yaml").write_text(
            yaml.safe_dump({"workflows": [{"name": "sample-workflow",
                                           "workflow": "workflows/sample-workflow/WORKFLOW.md"}]}),
            encoding="utf-8")
        for path in (skill, workflow):
            (path / "tests").mkdir()
            (path / "tests" / "cases.yaml").write_text(yaml.safe_dump({
                "cases": [
                    {"id": "positive", "input": "Use this tool for synthetic fixture.",
                     "expected": {"should_trigger": True, "must": ["synthetic"], "must_not": ["write"]}},
                    {"id": "negative", "input": "Unrelated synthetic user question.",
                     "expected": {"should_trigger": False, "must_not": ["trigger this"]}},
                ],
            }), encoding="utf-8")

    def freeze(self):
        return mod.freeze(self.root, self.executor, self.evaluator, SHA)

    def test_full_inventory_isolated_inputs_and_evaluator_rubrics(self):
        report = self.freeze()
        self.assertEqual("INPUTS_PREPARED_INDEPENDENT_REVIEW_REQUIRED", report["status"])
        self.assertEqual(1, report["skills"])
        self.assertEqual(1, report["workflows"])
        self.assertEqual(4, report["fixtures"])
        self.assertFalse(report["release_approved"])
        self.assertEqual("NOT_RUN", report["executor_runtime_state"])
        executor = (self.executor / "lock.json").read_text(encoding="utf-8")
        evaluator = (self.evaluator / "lock.json").read_text(encoding="utf-8")
        self.assertNotIn('"must":', executor)
        self.assertNotIn('"must_not":', executor)
        self.assertIn("rubric_path", evaluator)
        self.assertNotIn("rubric_path", executor)
        for row in report["cases"]:
            input_bytes = (self.executor / row["input_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(input_bytes).hexdigest(), row["input_sha256"])
            rubric = self.evaluator / "rubrics" / (row["case_id"] + ".json")
            self.assertEqual(hashlib.sha256(rubric.read_bytes()).hexdigest(),
                             row["rubric_sha256"])

    def test_refuse_overwrite_of_prior_attempt(self):
        self.freeze()
        with self.assertRaisesRegex(ValueError, "refuse overwrite"):
            self.freeze()

    def test_source_revision_and_output_isolation(self):
        with self.assertRaisesRegex(ValueError, "exact 40-digit"):
            mod.freeze(self.root, self.executor, self.evaluator, "not-a-SHA")
        with self.assertRaisesRegex(ValueError, "separate roots"):
            mod.freeze(self.root, self.executor, self.executor / "eval", SHA)

    def test_missing_workflow_suite_blocks_coverage_with_status(self):
        (self.root / "workflows/sample-workflow/tests/cases.yaml").unlink()
        out = self.freeze()
        self.assertEqual("SOURCE_FIXTURE_COVERAGE_INCOMPLETE", out["status"])
        self.assertEqual(1, len(out["missing_or_insufficient"]))
        self.assertEqual("workflow", out["missing_or_insufficient"][0]["kind"])

    def test_missing_polarity_reports_not_verified(self):
        path = self.root / "skills/sample/tests/cases.yaml"
        path.write_text(yaml.safe_dump({"cases": [{
            "id": "only-positive", "input": "Synthetic positive",
            "expected": {"should_trigger": True},
        }]}), encoding="utf-8")
        out = self.freeze()
        self.assertEqual("SOURCE_FIXTURE_COVERAGE_INCOMPLETE", out["status"])
        self.assertFalse(out["release_approved"])
        self.assertEqual("NOT_EVALUATED", out["model_behavior_verdict"])

    def test_malformed_fixture_fails_closed(self):
        path = self.root / "skills/sample/tests/cases.yaml"
        path.write_text("cases:\n - id: bad\n   input: Hello\n   expected: {must: [something]}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "polarity"):
            self.freeze()


if __name__ == "__main__":
    unittest.main()
