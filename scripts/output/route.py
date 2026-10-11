"""Deterministic policy gate for already-classified output requests.

This is NOT a natural-language intent classifier, runtime plugin router, artifact
builder, or proof that any connector action succeeded. See docs/architecture/
output-systems.md for the policy boundary.
"""
from __future__ import annotations

import json
import sys
from typing import Any, Mapping

FORMATS = {
    "chat": frozenset(("text",)),
    "report": frozenset(("docx", "pdf", "google_docs")),
    "presentation": frozenset(("canva", "figma_slides", "pptx")),
    "interactive_web": frozenset(("html", "hosted")),
    "spreadsheet": frozenset(("xlsx", "google_sheets")),
}
OWNERS = {
    "chat": "domain-response-or-report-composer",
    "report": "report-production",
    "presentation": "presentation-production",
    "interactive_web": "interactive-experience",
    "spreadsheet": "spreadsheet-adapter-deferred",
}
REQUEST_KINDS = frozenset(("ANALYZE_ONLY", "RENDER_EXISTING", "ANALYZE_THEN_RENDER", "EDIT_EXISTING"))
CAPABILITY_STATES = frozenset(("AVAILABLE", "UNAVAILABLE", "UNKNOWN"))
ANALYSIS_STATES = frozenset(("NOT_STARTED", "IN_PROGRESS", "UNAVAILABLE", "UNKNOWN"))


class RoutingInputError(ValueError):
    """Invalid preclassified intent or malformed policy input."""


