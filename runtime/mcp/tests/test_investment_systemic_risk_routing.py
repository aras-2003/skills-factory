import unittest

from runtime.mcp.investment_runtime import route_investment_request


class InvestmentSystemicRiskRoutingTests(unittest.TestCase):
    def test_systemic_cross_asset_signals_with_portfolio_context_route_to_attention(self):
        prompt = (
            "Using ONLY this synthetic fixture as of 2026-10-28T12:00:00Z, review systemic risk signals: "
            "HY spread 410bp published at 2026-10-28T09:00Z; IG spread 90bp published same time "
            "(same credit_conditions correlation group). Market breadth is 45% (named fictional index, "
            "2026-10-28) and stale 62% (2026-09-01). Real yield missing. Fictional issuer X reports "
            "2027 maturity 20m and liquidity 50m published 2026-10-20. Two fictional ETFs overlap issuer X "
            "by 8% and 5%; ETF-B constituent source is incomplete and dated 2025-01-01. Preserve original "
            "vintages, do not treat correlated signals as independent, say stale/missing/partial data explicitly, "
            "no crash odds. Do not read canonical portfolio state and do not write/update policy, portfolio, "
            "orders, or alerts. Return only whether routed and which workflow is appropriate."
        )
        result = route_investment_request(prompt)
        self.assertEqual("attention", result["route"])
        self.assertEqual("investment-attention-review", result["child_workflow"])
        self.assertTrue(result["must_invoke_child_workflow"])
        self.assertIn("NEXT_ACTION=load_skill(investment-attention-review)", result["routing_receipt"])

    def test_market_only_indicators_are_not_portfolio_observation(self):
        prompt = (
            "Triage these synthetic systemic market indicators only; no portfolio or holdings review: "
            "fictional HY spread 410bp and IG spread 90bp, both current as of 2026-10-28 and correlated "
            "within the credit_conditions group; a fictional index breadth figure is 45% current with prior "
            "value 62% from 2026-09-01 (stale); real yield is missing. Preserve publication vintages, separate "
            "direction and materiality, do not invent thresholds or crash probabilities, no external research, "
            "no canonical reads/writes, no policy changes."
        )
        result = route_investment_request(prompt)
        self.assertEqual("attention", result["route"])
        self.assertEqual("investment-attention-review", result["child_workflow"])

    def test_unscoped_systemic_market_changes_are_not_historical_replay(self):
        prompt = (
            "Systemic risk indicators across credit markets and macro conditions have changed. Assess these "
            "indicator groups, distinguish published historical vintages, deduplicate correlated evidence, and "
            "state materiality and direction separately. No portfolio-specific assessment, no holdings, no trades, "
            "no policy change, and no writes."
        )
        result = route_investment_request(prompt)
        self.assertEqual("attention", result["route"])
        self.assertEqual("investment-attention-review", result["child_workflow"])

    def test_systemic_triage_without_portfolio_language_is_investment_intent(self):
        result = route_investment_request(
            "Systemic risk indicators across credit markets and macro conditions have changed. Assess these "
            "indicator groups, distinguish published historical vintages, deduplicate correlated evidence, and "
            "state materiality and direction separately."
        )
        self.assertTrue(result["is_investment_request"])
        self.assertEqual("attention", result["route"])
        self.assertEqual("investment-attention-review", result["child_workflow"])

    def test_explicit_portfolio_review_stays_portfolio_review(self):
        result = route_investment_request(
            "Review my portfolio risk, concentration and allocation across 40% FictionalCo and 60% Sample ETF. "
            "I am not asking for systemic indicator triage."
        )
        self.assertEqual("portfolio", result["route"])
        self.assertEqual("investment-portfolio-review", result["child_workflow"])

    def test_generic_credit_spread_definition_does_not_route_to_investment_os(self):
        result = route_investment_request(
            "Explain in plain English what a credit spread measures, without discussing investments."
        )
        self.assertFalse(result["is_investment_request"])
        self.assertEqual("not_applicable", result["route"])
        self.assertFalse(result["must_invoke_child_workflow"])


if __name__ == "__main__":
    unittest.main()
