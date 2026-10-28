"""Deterministic benefit-ledger checks; no persistence or action execution."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


class LedgerInputError(ValueError):
    pass


def _date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise LedgerInputError(f"{field} must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise LedgerInputError(f"{field} must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise LedgerInputError(f"{field} must use YYYY-MM-DD")
    return parsed


def _number(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise LedgerInputError(f"{field} must be numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise LedgerInputError(f"{field} must be numeric") from exc
    if not result.is_finite():
        raise LedgerInputError(f"{field} must be finite")
    return result


def _evidence(value: Any, *, field: str, as_of: date) -> tuple[Decimal, dict[str, str]]:
    if not isinstance(value, dict):
        raise LedgerInputError(f"{field} needs a value and evidence")
    amount = _number(value.get("value"), f"{field}.value")
    source_id = value.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        raise LedgerInputError(f"{field}.source_id is required")
    published = _date(value.get("published_at"), f"{field}.published_at")
    if published > as_of:
        raise LedgerInputError(f"{field} is future-dated relative to as_of")
    return amount, {"source_id": source_id.strip(), "published_at": published.isoformat()}


def _period_series(items: Any, *, field: str, as_of: date) -> dict[str, tuple[Decimal, dict[str, str]]]:
    if not isinstance(items, list):
        raise LedgerInputError(f"{field} must be a list")
    result: dict[str, tuple[Decimal, dict[str, str]]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise LedgerInputError(f"{field}[{index}] must be an object")
        period = item.get("period")
        if not isinstance(period, str) or len(period) != 7 or period[4] != "-":
            raise LedgerInputError(f"{field}[{index}].period must be YYYY-MM")
        period_date = _date(period + "-01", f"{field}[{index}].period")
        if period_date > as_of.replace(day=1):
            raise LedgerInputError(f"{field}[{index}] period is after as_of")
        if period in result:
            raise LedgerInputError(f"{field} has duplicate period {period}")
        amount, evidence = _evidence(item, field=f"{field}[{index}]", as_of=as_of)
        result[period] = (amount, evidence)
    return result


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def evaluate_ledger(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise LedgerInputError("input must be an object")
    as_of = _date(data.get("as_of"), "as_of")
    initiatives = data.get("initiatives")
    if not isinstance(initiatives, list) or not initiatives:
        return {"status": "BLOCKED_NO_INITIATIVES", "as_of": as_of.isoformat(), "initiatives": []}
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for index, item in enumerate(initiatives):
        prefix = f"initiatives[{index}]"
        if not isinstance(item, dict):
            raise LedgerInputError(f"{prefix} must be an object")
        initiative_id = item.get("initiative_id")
        owner = item.get("owner")
        currency = item.get("currency")
        if not isinstance(initiative_id, str) or not initiative_id.strip() or initiative_id in seen:
            raise LedgerInputError(f"{prefix}.initiative_id must be unique and non-empty")
        if not isinstance(owner, str) or not owner.strip():
            raise LedgerInputError(f"{prefix}.owner is required")
        if not isinstance(currency, str) or not currency.strip():
            raise LedgerInputError(f"{prefix}.currency is required")
        seen.add(initiative_id)
        funded, funded_evidence = _evidence(item.get("funded_amount"), field=f"{prefix}.funded_amount", as_of=as_of)
        if funded < 0:
            raise LedgerInputError(f"{prefix}.funded_amount must be non-negative")
        cadence_value, cadence_evidence = _evidence(item.get("review_cadence_days"), field=f"{prefix}.review_cadence_days", as_of=as_of)
        if cadence_value != cadence_value.to_integral_value() or cadence_value <= 0:
            raise LedgerInputError(f"{prefix}.review_cadence_days.value must be a positive integer")
        cadence = int(cadence_value)
        last_review = item.get("last_review_at")
        review_state = "NOT_CONFIGURED"
        if last_review is not None:
            last_review_date = _date(last_review, f"{prefix}.last_review_at")
            if last_review_date > as_of:
                raise LedgerInputError(f"{prefix}.last_review_at is after as_of")
            review_state = "DUE" if (as_of - last_review_date).days >= cadence else "NOT_DUE"

        benefits = item.get("benefits")
        if not isinstance(benefits, list) or not benefits:
            raise LedgerInputError(f"{prefix}.benefits must be a non-empty list")
        benefit_results: list[dict[str, Any]] = []
        critical_variances: list[Decimal] = []
        benefit_ids: set[str] = set()
        for b_index, benefit in enumerate(benefits):
            bp = f"{prefix}.benefits[{b_index}]"
            if not isinstance(benefit, dict):
                raise LedgerInputError(f"{bp} must be an object")
            kpi_id = benefit.get("kpi_id")
            kind = benefit.get("kind")
            unit = benefit.get("unit")
            if not isinstance(kpi_id, str) or not kpi_id.strip() or kpi_id in benefit_ids:
                raise LedgerInputError(f"{bp}.kpi_id must be unique and non-empty")
            if kind not in {"leading", "lagging"}:
                raise LedgerInputError(f"{bp}.kind must be leading or lagging")
            if not isinstance(unit, str) or not unit.strip():
                raise LedgerInputError(f"{bp}.unit is required")
            if "decision_critical" in benefit and type(benefit["decision_critical"]) is not bool:
                raise LedgerInputError(f"{bp}.decision_critical must be boolean")
            benefit_ids.add(kpi_id)
            baseline, baseline_evidence = _evidence(benefit.get("baseline"), field=f"{bp}.baseline", as_of=as_of)
            target, target_evidence = _evidence(benefit.get("target"), field=f"{bp}.target", as_of=as_of)
            forecast = _period_series(benefit.get("forecast"), field=f"{bp}.forecast", as_of=as_of)
            actual = _period_series(benefit.get("actual"), field=f"{bp}.actual", as_of=as_of)
            aligned = sorted(set(forecast) & set(actual))
            period_rows = []
            for period in aligned:
                expected, _ = forecast[period]
                realized, _ = actual[period]
                variance = realized - expected
                variance_pct = None if expected == 0 else variance / abs(expected)
                period_rows.append({
                    "period": period,
                    "forecast": _money(expected),
                    "actual": _money(realized),
                    "variance": _money(variance),
                    "variance_pct": None if variance_pct is None else str(variance_pct),
                    "forecast_source_id": forecast[period][1]["source_id"],
                    "forecast_published_at": forecast[period][1]["published_at"],
                    "actual_source_id": actual[period][1]["source_id"],
                    "actual_published_at": actual[period][1]["published_at"],
                })
            if benefit.get("decision_critical") is True and period_rows:
                latest = period_rows[-1]
                if latest["variance_pct"] is not None:
                    critical_variances.append(Decimal(latest["variance_pct"]))
            benefit_results.append({
                "kpi_id": kpi_id,
                "kind": kind,
                "unit": unit.strip(),
                "baseline": {"value": _money(baseline), **baseline_evidence},
                "target": {"value": _money(target), **target_evidence},
                "periods": period_rows,
                "unmatched_forecast_periods": sorted(set(forecast) - set(actual)),
                "unmatched_actual_periods": sorted(set(actual) - set(forecast)),
                "status": "COMPARABLE" if period_rows else "BLOCKED_NO_ALIGNED_ACTUAL",
            })

        rules = item.get("decision_rules")
        decision = {"status": "NOT_CONFIGURED", "action": None}
        if isinstance(rules, dict) and critical_variances:
            if len(critical_variances) != 1:
                raise LedgerInputError(f"{prefix} needs exactly one comparable decision-critical KPI to apply thresholds")
            stop_below, stop_evidence = _evidence(rules.get("stop_if_variance_pct_at_or_below"), field=f"{prefix}.decision_rules.stop_if_variance_pct_at_or_below", as_of=as_of)
            correct_below, correct_evidence = _evidence(rules.get("correct_if_variance_pct_at_or_below"), field=f"{prefix}.decision_rules.correct_if_variance_pct_at_or_below", as_of=as_of)
            if stop_below > correct_below:
                raise LedgerInputError(f"{prefix}.decision_rules stop threshold must be <= correction threshold")
            latest_variance = critical_variances[-1]
            action = "STOP_REVIEW" if latest_variance <= stop_below else "CORRECT_REVIEW" if latest_variance <= correct_below else "CONTINUE_REVIEW"
            decision = {"status": "THRESHOLDS_APPLIED", "action": action, "latest_critical_variance_pct": str(latest_variance), "human_decision_required": True,
                        "stop_threshold": {"value": str(stop_below), **stop_evidence}, "correction_threshold": {"value": str(correct_below), **correct_evidence}}
        elif rules is not None and not isinstance(rules, dict):
            raise LedgerInputError(f"{prefix}.decision_rules must be an object")

        output.append({
            "initiative_id": initiative_id,
            "owner": owner.strip(),
            "currency": currency.strip(),
            "funded_amount": {"value": _money(funded), **funded_evidence},
            "review_cadence_days": {"value": cadence, **cadence_evidence},
            "review_state": review_state,
            "next_review_at": (last_review_date + timedelta(days=cadence)).isoformat() if last_review is not None else None,
            "benefits": benefit_results,
            "decision": decision,
        })
    return {"status": "REVIEWABLE", "as_of": as_of.isoformat(), "initiatives": output, "writes_performed": False}


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a sourced benefits-realization ledger from JSON.")
    parser.add_argument("input", nargs="?", help="JSON input path; stdin when omitted.")
    args = parser.parse_args()
    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        output = evaluate_ledger(json.loads(raw))
    except (OSError, json.JSONDecodeError, LedgerInputError) as exc:
        print(f"value-realization: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
