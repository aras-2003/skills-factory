#!/usr/bin/env python3
"""Fail-closed offline Site route-only tool-to-client evidence checker.

This reads untrusted, hash-pinned evidence only. It does NOT call the Site MCP,
authenticate screenshots, invoke child workflows, or declare runtime PASS.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import stat
from pathlib import Path

CASE_ID = "I02-149-cloud-e2e"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PNG = b"\x89PNG\r\n\x1a\n"


def valid(value: object, size: int = 64) -> bool:
    return isinstance(value, str) and bool((HEX40 if size == 40 else HEX64).fullmatch(value))


def evidence(root: Path, relative: object, expected: object, *, image: bool = False) -> bytes:
    if (not isinstance(relative, str) or not relative
            or Path(relative).is_absolute()
            or any(p in {".", ".."} for p in Path(relative).parts)):
        raise ValueError("invalid evidence path")
    if not valid(expected):
        raise ValueError("invalid artifact digest")
    root_abs = root.resolve()
    target = root / relative
    if not target.resolve().is_relative_to(root_abs):
        raise ValueError("artifact escapes evidence root")
    current = target
    while current != root:
        if current.is_symlink():
            raise ValueError("symlink evidence path")
        if current == current.parent:
            raise ValueError("invalid evidence root")
        current = current.parent
    if not stat.S_ISREG(target.lstat().st_mode):
        raise ValueError("nonregular evidence file")
    if not 0 < target.stat().st_size <= (8_000_000 if image else 512_000):
        raise ValueError("evidence file size out of bounds")
    contents = target.read_bytes()
    if hashlib.sha256(contents).hexdigest() != expected:
        raise ValueError("artifact hash mismatch")
    if image and not contents.startswith(PNG):
        raise ValueError("not PNG capture evidence")
    return contents


def iso_time(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return (t.tzinfo is not None and t.utcoffset() is not None
            and t <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5))


def assess(lock: object, capture: object, root: Path) -> dict:
    errors = []
    if not isinstance(lock, dict) or not isinstance(capture, dict):
        return {"status": "BLOCKED_EVIDENCE", "errors": ["invalid lock/capture"],
                "runtime_execution": "NOT_PERFORMED_BY_CHECKER", "release_approved": False}
    cases = lock.get("cases")
    rows = ([c for c in cases if isinstance(c, dict) and c.get("case_id") == CASE_ID]
            if isinstance(cases, list) else [])
    if len(rows) != 1 or rows[0].get("channel") != "site":
        errors.append("exact frozen Site route-only case missing")
        case = {}
    else:
        case = rows[0]
    if lock.get("kind") != "external_test_inputs_only" or lock.get("runtime_evidence") != "NOT_RUN" or lock.get("provider_calls_executed") is not False:
        errors.append("nonpristine external test source lock")
    if not valid(lock.get("source_revision"), 40) or not valid(lock.get("payload_content_sha256")) or not isinstance(lock.get("release_id"), str) or not lock["release_id"]:
        errors.append("exact candidate identity malformed")
    for key in ("case_id", "channel", "source_revision", "release_id", "payload_content_sha256", "input_sha256", "rubric_sha256"):
        expected = (CASE_ID if key == "case_id" else "site" if key == "channel" else
                    lock.get(key) if key in {"source_revision", "release_id", "payload_content_sha256"} else case.get(key))
        if capture.get(key) != expected:
            errors.append(f"unmatched {key}")
    attempt = capture.get("attempt")
    repetitions = case.get("repetitions")
    if type(attempt) is not int or type(repetitions) is not int or not 1 <= attempt <= repetitions:
        errors.append("invalid frozen attempt index")
    if capture.get("execution_state") != "executed" or capture.get("decision") not in (None, "REVIEW_REQUIRED"):
        errors.append("capture claims unexecuted or evaluated behavior")
    if not iso_time(capture.get("observed_at")):
        errors.append("missing offset-aware observed_at")
    for field in ("approval_reference", "observation_source", "executor", "evaluator", "correlation_id"):
        if not isinstance(capture.get(field), str) or not capture[field].strip():
            errors.append(f"missing {field}")
    if capture.get("executor") == capture.get("evaluator"):
        errors.append("independent evaluator required")
    raw = {}
    try:
        for name in ("tool_receipt", "tool_output", "client_observation", "screenshot"):
            item = capture.get(name)
            if not isinstance(item, dict):
                raise ValueError(f"{name} path/hash pair absent")
            raw[name] = evidence(root, item.get("path"), item.get("sha256"), image=(name == "screenshot"))
        receipt = json.loads(raw["tool_receipt"])
        output = json.loads(raw["tool_output"])
        client = json.loads(raw["client_observation"])
        if any(not isinstance(x, dict) for x in (receipt, output, client)):
            raise ValueError("tool/client must be JSON objects")
        for src_name, src in (("tool receipt", receipt), ("tool output", output), ("client", client)):
            for field in ("case_id", "attempt", "source_revision", "release_id", "payload_content_sha256", "input_sha256", "correlation_id"):
                if src.get(field) != capture.get(field):
                    errors.append(f"{src_name}: {field} drift")
        tool_call = receipt.get("tool_call")
        if not isinstance(tool_call, dict):
            errors.append("missing observed tool call")
            tool_call = {}
        if (not isinstance(tool_call.get("id"), str) or not tool_call.get("id")
                or not isinstance(tool_call.get("tool_name"), str) or not tool_call["tool_name"]
                or tool_call.get("execution_state") != "executed"
                or tool_call.get("output_sha256") != hashlib.sha256(raw["tool_output"]).hexdigest()):
            errors.append("selected tool call not bound to exact raw output bytes")
        if tool_call.get("side_effects") != "none" or output.get("writes") != []:
            errors.append("route-only request has missing or nonzero write-effects proof")
        if receipt.get("tool_call_id") != tool_call.get("id") or client.get("observed_tool_call_id") != tool_call.get("id"):
            errors.append("client-to-MCP call correlation mismatch")
        child = output.get("child_execution")
        if not isinstance(child, dict) or child.get("state") != "not_executed" or child.get("steps") != []:
            errors.append("route-only test ran or ambiguously reported a child")
        if output.get("selected_child") != client.get("selected_child") or not isinstance(output.get("selected_child"), str) or not output["selected_child"]:
            errors.append("route selection differs between tool and client")
        if client.get("client_display_state") != "observed" or not isinstance(client.get("accessible_text"), str) or not client["accessible_text"].strip():
            errors.append("client-visible UI and accessible text not captured")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"artifact read/shape failure: {type(exc).__name__}: {exc}")
    return {
        "schema_version": "1.0", "kind": "offline_site_route_only_evidence",
        "status": "BLOCKED_EVIDENCE" if errors else "STRUCTURAL_REVIEW_REQUIRED",
        "errors": errors, "case_id": CASE_ID,
        "runtime_execution": "NOT_PERFORMED_BY_CHECKER",
        "provider_attestation": "NOT_AUTHENTICATED",
        "client_screen_visual_verification": "NOT_PERFORMED",
        "model_behavior_verdict": "NOT_EVALUATED",
        "release_approved": False,
        "note": "Structure and hashes are caller-supplied. Independent Site/Chat tool trace + UI review is mandatory before any PASS or acceptance.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--external-lock", type=Path, required=True)
    p.add_argument("--capture", type=Path, required=True)
    p.add_argument("--evidence-root", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        result = assess(
            json.loads(args.external_lock.read_text(encoding="utf-8")),
            json.loads(args.capture.read_text(encoding="utf-8")), args.evidence_root)
    except (OSError, ValueError, TypeError) as exc:
        result = {"status": "BLOCKED_EVIDENCE", "errors": [type(exc).__name__],
                  "runtime_execution": "NOT_PERFORMED_BY_CHECKER", "release_approved": False}
    content = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0 if result["status"] == "STRUCTURAL_REVIEW_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
