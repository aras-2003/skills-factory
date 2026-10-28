from __future__ import annotations
import hashlib
import importlib.util
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/"skills/strategy-ea/market-economics"

class MarketEconomicsCoverageTests(unittest.TestCase):
    def test_sources_are_hash_pinned_and_runtime_is_not_run(self):
        campaign=(ROOT/"evals/campaigns/market-economics-2026-10/campaign.yaml").read_text()
        self.assertIn("runtime_status: PASS",campaign)
        self.assertIn("runtime_bundle_sha256: 3136c6de1c156dde2eb799b114583e80a4372b73741947ba4ab8f966c5dba920",campaign)
        self.assertIn("source_references:",(SOURCE/"tests/cases.yaml").read_text())
        self.assertIn("884d0050b34d53dd07a3fb0b86f0068888f541aade9367c8e23af8bfaefb21f0",(SOURCE/"tests/cases.yaml").read_text())
        self.assertIn("provenance_status: VERIFIED_SOURCE_CORPUS",campaign)
        pins=dict(re.findall(r"^  (skills/strategy-ea/market-economics/[^:]+): ([a-f0-9]{64})$",campaign,re.M))
        self.assertEqual({"skills/strategy-ea/market-economics/SKILL.md","skills/strategy-ea/market-economics/engine.py","skills/strategy-ea/market-economics/tests/cases.yaml"},set(pins))
        for path,digest in pins.items(): self.assertEqual(digest,hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
    def test_behavior_fixture_has_required_case_classes(self):
        cases=(SOURCE/"tests/cases.yaml").read_text()
        for name in ("market-reconciliation-golden","market-missing-source-negative","market-transferability-adversarial","market-future-source-regression","market-competitor-near-miss"): self.assertIn(f"id: {name}",cases)
    def test_catalog_and_contract_declare_candidate(self):
        self.assertIn("| market-economics | strategy-ea | candidate | 0.1.0 |",(ROOT/"CATALOG.md").read_text())
        self.assertIn("source: skills/strategy-ea/market-economics/SKILL.md",(ROOT/"release/capability-contract.yaml").read_text())
        self.assertTrue(any(x.get("name")=="market-economics" for x in __import__("json").loads((ROOT/"docs/catalog.json").read_text())["skills"]))
    def test_unit_suite_executes(self):
        spec=importlib.util.spec_from_file_location("market_economics_tests",SOURCE/"tests/test_engine.py"); module=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module)
        suite=unittest.defaultTestLoader.loadTestsFromModule(module); result=unittest.TestResult(); suite.run(result)
        self.assertEqual([],result.errors); self.assertEqual([],result.failures); self.assertEqual(4,result.testsRun)

if __name__=="__main__": unittest.main()
