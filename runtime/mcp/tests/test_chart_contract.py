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
            candidate("lower", dict(zip(names, [0.600, 0.600, 0.550, 0.500, 0.550, 0.500]))),
            candidate("higher", dict(zip(names, [0.600, 0.600, 0.550, 0.50625, 0.550, 0.500]))),
        ]}
        result = server.calculate_opportunity_scores(**inputs)
        self.assertEqual("0.56", result["scores"][0]["score"])
        self.assertEqual("0.001", result["scores"][0]["score_difference_to_next"])
        self.assertEqual("COMPARABLE", result["scores"][0]["ranking_status"])
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


if __name__ == "__main__":
    unittest.main()
