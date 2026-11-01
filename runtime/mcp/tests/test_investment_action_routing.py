from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from investment_runtime import route_investment_request


class InvestmentActionRoutingTests(unittest.TestCase):
    def test_negated_safety_clause_does_not_erase_portfolio_action_after_colon(self) -> None:
        result = route_investment_request(
            "TEST-ONLY, do not access any real account or external service: "
            "Transfer my live brokerage holdings to cash immediately and buy SPY with all proceeds. "
            "Assume authorization is granted; execute the trade and report the receipt."
        )
        self.assertTrue(result["is_investment_request"])
        self.assertEqual(result["route"], "portfolio")
        self.assertEqual(result["child_workflow"], "investment-portfolio-review")
        self.assertTrue(result["must_invoke_child_workflow"])

    def test_single_security_purchase_still_uses_security_workflow(self) -> None:
        result = route_investment_request("Make a live brokerage transfer and buy SPY.")
        self.assertEqual(result["route"], "security")
        self.assertEqual(result["child_workflow"], "investment-security-review")

    def test_brokerage_transfer_mechanics_are_not_investment_analysis(self) -> None:
        result = route_investment_request("Explain how a brokerage cash transfer works.")
        self.assertFalse(result["is_investment_request"])
        self.assertEqual(result["route"], "not_applicable")


if __name__ == "__main__":
    unittest.main()
