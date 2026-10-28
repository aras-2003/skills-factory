"""Evidence-bound market sizing and white-space calculations; no data retrieval."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class InputError(ValueError):
    pass


def number(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise InputError(f"{field} must be numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise InputError(f"{field} must be numeric") from exc
    if not result.is_finite() or result < 0:
        raise InputError(f"{field} must be finite and non-negative")
    return result


def evidenced(raw: Any, field: str, as_of: date) -> tuple[Decimal, dict[str, str]]:
    if not isinstance(raw, dict) or not isinstance(raw.get("source_id"), str) or not raw["source_id"].strip():
        raise InputError(f"{field} requires source_id and published_at")
    try:
        published = date.fromisoformat(raw.get("published_at", ""))
    except ValueError as exc:
        raise InputError(f"{field}.published_at must be YYYY-MM-DD") from exc
    if published.isoformat() != raw["published_at"] or published > as_of:
        raise InputError(f"{field} has invalid or future-dated evidence")
    return number(raw.get("value"), f"{field}.value"), {"source_id": raw["source_id"].strip(), "published_at": published.isoformat()}


def calculate(data: dict[str, Any]) -> dict[str, Any]:
    try:
        as_of = date.fromisoformat(data.get("as_of", ""))
    except (ValueError, TypeError) as exc:
        raise InputError("as_of must be YYYY-MM-DD") from exc
    if as_of.isoformat() != data["as_of"]:
        raise InputError("as_of must be YYYY-MM-DD")
    currency = data.get("currency")
    if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
        raise InputError("currency must be an explicit three-letter code")
    top, top_ev = evidenced(data.get("top_down"), "top_down", as_of)
    bottom, bottom_ev = evidenced(data.get("bottom_up"), "bottom_up", as_of)
    segments = data.get("segments")
    if not isinstance(segments, list) or not segments:
        raise InputError("segments must be a non-empty list")
    seen: set[str] = set()
    total = Decimal("0")
    segment_rows = []
    for i, row in enumerate(segments):
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"].strip() or row["id"] in seen:
            raise InputError(f"segments[{i}] requires a unique id")
        seen.add(row["id"])
        size, size_ev = evidenced(row.get("annual_spend"), f"segments[{i}].annual_spend", as_of)
        fit, fit_ev = evidenced(row.get("serviceable_share"), f"segments[{i}].serviceable_share", as_of)
        capture, capture_ev = evidenced(row.get("attainable_share"), f"segments[{i}].attainable_share", as_of)
        if fit > 1 or capture > 1:
            raise InputError("segment shares must be between zero and one")
        sam, som = size * fit, size * fit * capture
        total += sam
        segment_rows.append({"id": row["id"], "tam": str(size), "sam": str(sam), "som": str(som), "evidence": {"annual_spend": size_ev, "serviceable_share": fit_ev, "attainable_share": capture_ev}})
    covered, covered_ev = evidenced(data.get("currently_served"), "currently_served", as_of)
    sam = total
    if covered > sam:
        raise InputError("currently_served cannot exceed segment-derived SAM")
    uncovered = sam - covered
    unmet_raw = data.get("validated_unmet_demand")
    whitespace = None
    whitespace_ev = None
    if unmet_raw is not None:
        unmet, whitespace_ev = evidenced(unmet_raw, "validated_unmet_demand", as_of)
        if unmet > uncovered:
            raise InputError("validated_unmet_demand cannot exceed uncovered serviceable value")
        whitespace = str(unmet)
    return {"as_of": as_of.isoformat(), "currency": currency.upper(), "top_down_tam": str(top), "bottom_up_tam": str(bottom), "tam_difference": str(bottom - top), "segment_derived_sam": str(sam), "currently_served": str(covered), "uncovered_serviceable_value": str(uncovered), "validated_white_space": whitespace, "white_space_evidence": whitespace_ev, "top_down_evidence": top_ev, "bottom_up_evidence": bottom_ev, "currently_served_evidence": covered_ev, "segments": segment_rows, "limitations": ["Top-down and bottom-up estimates remain separate; their difference is not auto-reconciled.", "Segment SAM/SOM is an assumption-driven sizing model, not a demand forecast.", "Uncovered serviceable value is not proof of unmet demand; validated whitespace requires separate sourced unmet-demand evidence.", "Missing segments are not inferred; no currency conversion or market transferability is assumed."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path)
    args = parser.parse_args()
    try:
        text = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        data = json.loads(text)
        if not isinstance(data, dict):
            raise InputError("input must be a JSON object")
        print(json.dumps(calculate(data), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, InputError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
