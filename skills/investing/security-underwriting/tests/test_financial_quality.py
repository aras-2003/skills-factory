"""Synthetic regression fixtures for the financial-quality calculation contract."""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from financial_quality import FinancialFact, FactStatus, PeriodType, audit_financial_quality


AS_OF = "2026-08-01"


def fact(metric, label, year, *, period_type=PeriodType.FY, quarter=None, value="1",
         unit="currency_millions", currency="USD", basis="GAAP", published="2026-03-01",
         capex_sign=None, status=FactStatus.VERIFIED):
    start = f"{year}-01-01"
    end = f"{year}-12-31" if period_type == PeriodType.FY else f"{year}-{quarter * 3:02d}-30"
    return FinancialFact(
        metric=metric, value=D(str(value)) if value is not None else None,
        period_type=period_type, period_label=label, period_start=start, period_end=end,
        fiscal_year=year, fiscal_quarter=quarter, currency=currency, unit=unit,
        basis=basis, source_url=f"https://investor.example/{year}/{metric}",
        published_at=published, status=status, capex_sign=capex_sign,
        definition=f"Synthetic {metric} definition",
    )


def fixture_facts(*, cfo_unit="currency_millions", cfo_value="140", capex_value="20",
                 capex_sign="spend_positive", latest_year=2024):
    result = []
    for year in range(latest_year - 2, latest_year + 1):
        label = f"FY{year}"
        change = year - (latest_year - 2)
        values = {
            "revenue": str(1000 - 100 * change),
            "operating_income": str(180 - 30 * change),
            "net_income": str(100 - 10 * change),
            "cfo": cfo_value,
            "capex": capex_value,
            "nopat": "135",
            "average_invested_capital": "900",
            "shares_diluted": "100",
            "stock_compensation": "5",
            "total_debt": "200",
            "cash": "80",
            "working_capital_change": "-10",
        }
        for metric, value in values.items():
            unit = cfo_unit if metric == "cfo" else "currency_millions"
            if metric == "shares_diluted":
                unit = "shares_millions"
            result.append(fact(metric, label, year, value=value, unit=unit,
                               capex_sign=capex_sign if metric == "capex" else None))
    # Same fiscal quarter in adjacent years is required to call YTD comparable.
    for year in (2025, 2026):
        label = f"YTD{year}Q2"
        for metric, value in {"revenue": "520", "operating_income": "90", "net_income": "50", "cfo": "70", "capex": "10"}.items():
            result.append(fact(metric, label, year, period_type=PeriodType.YTD, quarter=2,
                               value=value, capex_sign="spend_positive" if metric == "capex" else None))
    return result


