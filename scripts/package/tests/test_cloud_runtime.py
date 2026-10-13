from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MCP_DIR = ROOT / "runtime" / "mcp"
sys.path.insert(0, str(MCP_DIR))


def load_cloud_server():
    spec = importlib.util.spec_from_file_location(
        "skills_factory_server", MCP_DIR / "server.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load cloud server")
    class TestMCPServer:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def tool(self):
            return lambda function: function

        def streamable_http_app(self):
            return object()

    fake_mcp = types.ModuleType("mcp")
    fake_mcp_server = types.ModuleType("mcp.server")
    fake_mcp_server.MCPServer = TestMCPServer
    fake_mcp.server = fake_mcp_server
    fake_mcpserver = types.ModuleType("mcp.server.mcpserver")
    fake_exceptions = types.ModuleType("mcp.server.mcpserver.exceptions")
    class TestToolError(Exception):
        pass
    fake_exceptions.ToolError = TestToolError

    fake_renderer = types.ModuleType("chart_renderer")
    fake_renderer.render_bar_chart = lambda *_args, **_kwargs: []
    fake_renderer.render_line_chart = lambda *_args, **_kwargs: []

    module = importlib.util.module_from_spec(spec)
    fake_investment = types.ModuleType("investment_runtime")
    def fake_route(request):
        if "ETF risk policy" in request:
            return {
                "is_investment_request": True,
                "route": "policy",
                "child_workflow": "investment-policy-design",
            }
        return {"is_investment_request": False, "route": "not_applicable"}

    fake_investment.route_investment_request = fake_route
    with patch.dict(
        sys.modules,
        {
            "mcp": fake_mcp,
            "mcp.server": fake_mcp_server,
            "mcp.server.mcpserver": fake_mcpserver,
            "mcp.server.mcpserver.exceptions": fake_exceptions,
            "chart_renderer": fake_renderer,
            "investment_runtime": fake_investment,
        },
    ):
        spec.loader.exec_module(module)
    return module


class CloudRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = load_cloud_server()

    def test_route_result_declares_routing_only_as_non_execution(self) -> None:
        result = self.server.route_investment_request(
            "Design an ETF risk policy with concentration caps and rebalancing rules."
        )

        self.assertEqual("policy", result["route"])
        self.assertEqual("investment-policy-design", result["child_workflow"])
        self.assertFalse(result["workflow_executed"])
        self.assertEqual("routed_only", result["execution_state"])
        self.assertEqual(
            "load_child_workflow_then_follow",
            result["response_policy"],
        )

    def test_runtime_info_is_explicitly_unattested_without_deployment_identity(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            result = self.server.runtime_info()

        self.assertEqual("unattested", result["attestation_status"])
        self.assertEqual("unattested", result["release_id"])
        self.assertEqual("unattested", result["source_revision"])
        self.assertEqual("runtime_info", result["tool_receipt"]["tool_name"])

    def test_runtime_info_verifies_only_when_all_identity_fields_are_present(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "SKILLS_FACTORY_RELEASE_ID": "0.33.4+abc123",
                "SKILLS_FACTORY_SOURCE_REVISION": "abc123",
                "SKILLS_FACTORY_CHANNEL": "lab",
                "SKILLS_FACTORY_CAPABILITY_CONTRACT_VERSION": "repository-side-v1",
                "SKILLS_FACTORY_TOOL_SCHEMA_DIGEST": "digest-123",
                "SKILLS_FACTORY_DEPLOYED_AT": "2026-10-07T12:00:00Z",
            },
            clear=True,
        ):
            result = self.server.runtime_info()

        self.assertEqual("verified", result["attestation_status"])
        self.assertEqual("lab", result["channel"])
        self.assertEqual("digest-123", result["tool_schema_digest"])

    def test_unrelated_finance_request_is_not_marked_routed_only(self) -> None:
        result = self.server.route_investment_request(
            "How does a fixed-rate mortgage work?"
        )

        self.assertFalse(result["is_investment_request"])
        self.assertNotIn("execution_state", result)
        self.assertNotIn("response_policy", result)

    def test_punctuation_only_request_is_not_misrouted_by_negated_investment_word(self) -> None:
        result = self.server.route_investment_request(
            "Fix punctuation only: 'Zespół, pracuje sprawnie'. No finance, process, organization or investments analysis."
        )

        self.assertFalse(result["is_investment_request"])
        self.assertEqual("not_applicable", result["route"])

    def test_unrelated_governance_and_security_prompts_are_not_investment_requests(self) -> None:
        for prompt in (
            "The archived BACKLOG.json says tasks are proposed, while Issues and Project show active work.",
            "A public repository has no confirmed LICENSE and private vulnerability reporting is not verified.",
            "Repo source CI is green, but reading branch protection /rules yields HTTP 403.",
            "A scanner passes a source fixture but no model/runtime tool trace exists.",
        ):
            with self.subTest(prompt=prompt):
                result = self.server.route_investment_request(prompt)
                self.assertFalse(result["is_investment_request"])
                self.assertEqual("not_applicable", result["route"])

    def test_cloud_instructions_separate_routing_from_loaded_workflow_execution(self) -> None:
        instructions = " ".join(self.server.CLOUD_SERVER_INSTRUCTIONS.lower().split())

        self.assertIn("do not call route_investment_request for an unrelated task", instructions)
        self.assertIn("load the exact returned child with load_skill", instructions)
        self.assertIn("they do not prohibit the host model", instructions)
        self.assertIn("if the child or a required", instructions)
        self.assertIn("do not draft policy", instructions)
        self.assertIn("does not attest to", instructions)
        self.assertIn("runtime_info", instructions)
        self.assertIn('attestation_status "unattested"', instructions)

    def test_chart_receipt_distinguishes_rendered_artifact_from_client_display(self) -> None:
        result = self.server.render_bar_chart(["A"], [1.0])
        receipt_text = next(item for item in result if isinstance(item, str) and item.startswith("MCP_TOOL_RECEIPT "))
        self.assertIn('"artifact_state": "rendered"', receipt_text)
        self.assertIn('"client_display_state": "not_observable"', receipt_text)

    def test_chart_renderer_error_has_explicit_failure_receipt(self) -> None:
        with patch.object(self.server, "_render_bar_chart", side_effect=RuntimeError("renderer unavailable")):
            with self.assertRaisesRegex(Exception, '"artifact_state": "FAIL_RENDERER_INVOCATION"'):
                self.server.render_bar_chart(["A"], [1.0])

    def test_controlled_mcp_failure_receipts_never_claim_client_display(self) -> None:
        for exc in (
            TimeoutError("fixture timeout"),
            PermissionError("fixture denied"),
            ValueError("fixture schema mismatch"),
            RuntimeError("fixture renderer unavailable"),
        ):
            with self.subTest(exception=type(exc).__name__):
                with patch.object(self.server, "_render_bar_chart", side_effect=exc):
                    with self.assertRaises(Exception) as context:
                        self.server.render_bar_chart(["A"], [1.0])
                message = str(context.exception)
                self.assertIn('"status": "FAILURE"', message)
                self.assertIn('"artifact_state": "FAIL_RENDERER_INVOCATION"', message)
                self.assertIn('"client_display_state": "not_applicable"', message)
                self.assertNotIn('"artifact_state": "rendered"', message)

    def test_route_receipt_distinguishes_routing_from_child_execution(self) -> None:
        result = self.server.route_investment_request("ETF risk policy")
        self.assertEqual("not_executed", result["workflow_execution_state"])
        self.assertIsNone(result["outcome"])
        self.assertEqual("route_investment_request", result["tool_receipt"]["tool_name"])


if __name__ == "__main__":
    unittest.main()
