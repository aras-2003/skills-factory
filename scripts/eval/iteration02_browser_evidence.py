#!/usr/bin/env python3
"""Offline browser/client artifact proof binder for Iteration 2.

Reads raw *untrusted* captured MCP receipts, screenshots and accessible UI data.
No browser/provider invocation, no OCR, no visual authenticity claim or PASS.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path

CASES = {"I02-251-browser-mcp", "I02-253-parity", "I02-254-charts"}
TOOLS = {"bar": "render_bar_chart", "line": "render_line_chart"}
MAX_BLOB = 2_000_000


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_evidence(root: Path, rel: object, *, binary: bool = False):
    """Refuse symlinks, path traversal and oversized attacker-supplied inputs."""
    if (not isinstance(rel, str) or not rel or rel.startswith("/")
            or "\\" in rel or any(part in {".", ".."} for part in Path(rel).parts)):
        raise ValueError("evidence path invalid")
    path = root / rel
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("evidence path leaves root")
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError("symlink in evidence path")
        if current.parent == current:
            raise ValueError("invalid evidence root")
        current = current.parent
    if path.is_symlink() or not path.is_file():
        raise ValueError("evidence path must be a regular file")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_BLOB:
        raise ValueError("evidence size invalid")
    if binary:
        return raw
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("evidence JSON must be an object")
    return obj, raw


def numeric(values: object) -> bool:
    return isinstance(values, list) and all(
        type(v) in (int, float) and math.isfinite(v) for v in values
    )


def content_matches(kind: str, observed: dict, expected: dict) -> bool:
    if kind == "bar":
        return (
            isinstance(expected.get("labels"), list)
            and all(isinstance(x, str) for x in expected["labels"])
            and numeric(expected.get("values"))
            and observed.get("labels") == expected["labels"]
            and observed.get("values") == expected["values"]
            and observed.get("title") == expected.get("title")
        )
    if kind == "line":
        series = expected.get("series_values")
        return (
            isinstance(expected.get("x_labels"), list)
            and isinstance(expected.get("series_names"), list)
            and isinstance(series, list) and bool(series)
            and all(numeric(s) for s in series)
            and observed.get("x_labels") == expected["x_labels"]
            and observed.get("series_names") == expected["series_names"]
            and observed.get("series_values") == series
            and observed.get("title") == expected.get("title")
        )
    return False


def assess(lock: object, capture: object, root: Path, *, now: dt.datetime | None = None) -> dict:
    issues = []
    if not isinstance(lock, dict) or not isinstance(capture, dict):
        return {"status": "BLOCKED_EVIDENCE", "issues": ["missing lock/capture"],
                "client_execution": "NOT_PERFORMED_BY_VALIDATOR", "release_approved": False}
    case = capture.get("case_id")
    entries = lock.get("cases")
    matched = [c for c in entries if isinstance(c, dict) and c.get("case_id") == case] if isinstance(entries, list) else []
    if not isinstance(case, str) or case not in CASES or len(matched) != 1 or matched[0].get("channel") != "browser":
        issues.append("case not in frozen browser handoff")
    if not isinstance(lock.get("source_revision"), str) or not re.fullmatch(r"[0-9a-f]{40}", lock["source_revision"]):
        issues.append("frozen source SHA missing/invalid")
    if not isinstance(lock.get("release_id"), str) or not lock["release_id"]:
        issues.append("frozen release ID missing/invalid")
    if not isinstance(lock.get("payload_content_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", lock["payload_content_sha256"]):
        issues.append("frozen payload digest missing/invalid")
    for key in ("source_revision", "release_id", "payload_content_sha256"):
        if capture.get(key) != lock.get(key):
            issues.append(f"stale release identity: {key}")
    if len(matched) == 1 and capture.get("input_sha256") != matched[0].get("input_sha256"):
        issues.append("mismatched frozen prompt digest")
    if lock.get("runtime_evidence") != "NOT_RUN" or lock.get("release_approved") is not False:
        issues.append("external lock is not pristine")
    if capture.get("installed_attestation") != "verified" or not capture.get("installed_observation_reference"):
        issues.append("installed client/provider identity not observed")
    if any(not isinstance(capture.get(k), str) or not capture[k].strip() for k in ("chat_reference", "capture_source")):
        issues.append("missing client chat reference/capture source")
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        stamp = dt.datetime.fromisoformat(capture["captured_at"].replace("Z", "+00:00"))
        if stamp.tzinfo is None or now.tzinfo is None or not dt.timedelta(0) <= now - stamp <= dt.timedelta(hours=48):
            raise ValueError("capture stale/future or timezone absent")
    except (KeyError, ValueError, TypeError, AttributeError):
        issues.append("capture timestamp is invalid/stale")
    checks = capture.get("chart_checks")
    if not isinstance(checks, list) or not checks:
        checks = []
        issues.append("no independently visible chart checks")
    encountered, correlations, evidence = set(), set(), []
    for i, check in enumerate(checks):
        prefix = f"chart[{i}]"
        if not isinstance(check, dict):
            issues.append(prefix + " malformed")
            continue
        kind = check.get("kind")
        corr = check.get("correlation_id")
        if not isinstance(kind, str) or kind not in TOOLS or not isinstance(corr, str) or not corr.strip() or corr in correlations:
            issues.append(prefix + " unsupported/duplicate correlation")
            continue
        correlations.add(corr)
        encountered.add(kind)
        try:
            tool, tool_raw = read_evidence(root, check.get("tool_receipt_path"))
            screenshot = read_evidence(root, check.get("screenshot_path"), binary=True)
            accessibility, accessibility_raw = read_evidence(root, check.get("accessibility_path"))
            tool_output, tool_output_raw = read_evidence(root, check.get("tool_output_path"))
            chart_payload_raw = read_evidence(root, check.get("chart_payload_path"), binary=True)
        except (OSError, ValueError, UnicodeError, TypeError) as error:
            issues.append(prefix + ": invalid/missing file " + type(error).__name__)
            continue
        if sha(tool_raw) != check.get("tool_receipt_sha256"):
            issues.append(prefix + ": tool receipt hash mismatch")
        if sha(screenshot) != check.get("screenshot_sha256"):
            issues.append(prefix + ": screenshot hash mismatch")
        if sha(accessibility_raw) != check.get("accessibility_sha256"):
            issues.append(prefix + ": accessibility hash mismatch")
        if sha(tool_output_raw) != check.get("tool_output_sha256"):
            issues.append(prefix + ": raw tool output hash mismatch")
        if sha(chart_payload_raw) != check.get("chart_payload_sha256"):
            issues.append(prefix + ": renderer artifact hash mismatch")
        if not chart_payload_raw.startswith(b"\x89PNG\r\n\x1a\n"):
            issues.append(prefix + ": rendered artifact is not PNG evidence")
        if not screenshot.startswith(b"\x89PNG\r\n\x1a\n"):
            issues.append(prefix + ": client screenshot is not a PNG file")
        receipt = tool.get("tool_receipt")
        if not isinstance(receipt, dict):
            issues.append(prefix + ": missing raw MCP tool receipt")
            continue
        if (receipt.get("tool_name") != TOOLS[kind] or receipt.get("execution_state") != "executed"
            or receipt.get("status") != "SUCCESS" or receipt.get("artifact_state") != "rendered"
            or receipt.get("source_revision") != lock.get("source_revision")
            or receipt.get("release_id") != lock.get("release_id")
            or receipt.get("payload_content_sha256") != lock.get("payload_content_sha256")):
            issues.append(prefix + ": tool did not render on exact locked source")
        if (receipt.get("correlation_id") != corr
            or receipt.get("output_sha256") != sha(tool_output_raw)
            or receipt.get("chart_payload_sha256") != sha(chart_payload_raw)):
            issues.append(prefix + ": raw renderer/tool artifact not bound to MCP call ID")
        if receipt.get("client_display_state") != "not_observable":
            issues.append(prefix + ": tool receipt must not claim client visibility")
        if check.get("client_display_state") != "observed" or check.get("tool_call_correlation_id") != corr or check.get("client_capture_correlation_id") != corr:
            issues.append(prefix + ": tool/client correlation or visible display missing")
        expected = check.get("expected_data")
        if not isinstance(expected, dict) or not content_matches(kind, accessibility, expected):
            issues.append(prefix + ": accessible UI does not match frozen expected numbers/labels/title")
        if not isinstance(expected, dict) or not content_matches(kind, tool_output, expected):
            issues.append(prefix + ": original tool data differs from client-visible expected data")
        if case == "I02-254-charts":
            if kind == "bar" and (not isinstance(expected, dict) or expected.get("values") != [-5, 0, 3]):
                issues.append(prefix + ": signed bar fixture diverges")
            if kind == "line" and (not isinstance(expected, dict) or expected.get("series_values") != [[-2, 0]]):
                issues.append(prefix + ": signed line fixture diverges")
        evidence.append({"kind": kind, "correlation_id": corr,
                         "tool_receipt_sha256": sha(tool_raw), "screenshot_sha256": sha(screenshot),
                         "accessibility_sha256": sha(accessibility_raw),
                         "tool_output_sha256": sha(tool_output_raw),
                         "chart_payload_sha256": sha(chart_payload_raw)})
    if case in {"I02-253-parity", "I02-254-charts"} and encountered != {"bar", "line"}:
        issues.append("bar and line client captures both required")
    return {
        "schema_version": "1.0", "kind": "offline_browser_chart_evidence_binding",
        "status": "BLOCKED_EVIDENCE" if issues else "STRUCTURALLY_CORRELATED_INDEPENDENT_REVIEW_REQUIRED",
        "issues": sorted(set(issues)), "case_id": case,
        "source_revision": lock.get("source_revision"),
        "bound_files": evidence,
        "client_execution": "NOT_PERFORMED_BY_VALIDATOR",
        "provider_trace_authenticity": "NOT_VERIFIED",
        "screenshot_visual_authenticity": "NOT_VERIFIED",
        "accessibility_capture_authenticity": "NOT_VERIFIED",
        "model_behavior_verdict": "NOT_EVALUATED",
        "release_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-lock", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        lock = json.loads(args.external_lock.read_text(encoding="utf-8"))
        capture = json.loads(args.capture.read_text(encoding="utf-8"))
        report = assess(lock, capture, args.evidence_root)
    except (OSError, ValueError, UnicodeError, TypeError) as error:
        report = {"status": "BLOCKED_EVIDENCE", "issues": [type(error).__name__],
                  "release_approved": False}
    content = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return int(report["status"] != "STRUCTURALLY_CORRELATED_INDEPENDENT_REVIEW_REQUIRED")


if __name__ == "__main__":
    raise SystemExit(main())
