# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp==2.3.0", "matplotlib==3.11.2", "PyYAML==6.0.3", "opentelemetry-sdk==1.45.0", "opentelemetry-exporter-otlp-proto-http==1.45.0"]
# ///

"""Single Skills Factory MCP runtime for local stdio and remote HTTP profiles."""

from __future__ import annotations

import os
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from chart_renderer import render_bar_chart as _render_bar_chart
from chart_renderer import render_line_chart as _render_line_chart
from investment_runtime import route_investment_request as _route_investment_request
from skill_catalog import list_skills as _list_skills
from skill_catalog import load_skill as _load_skill
from skill_catalog import (
    packaged_payload_integrity,
    packaged_release_identity,
    packaged_runtime_value,
    catalog_digest,
)
from mcp.server import MCPServer
from mcp.server.mcpserver.context import Context
from mcp.server.mcpserver.exceptions import ToolError
from observability import execute_tool, tool_span
from opportunity_score import calculate_opportunity_scores as _calculate_opportunity_scores
from issuer_exposure import calculate_issuer_exposure as _calculate_issuer_exposure

_PEER_SCRIPT_RELATIVE_PATH = Path("skills/investing/valuation-scenario-review/scripts")
_PEER_SCRIPT_DIRECTORY = next(
    (candidate for candidate in (
        Path(__file__).resolve().parent,
        *(base / _PEER_SCRIPT_RELATIVE_PATH for base in Path(__file__).resolve().parents[1:3]),
    ) if (candidate / "peer_comparison.py").is_file()),
    Path(__file__).resolve().parents[2] / _PEER_SCRIPT_RELATIVE_PATH,
)
if str(_PEER_SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(_PEER_SCRIPT_DIRECTORY))
from peer_comparison import (  # noqa: E402
    EconomicFitEvidence as _EconomicFitEvidence,
    EvidenceState as _PeerEvidenceState,
    IssuerSnapshot as _IssuerSnapshot,
    PeerMetric as _PeerMetric,
    compare_peer_set as _compare_peer_set,
)

