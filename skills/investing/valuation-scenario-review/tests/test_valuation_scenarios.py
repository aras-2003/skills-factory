from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from valuation_scenarios import (
    affo_multiple_per_share,
    affo_multiple_sensitivity,
    dcf_per_share,
    dcf_sensitivity,
    earnings_multiple_per_share,
    earnings_multiple_sensitivity,
    margin_of_safety,
    nav_per_share,
    nav_sensitivity,
    residual_income_per_share,
    upside,
)


class ValuationScenarioTests(unittest.TestCase):
    def test_margin_of_safety_and_upside_use_distinct_denominators(self) -> None:
        self.assertAlmostEqual(0.2, margin_of_safety(100, 80))
        self.assertAlmostEqual(0.25, upside(100, 80))

    def test_industry_methods_are_explicit_and_deterministic(self) -> None:
        self.assertEqual(40, earnings_multiple_per_share(4, 10))
        self.assertEqual(60, affo_multiple_per_share(3, 20))
        self.assertEqual(80, nav_per_share(1200, 400, 10))
        self.assertGreater(residual_income_per_share(50, [0.14, 0.13], [0.3, 0.3], 0.10, 0.02), 50)

    def test_dcf_discounting_and_equity_bridge(self) -> None:
        value = dcf_per_share([10, 12], 0.10, 0.02, 20, 2)
        expected = (10 / 1.1 + 12 / 1.1**2 + (12 * 1.02 / 0.08) / 1.1**2 - 20) / 2
        self.assertAlmostEqual(expected, value)

    def test_dcf_sensitivity_recomputes_fcf_and_discount_rate_cases(self) -> None:
        values = dcf_sensitivity([10, 12], 0.10, 0.02, 20, 2)
        self.assertEqual({"base", "fcf_down_20pct", "fcf_up_20pct", "discount_rate_up", "discount_rate_down"}, set(values))
        self.assertLess(values["fcf_down_20pct"], values["base"])
        self.assertGreater(values["fcf_up_20pct"], values["base"])
        self.assertLess(values["discount_rate_up"], values["base"])
        self.assertGreater(values["discount_rate_down"], values["base"])
        self.assertAlmostEqual(
            dcf_per_share([10, 12], 0.12, 0.02, 20, 2),
            values["discount_rate_up"],
        )
        self.assertAlmostEqual(
            dcf_per_share([10, 12], 0.08, 0.02, 20, 2),
            values["discount_rate_down"],
        )

    def test_affo_and_nav_sensitivities_recompute_method_inputs(self) -> None:
        affo = affo_multiple_sensitivity(3, 20)
        self.assertEqual(60, affo["base"])
        self.assertAlmostEqual(48, affo["affo_down_20pct"])
        self.assertAlmostEqual(72, affo["multiple_up_20pct"])

        nav = nav_sensitivity(1200, 400, 10)
        self.assertEqual(80, nav["base"])
        self.assertEqual(56, nav["assets_down_20pct"])
        self.assertEqual(72, nav["liabilities_up_20pct"])
        self.assertAlmostEqual(64, nav["price_to_nav_down_20pct"])

    def test_eps_sensitivity_changes_earnings_and_multiple_separately(self) -> None:
        values = earnings_multiple_sensitivity(4, 10)
        self.assertEqual(40, values["base"])
        self.assertEqual(32, values["eps_down_20pct"])
        self.assertEqual(48, values["eps_up_20pct"])
        self.assertEqual(32, values["multiple_down_20pct"])
        self.assertEqual(48, values["multiple_up_20pct"])

    def test_rejects_bad_denominators_and_terminal_assumptions(self) -> None:
        for args in ((0, 20), (20, 0)):
            with self.assertRaises(ValueError):
                margin_of_safety(*args)
        with self.assertRaises(ValueError):
            dcf_per_share([10], 0.08, 0.08, 0, 1)
        with self.assertRaises(ValueError):
            nav_per_share(10, 12, 1)
        with self.assertRaises(ValueError):
            earnings_multiple_per_share(-1, 12)
        with self.assertRaises(ValueError):
            residual_income_per_share(10, [0.12], [], 0.10, 0.02)


if __name__ == "__main__":
    unittest.main()
