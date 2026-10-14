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
                         if value.default is inspect.Parameter.empty)
            for name in contract["tools"]
        }
        self.assertEqual(actual, contract["tools"])

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


if __name__ == "__main__":
    unittest.main()
