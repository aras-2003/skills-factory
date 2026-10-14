# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp==2.3.0", "matplotlib==3.11.2", "PyYAML==6.0.3"]
# ///

"""Single Skills Factory MCP runtime for local stdio and remote HTTP profiles."""

from __future__ import annotations

import os
import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from chart_renderer import render_bar_chart as _render_bar_chart
from chart_renderer import render_line_chart as _render_line_chart
from investment_runtime import route_investment_request as _route_investment_request
from skill_catalog import list_skills as _list_skills
from skill_catalog import load_skill as _load_skill
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

SERVER_INSTRUCTIONS = """
Skills Factory runtime contract.

Call runtime_info first when a test, receipt or compatibility decision depends
on the exact runtime identity. A result with attestation_status "unattested"
must not be treated as evidence of exact-version compatibility.

For every request about investments, securities, ETFs, a portfolio, investment
themes, opportunities, policy or risk limits, call route_investment_request
before composing substantive output. This runtime only routes the request; it
does not execute a selected workflow, read holdings, fetch market data or
make investment recommendations. If execution_state is "routed_only" or
workflow_executed is false, stop without substantive investment output.
Do not draft policy, thresholds, allocations, valuations or buy/sell opinions
from a routing result alone.

Use chart tools only with explicit numeric inputs from the user or a completed,
source-backed workflow. Preserve supplied labels, values and units. Do not
invent missing observations.

Tool results include an unsigned tool_receipt with canonical input and output
SHA-256 digests. It records the MCP tool execution only; it does not attest to
client display or prove that a routed child workflow ran.

The packaged Lab catalog is the source of truth for skill parity. Use
list_skills when selecting a packaged capability and load_skill before
executing that capability. The MCP server loads the same packaged SKILL.md
instructions as the Lab; the host model executes those instructions. Do not
claim that the MCP server itself completed model reasoning or external actions.
""".strip()
CLOUD_SERVER_INSTRUCTIONS = SERVER_INSTRUCTIONS

RUNTIME_FIELDS = (
    "release_id",
    "source_revision",
    "channel",
    "capability_contract_version",
    "tool_schema_digest",
    "deployed_at",
)


def _runtime_value(name: str, default: str = "unattested") -> str:
    value = os.environ.get(name, "").strip()
    return value or default


