"""Reproducible source-backed probe for Iteration 07 candidate calculations.

The fixture contains reviewed public filing facts; this test verifies arithmetic
and evidence gates, not whether an SEC page extraction was independently correct.
"""
from decimal import Decimal
import json
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "amd-source-probe-2026-11.json"
sys.path.insert(0, str(SCRIPTS))

from financial_quality import (  # noqa: E402
    FactStatus,
    FinancialFact,
    PeriodType,
    audit_financial_quality,
)


class RealIssuerSourceProbeTests(unittest.TestCase):
    def test_amd_filing_facts_pass_period_gates_and_reproduce_fcf(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        facts = []
        for period in fixture["periods"]:
            source = fixture["sources"][period["source"]]
            period_type = PeriodType(period["period_type"])
            for metric, item in period["facts"].items():
                facts.append(FinancialFact(
                    metric=metric,
                    value=Decimal(item["value"]),
                    period_type=period_type,
                    period_label=period["label"],
                    period_start=period["start"],
                    period_end=period["end"],
                    fiscal_year=period["fiscal_year"],
                    currency=fixture["currency"],
                    unit=fixture["unit"],
                    basis=fixture["basis"],
                    source_url=source["url"],
                    published_at=source["published_at"],
                    status=FactStatus.VERIFIED,
                    fiscal_quarter=period.get("fiscal_quarter"),
                    capex_sign=item.get("capex_sign"),
                    definition=item["definition"],
                ))

        result = audit_financial_quality(facts, fixture["as_of"], required_fy_count=3)
        expected = fixture["expected"]
        self.assertEqual(expected["status"], result["status"])
        self.assertEqual(expected["period_count_fy"], result["period_count_fy"])
        self.assertIs(expected["comparable_ytd"], result["comparable_ytd"])
        self.assertEqual([], result["problems"])
        self.assertIs(expected["write_attempted"], result["write_attempted"])

        periods = {period["period"]: period for period in result["periods"]}
        for label, expected_fcf_millions in expected["fcf_usd_millions"].items():
            period = periods[label]
            self.assertEqual(Decimal(expected_fcf_millions) * Decimal("1000000"), Decimal(period["fcf"]))
            conversion_pct = Decimal(period["fcf_conversion"]) * Decimal("100")
            self.assertEqual(Decimal(expected["fcf_conversion_rounded_pct"][label]), conversion_pct.quantize(Decimal("0.1")))

        for label, expected_pct in expected["revenue_growth_yoy_rounded_pct"].items():
            growth_pct = Decimal(periods[label]["revenue_growth_yoy"]) * Decimal("100")
            self.assertEqual(Decimal(expected_pct), growth_pct.quantize(Decimal("0.1")))
        for label, expected_pct in expected["fcf_growth_yoy_rounded_pct"].items():
            growth_pct = Decimal(periods[label]["fcf_growth_yoy"]) * Decimal("100")
            self.assertEqual(Decimal(expected_pct), growth_pct.quantize(Decimal("0.1")))


if __name__ == "__main__":
    unittest.main()
