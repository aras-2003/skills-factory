from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "skills/strategy-ea/financial-modeling"


class FinancialModelingCoverageTests(unittest.TestCase):
    def test_candidate_source_and_behavior_suite_are_hash_pinned_and_runtime_verified(self):
        campaign = (ROOT / "evals/campaigns/financial-modeling-2026-10/campaign.yaml").read_text()
        self.assertIn("campaign: financial-modeling-2026-10", campaign)
        self.assertIn("runtime_status: PASS", campaign)
        self.assertIn("result_record: evals/results/financial-modeling-2026-10/2026-10-28-site-runtime/run.json", campaign)
        self.assertIn("release_approved: false", campaign)
        self.assertIn("provenance_status: VERIFIED_SOURCE_CORPUS", campaign)
        pins = dict(re.findall(r"^  (skills/strategy-ea/financial-modeling/[^:]+): ([a-f0-9]{64})$", campaign, re.M))
        expected = {
            "skills/strategy-ea/financial-modeling/SKILL.md",
            "skills/strategy-ea/financial-modeling/engine.py",
            "skills/strategy-ea/financial-modeling/tests/cases.yaml",
        }
        self.assertEqual(expected, set(pins))
        for relative, digest in pins.items():
            self.assertEqual(digest, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())

    def test_runtime_campaign_record_covers_all_required_cases_and_output_hashes(self):
        campaign = (ROOT / "evals/campaigns/financial-modeling-2026-10/campaign.yaml").read_text()
        result_record = re.search(r"^result_record: (\S+)$", campaign, re.M)
        self.assertIsNotNone(result_record)
        report_path = ROOT / result_record.group(1)
        report = json.loads(report_path.read_text())
        required_block = campaign.split("required_case_ids:", 1)[1].split("test_modules:", 1)[0]
        required = set(re.findall(r"^  - ([a-z0-9-]+)$", required_block, re.M))
        recorded = {item["case_id"]: item for item in report["cases"]}
        self.assertEqual(required, set(recorded))
        self.assertTrue(all(item["result"] == "PASS" for item in recorded.values()))
        for item in recorded.values():
            output = report_path.parent / item["executor_output"]
            self.assertEqual(item["output_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
        engine = report_path.parent / report["engine_execution"]["exact_mcp_reference_file"]
        self.assertEqual(report["engine_execution"]["engine_sha256"], hashlib.sha256(engine.read_bytes()).hexdigest())
        self.assertEqual(report["engine_execution"]["expected_source_sha256"], hashlib.sha256((SOURCE / "engine.py").read_bytes()).hexdigest())
        self.assertEqual(0, report["engine_execution"]["exit_code"])
        self.assertEqual("4.13", report["engine_execution"]["npv"])

    def test_case_suite_contains_golden_negative_adversarial_regression(self):
        cases = (SOURCE / "tests/cases.yaml").read_text()
        for case_id in (
            "finance-npv-golden", "finance-provenance-negative",
            "finance-lookahead-adversarial", "finance-scenario-weights-regression",
            "finance-near-miss-report-format",
        ):
            self.assertIn(f"id: {case_id}", cases)
        self.assertIn("should_trigger: false", cases)
        self.assertIn("should_trigger: true", cases)

    def test_catalog_and_capability_declaration_reference_candidate(self):
        skill = (SOURCE / "SKILL.md").read_text()
        self.assertIn("name: financial-modeling", skill)
        self.assertIn("source: skills/strategy-ea/financial-modeling/SKILL.md", (ROOT / "release/capability-contract.yaml").read_text())
        self.assertIn("| financial-modeling | strategy-ea | candidate | 0.1.1 |", (ROOT / "CATALOG.md").read_text())
        self.assertTrue(any(item.get("name") == "financial-modeling" for item in __import__("json").loads((ROOT / "docs/catalog.json").read_text())["skills"]))

    def test_source_unit_suite_executes(self):
        spec = importlib.util.spec_from_file_location("financial_model_tests", SOURCE / "tests/test_engine.py")
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        outcome = unittest.TestResult()
        suite.run(outcome)
        self.assertEqual([], outcome.failures)
        self.assertEqual([], outcome.errors)
        self.assertEqual(13, outcome.testsRun)


if __name__ == "__main__":
    unittest.main()
