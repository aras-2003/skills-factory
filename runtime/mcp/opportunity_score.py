"""Bounded deterministic opportunity scoring for the Python MCP facade.

This is the packaged-runtime mirror of the Worker calculator. It consumes only
caller-supplied normalized evidence and deliberately performs no research.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

MODEL = "opportunity-score-v0.1-provisional"
WEIGHTS = {
    "1-3m": {"catalyst_timing": (22, 45), "estimate_revisions": (18, 90), "valuation_expectations": (15, 90), "price_setup": (15, 30), "scenario_asymmetry": (20, 90), "cycle_resilience": (10, 180)},
    "6-12m": {"scenario_asymmetry": (23, 180), "valuation_expectations": (22, 180), "estimate_revisions": (18, 120), "business_quality": (17, 365), "risk_resilience": (10, 180), "cycle_resilience": (10, 365)},
    ">3y": {"growth_durability": (24, 365), "business_quality": (22, 365), "reinvestment_returns": (18, 365), "valuation_expectations": (16, 180), "balance_sheet_resilience": (10, 180), "cycle_resilience": (10, 730)},
}
FACTOR_KEYS = {"value", "confidence", "as_of_date", "source_ids", "definition", "normalization_profile", "quality"}


def _date(value: Any) -> date:
    if not isinstance(value, str):
        raise ValueError("date must be an ISO calendar date")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("date must be an ISO calendar date")
    return parsed


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("value must be numeric")
    number = Decimal(str(value))
    if not number.is_finite() or number < 0 or number > 1 or max(0, -number.as_tuple().exponent) > 8:
        raise ValueError("value must be finite, between 0 and 1, with at most 8 decimals")
    return number


def _validate(payload: Any) -> tuple[str, list[dict[str, Any]]]:
    if not isinstance(payload, dict) or set(payload) != {"as_of", "rows"}:
        raise ValueError("input must contain only as_of and rows")
    as_of = payload["as_of"]
    _date(as_of)
    rows = payload["rows"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 30:
        raise ValueError("rows must contain 1 to 30 candidates")
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"candidate_id", "horizon", "evidence"}:
            raise ValueError("each row must contain only candidate_id, horizon, and evidence")
        cid = row["candidate_id"]
        if not isinstance(cid, str) or not cid.strip() or len(cid.strip()) > 120:
            raise ValueError("candidate_id must contain 1 to 120 characters")
        row["candidate_id"] = cid.strip()
        if row["horizon"] not in WEIGHTS:
            raise ValueError("unsupported horizon")
        evidence = row["evidence"]
        if not isinstance(evidence, dict) or len(evidence) > 30:
            raise ValueError("evidence must be an object with at most 30 factors")
        for name, factor in evidence.items():
            if not isinstance(name, str) or not name or not isinstance(factor, dict) or set(factor) != FACTOR_KEYS:
                raise ValueError("invalid factor evidence shape")
            _decimal(factor["value"])
            _decimal(factor["confidence"])
            _date(factor["as_of_date"])
            ids = factor["source_ids"]
            if not isinstance(ids, list) or not 1 <= len(ids) <= 20 or any(not isinstance(x, str) or not x.strip() or len(x.strip()) > 200 for x in ids):
                raise ValueError("source_ids must contain 1 to 20 bounded identifiers")
            for key, limit in (("definition", 500), ("normalization_profile", 200)):
                value = factor[key]
                if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
                    raise ValueError(f"invalid {key}")
            if factor["quality"] not in {"VERIFIED", "PROVISIONAL", "BLOCKED"}:
                raise ValueError("invalid quality")
            factor["source_ids"] = [source_id.strip() for source_id in ids]
            factor["definition"] = factor["definition"].strip()
            factor["normalization_profile"] = factor["normalization_profile"].strip()
    return as_of, rows


def _score(row: dict[str, Any], as_of: str) -> dict[str, Any]:
    horizon = row["horizon"]
    missing, stale, future, weak, invalid = [], [], [], [], []
    valid: dict[str, dict[str, Any]] = {}
    target = _date(as_of)
    for name, (_, max_age) in WEIGHTS[horizon].items():
        item = row["evidence"].get(name)
        if item is None:
            missing.append(name); continue
        if item["quality"] == "BLOCKED":
            invalid.append(name); continue
        age = (target - _date(item["as_of_date"])).days
        if age < 0: future.append(name); continue
        if age > max_age: stale.append(name); continue
        if _decimal(item["confidence"]) < Decimal("0.5"): weak.append(name); continue
        valid[name] = item
    completeness = sum((Decimal(w) / 100 for n, (w, _) in WEIGHTS[horizon].items() if n in valid), Decimal(0))
    confidence = None
    if valid and completeness:
        confidence = sum((Decimal(WEIGHTS[horizon][n][0]) / 100 * _decimal(v["confidence"]) * (Decimal(1) if v["quality"] == "VERIFIED" else Decimal("0.70")) for n, v in valid.items()), Decimal(0)) / completeness
    reasons = {"missing_factors": missing, "stale_factors": stale, "future_dated_factors": future, "weak_evidence_factors": weak, "invalid_factors": invalid}
    if any((missing, stale, future, weak, invalid)):
        return {"candidate_id": row["candidate_id"].strip(), "horizon": horizon, "model_version": MODEL, "as_of": as_of, "status": "NOT_SCORED", "reason": "EVIDENCE_GATE", "score": None, "completeness": str(completeness.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)), "confidence": str(confidence.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)) if confidence is not None else None, **reasons}
    raw = sum((Decimal(WEIGHTS[horizon][n][0]) / 100 * _decimal(v["value"]) for n, v in valid.items()), Decimal(0))
    status = "PROVISIONAL" if any(x["quality"] == "PROVISIONAL" for x in valid.values()) else "SCORED"
    band = "VERY_ATTRACTIVE" if raw >= Decimal(".8") else "ATTRACTIVE" if raw >= Decimal(".65") else "NEUTRAL_WATCH" if raw >= Decimal(".45") else "WEAK" if raw >= Decimal(".25") else "UNFAVORABLE"
    action = "PRIORITIZE" if raw >= Decimal(".65") else "WATCH" if raw >= Decimal(".45") else "DEPRIORITIZE" if raw >= Decimal(".25") else "REJECT"
    return {"candidate_id": row["candidate_id"].strip(), "horizon": horizon, "model_version": MODEL, "status": status, "score": str(raw.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)), "unrounded_score": format(raw, "f"), "score_is_probability": False, "score_band": band, "research_action": "REVIEW_PROVISIONAL" if status == "PROVISIONAL" else action, "confidence": str(confidence.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)), "completeness": "1.00", "factor_contributions": {n: format(Decimal(WEIGHTS[horizon][n][0]) / 100 * _decimal(v["value"]), "f") for n, v in valid.items()}, "factor_weights": {n: format(Decimal(w) / 100, "f") for n, (w, _) in WEIGHTS[horizon].items()}, "factor_evidence": {n: {"value": format(_decimal(v["value"]), "f"), "confidence": format(_decimal(v["confidence"]), "f"), "quality": v["quality"], "as_of_date": v["as_of_date"], "source_ids": v["source_ids"], "definition": v["definition"]} for n, v in valid.items()}, "normalization_profiles": {n: v["normalization_profile"] for n, v in valid.items()}, "factor_source_ids": {n: v["source_ids"] for n, v in valid.items()}, "as_of": as_of}


def _rank(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = [{**r, "rank_within_horizon": None, "score_difference_to_next": None, "ranking_status": "NOT_RANKED", "ranking_reason": r.get("reason", "NOT_SCOREABLE")} for r in rows if r["status"] not in {"SCORED", "PROVISIONAL"}]
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if row["status"] in {"SCORED", "PROVISIONAL"}:
            groups.setdefault((row["horizon"], row["model_version"], row["as_of"]), []).append(row)
    for key, group in sorted(groups.items()):
        ids = [r["candidate_id"] for r in group]
        fingerprints = {(tuple(sorted(r["normalization_profiles"].items())), tuple(sorted((n, v["definition"]) for n, v in r["factor_evidence"].items()))) for r in group}
        if len(ids) != len(set(ids)) or len(fingerprints) != 1:
            reason = "DUPLICATE_CANDIDATE_ID" if len(ids) != len(set(ids)) else "INCOMPATIBLE_NORMALIZATION_OR_FACTOR_DEFINITION"
            result.extend({**r, "rank_within_horizon": None, "ranking_status": "NOT_COMPARABLE", "ranking_reason": reason} for r in group); continue
        group.sort(key=lambda r: (-Decimal(r["unrounded_score"]), r["candidate_id"]))
        for index, row in enumerate(group):
            gap = str((Decimal(row["unrounded_score"]) - Decimal(group[index + 1]["unrounded_score"])).quantize(Decimal(".001"), rounding=ROUND_HALF_UP)) if index + 1 < len(group) else None
            result.append({**row, "rank_within_horizon": index + 1, "score_difference_to_next": gap, "ranking_status": "COMPARABLE"})
    return result


def calculate_opportunity_scores(payload: Any) -> dict[str, Any]:
    as_of, rows = _validate(payload)
    return {"model_version": MODEL, "as_of": as_of, "scores": _rank([_score(r, as_of) for r in rows]), "source": "deterministic_runtime_calculation; supplied_factor_evidence_only", "score_is_probability": False}
