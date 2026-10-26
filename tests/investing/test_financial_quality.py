import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "scripts/investing/financial_quality.py"
spec = importlib.util.spec_from_file_location("financial_quality", PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class TestFinancialQuality(unittest.TestCase):
    def test_eight_buffett_metrics_and_cashflow(self):
        x = module.Financials(
            period="2025", revenue=100, cost_of_revenue=50, sga=10,
            research_development=15, depreciation_amortization=5,
            operating_income=20, interest_expense=2, pretax_income=18,
            income_tax_expense=4, net_income=14, diluted_eps=2,
            operating_cash_flow=19, capital_expenditure=6, invested_capital=100)
        p = module.Financials(period="2024", revenue=90, diluted_eps=1.5)
        r = module.financial_quality(x, p)
        m = r["metrics"]
        self.assertEqual(m["gross_margin"], .5)
        self.assertEqual(m["sga_to_gross_profit"], .2)
        self.assertEqual(m["rnd_to_gross_profit"], .3)
        self.assertEqual(m["depreciation_to_gross_profit"], .1)
        self.assertEqual(m["interest_to_operating_income"], .1)
        self.assertEqual(m["interest_coverage_ebit"], 10)
        self.assertEqual(m["net_margin"], .14)
        self.assertAlmostEqual(m["diluted_eps_growth"], .333333)
        self.assertEqual(m["free_cash_flow"], 13)
        self.assertIsNone(r["quality_score"])

    def test_loss_maker_does_not_invent_ratio(self):
        x = module.Financials(period="2025", revenue=80, cost_of_revenue=90,
                              operating_income=-5, interest_expense=2,
                              pretax_income=-8, income_tax_expense=0)
        m = module.financial_quality(x)["metrics"]
        self.assertIsNone(m["interest_to_operating_income"])
        self.assertIsNone(m["sga_to_gross_profit"])
        self.assertIsNone(m["effective_tax_rate"])

    def test_zero_base_eps_no_growth(self):
        current = module.Financials(period="2025", revenue=100, diluted_eps=2)
        prev = module.Financials(period="2024", revenue=100, diluted_eps=0)
        self.assertIsNone(module.financial_quality(current, prev)["metrics"]["diluted_eps_growth"])


if __name__ == "__main__":
    unittest.main()
