#!/usr/bin/env python3
"""Auditable R17 historical verdict reconciliation (no reruns, no rewrites).

Use transcript receipts as historical, not as current exact-revision model PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path("evals/results/runtime-campaign-r17/manifest.json")
VERDICTS = {"PASS", "FAIL", "REVIEW_REQUIRED"}


def audit(root: Path = ROOT, manifest_path: Path = MANIFEST) -> dict:
    try:
        data = json.loads((root / manifest_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status": "BLOCKED_SOURCE", "errors": [str(exc)], "current_candidate_runtime": "NOT_RUN"}
    errors: list[str] = []
    if not isinstance(data, dict) or not isinstance(data.get("valid_receipts"), list):
        return {"status": "BLOCKED_SOURCE", "errors": ["R17 manifest missing receipt list"], "current_candidate_runtime": "NOT_RUN"}
    referenced = data["valid_receipts"]
    if len(referenced) != len(set(x for x in referenced if isinstance(x, str))):
        errors.append("duplicate historical receipt path")
    rows: list[dict] = []
    statuses: Counter = Counter()
    case_names = set()
    safe_base = (root / "evals/results/runtime-campaign-r17").resolve()
    for rel in referenced:
        if not isinstance(rel, str):
            errors.append("nonstring historical receipt path")
            continue
        source = (root / rel).resolve()
        if not source.is_relative_to(safe_base) or source.name != "transcript-receipt.json":
            errors.append(f"unsafe historical receipt path {rel}")
            continue
        try:
            raw = source.read_bytes()
            receipt = json.loads(raw)
        except (OSError, ValueError) as exc:
            errors.append(f"{rel}: unreadable/malformed {type(exc).__name__}")
            continue
        if not isinstance(receipt, dict):
            errors.append(f"{rel}: receipt is not a mapping")
            continue
        cid = receipt.get("case_id")
        if not isinstance(cid, str) or not cid or cid != source.parent.parent.name:
            errors.append(f"{rel}: case identity mismatch")
            continue
        if cid in case_names:
            errors.append(f"{rel}: duplicated case {cid}")
            continue
        case_names.add(cid)
        status = receipt.get("status")
        if not isinstance(status, str) or status not in VERDICTS:
            errors.append(f"{rel}: invalid historical verdict")
            continue
        evaluation = receipt.get("independent_evaluation") or {}
        if not isinstance(evaluation, dict) or evaluation.get("status") != status:
            errors.append(f"{rel}: historical independent verdict inconsistent")
            continue
        statuses[status] += 1
        execution = receipt.get("execution") or {}
        if not isinstance(execution, dict):
            errors.append(f"{rel}: missing execution metadata")
            continue
        rows.append({
            "case_id": cid, "historical_status": status,
            "receipt_path": rel, "receipt_sha256": hashlib.sha256(raw).hexdigest(),
            "behavior_source_revision": execution.get("behavior_source_revision"),
            "lab_source_revision": execution.get("lab_source_revision"),
            "evidence_type": "HISTORICAL_TRANSCRIPT_REFERENCE_ONLY",
            "machine_validated_runtime": False,
            "current_candidate_outcome": "NOT_RUN",
            "next_action": "EXACT_VERSION_RERUN_REQUIRED" if status == "FAIL" else "PRESERVE_HISTORICAL_ONLY",
        })
    declared = data.get("counts")
    if not isinstance(declared, dict):
        errors.append("manifest counts absent")
        declared = {}
    for key in ("PASS", "FAIL", "REVIEW_REQUIRED"):
        if type(declared.get(key)) is not int or statuses[key] != declared[key]:
            errors.append(f"manifest {key} count disagrees with historical receipts")
    if data.get("case_count") != len(rows) or declared.get("valid_receipt_count") != len(rows):
        errors.append("manifest case and receipt totals differ")
    if data.get("machine_validated_runtime_receipt_count") != 0:
        errors.append("R17 is transcript-only and cannot be promoted to machine-validated receipts")
    excluded = data.get("excluded_production_only_case_ids") or []
    if not isinstance(excluded, list) or len(excluded) != len(set(str(x) for x in excluded)):
        errors.append("invalid/duplicated Production exclusions")
    if any(name in case_names for name in excluded):
        errors.append("Production-only case included in Lab historical counts")
    return {
        "schema_version": "1.0", "kind": "r17_history_exact_evidence_audit",
        "status": "BLOCKED_SOURCE" if errors else "HISTORICAL_RECEIPTS_RECONCILED_NOT_CURRENT",
        "errors": errors, "historical_counts": {x: statuses[x] for x in sorted(VERDICTS)},
        "historical_case_count": len(rows), "production_only_exclusions": excluded,
        "retest_failures": sorted(x["case_id"] for x in rows if x["historical_status"] == "FAIL"),
        "case_records": sorted(rows, key=lambda x: x["case_id"]),
        "current_candidate_runtime": "NOT_RUN", "release_approved": False,
        "provider_execution": "NOT_PERFORMED_BY_AUDIT",
        "note": "No R17 values, original receipts or independent verdicts were overwritten.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.root)
    content = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return int(report["status"] != "HISTORICAL_RECEIPTS_RECONCILED_NOT_CURRENT")


if __name__ == "__main__":
    raise SystemExit(main())
