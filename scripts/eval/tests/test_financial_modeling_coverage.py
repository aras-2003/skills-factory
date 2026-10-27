from __future__ import annotations

import hashlib
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "skills/strategy-ea/financial-modeling"


class FinancialModelingCoverageTests(unittest.TestCase):
    def test_candidate_source_and_behavior_suite_are_hash_pinned_not_run(self):
        campaign = (ROOT / "evals/campaigns/financial-modeling-2026-10/campaign.yaml").read_text()
        self.assertIn("campaign: financial-modeling-2026-10", campaign)
        self.assertIn("runtime_status: NOT_RUN", campaign)
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
        self.assertIn("| financial-modeling | strategy-ea | candidate | 0.1.0 |", (ROOT / "CATALOG.md").read_text())
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
