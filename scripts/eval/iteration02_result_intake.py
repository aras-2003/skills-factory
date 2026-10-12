#!/usr/bin/env python3
"""Read-only Iteration 2 runtime receipt intake; no model or provider execution.

All submitted receipts are caller-provided. Passing this structural check NEVER
attests authenticity, behavioral correctness or production readiness.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EXECUTED = {"executed"}
UNRUN = {"blocked", "awaiting_runner", "no_steps", "not_executed"}
REPORT_STATUSES = {"PASS", "FAIL", "REVIEW_REQUIRED", "NOT_RUN", "BLOCKED"}
EXTERNAL = {"site", "browser", "desktop", "production"}


def is_digest(value: object, size: int = 64) -> bool:
    return isinstance(value, str) and bool((HEX40 if size == 40 else HEX64).fullmatch(value))


def assess(lock: object, records: object) -> dict:
    errors: list[str] = []
    if not isinstance(lock, dict) or not isinstance(records, list):
        return {"status": "INVALID_RECEIPTS", "errors": ["lock must be mapping; records list"], "release_approved": False}
    source = lock.get("source_revision")
    release = lock.get("release_id")
    payload = lock.get("payload_content_sha256")
    if not is_digest(source, 40) or not is_digest(payload) or not isinstance(release, str) or not release:
        errors.append("lock: missing exact source/release/payload")
    if lock.get("runtime_execution_state") != "NOT_RUN" or lock.get("release_approved") is not False:
        errors.append("lock: must be executor-only original NOT_RUN baseline")
    cases = lock.get("cases")
    if not isinstance(cases, list):
        cases = []
        errors.append("lock: cases must be a list")
    indexed: dict[str, dict] = {}
    expected: set[tuple[str, int]] = set()
    for item in cases:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or item["id"] in indexed:
            errors.append("lock: invalid or duplicated case")
            continue
        n = item.get("repetitions")
        if type(n) is not int or n < 1 or n > 100:
            errors.append(f"lock: invalid repetitions for {item['id']}")
            continue
        if item.get("channel") not in {"lab", *EXTERNAL}:
            errors.append(f"lock: invalid channel for {item['id']}")
        if not is_digest(item.get("input_sha256")) or not is_digest(item.get("rubric_sha256")):
            errors.append(f"lock: missing frozen input/rubric digest for {item['id']}")
        indexed[item["id"]] = item
        expected.update((item["id"], i) for i in range(1, n + 1))

    observed: set[tuple[str, int]] = set()
    execution_counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "NOT_RUN": 0, "REVIEW_REQUIRED": 0}
    for idx, record in enumerate(records):
        prefix = f"record[{idx}]"
        if not isinstance(record, dict):
            errors.append(prefix + ": nonmapping")
            continue
        name, number = record.get("case_id"), record.get("attempt")
        if not isinstance(name, str) or type(number) is not int or (name, number) not in expected:
            errors.append(prefix + ": unknown case/attempt or attempt outside lock")
            continue
        key = (name, number)
        if key in observed:
            errors.append(prefix + ": duplicate execution receipt")
            continue
        observed.add(key)
        case = indexed[name]
        for field, expected_value in (
            ("source_revision", source), ("release_id", release),
            ("payload_content_sha256", payload),
            ("input_sha256", case.get("input_sha256")),
            ("rubric_sha256", case.get("rubric_sha256")),
            ("channel", case.get("channel")),
        ):
            if record.get(field) != expected_value:
                errors.append(prefix + f": stale/unmatched {field}")
        decision = record.get("decision")
        state = record.get("execution_state")
        if decision not in REPORT_STATUSES or state not in EXECUTED | UNRUN:
            errors.append(prefix + ": invalid status/execution state")
            continue
        execution_counts[decision] += 1
        if state in UNRUN:
            if decision not in {"NOT_RUN", "BLOCKED"}:
                errors.append(prefix + ": nonexecuted attempt must not claim behavior verdict")
            if record.get("actual_output_sha256") or record.get("tool_trace_sha256"):
                errors.append(prefix + ": nonexecuted attempt invents output or tool trace")
        else:
            if decision not in {"PASS", "FAIL", "REVIEW_REQUIRED"}:
                errors.append(prefix + ": executed attempt has no independent verdict")
            for field in ("actual_output_sha256", "tool_trace_sha256", "evaluator_receipt_sha256"):
                if not is_digest(record.get(field)):
                    errors.append(prefix + f": {field} missing/invalid")
            executor, evaluator = record.get("executor"), record.get("evaluator")
            if not isinstance(executor, str) or not executor or not isinstance(evaluator, str) or not evaluator or evaluator == executor:
                errors.append(prefix + ": independent evaluator is required")
            if record.get("assisted") is True and decision == "PASS":
                errors.append(prefix + ": assisted execution cannot be PASS")
            if case["channel"] in EXTERNAL and not record.get("approval_reference"):
                errors.append(prefix + ": external provider needs scoped approval")
            if case["channel"] in {"site", "browser"} and name in {
                "I02-149-cloud-e2e", "I02-251-browser-mcp", "I02-253-parity", "I02-254-charts"
            } and record.get("client_display_state") != "observed":
                errors.append(prefix + ": required client-visible evidence absent")
        if record.get("synthetic_fixture") is True and decision in {"PASS", "FAIL"}:
            errors.append(prefix + ": synthetic fixture must not certify runtime behavior")

    missing = sorted(expected - observed)
    gates = lock.get("manual_gates") or []
    if not isinstance(gates, list) or any(not isinstance(item, dict) or item.get("status") not in {"NOT_RUN", "BLOCKED"} for item in gates):
        errors.append("lock: manual gates not in original unresolved state")
    status = "INVALID_RECEIPTS" if errors else ("INCOMPLETE" if missing else "EVIDENCE_STRUCTURALLY_COMPLETE_REVIEW_REQUIRED")
    if not records and not errors:
        status = "NO_EXECUTION_RECEIPTS"
    return {
        "schema_version": "1.0", "status": status, "errors": errors,
        "locked_source_revision": source, "recorded_attempts": len(observed),
        "required_attempts": len(expected), "missing_attempts": len(missing),
        "missing_attempt_ids": [f"{name}#{number}" for name, number in missing],
        "reported_decisions_unverified": execution_counts,
        "manual_gates": [{"id": g.get("id"), "status": g.get("status")} for g in gates if isinstance(g, dict)],
        "authentication": "NOT_VERIFIED", "runtime_provider_execution": "NOT_PERFORMED_BY_INTAKE",
        "independent_rubric_review": "NOT_VERIFIED_BY_INTAKE", "release_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        lock = json.loads(args.lock.read_text(encoding="utf-8"))
        rows = json.loads(args.records.read_text(encoding="utf-8"))
        result = assess(lock, rows)
    except (ValueError, OSError, TypeError) as exc:
        result = {"status": "INVALID_RECEIPTS", "errors": [type(exc).__name__], "release_approved": False}
    content = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 1 if result["status"] in {"INVALID_RECEIPTS", "NO_EXECUTION_RECEIPTS", "INCOMPLETE"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
