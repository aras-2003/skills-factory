from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "skills/strategy-ea/value-realization"


class ValueRealizationCoverageTests(unittest.TestCase):
    def test_candidate_sources_are_hash_pinned_and_campaign_is_not_run(self):
        campaign = (ROOT / "evals/campaigns/value-realization-2026-10/campaign.yaml").read_text()
        self.assertIn("runtime_status: NOT_RUN", campaign)
        self.assertIn("release_approved: false", campaign)
        self.assertIn("provenance_status: VERIFIED_SOURCE_CORPUS", campaign)
        pins = dict(re.findall(r"^  (skills/strategy-ea/value-realization/[^:]+): ([a-f0-9]{64})$", campaign, re.M))
        expected = {
            "skills/strategy-ea/value-realization/SKILL.md",
            "skills/strategy-ea/value-realization/engine.py",
            "skills/strategy-ea/value-realization/tests/cases.yaml",
        }
        self.assertEqual(expected, set(pins))
        for relative, digest in pins.items():
            self.assertEqual(digest, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())

    def test_cases_cover_golden_negative_adversarial_and_regression(self):
        cases = (SOURCE / "tests/cases.yaml").read_text()
        for case_id in (
            "value-realization-golden", "value-realization-negative",
            "value-realization-adversarial", "value-realization-regression",
            "value-realization-near-miss-finance-model",
        ):
            self.assertIn(f"id: {case_id}", cases)
        for kind in ("golden", "negative", "adversarial", "regression", "near-miss"):
            self.assertIn(f"tags: [{kind}]", cases)
        self.assertIn("should_trigger: false", cases)

    def test_catalog_and_capability_contract_include_candidate(self):
        self.assertIn("| value-realization | strategy-ea | candidate | 0.1.0 |", (ROOT / "CATALOG.md").read_text())
        contract = (ROOT / "release/capability-contract.yaml").read_text()
        self.assertIn("value-realization:\n    source: skills/strategy-ea/value-realization/SKILL.md", contract)
        catalog = json.loads((ROOT / "docs/catalog.json").read_text())
        self.assertTrue(any(item.get("name") == "value-realization" for item in catalog["skills"]))

    def test_source_unit_suite_executes(self):
        spec = importlib.util.spec_from_file_location("value_realization_tests", SOURCE / "tests/test_engine.py")
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        outcome = unittest.TestResult()
        suite.run(outcome)
        self.assertEqual([], outcome.failures)
        self.assertEqual([], outcome.errors)
        self.assertEqual(9, outcome.testsRun)


if __name__ == "__main__":
    unittest.main()
