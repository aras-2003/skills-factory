#!/usr/bin/env python3
"""Offline structural intake for Browser/Site MCP + Chat client evidence.

Does not invoke a browser, inspect pixels, authenticate providers, or award PASS.
Screenshots and tool traces are untrusted caller-supplied artifacts; an
independent evaluator must inspect actual behavior and UI after this preflight.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import stat
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
CASE = re.compile(r"^I02-\d{3}-[a-z0-9-]+$")
CHART_CASES = {"I02-251-browser-mcp", "I02-253-parity", "I02-254-charts"}
BROWSER_CASES = CHART_CASES | {"I02-149-cloud-e2e"}
MAX_JSON_BYTES = 512_000
MAX_SCREENSHOT_BYTES = 8_000_000
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value: object, length: int = 64) -> bool:
    return isinstance(value, str) and bool((HEX40 if length == 40 else HEX64).fullmatch(value))


def _read(root: Path, rel: object, digest: object, *, png: bool = False) -> bytes:
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute() or any(part in {".", ".."} for part in Path(rel).parts):
        raise ValueError("artifact path must be relative")
    candidate = root / rel
    root_abs = root.resolve()
    resolved = candidate.resolve()
    if resolved == root_abs or not resolved.is_relative_to(root_abs):
        raise ValueError("artifact path escapes evidence root")
    # Do not follow any symlink segment (also prevents symlink-based indirection).
    p = candidate
    while p != root:
        if p.is_symlink():
            raise ValueError("symlink in evidence path")
        if p.parent == p:
            raise ValueError("invalid evidence root")
        p = p.parent
    if not stat.S_ISREG(candidate.lstat().st_mode):
        raise ValueError("artifact must be a regular file")
    if not _digest(digest):
        raise ValueError("artifact SHA256 missing or malformed")
    size = candidate.stat().st_size
    if size <= 0 or size > (MAX_SCREENSHOT_BYTES if png else MAX_JSON_BYTES):
        raise ValueError("artifact exceeds allowed size")
    data = candidate.read_bytes()
    if _sha(data) != digest:
        raise ValueError("artifact digest mismatch")
    if png and (not data.startswith(PNG_MAGIC) or not rel.lower().endswith(".png")):
        raise ValueError("client capture must be PNG evidence")
    return data


def _object(data: bytes, name: str) -> dict:
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"{name}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{name}: JSON object required")
    return value


def _instant(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        point = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return point.tzinfo is not None


def validate(lock: object, observations: object, evidence_root: Path) -> dict:
    errors: list[str] = []
    matches = []
    if not isinstance(lock, dict) or not isinstance(lock.get("cases"), list) or not isinstance(observations, list):
        return {"status": "INVALID_EVIDENCE", "errors": ["lock/cases/observations malformed"],
                "runtime_execution": "NOT_PERFORMED_BY_VALIDATOR", "release_approved": False}
    if not _digest(lock.get("source_revision"), 40) or not _digest(lock.get("payload_content_sha256")) or not isinstance(lock.get("release_id"), str) or not lock["release_id"]:
        errors.append("lock: exact Lab source/release/payload identity missing")
    if lock.get("kind") != "external_test_inputs_only" or lock.get("provider_calls_executed") is not False or lock.get("runtime_evidence") != "NOT_RUN":
        errors.append("lock: pristine external input handoff required")
    indexed = {}
    for case in lock["cases"]:
        if not isinstance(case, dict) or not isinstance(case.get("case_id"), str):
            errors.append("lock: invalid case")
            continue
        name = case["case_id"]
        if name in indexed:
            errors.append(f"lock: duplicate {name}")
        indexed[name] = case

    seen = set()
    for i, obs in enumerate(observations):
        key_label = f"observation[{i}]"
        if not isinstance(obs, dict):
            errors.append(f"{key_label}: not an object")
            continue
        name, attempt = obs.get("case_id"), obs.get("attempt")
        if not isinstance(name, str) or name not in indexed or type(attempt) is not int or attempt < 1:
            errors.append(f"{key_label}: unknown case/attempt")
            continue
        case = indexed[name]
        key_label = f"{name}#{attempt}"
        if (name, attempt) in seen:
            errors.append(f"{key_label}: duplicate receipt")
            continue
        seen.add((name, attempt))
        if name not in BROWSER_CASES or not isinstance(case.get("channel"), str) or case["channel"] not in {"site", "browser"}:
            errors.append(f"{key_label}: not a Browser/Site client case")
        if type(case.get("repetitions")) is not int or attempt > case["repetitions"]:
            errors.append(f"{key_label}: attempt exceeds locked repetitions")
        for field in ("source_revision", "release_id", "payload_content_sha256", "input_sha256", "rubric_sha256"):
            expected = lock.get(field) if field in {"source_revision", "release_id", "payload_content_sha256"} else case.get(field)
            if obs.get(field) != expected or (field.endswith("_sha256") and not _digest(expected)):
                errors.append(f"{key_label}: identity drift {field}")
        if obs.get("channel") != case.get("channel"):
            errors.append(f"{key_label}: channel drift")
        if obs.get("execution_state") != "executed" or (obs.get("decision") is not None and obs.get("decision") != "REVIEW_REQUIRED"):
            errors.append(f"{key_label}: executed trace with no behavioral PASS/FAIL required")
        if not _instant(obs.get("observed_at")):
            errors.append(f"{key_label}: offset-aware observation time required")
        if any(not isinstance(obs.get(k), str) or not obs.get(k).strip() for k in (
            "observation_source", "approval_reference", "executor", "evaluator")):
            errors.append(f"{key_label}: approval/source/operator references required")
        if obs.get("executor") == obs.get("evaluator"):
            errors.append(f"{key_label}: evaluator must be independent")
        try:
            blobs = {}
            for field in ("trace", "client", "capture", "tool_output"):
                ref = obs.get(field)
                if not isinstance(ref, dict):
                    raise ValueError(f"{field}: path and sha256 required")
                blobs[field] = _read(evidence_root, ref.get("path"), ref.get("sha256"), png=(field == "capture"))
            trace = _object(blobs["trace"], "trace")
            client = _object(blobs["client"], "client")
            for field in ("case_id", "attempt", "source_revision", "release_id", "payload_content_sha256", "input_sha256"):
                for label, artifact in (("trace", trace), ("client", client)):
                    if artifact.get(field) != obs.get(field):
                        errors.append(f"{key_label}: {label} {field} mismatch")
            corr = obs.get("correlation_id")
            if not isinstance(corr, str) or not corr.strip() or trace.get("correlation_id") != corr or client.get("correlation_id") != corr:
                errors.append(f"{key_label}: tool/client correlation mismatch")
            calls = trace.get("tool_calls")
            if not isinstance(calls, list) or not calls or any(
                not isinstance(x, dict)
                or not isinstance(x.get("id"), str)
                or not x.get("id")
                or x.get("execution_state") != "executed"
                or not isinstance(x.get("tool_name"), str)
                or not x.get("tool_name")
                or not _digest(x.get("output_sha256"))
                for x in calls
            ):
                errors.append(f"{key_label}: nonempty executed tool trace required")
                calls = []
            call_ids = [x["id"] for x in calls]
            if len(call_ids) != len(set(call_ids)) or client.get("observed_tool_call_id") not in call_ids:
                errors.append(f"{key_label}: UI not correlated to unique executed tool call")
            selected = [x for x in calls if x["id"] == client.get("observed_tool_call_id")]
            if selected and _sha(blobs["tool_output"]) != selected[0]["output_sha256"]:
                errors.append(f"{key_label}: raw tool output hash differs from selected tool receipt")
            if client.get("client_display_state") != "observed" or not isinstance(client.get("accessible_text"), str) or not client["accessible_text"].strip():
                errors.append(f"{key_label}: missing client-visible display/accessibility claim")
            if name in CHART_CASES:
                if not isinstance(obs.get("chart"), dict):
                    errors.append(f"{key_label}: chart artifact file is required")
                    chart_bytes = b""
                else:
                    chart_bytes = _read(evidence_root, obs["chart"].get("path"), obs["chart"].get("sha256"), png=True)
                if not selected:
                    errors.append(f"{key_label}: selected chart tool call missing")
                else:
                    call = selected[0]
                    if not _digest(call.get("chart_payload_sha256")) or client.get("chart_payload_sha256") != call.get("chart_payload_sha256") or (chart_bytes and _sha(chart_bytes) != call.get("chart_payload_sha256")):
                        errors.append(f"{key_label}: chart payload/client/file correlation mismatch")
                    if not _digest(call.get("normalized_data_sha256")) or client.get("normalized_data_sha256") != call.get("normalized_data_sha256"):
                        errors.append(f"{key_label}: chart normalized data differs between tool and client")
            matches.append({"case_id": name, "attempt": attempt, "channel": case.get("channel"),
                            "correlation_id": corr, "capture_sha256": obs["capture"]["sha256"],
                            "tool_steps_reported": len(calls),
                            "evidence_state": "STRUCTURAL_ONLY_INDEPENDENT_REVIEW_REQUIRED"})
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"{key_label}: {type(exc).__name__}: {exc}")
    return {
        "schema_version": "1.0", "kind": "offline_client_mcp_evidence_correlation",
        "status": "INVALID_EVIDENCE" if errors else "STRUCTURAL_EVIDENCE_REVIEW_REQUIRED" if matches else "NO_EXECUTION_EVIDENCE",
        "errors": errors, "observations_structurally_checked": len(matches), "receipts": matches,
        "provider_authenticity": "NOT_VERIFIED", "pixel_accessibility_inspection": "NOT_PERFORMED",
        "independent_behavioral_review": "NOT_PERFORMED",
        "runtime_execution": "NOT_PERFORMED_BY_VALIDATOR", "release_approved": False,
        "note": "Hashes and claims do not prove provider provenance, real browser pixels, or a correct chart. Inspect source tool receipts and the actual rendered UI independently.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--external-lock", type=Path, required=True)
    p.add_argument("--observations", type=Path, required=True)
    p.add_argument("--evidence-root", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        result = validate(
            json.loads(args.external_lock.read_text(encoding="utf-8")),
            json.loads(args.observations.read_text(encoding="utf-8")),
            args.evidence_root,
        )
    except (OSError, ValueError, TypeError) as exc:
        result = {"status": "INVALID_EVIDENCE", "errors": [type(exc).__name__],
                  "runtime_execution": "NOT_PERFORMED_BY_VALIDATOR", "release_approved": False}
    content = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0 if result["status"] == "STRUCTURAL_EVIDENCE_REVIEW_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
