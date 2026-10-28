"""Execute the exact JSON supplied to the host by each positive runtime case."""

import importlib.util
import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def run_golden(name, case_id, entrypoint):
    source = ROOT / "skills/strategy-ea" / name
    cases = yaml.safe_load((source / "tests/cases.yaml").read_text())["cases"]
    case = next(case for case in cases if case["id"] == case_id)
    # Only the executor input carries the payload; expected output is never
    # used to supply missing data or to manufacture the calculator result.
    payload = json.loads(case["input"].split("Input JSON:\n", 1)[1])
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), source / "engine.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return getattr(module, entrypoint)(payload)


class StrategyGoldenInputTests(unittest.TestCase):
    def test_financial_golden_has_complete_evidence_and_calculates(self):
        result = run_golden("financial-modeling", "finance-npv-golden", "evaluate_model")
        self.assertEqual("4.13", result["npv"])

    def test_market_golden_has_complete_evidence_and_reconciles(self):
        result = run_golden("market-economics", "market-reconciliation-golden", "calculate")
        self.assertEqual("200", result["tam_difference"])
        self.assertEqual("100.00", result["segment_derived_sam"])
        self.assertEqual("80.00", result["uncovered_serviceable_value"])
        self.assertIsNone(result["validated_white_space"])

    def test_strategy_golden_has_complete_evidence_and_reconciles(self):
        result = run_golden("strategy-economics", "strategy-econ-profit-pool-golden", "calculate")
        self.assertEqual("300", result["profit_pool"]["total_revenue"])
        self.assertEqual("50", result["profit_pool"]["total_operating_profit"])
        self.assertTrue(result["pvm"]["reconciles"])

    def test_benefit_golden_has_sourced_thresholds_and_aligned_periods(self):
        result = run_golden("value-realization", "value-realization-golden", "evaluate_ledger")
        initiative = result["initiatives"][0]
        self.assertEqual("-200.00", initiative["benefits"][0]["periods"][0]["variance"])
        self.assertEqual("CORRECT_REVIEW", initiative["decision"]["action"])


if __name__ == "__main__":
    unittest.main()