SERVER_INSTRUCTIONS = """
Skills Factory runtime contract.

Call runtime_info first when a test, receipt or compatibility decision depends
on the exact runtime identity. A result with attestation_status "unattested"
does not attest the host's deployment identity. For a Lab package, exact
package compatibility may be established only when package_integrity_status is
"verified" and the Lab release_id, source_revision and payload digest all match
the expected artifact. This checks installed bytes against the adjacent
unsigned manifest; it is not host/deployment attestation or evidence that an
installer behaved correctly. Do not infer identity from version labels alone.

Do not call route_investment_request for an unrelated task, including editing,
proofreading, security review, governance, or accounting. A negated mention of
investing does not turn such a task into an Investment OS request.

For a request whose decision object is an investment, security, ETF, portfolio,
investment theme, opportunity, policy or risk limit:
1. Call route_investment_request before substantive investment work.
2. Load the exact returned child with load_skill before analysis.
3. The routing result's routed_only / workflow_executed=false fields mean that
   the router performed routing only. They do not prohibit the host model from
   following a successfully loaded child workflow. The host model, not this MCP
   server, executes those instructions.
   When next_action is load_front_door_then_clarify, load the front door and ask
   the user to clarify before substantive analysis or recommendations.
4. Follow the child's sequence and evidence gates. If the child or a required
   provider/read/write capability is unavailable, stop and report BLOCKED or
   NOT RUN. Never imply that route execution alone completed the workflow.
Do not draft policy, thresholds, allocations, valuations or buy/sell opinions
from a routing result alone.

When the caller supplies already-normalized, dated, source-identified factor
evidence, use calculate_opportunity_scores for the fixed provisional model.
It applies evidence gates and comparable ranking only; it does not verify
sources, derive factors, research candidates, estimate probabilities or
recommend trades. Preserve NOT_SCORED results.

Use calculate_issuer_exposure only for explicit caller-supplied positions and
dated fund constituent snapshots. It is a read-only calculation: it does not
retrieve or verify sources, access canonical portfolios, persist data, or
execute trades. Preserve partial coverage and blocked concentration results.

Use chart tools only with explicit numeric inputs from the user or a completed,
source-backed workflow. Preserve supplied labels, values and units. Do not
invent missing observations.

Tool results include an unsigned tool_receipt with canonical input and output
SHA-256 digests. It records the MCP tool execution only; it does not attest to
client display, host-model reasoning, or execution of a routed child workflow.

For source/backlog reconciliation, request the exact source revision and ID sets
before identifying a missing item. Catalog counts do not prove GitHub Project
membership, native fields/dependencies, or runtime acceptance. Missing revision
means BLOCKED_SOURCE_REVISION for that comparison, not an invented source match.

The packaged Lab catalog is the source of truth for skill parity. Use
list_skills when selecting a packaged capability and load_skill before
executing that capability. Do not claim that the MCP server itself completed
model reasoning or external actions.
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


def _runtime_identity_is_well_formed(values: Mapping[str, str]) -> bool:
    """Validate unsigned runtime identity fields, not deployment authenticity."""
    if any(values.get(field) in {None, "", "unattested", "unknown"} for field in RUNTIME_FIELDS):
        return False
    if not re.fullmatch(r"[0-9a-f]{40}", values["source_revision"]):
        return False
    digest = values["tool_schema_digest"].removeprefix("sha256:")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        return False
    try:
        observed = datetime.fromisoformat(values["deployed_at"].replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return False
    return observed.tzinfo is not None

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


def _tool_receipt(tool_name: str, arguments: Any, result: Any, run_id: str | None = None) -> dict[str, Any]:
    receipt = {
        "schema_version": "1.0",
        "kind": "unsigned_mcp_tool_call_receipt",
        "tool_name": tool_name,
        "status": "SUCCESS",
        "execution_state": "executed",
        "completed_at": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "source_revision": packaged_runtime_value("source_revision"),
        "input_sha256": _json_sha256(arguments),
        "output_sha256": _json_sha256(result),
    }
    if tool_name in {"render_bar_chart", "render_line_chart"}:
        receipt.update({"artifact_state": "rendered", "client_display_state": "not_observable"})
    if run_id:
        receipt["run_id"] = run_id
    return receipt


def _with_tool_receipt(tool_name: str, arguments: Any, result: Any, run_id: str | None = None) -> Any:
    receipt = _tool_receipt(tool_name, arguments, result, run_id)
    if isinstance(result, dict):
        return {**result, "tool_receipt": receipt}
    if isinstance(result, list):
        return [*result, "MCP_TOOL_RECEIPT " + json.dumps(receipt, sort_keys=True)]
    return {"result": result, "tool_receipt": receipt}


def _request_meta(context: Context | None) -> Mapping[str, Any] | None:
    """Return untrusted MCP metadata only for W3C trace correlation."""
    return context.request_context.meta if context is not None else None


def _render_with_receipt(tool_name: str, arguments: dict[str, Any], render, context: Context | None = None) -> Any:
    with tool_span(tool_name, arguments, request_meta=_request_meta(context)) as (span, run_id):
        try:
            result = render()
        except Exception as exc:
            error = {"error_type": type(exc).__name__, "error_sha256": _json_sha256(str(exc))}
            receipt = _tool_receipt(tool_name, arguments, error, run_id)
            receipt.update(
                {
                    "status": "FAILURE",
                    "artifact_state": "FAIL_RENDERER_INVOCATION",
                    "client_display_state": "not_applicable",
                    **error,
                }
            )
            raise ToolError("CHART_RENDER_FAILED " + json.dumps(receipt, sort_keys=True)) from exc
        if isinstance(result, Mapping):
            for key, attribute in (("version", "version"), ("content_sha256", "digest")):
                if result.get(key):
                    span.set_attribute(f"skills_factory.capability.{attribute}", str(result[key]))
        return _with_tool_receipt(tool_name, arguments, result, run_id)

mcp = MCPServer(
    "Skills Factory runtime",
    description="Unified Skills Factory runtime for investment routing and factual chart rendering.",
    instructions=SERVER_INSTRUCTIONS,
)


@mcp.tool()
def runtime_info(context: Context = None) -> dict[str, Any]:
    """Return deployment identity without performing any external action."""
    def operation() -> dict[str, Any]:
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
            "verified" if _runtime_identity_is_well_formed(values) else "unattested"
        )
        values["attestation_basis"] = "unsigned_runtime_environment_fields_only"
        values["installation_behavior_verified"] = False
        installed = packaged_release_identity()
        package_integrity = packaged_payload_integrity(installed)
        values["package_integrity_status"] = package_integrity["status"]
        values["package_integrity_basis"] = "installed_payload_digest_matches_adjacent_unsigned_manifest"
        if package_integrity.get("payload_content_sha256"):
            values["package_integrity_sha256"] = package_integrity["payload_content_sha256"]
        values["lab_release"] = installed or None
        values["software_release"] = ({k: installed[k] for k in ("version", "release_id", "source_revision")} if installed else None)
        values["capabilities"] = ["runtime_info", "list_skills", "load_skill", "route_investment_request", "calculate_opportunity_scores", "compare_peer_comparability", "calculate_issuer_exposure", "render_bar_chart", "render_line_chart"]
        if (installed and package_integrity["status"] == "verified"
                and values["channel"] == "lab"
                and installed["source_revision"] == values["source_revision"]
                and installed["release_id"] == values["release_id"]):
            values["payload_content_sha256"] = installed["payload_content_sha256"]
            values["catalog_digest"] = catalog_digest()
            values["manifest_binding"] = "installed_manifest_matches_runtime_environment"
        elif installed and package_integrity["status"] == "verified":
            values["payload_content_sha256"] = installed["payload_content_sha256"]
            values["catalog_digest"] = catalog_digest()
            values["manifest_binding"] = "installed_manifest_matches_runtime_payload"
        else:
            values["manifest_binding"] = "unavailable_or_mismatched"
        return values
    return execute_tool("runtime_info", {}, operation, _with_tool_receipt, request_meta=_request_meta(context))


@mcp.tool()
def list_skills(context: Context = None) -> dict:
    """List the skills packaged in the same catalog as the active Lab profile."""
    return execute_tool("list_skills", {}, _list_skills, _with_tool_receipt, request_meta=_request_meta(context))


@mcp.tool()
def load_skill(skill_name: str, context: Context = None) -> dict:
    """Load packaged skill instructions and safe textual references for host-model execution."""
    return execute_tool(
        "load_skill", {"skill_name": skill_name}, lambda: _load_skill(skill_name), _with_tool_receipt,
        request_meta=_request_meta(context),
    )


@mcp.tool()
def route_investment_request(user_request: str, context: Context = None) -> dict[str, Any]:
    """MANDATORY first step for every investment request, before analysis."""
    def operation() -> dict[str, Any]:
        result = _route_investment_request(user_request)
        if result.get("is_investment_request"):
            result.update(
                {
                    "workflow_executed": False,
                    "execution_state": "routed_only",
                    "workflow_execution_state": "not_executed",
                    "execution_state_reason": "router selected a workflow but did not execute it",
                    "outcome": None,
                    "response_policy": (
                        "load_front_door_then_clarify_before_analysis"
                        if result.get("next_action") == "load_front_door_then_clarify"
                        else "load_child_workflow_then_follow"
                    ),
                }
            )
        return result
    return execute_tool(
        "route_investment_request", {"user_request": user_request}, operation, _with_tool_receipt,
        request_meta=_request_meta(context),
    )


@mcp.tool()
def calculate_opportunity_scores(as_of: str, rows: list[dict[str, Any]], context: Context = None) -> dict[str, Any]:
    """Score supplied normalized candidate evidence with the fixed provisional model."""
    arguments = {"as_of": as_of, "rows": rows}
    def operation() -> dict[str, Any]:
        try:
            return _calculate_opportunity_scores(arguments)
        except (ValueError, TypeError) as exc:
            raise ToolError("INVALID_OPPORTUNITY_SCORE_INPUT") from exc
    return execute_tool("calculate_opportunity_scores", arguments, operation, _with_tool_receipt, request_meta=_request_meta(context))


@mcp.tool()
def calculate_issuer_exposure(
    as_of: str,
    base_currency: str,
    fund_snapshots: list[dict[str, Any]],
    portfolio_id: str,
    positions: list[dict[str, Any]],
    portfolio_value_pln: float | None = None,
    previous_snapshot: dict[str, Any] | None = None,
    scenario_positions: list[dict[str, Any]] | None = None,
    factor_shocks: list[dict[str, Any]] | None = None,
    context: Context = None,
) -> dict[str, Any]:
    """Calculate issuer look-through from explicit, dated caller evidence only."""
    arguments = {
        "as_of": as_of,
        "base_currency": base_currency,
        "fund_snapshots": fund_snapshots,
        "portfolio_id": portfolio_id,
        "positions": positions,
        "portfolio_value_pln": portfolio_value_pln,
        "previous_snapshot": previous_snapshot,
        "scenario_positions": scenario_positions,
        "factor_shocks": factor_shocks,
    }
    def operation() -> dict[str, Any]:
        try:
            return _calculate_issuer_exposure(arguments)
        except (ValueError, TypeError, KeyError) as exc:
            raise ToolError("INVALID_ISSUER_EXPOSURE_INPUT") from exc
    return execute_tool("calculate_issuer_exposure", arguments, operation, _with_tool_receipt, request_meta=_request_meta(context))


@mcp.tool()
def compare_peer_comparability(as_of: str, peers: list[dict[str, Any]], target: dict[str, Any], context: Context = None) -> dict[str, Any]:
    """Compare caller-supplied issuer snapshots without ranking or advice."""
    arguments = {"as_of": as_of, "peers": peers, "target": target}

    def snapshot(value: Mapping[str, Any]) -> _IssuerSnapshot:
        metrics = {
            name: _PeerMetric(
                name=item["name"], value=None if item["value"] is None else Decimal(item["value"]),
                unit=item["unit"], definition=item["definition"], period=item["period"], basis=item["basis"],
                published_at=item["published_at"], source_url=item["source_url"],
                status=_PeerEvidenceState(item["status"]), horizon=item.get("horizon", ""),
                currency=item["currency"], period_alignment_group=item.get("period_alignment_group", ""),
                basis_group=item.get("basis_group", ""), supporting_source_urls=tuple(item.get("supporting_source_urls", [])),
            ) for name, item in value["metrics"].items()
        }
        fit = {name: _EconomicFitEvidence(**item) for name, item in value.get("economic_fit", {}).items()}
        return _IssuerSnapshot(
            ticker=value["ticker"], sector=value["sector"], industry=value["industry"],
            business_model=value["business_model"], as_of=value["as_of"], metrics=metrics,
            cyclical=value.get("cyclical", False), comparison_group=value["comparison_group"],
            inclusion_rationale=value.get("inclusion_rationale", ""), peer_tier=value.get("peer_tier", "TARGET"), economic_fit=fit,
        )

    def operation() -> dict[str, Any]:
        try:
            result = _compare_peer_set(snapshot(target), [snapshot(peer) for peer in peers], as_of)
        except (ValueError, TypeError, KeyError) as exc:
            raise ToolError("INVALID_PEER_COMPARABILITY_INPUT") from exc
        if result.get("status") == "NOT_COMPARABLE":
            raise ToolError("INVALID_PEER_COMPARABILITY_INPUT")
        if "table" not in result:
            metric_names = sorted(target["metrics"])
            table_rows = [{
                "ticker": target["ticker"], "business_model": target["business_model"],
                "comparability_tier": "TARGET", "eligibility": "TARGET", "reason": None,
                "metrics": {name: {
                    "value": str(target["metrics"][name]["value"]), "unit": target["metrics"][name]["unit"],
                    "status": target["metrics"][name]["status"], "reason": None,
                } for name in metric_names},
            }]
            for peer in result.get("peers", []):
                table_metrics = {}
                for name in metric_names:
                    details = peer["metrics"].get(name, {})
                    table_metrics[name] = {
                        "value": details.get("value", "N/M"), "unit": details.get("unit"),
                        "status": details.get("status", "NOT_MEANINGFUL"), "reason": details.get("reason"),
                        "definition": details.get("definition"), "period": details.get("period"),
                        "basis": details.get("basis"),
                        "currency": details.get("peer_currency", details.get("target_currency")),
                        "horizon": details.get("horizon"),
                        "published_at": details.get("published_at", details.get("peer_published_at")),
                        "source_url": details.get("source_url", details.get("peer_source_url")),
                        "supporting_source_urls": details.get("supporting_source_urls", details.get("peer_supporting_source_urls", [])),
                    }
                table_rows.append({
                    "ticker": peer["ticker"], "business_model": peer["business_model"],
                    "comparability_tier": peer["comparability_tier"], "eligibility": peer["eligibility"],
                    "reason": peer["reason"], "metrics": table_metrics,
                })
            result["table"] = {"as_of": as_of, "metric_names": metric_names, "rows": table_rows}
            result["evidence_status_semantics"] = "Caller-supplied status; source verification is not performed by this tool."
            result["limitations"] = [
                "Caller-supplied snapshots only; no source retrieval or verification.",
                "N/M marks missing or incompatible metrics; no values are inferred.",
                "Comparability checks only; no investment recommendation, ranking, valuation, or portfolio action.",
            ]
        # Keep the facade aligned with the cloud contract and omit helper-only
        # PEG/P-S heuristics and summaries that are outside this tool's schema.
        return {key: result[key] for key in (
            "status", "comparability_reason", "as_of", "target", "sector", "industry", "business_model",
            "comparison_group", "evidence_status_semantics", "included_peer_count", "direct_peer_count",
            "core_metric_peer_counts", "cycle_normalization_required", "required_peer_range", "table", "peers",
            "recommendation", "ranked", "cross_sector_ranking", "limitations",
        )}

    return execute_tool("compare_peer_comparability", arguments, operation, _with_tool_receipt, request_meta=_request_meta(context))


@mcp.tool()
def render_bar_chart(
    labels: list[str],
    values: list[float],
    expected_points: int,
    title: str,
    unit: str,
    horizontal: bool,
    context: Context = None,
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
        context,
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
    context: Context = None,
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
        context,
    )


app = mcp.streamable_http_app()


if __name__ == "__main__":
    mcp.run()
