import unittest
from decimal import Decimal as D
from engine import (
    HORIZON_WEIGHTS,
    FactorEvidence,
    Metric,
    Quality,
    _research_action,
    compare,
    economic_spread,
    percentile,
    rank_opportunities,
    score_opportunity,
)
class Tests(unittest.TestCase):
    def setUp(self):
        self.a=Metric("pe","ttm",D(12),"multiple","2026-02-01","SEC",Quality.VERIFIED)
        self.b=Metric("pe","ttm",D(15),"multiple","2026-01-01","NYU",Quality.VERIFIED)
    def test_valid(self): self.assertEqual(compare(self.a,self.b,"2026-10-22")["delta"],"-3")
    def test_lookahead(self): self.assertEqual(compare(self.a,self.b,"2026-01-02")["reason"],"LOOKAHEAD")
    def test_mismatch(self):
        b=Metric("pe","forward",D(15),"multiple","2026-01-01","NYU",Quality.VERIFIED)
        self.assertEqual(compare(self.a,b,"2026-10-22")["status"],"BLOCKED")
    def test_missing(self):
        a=Metric("pe","ttm",None,"multiple","2026-02-01","SEC",Quality.VERIFIED)
        self.assertEqual(compare(a,self.b,"2026-10-22")["status"],"BLOCKED")
    def test_percentile(self):
        self.assertIsNone(percentile(D(1),[D(1)]))
        self.assertEqual(percentile(D(3),[D(i) for i in range(5)]),D("0.7"))
    def test_spread(self):
        a=Metric("roic","roic",D("0.2"),"fraction","2026-01-01","SEC",Quality.VERIFIED)
        b=Metric("wacc","wacc",D("0.1"),"fraction","2026-01-01","NYU",Quality.VERIFIED)
        self.assertEqual(economic_spread(a,b,"2026-10-22")["value"],"0.1")
    def test_invalid_dates_and_quality_fail_closed(self):
        from dataclasses import replace
        for metric in [replace(self.a,published_at="yesterday"), replace(self.a,published_at="2026-2-1"), replace(self.a,quality="UNKNOWN")]:
            self.assertEqual(compare(metric,self.b,"2026-10-22")["status"],"BLOCKED")
        self.assertEqual(compare(self.a,self.b,"tomorrow")["status"],"BLOCKED")

    def test_spread_cannot_subtract_unrelated_metrics(self):
        from dataclasses import replace
        a=replace(self.a,unit="fraction")
        b=replace(self.b,unit="fraction")
        self.assertEqual(economic_spread(a,b,"2026-10-22")["status"],"BLOCKED")

    def factor_evidence(self, horizon, values, *, candidate="synthetic", quality=Quality.PROVISIONAL, dates=None):
        result = {}
        for name in HORIZON_WEIGHTS[horizon]:
            if name not in values:
                continue
            observed = (dates or {}).get(name, "2026-10-27")
            result[name] = FactorEvidence(
                value=D(str(values[name])), confidence=D("0.80"), as_of_date=observed,
                source_ids=(f"synthetic:{candidate}:{name}",),
                definition=f"Synthetic test factor: {name}",
                normalization_profile=f"normalized-{name}-v1", quality=quality,
            )
        return result

    def test_six_synthetic_candidates_distinguish_horizons_and_block_bad_inputs(self):
        # Every candidate is a synthetic factor vector, not current market data
        # or an investment recommendation. MU only labels the cyclicality case.
        profiles = {
            "MU-cycle": {
                "1-3m": dict(catalyst_timing="0.80", estimate_revisions="0.90", valuation_expectations="0.70", price_setup="0.85", scenario_asymmetry="0.45", cycle_resilience="0.25"),
                "6-12m": dict(scenario_asymmetry="0.55", valuation_expectations="0.65", estimate_revisions="0.80", business_quality="0.65", risk_resilience="0.40", cycle_resilience="0.30"),
                ">3y": dict(growth_durability="0.55", business_quality="0.65", reinvestment_returns="0.70", valuation_expectations="0.55", balance_sheet_resilience="0.45", cycle_resilience="0.20"),
            },
            "quality-compounder": {
                "1-3m": dict(catalyst_timing="0.50", estimate_revisions="0.60", valuation_expectations="0.55", price_setup="0.50", scenario_asymmetry="0.60", cycle_resilience="0.80"),
                "6-12m": dict(scenario_asymmetry="0.65", valuation_expectations="0.55", estimate_revisions="0.60", business_quality="0.90", risk_resilience="0.85", cycle_resilience="0.80"),
                ">3y": dict(growth_durability="0.85", business_quality="0.90", reinvestment_returns="0.85", valuation_expectations="0.50", balance_sheet_resilience="0.90", cycle_resilience="0.85"),
            },
            "event-driven": {
                "1-3m": dict(catalyst_timing="0.90", estimate_revisions="0.80", valuation_expectations="0.55", price_setup="0.85", scenario_asymmetry="0.80", cycle_resilience="0.70"),
                "6-12m": dict(scenario_asymmetry="0.55", valuation_expectations="0.50", estimate_revisions="0.60", business_quality="0.60", risk_resilience="0.55", cycle_resilience="0.65"),
                ">3y": dict(growth_durability="0.40", business_quality="0.50", reinvestment_returns="0.45", valuation_expectations="0.40", balance_sheet_resilience="0.55", cycle_resilience="0.50"),
            },
            "cyclical-value-trap": {
                "1-3m": dict(catalyst_timing="0.25", estimate_revisions="0.30", valuation_expectations="0.90", price_setup="0.25", scenario_asymmetry="0.30", cycle_resilience="0.20"),
                "6-12m": dict(scenario_asymmetry="0.25", valuation_expectations="0.90", estimate_revisions="0.20", business_quality="0.35", risk_resilience="0.20", cycle_resilience="0.15"),
                ">3y": dict(growth_durability="0.30", business_quality="0.35", reinvestment_returns="0.30", valuation_expectations="0.60", balance_sheet_resilience="0.25", cycle_resilience="0.15"),
            },
            "negative-eps-no-fcf": {
                "1-3m": dict(catalyst_timing="0.60", estimate_revisions="0.50", price_setup="0.55", scenario_asymmetry="0.50", cycle_resilience="0.40"),
                "6-12m": dict(scenario_asymmetry="0.50", estimate_revisions="0.50", business_quality="0.50", risk_resilience="0.45", cycle_resilience="0.40"),
                ">3y": dict(growth_durability="0.60", business_quality="0.50", reinvestment_returns="0.45", balance_sheet_resilience="0.50", cycle_resilience="0.40"),
            },
            "stale-consensus": {
                "1-3m": dict(catalyst_timing="0.50", estimate_revisions="0.80", valuation_expectations="0.50", price_setup="0.50", scenario_asymmetry="0.50", cycle_resilience="0.50"),
                "6-12m": dict(scenario_asymmetry="0.50", valuation_expectations="0.50", estimate_revisions="0.80", business_quality="0.60", risk_resilience="0.50", cycle_resilience="0.50"),
                ">3y": dict(growth_durability="0.60", business_quality="0.60", reinvestment_returns="0.55", valuation_expectations="0.50", balance_sheet_resilience="0.55", cycle_resilience="0.50"),
            },
        }
        results = []
        for candidate, horizons in profiles.items():
            for horizon, values in horizons.items():
                dates = ({"estimate_revisions": "2026-01-01"}
                         if candidate == "stale-consensus" and "estimate_revisions" in values else None)
                result = score_opportunity(
                    candidate, horizon,
                    self.factor_evidence(horizon, values, candidate=candidate, dates=dates),
                    "2026-10-27",
                )
                results.append(result)

        by_key = {(row["candidate_id"], row["horizon"]): row for row in results}
        self.assertEqual(18, len(by_key))
        self.assertEqual("PROVISIONAL", by_key[("MU-cycle", "1-3m")]["status"])
        self.assertEqual("0.69", by_key[("MU-cycle", "1-3m")]["score"])
        self.assertEqual("0.59", by_key[("MU-cycle", "6-12m")]["score"])
        self.assertEqual("0.55", by_key[("MU-cycle", ">3y")]["score"])
        self.assertEqual("VERY_ATTRACTIVE", by_key[("quality-compounder", ">3y")]["score_band"])
        self.assertEqual("NOT_SCORED", by_key[("negative-eps-no-fcf", "1-3m")]["status"])
        self.assertIn("valuation_expectations", by_key[("negative-eps-no-fcf", "1-3m")]["missing_factors"])
        self.assertEqual("NOT_SCORED", by_key[("stale-consensus", "1-3m")]["status"])
        self.assertIn("estimate_revisions", by_key[("stale-consensus", "6-12m")]["stale_factors"])
        self.assertEqual("PROVISIONAL", by_key[("stale-consensus", ">3y")]["status"])
        self.assertFalse(by_key[("MU-cycle", "1-3m")]["score_is_probability"])
        self.assertEqual("REVIEW_PROVISIONAL", by_key[("MU-cycle", "1-3m")]["research_action"])
        self.assertEqual("0.56", by_key[("MU-cycle", "1-3m")]["confidence"])
        self.assertEqual("1.00", by_key[("MU-cycle", "1-3m")]["completeness"])
        self.assertEqual("2026-10-27", by_key[("MU-cycle", "1-3m")]["as_of"])
        self.assertEqual("PROVISIONAL", by_key[("quality-compounder", ">3y")]["status"])
        self.assertEqual("0.22", by_key[("MU-cycle", "1-3m")]["factor_weights"]["catalyst_timing"])
        self.assertEqual("0.80", by_key[("MU-cycle", "1-3m")]["factor_evidence"]["catalyst_timing"]["value"])
        self.assertEqual("synthetic:MU-cycle:catalyst_timing", by_key[("MU-cycle", "1-3m")]["factor_evidence"]["catalyst_timing"]["source_ids"][0])

        scored = [row for row in results if row["status"] == "PROVISIONAL"]
        self.assertGreaterEqual(len({row["candidate_id"] for row in scored}), 5)
        self.assertTrue({"VERY_ATTRACTIVE", "NEUTRAL_WATCH", "WEAK"}.issubset(
            {row["score_band"] for row in scored}
        ))
        self.assertEqual(5, len([row for row in results if row["status"] == "NOT_SCORED"]))
        self.assertTrue(all(row["score_is_probability"] is False for row in scored))
        ranked = rank_opportunities(scored)
        self.assertTrue(all(row["ranking_status"] == "COMPARABLE" for row in ranked))
        for horizon in HORIZON_WEIGHTS:
            horizon_rows = [row for row in ranked if row["horizon"] == horizon]
            scores = [D(row["unrounded_score"]) for row in horizon_rows]
            self.assertEqual(sorted(scores, reverse=True), scores)
            if len(horizon_rows) > 1:
                self.assertIsNotNone(horizon_rows[0]["score_difference_to_next"])

        # Preserve unscored rows in the presentation contract and rank by exact
        # values even when two displayed scores round to the same hundredth.
        near_tie = [
            {**by_key[("MU-cycle", "1-3m")], "candidate_id": "lower", "score": "0.70", "unrounded_score": "0.704"},
            {**by_key[("quality-compounder", "1-3m")], "candidate_id": "higher", "score": "0.70", "unrounded_score": "0.705"},
            by_key[("negative-eps-no-fcf", "1-3m")],
        ]
        near_tie[0].update(horizon="1-3m", model_version="test-v1", as_of="2026-10-27")
        near_tie[1].update(horizon="1-3m", model_version="test-v1", as_of="2026-10-27")
        result = rank_opportunities(near_tie)
        ordered = [row for row in result if row.get("ranking_status") == "COMPARABLE"]
        self.assertEqual(["higher", "lower"], [row["candidate_id"] for row in ordered])
        self.assertEqual("0.001", ordered[0]["score_difference_to_next"])
        unscored = next(row for row in result if row["candidate_id"] == "negative-eps-no-fcf")
        self.assertIsNone(unscored["rank_within_horizon"])
        self.assertEqual("NOT_RANKED", unscored["ranking_status"])

    def test_stale_future_low_confidence_and_incompatible_normalization_fail_closed(self):
        values = {name: "0.70" for name in HORIZON_WEIGHTS["1-3m"]}
        stale = self.factor_evidence("1-3m", values, dates={"price_setup": "2026-08-01"})
        self.assertIn("price_setup", score_opportunity("x", "1-3m", stale, "2026-10-27")["stale_factors"])
        future = self.factor_evidence("1-3m", values, dates={"price_setup": "2026-11-01"})
        self.assertIn("price_setup", score_opportunity("x", "1-3m", future, "2026-10-27")["future_dated_factors"])
        weak = self.factor_evidence("1-3m", values)
        weak["price_setup"] = FactorEvidence(D("0.7"), D("0.2"), "2026-10-27", ("source",), "price setup", "normalized-price_setup-v1")
        self.assertIn("price_setup", score_opportunity("x", "1-3m", weak, "2026-10-27")["weak_evidence_factors"])

        a = score_opportunity("a", "1-3m", self.factor_evidence("1-3m", values, candidate="a"), "2026-10-27")
        b_evidence = self.factor_evidence("1-3m", values, candidate="b")
        b_evidence["price_setup"] = FactorEvidence(D("0.7"), D("0.8"), "2026-10-27", ("synthetic:b:price",), "price setup", "incompatible-profile-v2")
        b = score_opportunity("b", "1-3m", b_evidence, "2026-10-27")
        incomparable = rank_opportunities([a, b])
        self.assertTrue(all(row["ranking_status"] == "NOT_COMPARABLE" for row in incomparable))
        self.assertTrue(all(row["rank_within_horizon"] is None for row in incomparable))
        b_definition = self.factor_evidence("1-3m", values, candidate="b")
        b_definition["price_setup"] = FactorEvidence(
            D("0.7"), D("0.8"), "2026-10-27", ("synthetic:b:price",),
            "different definition", "normalized-price_setup-v1",
        )
        different_definition = score_opportunity("b", "1-3m", b_definition, "2026-10-27")
        self.assertTrue(all(
            row["ranking_reason"] == "INCOMPATIBLE_NORMALIZATION_OR_FACTOR_DEFINITION"
            for row in rank_opportunities([a, different_definition])
        ))
        duplicate = rank_opportunities([a, a])
        self.assertTrue(all(row["ranking_reason"] == "DUPLICATE_CANDIDATE_ID" for row in duplicate))

    def test_weight_sensitivity_requires_a_new_model_version(self):
        scores = {name: "0.50" for name in HORIZON_WEIGHTS["1-3m"]}
        scores["catalyst_timing"] = "1.00"
        evidence = self.factor_evidence("1-3m", scores)
        base = score_opportunity("candidate", "1-3m", evidence, "2026-10-27")
        weights = dict(HORIZON_WEIGHTS["1-3m"])
        weights["catalyst_timing"] = (D("0.32"), weights["catalyst_timing"][1])
        weights["estimate_revisions"] = (D("0.08"), weights["estimate_revisions"][1])
        blocked = score_opportunity("candidate", "1-3m", evidence, "2026-10-27", weights=weights)
        self.assertEqual("NOT_SCORED", blocked["status"])
        changed = score_opportunity("candidate", "1-3m", evidence, "2026-10-27", model_version="opportunity-score-sensitivity-v1", weights=weights)
        self.assertNotEqual(base["score"], changed["score"])
        self.assertEqual("opportunity-score-sensitivity-v1", changed["model_version"])

    def test_research_queue_thresholds_are_distinct_and_not_trade_actions(self):
        self.assertEqual("PRIORITIZE", _research_action(D("0.65")))
        self.assertEqual("WATCH", _research_action(D("0.45")))
        self.assertEqual("DEPRIORITIZE", _research_action(D("0.25")))
        self.assertEqual("REJECT", _research_action(D("0.24")))

    def test_threshold_decisions_use_unrounded_score(self):
        evidence = self.factor_evidence(
            "1-3m", {name: "0.648" for name in HORIZON_WEIGHTS["1-3m"]},
            quality=Quality.VERIFIED,
        )
        result = score_opportunity("edge", "1-3m", evidence, "2026-10-27")
        self.assertEqual("0.65", result["score"])
        self.assertEqual("NEUTRAL_WATCH", result["score_band"])
        self.assertEqual("WATCH", result["research_action"])
if __name__=="__main__": unittest.main()