def _fields(data: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(data, dict):
        raise RoutingInputError(f"{label} must be a JSON object")
    return data


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RoutingInputError(f"{label} must be a non-empty string")
    return value.strip()


def _outputs(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise RoutingInputError("requested_outputs must be an array")
    unique: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []
    for i, item in enumerate(value):
        record = _fields(item, f"requested_outputs[{i}]")
        kind = _nonempty(record.get("kind"), f"requested_outputs[{i}].kind")
        fmt = _nonempty(record.get("format"), f"requested_outputs[{i}].format")
        if kind not in FORMATS or fmt not in FORMATS[kind]:
            raise RoutingInputError(f"Unsupported target/format: {kind}/{fmt}")
        if (kind, fmt) not in unique:
            unique.add((kind, fmt))
            result.append({"kind": kind, "format": fmt})
    return result


def _source(raw: Any) -> dict[str, str] | None:
    if raw is None:
        return None
    obj = _fields(raw, "source_result")
    return {
        "result_id": _nonempty(obj.get("result_id"), "source_result.result_id"),
        "revision": _nonempty(obj.get("revision"), "source_result.revision"),
        "domain": _nonempty(obj.get("domain"), "source_result.domain"),
    }


def plan_outputs(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Return routing decisions only, never execute domain analysis or create files.

    `semantic_resolution` is supplied by an upstream semantic classifier/human;
    this function deliberately does not guess meaning from natural-language text.
    """
    request = _fields(raw, "request")
    kind = request.get("request_kind")
    if kind not in REQUEST_KINDS:
        raise RoutingInputError("request_kind must be an explicit supported mode")
    semantic = request.get("semantic_resolution")
    if semantic not in ("RESOLVED", "AMBIGUOUS"):
        raise RoutingInputError("semantic_resolution must be RESOLVED or AMBIGUOUS")
    if semantic == "AMBIGUOUS":
        return {
            "routing_state": "NEEDS_CLARIFICATION",
            "reason": "Output or intent is unresolved; ask one material question.",
            "delegations": [],
            "executed": False,
        }

    outputs = _outputs(request.get("requested_outputs", []))
    if kind == "ANALYZE_ONLY":
        if outputs and outputs != [{"kind": "chat", "format": "text"}]:
            raise RoutingInputError("ANALYZE_ONLY must not silently generate artifacts")
        outputs = [{"kind": "chat", "format": "text"}]
    elif not outputs:
        return {
            "routing_state": "NEEDS_CLARIFICATION",
            "reason": "A concrete delivery medium has not been selected.",
            "delegations": [],
            "executed": False,
        }

    artifact_ref = None
    if kind == "EDIT_EXISTING":
        if len(outputs) != 1:
            raise RoutingInputError("EDIT_EXISTING requires one exact target and format")
        artifact_ref = _nonempty(request.get("artifact_ref"), "artifact_ref")

    source = _source(request.get("source_result"))
    analysis_state = request.get("analysis_state", "UNKNOWN")
    if analysis_state not in ANALYSIS_STATES:
        raise RoutingInputError("analysis_state must be NOT_STARTED, IN_PROGRESS, UNAVAILABLE or UNKNOWN")
    capabilities = _fields(request.get("capabilities", {}), "capabilities")
    for key, value in capabilities.items():
        if value not in CAPABILITY_STATES:
            raise RoutingInputError(f"Invalid capability state for {key}")
        if not isinstance(key, str):
            raise RoutingInputError("Capability names must be strings")

    publish_requested = request.get("publish_requested", False)
    publish_authorized = request.get("publish_authorized", False)
    if not isinstance(publish_requested, bool) or not isinstance(publish_authorized, bool):
        raise RoutingInputError("Publishing flags must be booleans")
    publication_state = ("NOT_REQUESTED" if not publish_requested else
                         "AUTHORIZED_SEPARATE_STEP" if publish_authorized else
                         "REQUIRES_EXPLICIT_APPROVAL")

    mode = ("MULTI_OUTPUT" if len({o["kind"] for o in outputs}) > 1 else
            "ANALYZE_ONLY" if kind == "ANALYZE_ONLY" else
            "EDIT_EXISTING" if kind == "EDIT_EXISTING" else
            "PRESENT_EXISTING" if kind == "RENDER_EXISTING" else "ANALYZE_THEN_RENDER")

    delegations = []
    for item in outputs:
        output_kind, fmt = item["kind"], item["format"]
        # Edit availability is a different capability from create/export availability.
        cap_key = (f"edit:{output_kind}:{fmt}" if kind == "EDIT_EXISTING"
                   else f"{output_kind}:{fmt}")
        capability = "AVAILABLE" if output_kind == "chat" and fmt == "text" else capabilities.get(cap_key, "UNKNOWN")
        state = "READY_TO_DELEGATE"
        reason = "Validated policy route; no workflow or provider was executed."

        if output_kind == "spreadsheet":
            state, reason = "DEFERRED_PRODUCT", "Spreadsheet adapter is P2 discovery / P3 optional implementation."
        elif kind != "ANALYZE_ONLY" and kind != "EDIT_EXISTING" and source is None:
            if kind == "RENDER_EXISTING":
                state, reason = "WAITING_FOR_SOURCE", "No versioned source result supplied."
            elif analysis_state in ("NOT_STARTED", "IN_PROGRESS"):
                state, reason = "WAITING_UPSTREAM", "Upstream domain analysis must complete first."
            else:
                state, reason = "BLOCKED_UPSTREAM", "Domain analysis unavailable or unverified."
        elif capability != "AVAILABLE":
            state = "BLOCKED_CAPABILITY" if capability == "UNAVAILABLE" else "UNVERIFIED_CAPABILITY"
            reason = "Required target operation is unavailable or not observed."
        elif fmt == "hosted" and publication_state != "AUTHORIZED_SEPARATE_STEP":
            state, reason = "BLOCKED_PUBLICATION_APPROVAL", "Hosted deployment needs explicit permission."

        delegations.append({
            "kind": output_kind,
            "format": fmt,
            "owner": OWNERS[output_kind],
            "route_state": state,
            "reason": reason,
            "capability_state": capability,
            "source_result": source,
            "artifact_ref": artifact_ref,
            "execution_state": "NOT_RUN",
            "delivery_state": "NOT_RUN",
        })

    return {
        "routing_state": "PLANNED",
        "request_kind": kind,
        "mode": mode,
        "source_result": source,
        "delegations": delegations,
        "publication_state": publication_state,
        "executed": False,
    }


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
        print(json.dumps(plan_outputs(input_data), indent=2, sort_keys=True))
        return 0
    except (RoutingInputError, json.JSONDecodeError) as exc:
        print(f"Invalid output-routing request: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