class FinancialQualityTests(unittest.TestCase):
    def test_three_fy_and_comparable_ytd_normalize_units_and_expose_formulas(self):
        facts = fixture_facts(cfo_unit="currency_thousands", cfo_value="140000")
        result = audit_financial_quality(facts, AS_OF, cyclical=True)
        self.assertEqual("VERIFIED", result["status"])
        self.assertEqual(3, result["period_count_fy"])
        self.assertTrue(result["comparable_ytd"])
        last = next(p for p in result["periods"] if p["period"] == "FY2024")
        self.assertEqual("120000000", last["fcf"])
        self.assertEqual("free_cash_flow / positive_net_income", last["fcf_conversion_definition"])
        self.assertEqual("NOPAT / average invested capital", last["roic_method"])
        self.assertIn("CYCLE_NORMALIZATION_REQUIRED_NO_PEAK_EXTRAPOLATION", result["deterioration_flags"])
        self.assertIn("source_url", last["evidence"]["revenue"])
        self.assertIn("stock_compensation", last["optional_metrics"])
        self.assertEqual(D("800") / D("900") - 1, D(last["revenue_growth_yoy"]))
        self.assertEqual("0", last["shares_dilution_yoy"])
        self.assertIn("one_off_adjustments", last["optional_metrics"])
        self.assertEqual("-10000000", last["optional_metrics"]["working_capital_change"]["value"])
        self.assertFalse(result["write_attempted"])
        current_ytd = next(p for p in result["periods"] if p["period"] == "YTD2026Q2")
        self.assertEqual("0", current_ytd["revenue_growth_yoy"])

    def test_optional_cashflow_and_dilution_gaps_remain_nm_with_reason(self):
        result = audit_financial_quality(fixture_facts(), AS_OF)
        latest = next(p for p in result["periods"] if p["period"] == "FY2024")
        self.assertEqual("N/M", latest["optional_metrics"]["gross_profit"]["value"])
        self.assertEqual("MISSING", latest["optional_metrics"]["gross_profit"]["reason"])
        self.assertEqual("100000000", latest["optional_metrics"]["shares_diluted"]["value"])

    def test_positive_income_with_negative_ocf_is_reported_as_poor_conversion(self):
        facts = fixture_facts(cfo_value="-10")
        result = audit_financial_quality(facts, AS_OF)
        latest = next(p for p in result["periods"] if p["period"] == "FY2024")
        self.assertEqual("-30000000", latest["fcf"])
        self.assertEqual("-0.375", latest["fcf_conversion"])

    def test_adjusted_ebitda_is_visible_separately_from_gaap_inputs(self):
        facts = fixture_facts()
        base = next(f for f in facts if f.period_label == "FY2024" and f.metric == "net_income")
        facts.append(replace(base, metric="adjusted_ebitda", value=D("220"),
                             basis="Adjusted EBITDA excluding SBC",
                             definition="Issuer-reported adjusted EBITDA excluding SBC"))
        result = audit_financial_quality(facts, AS_OF)
        latest = next(p for p in result["periods"] if p["period"] == "FY2024")
        self.assertEqual("220000000", latest["optional_metrics"]["adjusted_ebitda"]["value"])
        self.assertEqual("Adjusted EBITDA excluding SBC", latest["optional_metrics"]["adjusted_ebitda"]["basis"])
        self.assertEqual("800000000", latest["revenue"])

    def test_cashflow_signed_capex_reconciles_but_wrong_sign_blocks(self):
        facts = fixture_facts(capex_value="-20", capex_sign="cashflow_signed")
        result = audit_financial_quality(facts, AS_OF)
        self.assertEqual("VERIFIED", result["status"])
        latest = next(p for p in result["periods"] if p["period"] == "FY2024")
        self.assertEqual("120000000", latest["fcf"])

        bad = [replace(x, value=D("20")) if x.metric == "capex" and x.period_label == "FY2024" else x for x in facts]
        blocked = audit_financial_quality(bad, AS_OF)
        self.assertEqual("BLOCKED", blocked["status"])
        self.assertIn("FY2024:CAPEX_CASHFLOW_SIGN_MISMATCH", blocked["problems"])

    def test_missing_core_fact_blocks_dependent_period_metrics(self):
        facts = [x for x in fixture_facts() if not (x.metric == "cfo" and x.period_label == "FY2023")]
        result = audit_financial_quality(facts, AS_OF)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("FY2023/cfo:MISSING_CRITICAL", result["problems"])
        period = next(p for p in result["periods"] if p["period"] == "FY2023")
        self.assertNotIn("fcf", period)

    def test_lookahead_and_conflicting_restatement_fail_closed(self):
        future = [replace(x, published_at="2026-09-01") if x.metric == "revenue" and x.period_label == "FY2024" else x for x in fixture_facts()]
        result = audit_financial_quality(future, AS_OF)
        self.assertEqual("BLOCKED", result["status"])
        self.assertTrue(any(x.endswith(":LOOKAHEAD") for x in result["problems"]))

        facts = fixture_facts()
        revenue = next(x for x in facts if x.metric == "revenue" and x.period_label == "FY2024")
        facts.append(replace(revenue, value=D("999"), source_url="https://ir.example/restatement"))
        conflict = audit_financial_quality(facts, AS_OF)
        self.assertEqual("BLOCKED", conflict["status"])
        self.assertIn("FY2024/revenue:CONFLICTED_DUPLICATE_FACTS", conflict["problems"])

    def test_later_filing_revision_is_selected_and_older_value_remains_visible(self):
        facts = fixture_facts()
        old = next(f for f in facts if f.period_label == "FY2024" and f.metric == "revenue")
        facts.append(replace(old, value=D("780"), published_at="2025-02-01"))
        result = audit_financial_quality(facts, AS_OF)
        period = next(p for p in result["periods"] if p["period"] == "FY2024")
        self.assertEqual("800000000", period["revenue"])
        self.assertEqual("780000000", period["evidence"]["revenue"]["prior_revisions"][0]["value"])
        self.assertEqual("2025-02-01", period["evidence"]["revenue"]["prior_revisions"][0]["published_at"])

    def test_equivalent_unit_scales_for_same_fact_are_normalized_not_conflicted(self):
        facts = fixture_facts()
        revenue = next(f for f in facts if f.period_label == "FY2024" and f.metric == "revenue")
        facts.append(replace(revenue, value=D("800000"), unit="currency_thousands"))
        result = audit_financial_quality(facts, AS_OF)
        period = next(p for p in result["periods"] if p["period"] == "FY2024")
        self.assertEqual("800000000", period["revenue"])
        self.assertNotIn("FY2024/revenue:CONFLICTED_DUPLICATE_FACTS", result["problems"])

    def test_optional_percent_is_normalized_and_reported_net_debt_is_a_fallback(self):
        facts = fixture_facts()
        facts = [f for f in facts if not (f.period_label == "FY2024" and f.metric in {"total_debt", "cash"})]
        facts.append(fact("net_debt", "FY2024", 2024, value="120"))
        facts.append(fact("gross_margin", "FY2024", 2024, value="35", unit="percent"))
        result = audit_financial_quality(facts, AS_OF)
        latest = next(p for p in result["periods"] if p["period"] == "FY2024")
        self.assertEqual("120000000", latest["net_debt"])
        self.assertEqual("source-reported net_debt", latest["net_debt_method"])
        self.assertEqual("0.35", latest["gross_margin"])
        self.assertEqual("fraction", latest["optional_metrics"]["gross_margin"]["unit"])

    def test_optional_money_in_another_currency_remains_nm_without_fx(self):
        facts = fixture_facts()
        debt = next(f for f in facts if f.period_label == "FY2024" and f.metric == "total_debt")
        facts[facts.index(debt)] = replace(debt, currency="CAD")
        latest = next(p for p in audit_financial_quality(facts, AS_OF)["periods"] if p["period"] == "FY2024")
        self.assertEqual("N/M", latest["optional_metrics"]["total_debt"]["value"])
        self.assertEqual("INCOMPATIBLE_UNIT_OR_CURRENCY_OR_BASIS", latest["optional_metrics"]["total_debt"]["reason"])

    def test_gaap_adjusted_basis_mismatch_is_not_silently_combined(self):
        facts = [replace(x, basis="Adjusted EBITDA excluding SBC") if x.metric == "net_income" and x.period_label == "FY2024" else x for x in fixture_facts()]
        result = audit_financial_quality(facts, AS_OF)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("FY2024:MIXED_GAAP_OR_ADJUSTED_BASIS", result["problems"])

    def test_noncontiguous_fy_and_missing_comparable_ytd_are_blockers(self):
        facts = [x for x in fixture_facts() if x.period_label != "FY2023" and not (x.period_type == PeriodType.YTD and x.fiscal_year == 2025)]
        result = audit_financial_quality(facts, AS_OF)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("INSUFFICIENT_FY_HISTORY", result["problems"])
        self.assertIn("COMPARABLE_YTD_MISSING", result["problems"])

    def test_mixed_currency_is_blocked_without_fx_assumption(self):
        facts = [replace(x, currency="EUR") if x.metric == "cfo" and x.period_label == "FY2024" else x for x in fixture_facts()]
        result = audit_financial_quality(facts, AS_OF)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("FY2024:MIXED_CURRENCY_REQUIRES_CONVERSION", result["problems"])

    def test_ytd_period_lengths_must_be_comparable(self):
        facts = [replace(f, period_end="2026-07-15") if f.period_type == PeriodType.YTD and f.fiscal_year == 2026 else f for f in fixture_facts()]
        result = audit_financial_quality(facts, AS_OF)
        self.assertEqual("BLOCKED", result["status"])
        self.assertFalse(result["comparable_ytd"])
        self.assertIn("YTD_PERIOD_LENGTH_MISMATCH", result["problems"])

    def test_definition_or_basis_changes_block_cross_period_comparison(self):
        facts = [replace(f, definition="Changed revenue basis") if f.metric == "revenue" and f.period_label == "FY2023" else f for f in fixture_facts()]
        result = audit_financial_quality(facts, AS_OF)
        self.assertEqual("BLOCKED", result["status"])
        self.assertFalse(result["comparable_ytd"])
        self.assertIn("METRIC_DEFINITION_CHANGED:revenue", result["problems"])

    def test_bank_and_etf_use_alternative_path_not_zeroed_industrial_metrics(self):
        for path in ("bank", "ETF"):
            result = audit_financial_quality(fixture_facts(), AS_OF, industry_path=path)
            self.assertEqual("ALTERNATIVE_INDUSTRY_PATH", result["status"])
            self.assertTrue(all(p["standard_industrial_fcf"] == "NOT_APPLICABLE" for p in result["periods"]))
            self.assertTrue(all("USE_INDUSTRY_SPECIFIC_CAPITAL_OR_PROVIDER_METRICS" in p["flags"] for p in result["periods"]))

    def test_invalid_metadata_and_missing_units_are_not_verified(self):
        facts = [replace(x, source_url="file://local") if x.metric == "revenue" and x.period_label == "FY2024" else x for x in fixture_facts()]
        self.assertEqual("BLOCKED", audit_financial_quality(facts, AS_OF)["status"])
        facts = [replace(x, unit="widgets") if x.metric == "cfo" and x.period_label == "FY2024" else x for x in fixture_facts()]
        self.assertEqual("BLOCKED", audit_financial_quality(facts, AS_OF)["status"])


if __name__ == "__main__":
    unittest.main()
