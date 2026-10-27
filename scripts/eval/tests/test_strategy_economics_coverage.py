from __future__ import annotations
import hashlib, importlib.util, re, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; SOURCE=ROOT/"skills/strategy-ea/strategy-economics"
class StrategyEconomicsCoverageTests(unittest.TestCase):
    def test_candidate_is_hash_pinned_and_not_run(self):
        campaign=(ROOT/"evals/campaigns/strategy-economics-2026-10/campaign.yaml").read_text();self.assertIn("runtime_status: NOT_RUN",campaign);self.assertIn("provenance_status: BLOCKED_SOURCE_CORPUS",campaign)
        pins=dict(re.findall(r"^  (skills/strategy-ea/strategy-economics/[^:]+): ([a-f0-9]{64})$",campaign,re.M));self.assertEqual({"skills/strategy-ea/strategy-economics/SKILL.md","skills/strategy-ea/strategy-economics/engine.py","skills/strategy-ea/strategy-economics/tests/cases.yaml"},set(pins))
        for path,digest in pins.items():self.assertEqual(digest,hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
    def test_fixtures_cover_golden_negative_adversarial_regression(self):
        text=(SOURCE/"tests/cases.yaml").read_text()
        for name in ("strategy-econ-profit-pool-golden","strategy-econ-driver-reconcile-negative","strategy-econ-pvm-adversarial","strategy-econ-future-evidence-regression","strategy-econ-competitor-near-miss"):self.assertIn(f"id: {name}",text)
    def test_catalog_and_contract_declare_candidate(self):
        self.assertIn("| strategy-economics | strategy-ea | candidate | 0.1.0 |",(ROOT/"CATALOG.md").read_text());self.assertIn("source: skills/strategy-ea/strategy-economics/SKILL.md",(ROOT/"release/capability-contract.yaml").read_text());self.assertTrue(any(x.get("name")=="strategy-economics" for x in __import__("json").loads((ROOT/"docs/catalog.json").read_text())["skills"]))
    def test_unit_suite_executes(self):
        spec=importlib.util.spec_from_file_location("strategy_economics_tests",SOURCE/"tests/test_engine.py");module=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(module);suite=unittest.defaultTestLoader.loadTestsFromModule(module);result=unittest.TestResult();suite.run(result);self.assertEqual([],result.errors);self.assertEqual([],result.failures);self.assertEqual(4,result.testsRun)
if __name__=="__main__":unittest.main()
