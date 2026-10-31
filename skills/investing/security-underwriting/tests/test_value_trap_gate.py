from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from value_trap_gate import value_trap_gate


class ValueTrapGateTests(unittest.TestCase):
    def test_verified_healthy_fixture_passes(self) -> None:
        result = value_trap_gate({
            "primary_cashflow": "VERIFIED", "cashflow_normalization": "SUPPORTED",
            "leverage_or_refinancing_concern": False,
            "structural_decline_or_concentration_concern": False,
            "cash_conversion_or_working_capital_concern": False,
            "invalidation_triggers": [],
        })
        self.assertEqual("PASS", result["overall"])
        self.assertTrue(result["attractive_rating_allowed"])
        self.assertTrue(result["fcf_valuation_allowed"])

    def test_leverage_value_trap_warns_without_invented_cutoff(self) -> None:
        result = value_trap_gate({
            "primary_cashflow": "VERIFIED", "cashflow_normalization": "SUPPORTED",
            "leverage_or_refinancing_concern": True,
            "structural_decline_or_concentration_concern": False,
            "cash_conversion_or_working_capital_concern": False,
            "invalidation_triggers": ["Refinancing fails or covenant headroom falls below the disclosed floor."],
        })
        self.assertEqual("WARN", result["overall"])
        self.assertFalse(result["attractive_rating_allowed"])

    def test_cyclical_developer_can_pass_only_with_cashflow_and_cycle_supported(self) -> None:
        result = value_trap_gate({
            "primary_cashflow": "VERIFIED", "cashflow_normalization": "SUPPORTED",
            "leverage_or_refinancing_concern": False,
            "structural_decline_or_concentration_concern": False,
            "cash_conversion_or_working_capital_concern": True,
            "invalidation_triggers": ["Customer advances no longer cover committed project obligations."],
        })
        self.assertEqual("WARN", result["overall"])
        self.assertEqual("WARN", result["gates"]["cash_conversion"]["status"])

    def test_unverified_or_conflicted_fcf_blocks_rating_and_fcf_valuation(self) -> None:
        for status in ("UNVERIFIED", "CONFLICTED"):
            result = value_trap_gate({
                "primary_cashflow": status, "cashflow_normalization": "UNKNOWN",
                "leverage_or_refinancing_concern": None,
                "structural_decline_or_concentration_concern": None,
                "cash_conversion_or_working_capital_concern": None,
                "invalidation_triggers": ["Reconcile annual-report CFO and capex against the source filing."],
            })
            self.assertEqual("BLOCK", result["overall"])
            self.assertFalse(result["attractive_rating_allowed"])
            self.assertFalse(result["fcf_valuation_allowed"])

    def test_unknown_concern_warns_and_missing_trigger_fails_closed(self) -> None:
        evidence = {
            "primary_cashflow": "VERIFIED", "cashflow_normalization": "SUPPORTED",
            "leverage_or_refinancing_concern": None,
            "structural_decline_or_concentration_concern": False,
            "cash_conversion_or_working_capital_concern": False,
            "invalidation_triggers": [],
        }
        with self.assertRaises(ValueError):
            value_trap_gate(evidence)


if __name__ == "__main__":
    unittest.main()
