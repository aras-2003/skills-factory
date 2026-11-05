from __future__ import annotations

import sys
import unittest
from pathlib import Path

RUNTIME_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_DIR))

from issuer_exposure import calculate_issuer_exposure  # noqa: E402


AS_OF = "2026-11-05"


def position(position_id: str, instrument_id: str, weight_pct: float, instrument_type: str, **extra):
    return {
        "position_id": position_id,
        "account_id": "SYN-ACCOUNT",
        "instrument_id": instrument_id,
        "isin": f"SYN-{instrument_id}",
        "share_class": "ETF" if instrument_type == "fund" else "Common",
        "source_id": f"synthetic:position:{position_id}",
        "source_uri": f"https://example.test/positions/{position_id}",
        "published_at": AS_OF,
        "retrieved_at": AS_OF,
        "weight_pct": weight_pct,
        "instrument_type": instrument_type,
        **extra,
    }


def issuer(issuer_id: str, weight_pct: float, factors: list[str]):
    return {
        "security_type": "issuer",
        "isin": f"SYN-{issuer_id}",
        "share_class": "Common",
        "issuer_id": issuer_id,
        "issuer_name": f"Synthetic {issuer_id}",
        "weight_pct": weight_pct,
        "factors": factors,
    }


def fund_reference(instrument_id: str, weight_pct: float):
    return {
        "security_type": "fund",
        "instrument_id": instrument_id,
        "isin": f"SYN-{instrument_id}",
        "share_class": "ETF",
        "weight_pct": weight_pct,
    }


def snapshot(instrument_id: str, constituents: list[dict]):
    return {
        "instrument_id": instrument_id,
        "as_of": AS_OF,
        "published_at": AS_OF,
        "retrieved_at": AS_OF,
        "completeness": "COMPLETE",
        "coverage_pct": 100,
        "source_id": f"synthetic:snapshot:{instrument_id}",
        "source_uri": f"https://example.test/snapshots/{instrument_id}",
        "constituents": constituents,
    }


