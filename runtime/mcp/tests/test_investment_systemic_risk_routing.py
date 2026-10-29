from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from investment_runtime import route_investment_request


class SystemicRiskRoutingTests(unittest.TestCase):
    def test_cross_asset_signals_route_to_attention(self) -> None:
        result = route_investment_request(
            "Systemic risk indicators across credit markets and macro conditions have changed. "
            "Assess these indicator groups, distinguish published historical vintages, deduplicate "
            "correlated evidence, and state materiality and direction separately. No portfolio-specific "
            "assessment, no holdings, no trades, no policy change, and no writes."
        )
        self.assertEqual(result["route"], "attention")
        self.assertEqual(result["child_workflow"], "investment-attention-review")

    def test_systemic_triage_does_not_require_portfolio_wording(self) -> None:
        result = route_investment_request(
            "Triage these systemic market risk indicators: HY and IG spreads are correlated, "
            "breadth data is stale, and real yield is missing. Preserve vintages and say whether "
            "the evidence is material; do not estimate crash odds."
        )
        self.assertEqual(result["route"], "attention")

    def test_generic_credit_spread_definition_stays_outside_investment_os(self) -> None:
        result = route_investment_request("Explain what a credit spread means in one sentence.")
        self.assertFalse(result["is_investment_request"])
        self.assertEqual(result["route"], "not_applicable")

    def test_explicit_portfolio_review_keeps_portfolio_ownership(self) -> None:
        result = route_investment_request("Review my portfolio concentration and ETF overlap.")
        self.assertEqual(result["route"], "portfolio")
        self.assertEqual(result["child_workflow"], "investment-portfolio-review")


if __name__ == "__main__":
    unittest.main()
