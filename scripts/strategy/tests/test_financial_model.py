import unittest
from decimal import Decimal

from scripts.strategy.financial_model import irr, npv, payback, profit_bridge


class FinancialModelTests(unittest.TestCase):
    def test_npv_includes_time_zero_once(self):
        self.assertLess(abs(npv("0.10", [-100, 60, 60]) - Decimal("4.132231404958677685950413223")), Decimal("1e-24"))

    def test_irr_root_reconciles_to_zero_npv(self):
        flows = [-100, 60, 60]
        rate = irr(flows)
        self.assertIsNotNone(rate)
        self.assertLess(abs(npv(rate, flows)), Decimal("1e-10"))

    def test_payback_and_discounted_payback_are_distinct(self):
        flows = [-100, 60, 60]
        self.assertEqual(payback(flows), Decimal(1) + Decimal(40) / Decimal(60))
        self.assertGreater(payback(flows, "0.10"), payback(flows))

    def test_irr_returns_none_for_unbracketed_or_no_sign_change(self):
        self.assertIsNone(irr([-1, -2]))
        self.assertIsNone(irr([-100, 1, -1]))

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            npv(-1, [0, 1])
        self.assertIsNone(payback([-10, 1, 1]))

    def test_profit_bridge_reconciles_volume_mix_price_and_cost(self):
        result = profit_bridge(
            {"A": [60, 10, 4], "B": [40, 15, 8]},
            {"A": [80, 11, 5], "B": [50, 16, 9]},
        )
        self.assertEqual(result["baseline_profit"], Decimal(640))
        self.assertEqual(result["target_profit"], Decimal(830))
        self.assertEqual(result["residual"], Decimal(0))
        self.assertEqual(
            sum(result[k] for k in ("volume_effect", "mix_effect", "price_effect", "unit_cost_effect")),
            Decimal(190),
        )

    def test_profit_bridge_rejects_missing_segments_and_negative_volume(self):
        with self.assertRaises(ValueError):
            profit_bridge({"A": [1, 2, 1]}, {"B": [1, 2, 1]})
        with self.assertRaises(ValueError):
            profit_bridge({"A": [-1, 2, 1]}, {"A": [1, 2, 1]})


if __name__ == "__main__":
    unittest.main()
