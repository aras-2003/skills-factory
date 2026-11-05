"""Deterministic, evidence-gated financial model primitives.

No data retrieval, assumption generation, persistence, or investment decisioning.
All rates are effective per model period and all cash flows share one currency.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path
from typing import Any


class ModelInputError(ValueError):
    """Raised when supplied model inputs are malformed or internally inconsistent."""


ZERO = Decimal("0")
ONE = Decimal("1")
CENT = Decimal("0.01")
RATE_EPSILON = Decimal("0.000000000001")


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise ModelInputError(f"{field} must be a decimal number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ModelInputError(f"{field} must be a decimal number") from exc
    if not result.is_finite():
        raise ModelInputError(f"{field} must be finite")
    return result


def _date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise ModelInputError(f"{field} must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ModelInputError(f"{field} must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise ModelInputError(f"{field} must use YYYY-MM-DD")
    return parsed


def _evidence_value(item: Any, *, field: str, as_of: date) -> tuple[Decimal, dict[str, str]]:
    if not isinstance(item, dict):
        raise ModelInputError(f"{field} must include value and provenance")
    value = _decimal(item.get("value"), f"{field}.value")
    source_id = item.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ModelInputError(f"{field}.source_id is required")
    published = _date(item.get("published_at"), f"{field}.published_at")
    if published > as_of:
        raise ModelInputError(f"{field} is future-dated relative to as_of")
    return value, {"source_id": source_id.strip(), "published_at": published.isoformat()}


def _cash_flows(items: Any, *, field: str, as_of: date) -> tuple[list[Decimal], list[dict[str, Any]]]:
    if not isinstance(items, list) or len(items) < 2:
        raise ModelInputError(f"{field} must contain at least periods 0 and 1")
    ordered = sorted(items, key=lambda row: row.get("period", -1) if isinstance(row, dict) else -1)
    values: list[Decimal] = []
    audit: list[dict[str, Any]] = []
    for expected_period, row in enumerate(ordered):
        if not isinstance(row, dict) or type(row.get("period")) is not int or row["period"] != expected_period:
            raise ModelInputError(f"{field} periods must be unique contiguous integers starting at 0")
        value, evidence = _evidence_value(row, field=f"{field}[{expected_period}]", as_of=as_of)
        values.append(value)
        audit.append({"period": expected_period, "value": str(value), **evidence})
    return values, audit


def npv(cash_flows: list[Decimal], rate: Decimal) -> Decimal:
    """Present value of equally spaced period cash flows, including period zero."""
    if not cash_flows:
        raise ModelInputError("cash_flows must not be empty")
    if rate <= Decimal("-1"):
        raise ModelInputError("discount_rate must be greater than -1")
    with localcontext() as ctx:
        ctx.prec = 40
        factor = ONE + rate
        return sum((flow / (factor ** period) for period, flow in enumerate(cash_flows)), ZERO)


def _irr(cash_flows: list[Decimal]) -> Decimal | None:
    signs = [1 if value > ZERO else -1 if value < ZERO else 0 for value in cash_flows]
    nonzero = [sign for sign in signs if sign]
    if not nonzero or nonzero[0] >= 0 or nonzero[-1] <= 0:
        return None
    if sum(left != right for left, right in zip(nonzero, nonzero[1:])) != 1:
        return None

    low, high = Decimal("-0.999999"), Decimal("1")
    low_value = npv(cash_flows, low)
    high_value = npv(cash_flows, high)
    while low_value * high_value > ZERO and high < Decimal("1000000"):
        high *= 2
        high_value = npv(cash_flows, high)
    if low_value * high_value > ZERO:
        return None
    with localcontext() as ctx:
        ctx.prec = 40
        for _ in range(256):
            midpoint = (low + high) / 2
            value = npv(cash_flows, midpoint)
            if abs(value) <= RATE_EPSILON or high - low <= RATE_EPSILON:
                return midpoint
            if (value > ZERO) == (low_value > ZERO):
                low, low_value = midpoint, value
            else:
                high, high_value = midpoint, value
        return (low + high) / 2


def _payback(flows: list[Decimal], rate: Decimal | None = None) -> Decimal | None:
    cumulative = flows[0]
    for period, flow in enumerate(flows[1:], start=1):
        discounted = flow if rate is None else flow / ((ONE + rate) ** period)
        before = cumulative
        cumulative += discounted
        if before < ZERO <= cumulative and discounted > ZERO:
            return Decimal(period - 1) + (-before / discounted)
    return None


def _terminal_value(last_flow: Decimal, discount_rate: Decimal, growth_rate: Decimal) -> Decimal:
    if growth_rate <= Decimal("-1"):
        raise ModelInputError("terminal_growth must be greater than -1")
    if growth_rate >= discount_rate:
        raise ModelInputError("terminal_growth must be lower than discount_rate")
    return last_flow * (ONE + growth_rate) / (discount_rate - growth_rate)


def _money(value: Decimal) -> str:
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def evaluate_model(data: dict[str, Any]) -> dict[str, Any]:
    """Calculate NPV, optional DCF terminal value, IRR, payback and explicit scenarios.

    Probabilities are treated as user-supplied scenario weights, never as calibrated
    outcome probabilities. A result is arithmetic, not an investment recommendation.
    """
    if not isinstance(data, dict):
        raise ModelInputError("model input must be an object")
    currency = data.get("currency")
    if not isinstance(currency, str) or not currency.strip():
        raise ModelInputError("currency is required")
    as_of = _date(data.get("as_of"), "as_of")
    discount_rate, discount_evidence = _evidence_value(data.get("discount_rate"), field="discount_rate", as_of=as_of)
    if discount_rate <= Decimal("-1"):
        raise ModelInputError("discount_rate must be greater than -1")
    flows, flows_audit = _cash_flows(data.get("cash_flows"), field="cash_flows", as_of=as_of)
    growth_rate = None
    growth_evidence = None
    if data.get("terminal_growth") is not None:
        growth_rate, growth_evidence = _evidence_value(data["terminal_growth"], field="terminal_growth", as_of=as_of)
        terminal = _terminal_value(flows[-1], discount_rate, growth_rate)
        terminal_pv = terminal / ((ONE + discount_rate) ** (len(flows) - 1))
    else:
        terminal = terminal_pv = ZERO

    base_npv = npv(flows, discount_rate) + terminal_pv
    irr_flows = list(flows)
    if growth_rate is not None:
        irr_flows[-1] += terminal
    irr_value = _irr(irr_flows)
    result: dict[str, Any] = {
        "status": "CALCULATED",
        "currency": currency.strip(),
        "as_of": as_of.isoformat(),
        "period_convention": "equally spaced periods; period 0 is undiscounted",
        "discount_rate": {"value": str(discount_rate), **discount_evidence},
        "cash_flows": flows_audit,
        "npv": _money(base_npv),
        "irr": (str(irr_value) if irr_value is not None else None),
        "simple_payback_periods": (str(_payback(flows)) if _payback(flows) is not None else None),
        "discounted_payback_periods": (str(_payback(flows, discount_rate)) if _payback(flows, discount_rate) is not None else None),
        "terminal_value": None,
        "assumption_status": "USER_OR_EVIDENCE_SUPPLIED",
        "risk_adjusted_value": None,
        "statistical_or_outcome_probability_claimed": False,
        "source_ids": sorted({discount_evidence["source_id"], *(row["source_id"] for row in flows_audit)}),
    }
    if growth_rate is not None:
        result["terminal_value"] = {
            "method": "Gordon growth",
            "growth_rate": {"value": str(growth_rate), **growth_evidence},
            "undiscounted": _money(terminal),
            "present_value": _money(terminal_pv),
        }
        result["source_ids"] = sorted({*result["source_ids"], growth_evidence["source_id"]})

    scenarios = data.get("scenarios", [])
    if not isinstance(scenarios, list):
        raise ModelInputError("scenarios must be a list")
    scenario_rows = []
    scenario_npvs: list[tuple[Decimal, Decimal]] = []
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict) or not isinstance(scenario.get("name"), str) or not scenario["name"].strip():
            raise ModelInputError(f"scenarios[{index}] needs a name")
        probability, probability_evidence = _evidence_value(scenario.get("weight"), field=f"scenarios[{index}].weight", as_of=as_of)
        if not ZERO <= probability <= ONE:
            raise ModelInputError(f"scenarios[{index}].weight.value must be between 0 and 1")
        scenario_flows, scenario_audit = _cash_flows(scenario.get("cash_flows"), field=f"scenarios[{index}].cash_flows", as_of=as_of)
        scenario_npv = npv(scenario_flows, discount_rate)
        if growth_rate is not None:
            scenario_terminal = _terminal_value(scenario_flows[-1], discount_rate, growth_rate)
            scenario_npv += scenario_terminal / ((ONE + discount_rate) ** (len(scenario_flows) - 1))
        scenario_npvs.append((probability, scenario_npv))
        scenario_rows.append({
            "name": scenario["name"].strip(), "weight": str(probability),
            "weight_source_id": probability_evidence["source_id"],
            "npv": _money(scenario_npv),
            "cash_flows": scenario_audit,
        })
    if scenarios:
        total_weight = sum((_decimal(row["weight"], "scenario.weight") for row in scenario_rows), ZERO)
        if total_weight != ONE:
            raise ModelInputError("scenario weights must sum exactly to 1.0")
        result["scenarios"] = scenario_rows
        result["risk_adjusted_value"] = {
            "method": "explicitly weighted scenario NPV",
            "value": _money(sum((weight * scenario_value for weight, scenario_value in scenario_npvs), ZERO)),
            "weights_are_calibrated_probabilities": False,
        }

    sensitivity = data.get("sensitivity")
    if sensitivity is not None:
        if not isinstance(sensitivity, dict):
            raise ModelInputError("sensitivity must be an object")
        rates = sensitivity.get("discount_rates")
        if not isinstance(rates, list) or not rates:
            raise ModelInputError("sensitivity.discount_rates must be explicit and non-empty")
        rate_values = [_evidence_value(rate, field=f"sensitivity.discount_rates[{i}]", as_of=as_of) for i, rate in enumerate(rates)]
        growth_values = [None]
        if growth_rate is not None:
            values = sensitivity.get("terminal_growth_rates")
            if not isinstance(values, list) or not values:
                raise ModelInputError("sensitivity.terminal_growth_rates must be explicit when terminal growth is used")
            growth_values = [_evidence_value(value, field=f"sensitivity.terminal_growth_rates[{i}]", as_of=as_of) for i, value in enumerate(values)]
        elif sensitivity.get("terminal_growth_rates") is not None:
            raise ModelInputError("terminal growth sensitivity requires a terminal_growth assumption")
        rows = []
        for rate, rate_evidence in rate_values:
            if rate <= Decimal("-1"):
                raise ModelInputError("sensitivity discount rates must be greater than -1")
            for growth in growth_values:
                growth_value, growth_evidence = growth if growth is not None else (None, None)
                pv_terminal = ZERO if growth_value is None else _terminal_value(flows[-1], rate, growth_value) / ((ONE + rate) ** (len(flows) - 1))
                rows.append({
                    "discount_rate": {"value": str(rate), **rate_evidence},
                    "terminal_growth": None if growth_value is None else {"value": str(growth_value), **growth_evidence},
                    "npv": _money(npv(flows, rate) + pv_terminal),
                })
        result["sensitivity"] = rows
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate an evidence-bound financial model from JSON.")
    parser.add_argument("input", nargs="?", help="Input JSON path; reads stdin when omitted.")
    args = parser.parse_args()
    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        result = evaluate_model(json.loads(raw))
    except (OSError, json.JSONDecodeError, ModelInputError) as exc:
        print(f"financial-modeling: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
