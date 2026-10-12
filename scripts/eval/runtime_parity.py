#!/usr/bin/env python3
"""Offline, evidence-neutral Work Lab vs Site MCP parity preflight.

Inputs are independently captured observations, NEVER claims of live tool calls
by this CLI. MATCH_PENDING_REVIEW is not a runtime or client-display PASS.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
FLOWS = ("routing", "architecture-review", "bar-chart", "line-chart")
FIELDS = ("source_revision", "release_id", "payload_content_sha256", "catalog_digest")
PLACEHOLDERS = {"", "unknown", "unattested", "not_observable", "not_verified", "NOT_RUN"}


def valid_sha(value: object, size: int = 64) -> bool:
    if not isinstance(value, str):
        return False
    # Site runtime_info currently advertises tool_schema_digest as sha256:<hex>.
    # Canonicalize the public digest prefix, never accept other algorithms.
    raw = value.removeprefix("sha256:") if size == 64 else value
    return bool((HEX40 if size == 40 else HEX64).fullmatch(raw))


def normalize_observation(raw: dict, label: str) -> tuple[dict, list[str]]:
    """Require an independently acquired installed-identity/flow observation."""
    errors = []
    if not isinstance(raw, dict):
        return {}, [f"{label}: invalid observation"]
    state = raw.get("attestation_status")
    if state != "verified":
        errors.append(f"{label}: runtime identity not verified")
    for key in FIELDS:
        val = raw.get(key)
        if not isinstance(val, str) or val.strip().lower() in PLACEHOLDERS:
            errors.append(f"{label}: missing or unattested {key}")
    if not valid_sha(raw.get("source_revision"), 40):
        errors.append(f"{label}: malformed source_revision")
    for key in ("payload_content_sha256", "catalog_digest", "tool_schema_digest"):
        if not valid_sha(raw.get(key)):
            errors.append(f"{label}: missing/malformed {key}")
    when = raw.get("observed_at")
    try:
        date = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError("naive")
    except (AttributeError, ValueError, TypeError):
        errors.append(f"{label}: observed_at must be timezone-aware ISO8601")
    if not isinstance(raw.get("observation_source"), str) or not raw["observation_source"].strip():
        errors.append(f"{label}: no independent observation_source")
    tools = raw.get("capabilities")
    if not isinstance(tools, list) or len(tools) != len(set(map(str, tools))) or any(not isinstance(t, str) or not t for t in tools):
        errors.append(f"{label}: capabilities must be unique nonempty strings")
    flows = raw.get("flows")
    if not isinstance(flows, list):
        flows = []
        errors.append(f"{label}: flows must be a list")
    seen = set()
    flow_map = {}
    for flow in flows:
        if not isinstance(flow, dict) or flow.get("flow") not in FLOWS:
            errors.append(f"{label}: unknown or malformed flow")
            continue
        name = flow["flow"]
        if name in seen:
            errors.append(f"{label}: duplicate flow {name}")
        seen.add(name)
        flow_map[name] = flow
        if flow.get("execution_state") != "executed" or not valid_sha(flow.get("tool_trace_sha256")):
            errors.append(f"{label}: {name} requires real executed tool trace digest")
        if not valid_sha(flow.get("semantic_result_sha256")):
            errors.append(f"{label}: {name} requires normalized result digest")
        if name.endswith("chart") and flow.get("client_display_state") != "observed":
            errors.append(f"{label}: {name} requires client-observed chart receipt")
    for missing in sorted(set(FLOWS) - seen):
        errors.append(f"{label}: missing representative flow {missing}")
    normalized = dict(raw)
    if isinstance(normalized.get("tool_schema_digest"), str):
        normalized["tool_schema_digest"] = normalized["tool_schema_digest"].removeprefix("sha256:")
    return {**normalized, "flows_by_name": flow_map}, errors


def assess(candidate: dict, work: dict, site: dict) -> dict:
    """No provider calls or execution; all claims stay at evidence-review level."""
    blockers, mismatches = [], []
    if not isinstance(candidate, dict):
        return {"status": "BLOCKED", "blockers": ["candidate: invalid manifest"], "mismatches": [], "runtime_execution": "NOT_RUN_BY_PREFLIGHT", "release_approved": False}
    expected_source = candidate.get("source_revision")
    expected_payload = candidate.get("payload_content_sha256")
    expected_id = candidate.get("release_id")
    if not valid_sha(expected_source, 40) or not valid_sha(expected_payload) or not isinstance(expected_id, str) or not expected_id.strip():
        blockers.append("candidate: malformed exact Lab identity")
    w, werr = normalize_observation(work, "work")
    s, serr = normalize_observation(site, "site")
    blockers.extend(werr + serr)
    for label, observation in (("work", w), ("site", s)):
        for field, target in (("source_revision", expected_source), ("payload_content_sha256", expected_payload), ("release_id", expected_id)):
            actual = observation.get(field)
            if actual is not None and target is not None and actual != target:
                mismatches.append(f"{label}: candidate {field} mismatch")
    if w and s:
        for field in ("catalog_digest", "tool_schema_digest"):
            if w.get(field) and s.get(field) and w[field] != s[field]:
                mismatches.append(f"Work/Site {field} mismatch")
        for name in FLOWS:
            wf = w.get("flows_by_name", {}).get(name, {})
            sf = s.get("flows_by_name", {}).get(name, {})
            if wf.get("semantic_result_sha256") and sf.get("semantic_result_sha256") and wf["semantic_result_sha256"] != sf["semantic_result_sha256"]:
                mismatches.append(f"Work/Site {name} semantic output mismatch")
    status = "BLOCKED" if blockers else "MISMATCH" if mismatches else "MATCH_PENDING_INDEPENDENT_REVIEW"
    return {
        "schema_version": "1.0",
        "kind": "offline_runtime_parity_preflight",
        "status": status,
        "blockers": sorted(set(blockers)),
        "mismatches": sorted(set(mismatches)),
        "source_revision": expected_source,
        "candidate_release_id": expected_id,
        "runtime_execution": "NOT_RUN_BY_PREFLIGHT",
        "release_approved": False,
        "note": "Caller-supplied observation metadata is not independently authenticated by this tool. Equal digests are not behavioral PASS, client rendering proof, or publish authority.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-lab-release", type=Path, required=True)
    parser.add_argument("--work-observation", type=Path, required=True)
    parser.add_argument("--site-observation", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = assess(*[json.loads(p.read_text(encoding="utf-8")) for p in (args.candidate_lab_release, args.work_observation, args.site_observation)])
    except (ValueError, TypeError, OSError) as error:
        result = {"status": "BLOCKED", "blockers": [type(error).__name__], "runtime_execution": "NOT_RUN_BY_PREFLIGHT", "release_approved": False}
    report = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0 if result["status"] == "MATCH_PENDING_INDEPENDENT_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