def _digest_value(value: Any) -> Any:
    """Return a stable, content-only representation suitable for receipt hashing."""
    if hasattr(value, "data") and hasattr(value, "format"):
        payload = bytes(value.data)
        return {
            "mime_type": value.format,
            "content_sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }
    if isinstance(value, bytes):
        return {"content_sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
    if isinstance(value, Mapping):
        return {str(key): _digest_value(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_digest_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _json_sha256(value: Any) -> str:
    canonical = json.dumps(
        _digest_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _tool_receipt(tool_name: str, arguments: Any, result: Any) -> dict[str, Any]:
    receipt = {
        "schema_version": "1.0",
        "kind": "unsigned_mcp_tool_call_receipt",
        "tool_name": tool_name,
        "status": "SUCCESS",
        "execution_state": "executed",
        "completed_at": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "source_revision": _runtime_value("SKILLS_FACTORY_SOURCE_REVISION"),
        "input_sha256": _json_sha256(arguments),
        "output_sha256": _json_sha256(result),
    }
    if tool_name in {"render_bar_chart", "render_line_chart"}:
        receipt.update({"artifact_state": "rendered", "client_display_state": "not_observable"})
    return receipt


def _with_tool_receipt(tool_name: str, arguments: Any, result: Any) -> Any:
    receipt = _tool_receipt(tool_name, arguments, result)
    if isinstance(result, dict):
        return {**result, "tool_receipt": receipt}
    if isinstance(result, list):
        return [*result, "MCP_TOOL_RECEIPT " + json.dumps(receipt, sort_keys=True)]
    return {"result": result, "tool_receipt": receipt}


def _render_with_receipt(tool_name: str, arguments: dict[str, Any], render) -> Any:
    try:
        result = render()
    except Exception as exc:
        error = {"error_type": type(exc).__name__, "error_sha256": _json_sha256(str(exc))}
        receipt = _tool_receipt(tool_name, arguments, error)
        receipt.update(
            {
                "status": "FAILURE",
                "artifact_state": "FAIL_RENDERER_INVOCATION",
                "client_display_state": "not_applicable",
                **error,
            }
        )
        raise ToolError("CHART_RENDER_FAILED " + json.dumps(receipt, sort_keys=True)) from exc
    return _with_tool_receipt(tool_name, arguments, result)

mcp = MCPServer(
    "Skills Factory runtime",
    description="Unified Skills Factory runtime for investment routing and factual chart rendering.",
    instructions=SERVER_INSTRUCTIONS,
)


@mcp.tool()
def runtime_info() -> dict[str, str]:
    """Return deployment identity without performing any external action."""
    values = {
        "runtime_name": "Skills Factory runtime",
        "release_id": _runtime_value("SKILLS_FACTORY_RELEASE_ID"),
        "source_revision": _runtime_value("SKILLS_FACTORY_SOURCE_REVISION"),
        "channel": _runtime_value("SKILLS_FACTORY_CHANNEL", "unknown"),
        "capability_contract_version": _runtime_value(
            "SKILLS_FACTORY_CAPABILITY_CONTRACT_VERSION", "repository-side-v1"
        ),
        "tool_schema_digest": _runtime_value("SKILLS_FACTORY_TOOL_SCHEMA_DIGEST"),
        "deployed_at": _runtime_value("SKILLS_FACTORY_DEPLOYED_AT"),
    }
    values["attestation_status"] = (
        "verified"
        if all(values[field] not in {"unattested", "unknown"} for field in RUNTIME_FIELDS)
        else "unattested"
    )
    return _with_tool_receipt("runtime_info", {}, values)


@mcp.tool()
def list_skills() -> dict:
    """List the skills packaged in the same catalog as the active Lab profile."""
    return _with_tool_receipt("list_skills", {}, _list_skills())


@mcp.tool()
def load_skill(skill_name: str) -> dict:
    """Load packaged skill instructions and safe textual references for host-model execution."""
    return _with_tool_receipt(
        "load_skill", {"skill_name": skill_name}, _load_skill(skill_name)
    )


@mcp.tool()
def route_investment_request(user_request: str) -> dict[str, str | bool]:
    """MANDATORY first step for every investment request, before analysis."""
    result = _route_investment_request(user_request)
    if result.get("is_investment_request"):
        result.update(
            {
                "workflow_executed": False,
                "execution_state": "routed_only",
                "workflow_execution_state": "not_executed",
                "execution_state_reason": "router selected a workflow but did not execute it",
                "outcome": None,
                "response_policy": "stop_without_substantive_investment_output",
            }
        )
    return _with_tool_receipt("route_investment_request", {"user_request": user_request}, result)


@mcp.tool()
def render_bar_chart(
    labels: list[str],
    values: list[float],
    expected_points: int,
    title: str,
    unit: str,
    horizontal: bool,
):
    """Render a deterministic factual bar chart from explicit values."""
    arguments = {
        "labels": labels,
        "values": values,
        "expected_points": expected_points,
        "title": title,
        "unit": unit,
        "horizontal": horizontal,
    }
    return _render_with_receipt(
        "render_bar_chart",
        arguments,
        lambda: _render_bar_chart(labels, values, expected_points, title, unit, horizontal),
    )


@mcp.tool()
def render_line_chart(
    x_labels: list[str],
    series_names: list[str],
    series_values: list[list[float]],
    expected_x_labels: int,
    expected_series: int,
    expected_points_per_series: int,
    title: str,
    unit: str,
):
    """Render a deterministic factual line chart from explicit values."""
    arguments = {
        "x_labels": x_labels,
        "series_names": series_names,
        "series_values": series_values,
        "expected_x_labels": expected_x_labels,
        "expected_series": expected_series,
        "expected_points_per_series": expected_points_per_series,
        "title": title,
        "unit": unit,
    }
    return _render_with_receipt(
        "render_line_chart",
        arguments,
        lambda: _render_line_chart(
            x_labels, series_names, series_values,
            expected_x_labels, expected_series, expected_points_per_series,
            title, unit,
        ),
    )


app = mcp.streamable_http_app()


if __name__ == "__main__":
    mcp.run()
