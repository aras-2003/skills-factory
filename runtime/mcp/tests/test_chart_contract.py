import unittest
import json
import inspect
import sys
from pathlib import Path

RUNTIME_DIR = Path(__file__).resolve().parents[1]
ROOT = RUNTIME_DIR.parents[1]
sys.path.insert(0, str(RUNTIME_DIR))

from mcp.server.mcpserver.exceptions import ToolError

from chart_renderer import render_bar_chart, render_line_chart
import server


class ChartContractTests(unittest.TestCase):
    def test_python_peer_comparability_exposes_table_and_unsigned_receipt(self):
        def issuer(ticker, tier="TARGET", industry="Semiconductors"):
            return {
                "ticker": ticker, "sector": "Technology", "industry": industry,
                "business_model": "compute hardware" if tier != "ADJACENT" else "cloud software",
                "as_of": "2026-11-08", "cyclical": False,
                "comparison_group": "compute peers", "inclusion_rationale": "Synthetic contract fixture.",
                "peer_tier": tier, "economic_fit": {},
                "metrics": {"ev_sales": {
                    "name": "ev_sales", "value": "5", "unit": "multiple", "definition": "EV / sales",
                    "period": "TTM FY2025", "basis": "GAAP", "published_at": "2026-11-01",
                    "source_url": "https://example.test/source", "status": "VERIFIED", "horizon": "",
                    "currency": "USD", "period_alignment_group": "", "basis_group": "",
                    "supporting_source_urls": [],
                }},
            }
        result = server.compare_peer_comparability(
            as_of="2026-11-08", target=issuer("AMD"),
            peers=[issuer("MSFT", "ADJACENT", "Software")],
        )
        self.assertEqual("INSUFFICIENT_COMPARABLE_PEERS", result["status"])
        self.assertEqual("ADJACENT", result["table"]["rows"][1]["comparability_tier"])
        self.assertFalse(result["ranked"])
        self.assertEqual("compare_peer_comparability", result["tool_receipt"]["tool_name"])

    def test_python_facade_matches_canonical_tool_contract(self):
        contract = json.loads((ROOT / "runtime/contracts/mcp-tools-v1.json").read_text())
        actual = {
            name: sorted(parameter for parameter, value in inspect.signature(getattr(server, name)).parameters.items()
                         if value.default is inspect.Parameter.empty and parameter != "context")
            for name in contract["tools"]
        }
        self.assertEqual(actual, contract["tools"])

    def test_trace_context_is_injected_without_changing_published_tool_arguments(self):
        for name in json.loads((ROOT / "runtime/contracts/mcp-tools-v1.json").read_text())["tools"]:
            with self.subTest(tool=name):
                function_parameters = inspect.signature(getattr(server, name)).parameters
                self.assertEqual(function_parameters["context"].annotation, "Context")
                advertised = server.mcp._tool_manager.get_tool(name).parameters
                self.assertNotIn("context", advertised.get("properties", {}))

    def test_bar_chart_requires_original_shape_and_matches_cloud_limits(self):
        with self.assertRaises(ToolError):
            render_bar_chart(["a", "b"], [1], 2, "Example", "PLN", True)
        with self.assertRaises(ToolError):
            render_bar_chart(["a"], [1], 2, "Example", "PLN", True)
        with self.assertRaises(ToolError):
            render_bar_chart(["a"], [1], 1, "x" * 161, "PLN", True)

    def test_line_chart_rejects_stale_or_truncated_shape(self):
        with self.assertRaises(ToolError):
            render_line_chart(["Q1", "Q2"], ["series"], [[1]], 2, 1, 2, "Example", "PLN")
        with self.assertRaises(ToolError):
            render_line_chart(["Q1", "Q2"], ["series"], [[1, 2]], 2, 2, 2, "Example", "PLN")
        with self.assertRaises(ToolError):
            render_line_chart(["Q1", "Q2"], ["series"], [[1, 2]], 2, 1, 1, "Example", "PLN")

    def test_line_chart_enforces_cloud_point_and_series_limits(self):
        with self.assertRaises(ToolError):
            render_line_chart([f"x{i}" for i in range(101)], ["s"], [[0] * 101], 101, 1, 101, "Example", "")
        with self.assertRaises(ToolError):
            render_line_chart(["a", "b"], [f"s{i}" for i in range(9)], [[0, 1] for _ in range(9)], 2, 9, 2, "Example", "")

    def test_python_opportunity_score_matches_known_synthetic_contract(self):
        names = ["growth_durability", "business_quality", "reinvestment_returns", "valuation_expectations", "balance_sheet_resilience", "cycle_resilience"]
        def candidate(cid, values):
            return {"candidate_id": cid, "horizon": ">3y", "evidence": {
                name: {"value": values[name], "confidence": 0.8, "as_of_date": "2026-10-27", "source_ids": [f"synthetic:{cid}:{name}"], "definition": f"Synthetic test factor: {name}", "normalization_profile": f"normalized-{name}-v1", "quality": "PROVISIONAL"}
                for name in names
            }}
        inputs = {"as_of": "2026-10-27", "rows": [
            candidate(" lower ", dict(zip(names, [0.600, 0.600, 0.550, 0.500, 0.550, 0.500]))),
            candidate("higher", dict(zip(names, [0.600, 0.600, 0.550, 0.50625, 0.550, 0.500]))),
        ]}
        first = inputs["rows"][0]["evidence"][names[0]]
        first["source_ids"] = [" synthetic:lower " ]
        first["definition"] = " Synthetic test factor: growth_durability "
        first["normalization_profile"] = " normalized-growth_durability-v1 "
        result = server.calculate_opportunity_scores(**inputs)
        self.assertEqual("0.56", result["scores"][0]["score"])
        self.assertEqual("0.001", result["scores"][0]["score_difference_to_next"])
        self.assertEqual("COMPARABLE", result["scores"][0]["ranking_status"])
        self.assertEqual("lower", result["scores"][1]["candidate_id"])
        self.assertEqual(["synthetic:lower"], result["scores"][1]["factor_evidence"][names[0]]["source_ids"])
        self.assertEqual("unsigned_mcp_tool_call_receipt", result["tool_receipt"]["kind"])

    def test_python_opportunity_score_fails_closed_for_stale_evidence_and_bad_shape(self):
        names = ["growth_durability", "business_quality", "reinvestment_returns", "valuation_expectations", "balance_sheet_resilience", "cycle_resilience"]
        row = {"candidate_id": "synthetic", "horizon": ">3y", "evidence": {
            name: {"value": 0.6, "confidence": 0.8, "as_of_date": "2024-01-01" if name == "cycle_resilience" else "2026-10-27", "source_ids": [f"synthetic:{name}"], "definition": name, "normalization_profile": f"normalized-{name}-v1", "quality": "VERIFIED"}
            for name in names
        }}
        result = server.calculate_opportunity_scores(as_of="2026-10-27", rows=[row])
        self.assertEqual("NOT_SCORED", result["scores"][0]["status"])
        self.assertIn("cycle_resilience", result["scores"][0]["stale_factors"])
        with self.assertRaises(ToolError):
            server.calculate_opportunity_scores(as_of="2026-02-30", rows=[row])

    def test_python_issuer_exposure_calculates_complete_direct_position_with_receipt(self):
        result = server.calculate_issuer_exposure(
            as_of="2026-11-04",
            base_currency="PLN",
            portfolio_id="synthetic-portfolio",
            fund_snapshots=[],
            positions=[{
                "position_id": "synthetic-position",
                "account_id": "synthetic-account",
                "instrument_id": "SYNTHETIC-EQUITY",
                "isin": "US0000000001",
                "share_class": "Common",
                "source_id": "synthetic:position",
                "source_uri": "https://example.test/position",
                "published_at": "2026-11-04",
                "retrieved_at": "2026-11-04",
                "weight_pct": 100,
                "instrument_type": "equity",
                "issuer_id": "SYNTHETIC-ISSUER",
                "issuer_name": "Synthetic Issuer",
                "factors": ["SEMICONDUCTOR"],
            }],
        )
        self.assertEqual("COMPLETE", result["status"])
        self.assertEqual(100, result["issuers"][0]["known_minimum_total_pct"])
        self.assertEqual("SEMICONDUCTOR", result["overlapping_factor_views"][0]["factor"])
        self.assertEqual("calculate_issuer_exposure", result["tool_receipt"]["tool_name"])


if __name__ == "__main__":
    unittest.main()