class IssuerExposureTests(unittest.TestCase):
    def test_direct_and_overlapping_fund_positions_are_aggregated_once_per_issuer(self):
        arguments = {
            "as_of": AS_OF,
            "base_currency": "USD",
            "portfolio_id": "synthetic-portfolio",
            "positions": [
                position("direct-x", "SYN-EQUITY-X", 20, "equity", issuer_id="X", issuer_name="Synthetic X", factors=["AI"]),
                position("fund-a", "SYN-FUND-A", 40, "fund"),
                position("fund-b", "SYN-FUND-B", 40, "fund"),
            ],
            "fund_snapshots": [
                snapshot("SYN-FUND-A", [issuer("X", 25, ["AI"]), issuer("Y", 25, ["AI"]), issuer("Z", 50, ["SEMIS"])]),
                snapshot("SYN-FUND-B", [issuer("X", 50, ["AI"]), issuer("Y", 50, ["AI"])]),
            ],
            "factor_shocks": [{"scenario_id": "synthetic-ai-shock", "factor": "AI", "shock_pct": -20}],
        }

        result = calculate_issuer_exposure(arguments)

        self.assertEqual("COMPLETE", result["status"])
        self.assertEqual(100, result["source_coverage_pct"])
        by_issuer = {row["issuer_id"]: row for row in result["issuers"]}
        self.assertEqual({"X": 50, "Y": 30, "Z": 20}, {
            issuer_id: row["known_minimum_total_pct"] for issuer_id, row in by_issuer.items()
        })
        self.assertEqual(20, by_issuer["X"]["direct_weight_pct"])
        self.assertEqual(30, by_issuer["X"]["lookthrough_min_pct"])
        self.assertEqual(3800, result["concentration"]["hhi_pct_squared"])

        overlap = result["etf_overlap"][0]
        self.assertEqual("COMPLETE", overlap["status"])
        self.assertEqual(["X", "Y"], overlap["shared_issuer_ids"])
        self.assertEqual(50, overlap["shared_weight_pct_of_fund_a_min"])
        self.assertEqual(-16, result["stress"]["results"][0]["impact_pct_points"])
        self.assertEqual("NOT_SUMMED_OVERLAPPING_FACTORS", result["stress"]["aggregate_result"])

    def test_missing_fund_snapshots_withhold_concentration_metrics(self):
        arguments = {
            "as_of": AS_OF,
            "base_currency": "USD",
            "portfolio_id": "synthetic-portfolio",
            "positions": [
                position("direct-x", "SYN-EQUITY-X", 40, "equity", issuer_id="X", issuer_name="Synthetic X"),
                position("fund-a", "SYN-FUND-A", 60, "fund"),
            ],
            "fund_snapshots": [],
        }

        result = calculate_issuer_exposure(arguments)

        self.assertEqual("PARTIAL_MINIMUM", result["status"])
        self.assertFalse(result["decomposition_complete"])
        self.assertIn("FUND_SNAPSHOT_MISSING", result["decomposition_reasons"])
        self.assertEqual(40, result["source_coverage_pct"])
        self.assertEqual("MISSING", result["funds"][0]["decomposition"])
        self.assertEqual(60, result["funds"][0]["unknown_weight_pct"])
        self.assertEqual("BLOCKED_INCOMPLETE_ISSUER_DECOMPOSITION", result["concentration"]["completeness"])
        self.assertIsNone(result["concentration"]["hhi_pct_squared"])

    def test_partial_fund_snapshot_reports_known_minimum_without_complete_concentration(self):
        partial = snapshot("SYN-FUND-A", [issuer("X", 50, ["AI"])])
        partial.update(completeness="PARTIAL", coverage_pct=50)
        result = calculate_issuer_exposure({
            "as_of": AS_OF,
            "base_currency": "USD",
            "portfolio_id": "synthetic-portfolio",
            "positions": [position("fund-a", "SYN-FUND-A", 100, "fund")],
            "fund_snapshots": [partial],
        })

        self.assertEqual("PARTIAL_MINIMUM", result["status"])
        self.assertEqual(50, result["source_coverage_pct"])
        self.assertEqual(50, result["issuers"][0]["known_minimum_total_pct"])
        self.assertEqual(50, result["funds"][0]["unknown_weight_pct"])
        self.assertIsNone(result["concentration"]["top_3_issuer_weight_pct"])

    def test_nested_funds_are_looked_through_and_cycles_fail_closed(self):
        common = {
            "as_of": AS_OF,
            "base_currency": "USD",
            "portfolio_id": "synthetic-portfolio",
            "positions": [position("fund-a", "SYN-FUND-A", 100, "fund")],
        }
        nested = calculate_issuer_exposure({
            **common,
            "fund_snapshots": [
                snapshot("SYN-FUND-A", [fund_reference("SYN-FUND-B", 60), issuer("X", 40, [])]),
                snapshot("SYN-FUND-B", [issuer("Y", 100, [])]),
            ],
        })
        self.assertEqual("COMPLETE", nested["status"])
        self.assertEqual({"X": 40, "Y": 60}, {
            row["issuer_id"]: row["known_minimum_total_pct"] for row in nested["issuers"]
        })

        cyclic = calculate_issuer_exposure({
            **common,
            "fund_snapshots": [
                snapshot("SYN-FUND-A", [fund_reference("SYN-FUND-B", 100)]),
                snapshot("SYN-FUND-B", [fund_reference("SYN-FUND-A", 100)]),
            ],
        })
        self.assertEqual("PARTIAL_MINIMUM", cyclic["status"])
        self.assertIn("NESTED_FUND_SNAPSHOT_MISSING_OR_CYCLE", cyclic["decomposition_reasons"])
        self.assertEqual("BLOCKED_INCOMPLETE_ISSUER_DECOMPOSITION", cyclic["concentration"]["completeness"])
        self.assertIsNone(cyclic["concentration"]["hhi_pct_squared"])

    def test_prior_snapshot_comparison_requires_matching_complete_provenance(self):
        arguments = {
            "as_of": AS_OF,
            "base_currency": "USD",
            "portfolio_id": "synthetic-portfolio",
            "positions": [position("direct-x", "SYN-EQUITY-X", 100, "equity", issuer_id="X", issuer_name="Synthetic X")],
            "fund_snapshots": [],
            "previous_snapshot": {
                "as_of": "2026-11-04",
                "base_currency": "USD",
                "decomposition_complete": True,
                "issuers": [{"issuer_id": "X", "known_minimum_total_pct": 100}],
                "method": "issuer-lookthrough-v1",
                "portfolio_id": "synthetic-portfolio",
                "source_coverage_pct": 100,
                "status": "COMPLETE",
            },
        }
        comparable = calculate_issuer_exposure(arguments)
        self.assertEqual("COMPARABLE", comparable["snapshot_comparison"]["status"])
        self.assertEqual(0, comparable["snapshot_comparison"]["deltas"][0]["delta_pct_points"])

        incomplete = {**arguments, "previous_snapshot": {**arguments["previous_snapshot"], "source_coverage_pct": 95}}
        blocked = calculate_issuer_exposure(incomplete)
        self.assertEqual("NOT_COMPARABLE", blocked["snapshot_comparison"]["status"])
        self.assertIn("INCOMPLETE_DECOMPOSITION", blocked["snapshot_comparison"]["reasons"])


if __name__ == "__main__":
    unittest.main()
