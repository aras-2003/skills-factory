from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from decimal import Decimal
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "engine.py"
spec = importlib.util.spec_from_file_location("strategy_financial_model", MODULE)
model = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(model)


def evidence(value, source_id, date="2026-01-01"):
    return {"value": str(value), "source_id": source_id, "published_at": date}


def base():
    return {
        "currency": "USD",
        "as_of": "2026-01-31",
        "discount_rate": evidence("0.10", "approved-wacc"),
        "cash_flows": [
            {"period": 0, **evidence("-100", "initial-investment")},
            {"period": 1, **evidence("60", "year-1-cash-flow")},
            {"period": 2, **evidence("60", "year-2-cash-flow")},
        ],
    }


class FinancialModelTests(unittest.TestCase):
    def test_npv_known_answer_includes_period_zero(self):
        result = model.evaluate_model(base())
        self.assertEqual("CALCULATED", result["status"])
        self.assertEqual("4.13", result["npv"])
        self.assertFalse(result["statistical_or_outcome_probability_claimed"])

    def test_irr_known_answer(self):
        result = model.evaluate_model(base())
        self.assertAlmostEqual(Decimal("0.130662386"), Decimal(result["irr"]), places=8)

    def test_simple_and_discounted_payback_are_explicit(self):
        result = model.evaluate_model(base())
        self.assertEqual("1.666666666666666666666666667", result["simple_payback_periods"])
        self.assertEqual("1.916666666666666666666666666", result["discounted_payback_periods"])

    def test_gordon_growth_dcf_and_irr_include_terminal_value(self):
        data = base()
        data["terminal_growth"] = evidence("0.02", "approved-terminal-growth")
        result = model.evaluate_model(data)
        self.assertEqual("765.00", result["terminal_value"]["undiscounted"])
        self.assertGreater(Decimal(result["npv"]), Decimal("4.13"))
        self.assertGreater(Decimal(result["irr"]), Decimal("0.13"))

    def test_scenario_weighted_value_is_explicit_and_not_called_probability(self):
        data = base()
        data["scenarios"] = [
            {"name": "downside", "weight": evidence("0.25", "scenario-weights"), "cash_flows": [
                {"period": 0, **evidence("-100", "down-0")},
                {"period": 1, **evidence("20", "down-1")},
                {"period": 2, **evidence("20", "down-2")},
            ]},
            {"name": "base", "weight": evidence("0.75", "scenario-weights"), "cash_flows": [
                {"period": 0, **evidence("-100", "base-0")},
                {"period": 1, **evidence("60", "base-1")},
                {"period": 2, **evidence("60", "base-2")},
            ]},
        ]
        result = model.evaluate_model(data)
        self.assertEqual("explicitly weighted scenario NPV", result["risk_adjusted_value"]["method"])
        self.assertFalse(result["risk_adjusted_value"]["weights_are_calibrated_probabilities"])
        self.assertEqual("0.25", result["scenarios"][0]["weight"])

    def test_sensitivity_uses_only_explicit_user_values(self):
        data = base()
        data["sensitivity"] = {"discount_rates": [
            evidence("0.08", "low-rate"), evidence("0.10", "base-rate"), evidence("0.12", "high-rate")
        ]}
        result = model.evaluate_model(data)
        self.assertEqual(["0.08", "0.10", "0.12"], [row["discount_rate"]["value"] for row in result["sensitivity"]])
        self.assertEqual("high-rate", result["sensitivity"][2]["discount_rate"]["source_id"])

    def test_future_dated_sensitivity_assumption_is_rejected(self):
        data = base()
        data["sensitivity"] = {"discount_rates": [evidence("0.12", "future-rate", "2026-02-01")]}
        with self.assertRaisesRegex(model.ModelInputError, "future-dated"):
            model.evaluate_model(data)

    def test_future_dated_source_is_rejected(self):
        data = base()
        data["cash_flows"][1]["published_at"] = "2026-02-01"
        with self.assertRaisesRegex(model.ModelInputError, "future-dated"):
            model.evaluate_model(data)

    def test_missing_provenance_and_noncontiguous_periods_are_rejected(self):
        data = base()
        del data["cash_flows"][1]["source_id"]
        with self.assertRaisesRegex(model.ModelInputError, "source_id"):
            model.evaluate_model(data)
        data = base()
        data["cash_flows"][1]["period"] = 3
        with self.assertRaisesRegex(model.ModelInputError, "contiguous"):
            model.evaluate_model(data)

    def test_terminal_growth_must_be_below_discount_rate(self):
        data = base()
        data["terminal_growth"] = evidence("0.10", "growth")
        with self.assertRaisesRegex(model.ModelInputError, "lower than discount_rate"):
            model.evaluate_model(data)

    def test_scenario_weights_must_sum_exactly_to_one(self):
        data = base()
        data["scenarios"] = [{
            "name": "only", "weight": evidence("0.9", "weights"),
            "cash_flows": [{"period": i, **evidence(value, f"scenario-{i}")} for i, value in enumerate(("-100", "60", "60"))],
        }]
        with self.assertRaisesRegex(model.ModelInputError, "sum exactly"):
            model.evaluate_model(data)

    def test_cli_reads_json_and_returns_machine_readable_result(self):
        result = subprocess.run(
            [sys.executable, str(MODULE)], input=json.dumps(base()), text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("4.13", json.loads(result.stdout)["npv"])

    def test_cli_rejects_invalid_json_without_traceback(self):
        result = subprocess.run(
            [sys.executable, str(MODULE)], input="{bad json", text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("financial-modeling:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
