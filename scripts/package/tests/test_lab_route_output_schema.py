from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SERVER_PATH = ROOT / "plugins" / "skills-factory-lab" / "mcp" / "server.py"


def load_lab_server():
    spec = importlib.util.spec_from_file_location("skills_factory_lab_server_test", SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Lab MCP server")

    class TestMCPServer:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def tool(self):
            return lambda function: function

        def streamable_http_app(self):
            return object()

    mcp_package = types.ModuleType("mcp")
    mcp_package.__path__ = []
    mcp_server_package = types.ModuleType("mcp.server")
    mcp_server_package.__path__ = []
    mcp_server_package.MCPServer = TestMCPServer
    mcp_server_mcpserver = types.ModuleType("mcp.server.mcpserver")
    mcp_server_mcpserver.__path__ = []
    exceptions = types.ModuleType("mcp.server.mcpserver.exceptions")
    exceptions.ToolError = type("ToolError", (Exception,), {})

    chart_renderer = types.ModuleType("chart_renderer")
    chart_renderer.render_bar_chart = lambda *_args, **_kwargs: []
    chart_renderer.render_line_chart = lambda *_args, **_kwargs: []

    investment_runtime = types.ModuleType("investment_runtime")
    investment_runtime.route_investment_request = lambda _request: {
        "is_investment_request": True,
        "route": "portfolio",
        "child_workflow": "investment-portfolio-review",
        "must_invoke_child_workflow": True,
        "routing_receipt": (
            "ROUTE=portfolio; CHILD=investment-portfolio-review; "
            "NEXT_ACTION=load_skill(investment-portfolio-review)"
        ),
    }

    skill_catalog = types.ModuleType("skill_catalog")
    skill_catalog.list_skills = lambda: {}
    skill_catalog.load_skill = lambda _name: {}
    skill_catalog.packaged_release_identity = lambda: None
    skill_catalog.catalog_digest = lambda: ""

    modules = {
        "mcp": mcp_package,
        "mcp.server": mcp_server_package,
        "mcp.server.mcpserver": mcp_server_mcpserver,
        "mcp.server.mcpserver.exceptions": exceptions,
        "chart_renderer": chart_renderer,
        "investment_runtime": investment_runtime,
        "skill_catalog": skill_catalog,
    }
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class LabRouteOutputSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = load_lab_server()

    def test_route_tool_annotation_accepts_nullable_and_nested_receipt_fields(self) -> None:
        annotation = get_type_hints(self.server.route_investment_request)["return"]
        self.assertIs(get_origin(annotation), dict)
        self.assertIs(get_args(annotation)[1], Any)

        result = self.server.route_investment_request(
            "Review a hypothetical investment portfolio."
        )
        self.assertIsNone(result["outcome"])
        self.assertIsInstance(result["tool_receipt"], dict)
        self.assertEqual("investment-portfolio-review", result["child_workflow"])
        json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
