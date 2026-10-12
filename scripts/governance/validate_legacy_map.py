#!/usr/bin/env python3
"""Offline source-bound historical legacy-ID map audit; never mutates Projects."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = Path("docs/governance/backlog-legacy-issue-map.json")


def blob_sha(data: bytes) -> str:
    """Git blob object hash for the exact historical source bytes."""
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def validate(root: Path, mapping_file: Path = MAP) -> tuple[dict, list[str]]:
    root = root.resolve()
    issues: list[str] = []
    map_path = root / mapping_file
    try:
        if map_path.resolve().is_relative_to(root) is False:
            raise ValueError("mapping escapes repository root")
        mapping = json.loads(map_path.read_text(encoding="utf-8"))
        historical_name = mapping["source"]
        historical_path = Path(historical_name)
        if historical_path.is_absolute() or ".." in historical_path.parts:
            raise ValueError("unsafe historical source path")
        source_path = (root / historical_path).resolve()
        if not source_path.is_relative_to(root):
            raise ValueError("historical source escapes repository root")
        data = source_path.read_bytes()
        source = json.loads(data.decode("utf-8"))
        items = source["items"]
        mapped = mapping["items"]
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        return {"schema_version": 1, "status": "BLOCKED_SOURCE"}, [f"cannot validate source/map: {error}"]

    if not isinstance(items, list) or not isinstance(mapped, list):
        return {"schema_version": 1, "status": "BLOCKED_SCHEMA"}, ["source and map items must be lists"]

    expected = [item.get("id") if isinstance(item, dict) else None for item in items]
    actual = [item.get("legacy_id") if isinstance(item, dict) else None for item in mapped]
    # Malformed input is untrusted. Validate types before hashing/sorting IDs;
    # dict/list/int IDs must yield a blocker instead of crashing the CI step.
    if any(not isinstance(value, str) or not value for value in expected + actual):
        return {"schema_version": 1, "status": "BLOCKED_SCHEMA"}, [
            "all historical and mapped IDs must be nonempty strings"
        ]
    if len(expected) != len(set(expected)):
        issues.append("duplicate IDs in historical source")
    if len(actual) != len(set(actual)):
        issues.append("duplicate IDs in issue map")
    missing, extra = sorted(set(expected) - set(actual)), sorted(set(actual) - set(expected))
    if missing:
        issues.append("unmapped historical IDs: " + ", ".join(missing))
    if extra:
        issues.append("unknown mapped IDs: " + ", ".join(extra))
    numbers = [row.get("issue") if isinstance(row, dict) else None for row in mapped]
    if any(type(number) is not int or number < 1 for number in numbers):
        issues.append("all mapped issues must be positive integer numbers")
    if len(numbers) != len(set(numbers)):
        issues.append("multiple historical IDs mapped to the same GitHub Issue")
    if any(not isinstance(row, dict) or type(row.get("review_required")) is not bool for row in mapped):
        issues.append("every mapping must declare review_required boolean")
    expected_sha = blob_sha(data)
    if mapping.get("source_blob_sha") != expected_sha:
        issues.append("historical blob SHA mismatch; review exact source rather than repinning silently")
    report = {
        "schema_version": 1,
        "status": "STATIC_ID_MAP_OK" if not issues else "BLOCKED",
        "source": historical_name,
        "source_blob_sha": expected_sha,
        "historical_count": len(expected),
        "mapped_count": len(actual),
        "unique_issue_count": len(set(numbers)),
        "review_required_count": sum(row.get("review_required") is True for row in mapped if isinstance(row, dict)),
        "project_v2_membership_and_fields": "NOT_VERIFIED",
        "runtime_evidence": "NOT_RUN",
        "note": "Offline ID mapping only; not Project V2 readback, duplicate implementation review, or approved cutover.",
    }
    return report, issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report, errors = validate(args.root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"report": report, "errors": errors}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": report, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
