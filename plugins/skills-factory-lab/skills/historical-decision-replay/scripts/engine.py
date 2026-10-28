"""Small deterministic replay primitives; deliberately no data fetching or persistence."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import re


class ReplayInputError(ValueError):
    pass


def _time(value):
    if not isinstance(value, str):
        raise ReplayInputError("timestamp must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReplayInputError("invalid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReplayInputError("timestamp must include a timezone")
    return parsed


def validate_information_set(decision_at, inputs):
    """Return eligible inputs; reject malformed or post-decision information."""
    cutoff = _time(decision_at)
    eligible = []
    for item in inputs:
        if not isinstance(item, dict) or not item.get("source_id"):
            raise ReplayInputError("each input needs a source_id")
        if _time(item.get("published_at")) > cutoff:
            raise ReplayInputError("future-published information cannot enter a decision")
        if _time(item.get("observed_at")) > cutoff:
            raise ReplayInputError("future observation cannot enter a decision")
        eligible.append(dict(item))
    return eligible


def net_return(entry, exit_, fee_bps, slippage_bps):
    """Simple long-only return with symmetric entry/exit costs, as a fraction."""
    try:
        start, end = Decimal(str(entry)), Decimal(str(exit_))
        fee, slip = Decimal(str(fee_bps)), Decimal(str(slippage_bps))
    except (InvalidOperation, TypeError) as exc:
        raise ReplayInputError("prices and costs must be decimal numbers") from exc
    if not start.is_finite() or not end.is_finite() or start <= 0 or end <= 0:
        raise ReplayInputError("prices must be finite and positive")
    if not fee.is_finite() or not slip.is_finite() or fee < 0 or slip < 0:
        raise ReplayInputError("cost assumptions must be finite and non-negative")
    cost = (fee + slip) / Decimal(10000)
    if cost >= 1:
        raise ReplayInputError("per-side cost must be below 100%")
    return (end * (1 - cost) / (start * (1 + cost))) - 1


def summarize_returns(rows):
    """Summarize paired outcomes without implying statistical significance."""
    if not rows:
        return {"status": "BLOCKED_NO_OBSERVATIONS", "n": 0}
    strategy = [Decimal(str(r["strategy_net_return"])) for r in rows]
    baseline = [Decimal(str(r["baseline_net_return"])) for r in rows]
    if any(not x.is_finite() for x in strategy + baseline):
        raise ReplayInputError("returns must be finite")
    wins = sum(s > b for s, b in zip(strategy, baseline))
    n = len(rows)
    return {
        "status": "DESCRIPTIVE_ONLY",
        "n": n,
        "strategy_mean_net_return": str(sum(strategy) / n),
        "baseline_mean_net_return": str(sum(baseline) / n),
        "paired_outperformance_rate": str(Decimal(wins) / n),
        "denominator": n,
        "statistical_significance_claimed": False,
    }


def _finite_decimal(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ReplayInputError(f"{field} must be a decimal number") from exc
    if not result.is_finite():
        raise ReplayInputError(f"{field} must be finite")
    return result


def _series_metrics(period_returns):
    if not period_returns:
        return {"n": 0, "cumulative_return": None, "mean_period_return": None,
                "max_drawdown": None, "positive_period_rate": None, "denominator": 0}
    equity = Decimal(1)
    peak = Decimal(1)
    max_drawdown = Decimal(0)
    positive = 0
    for result in period_returns:
        equity *= Decimal(1) + result
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - Decimal(1))
        positive += result > 0
    return {
        "n": len(period_returns),
        "cumulative_return": str(equity - Decimal(1)),
        "mean_period_return": str(sum(period_returns) / len(period_returns)),
        "max_drawdown": str(max_drawdown),
        "positive_period_rate": str(Decimal(positive) / len(period_returns)),
        "denominator": len(period_returns),
    }


def _net_series(rows, gross_field, exposure_field, cost_per_side):
    result, turnovers = [], []
    previous = Decimal(0)
    for index, row in enumerate(rows):
        exposure = _finite_decimal(row[exposure_field], exposure_field)
        if exposure < 0 or exposure > 1:
            raise ReplayInputError(f"{exposure_field} must be between zero and one")
        gross = _finite_decimal(row[gross_field], gross_field)
        if gross <= -1:
            raise ReplayInputError(f"{gross_field} must be greater than -1")
        turnover = abs(exposure - previous)
        if index == len(rows) - 1:
            turnover += exposure  # include final liquidation in reported costs
        factor = (Decimal(1) + exposure * gross) * (Decimal(1) - turnover * cost_per_side)
        net = factor - Decimal(1)
        if net <= -1:
            raise ReplayInputError("net period return cannot be -100% or lower")
        result.append(net)
        turnovers.append(turnover)
        previous = exposure
    return result, turnovers


def _fixed_baseline(rows, gross_field, cost_per_side):
    result = []
    for index, row in enumerate(rows):
        gross = _finite_decimal(row[gross_field], gross_field)
        if gross <= -1:
            raise ReplayInputError(f"{gross_field} must be greater than -1")
        turnover = Decimal(1) if index == 0 else Decimal(0)
        if index == len(rows) - 1:
            turnover += Decimal(1)
        result.append((Decimal(1) + gross) * (Decimal(1) - turnover * cost_per_side) - Decimal(1))
    return result


def evaluate_replay(rows, *, rule_id, rule_revision, rule_frozen_at,
                    fee_bps, slippage_bps, sample_metadata, split_at=None):
    """Evaluate a frozen long/flat rule against fixed supplied baselines.

    Rows contain only decision-time evidence plus separately labelled period outcomes.
    This deterministic calculation is descriptive; it does not fetch data, establish
    source truth, choose a sample, or prove economic edge.
    """
    if not isinstance(rows, list) or not rows:
        return {"status": "BLOCKED_NO_OBSERVATIONS", "n": 0}
    if fee_bps is None or slippage_bps is None:
        return {"status": "BLOCKED_MISSING_COSTS", "n": len(rows)}
    if not isinstance(rule_id, str) or not rule_id.strip() or not isinstance(rule_revision, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", rule_revision):
        raise ReplayInputError("frozen rule ID and immutable revision SHA are required")
    frozen_at = _time(rule_frozen_at)
    fee = _finite_decimal(fee_bps, "fee_bps")
    slippage = _finite_decimal(slippage_bps, "slippage_bps")
    if fee < 0 or slippage < 0:
        raise ReplayInputError("fee and slippage assumptions must be non-negative")
    cost_per_side = (fee + slippage) / Decimal(10000)
    if cost_per_side >= 1:
        raise ReplayInputError("per-side costs must be below 100%")
    if not isinstance(sample_metadata, dict) or not all(
        isinstance(sample_metadata.get(key), str) and sample_metadata[key].strip()
        for key in ("universe", "selection_method", "exclusions", "survivorship_status")
    ):
        raise ReplayInputError("sample universe, selection, exclusions and survivorship status are required")
    if sample_metadata["survivorship_status"] not in {"ASSESSED", "KNOWN_LIMITATION", "UNRESOLVED"}:
        raise ReplayInputError("survivorship_status must be ASSESSED, KNOWN_LIMITATION or UNRESOLVED")

    required = {
        "decision_at", "outcome_at", "source_id", "benchmark_source_id", "trend_source_id", "information_inputs",
        "asset_return", "benchmark_return", "trend_return",
        "strategy_exposure", "trend_exposure",
    }
    ordered = []
    for raw in rows:
        if not isinstance(raw, dict) or not required.issubset(raw):
            raise ReplayInputError("each period needs decision/outcome times, sources, information and baseline inputs")
        decision_at = _time(raw["decision_at"])
        outcome_at = _time(raw["outcome_at"])
        if decision_at < frozen_at:
            raise ReplayInputError("decision predates the frozen rule revision")
        if outcome_at <= decision_at:
            raise ReplayInputError("outcome must follow the decision timestamp")
        if not isinstance(raw["source_id"], str) or not raw["source_id"].strip():
            raise ReplayInputError("each period needs an outcome source_id")
        for field in ("benchmark_source_id", "trend_source_id"):
            if not isinstance(raw[field], str) or not raw[field].strip():
                raise ReplayInputError(f"each period needs a {field}")
        validate_information_set(raw["decision_at"], raw["information_inputs"])
        for field in ("asset_return", "benchmark_return", "trend_return"):
            value = _finite_decimal(raw[field], field)
            if value <= -1:
                raise ReplayInputError(f"{field} must be greater than -1")
        ordered.append((decision_at, dict(raw)))
    ordered.sort(key=lambda item: item[0])
    if len({item[0] for item in ordered}) != len(ordered):
        raise ReplayInputError("duplicate decision timestamps")
    chronological = [item[1] for item in ordered]
    if any(_time(current["outcome_at"]) > _time(following["decision_at"])
           for current, following in zip(chronological, chronological[1:])):
        raise ReplayInputError("outcome windows overlap the next decision; use non-overlapping periods")

    strategy, strategy_turnover = _net_series(chronological, "asset_return", "strategy_exposure", cost_per_side)
    trend, trend_turnover = _net_series(chronological, "trend_return", "trend_exposure", cost_per_side)
    asset = [_finite_decimal(row["asset_return"], "asset_return") for row in chronological]
    buy_hold = _fixed_baseline(chronological, "asset_return", cost_per_side)
    benchmark = _fixed_baseline(chronological, "benchmark_return", cost_per_side)

    if any(("alert_triggered" in row) != ("event_occurred" in row) for row in chronological):
        raise ReplayInputError("alert_triggered and event_occurred must be supplied together")
    event_rows = [row for row in chronological if "alert_triggered" in row and "event_occurred" in row]
    if any(type(row["alert_triggered"]) is not bool or type(row["event_occurred"]) is not bool for row in event_rows):
        raise ReplayInputError("alert and event labels must be booleans")
    event_metrics = None
    if event_rows:
        tp = sum(bool(row["alert_triggered"]) and bool(row["event_occurred"]) for row in event_rows)
        fp = sum(bool(row["alert_triggered"]) and not bool(row["event_occurred"]) for row in event_rows)
        fn = sum(not bool(row["alert_triggered"]) and bool(row["event_occurred"]) for row in event_rows)
        event_metrics = {
            "n": len(event_rows), "true_positives": tp, "false_positives": fp,
            "false_negatives": fn,
            "precision": str(Decimal(tp) / (tp + fp)) if tp + fp else None,
            "precision_denominator": tp + fp,
            "recall": str(Decimal(tp) / (tp + fn)) if tp + fn else None,
            "recall_denominator": tp + fn,
            "labels_are_outcomes_not_decision_inputs": True,
        }

    event_hit_rates = {}
    for row, result in zip(chronological, strategy):
        event_type = row.get("event_type")
        if isinstance(event_type, str) and event_type.strip():
            event_hit_rates.setdefault(event_type, []).append(result)
    event_hit_rates = {
        name: {"positive_net_rate": str(Decimal(sum(value > 0 for value in values)) / len(values)), "n": len(values), "denominator": len(values)}
        for name, values in sorted(event_hit_rates.items())
    }

    best_hindsight = [max(value, Decimal(0)) for value in asset]
    regret = [best - result for best, result in zip(best_hindsight, strategy)]
    strategy_metrics = _series_metrics(strategy)
    buy_hold_metrics = _series_metrics(buy_hold)
    result = {
        "status": "DESCRIPTIVE_ONLY",
        "rule": {"id": rule_id, "revision": rule_revision, "frozen_at": frozen_at.isoformat()},
        "sample": dict(sample_metadata),
        "sample_bias_status": sample_metadata["survivorship_status"],
        "costs": {"fee_bps_per_side": str(fee), "slippage_bps_per_side": str(slippage), "taxes": "NOT_MODELED"},
        "information_source_ids": sorted({item["source_id"] for row in chronological for item in row["information_inputs"]}),
        "outcome_source_ids": sorted({row["source_id"] for row in chronological}),
        "benchmark_source_ids": sorted({row["benchmark_source_id"] for row in chronological}),
        "trend_source_ids": sorted({row["trend_source_id"] for row in chronological}),
        "strategy": strategy_metrics,
        "buy_and_hold": buy_hold_metrics,
        "benchmark": _series_metrics(benchmark),
        "trend_following_baseline": _series_metrics(trend),
        "turnover": {
            "strategy_one_way_notional": str(sum(strategy_turnover)),
            "strategy_denominator": len(chronological),
            "trend_one_way_notional": str(sum(trend_turnover)),
            "trend_denominator": len(chronological),
        },
        "event_hit_rates": event_hit_rates,
        "alert_precision_recall": event_metrics,
        "hindsight_regret": {
            "mean_per_period": str(sum(regret) / len(regret)),
            "denominator": len(regret),
            "interpretation": "ex-post cash-or-asset comparator; not a forecast or process-quality score",
        },
        "opportunity_cost_vs_buy_and_hold": str(
            Decimal(buy_hold_metrics["cumulative_return"]) - Decimal(strategy_metrics["cumulative_return"])
        ),
        "statistical_significance_claimed": False,
        "economic_edge_claimed": False,
        "uncertainty": "sample-dependent; no statistical significance or predictive edge is inferred",
    }
    if split_at is None:
        result["out_of_sample"] = {"status": "BLOCKED_MISSING_SPLIT", "n": 0}
    else:
        split = _time(split_at)
        if split < frozen_at:
            raise ReplayInputError("out-of-sample split predates the frozen rule revision")
        oos_rows = [row for row in chronological if _time(row["decision_at"]) > split]
        if not oos_rows:
            result["out_of_sample"] = {"status": "BLOCKED_NO_OOS_OBSERVATIONS", "n": 0, "split_at": split.isoformat()}
        else:
            oos_strategy, _ = _net_series(oos_rows, "asset_return", "strategy_exposure", cost_per_side)
            oos_asset = _fixed_baseline(oos_rows, "asset_return", cost_per_side)
            oos_benchmark = _fixed_baseline(oos_rows, "benchmark_return", cost_per_side)
            oos_trend, _ = _net_series(oos_rows, "trend_return", "trend_exposure", cost_per_side)
            result["out_of_sample"] = {
                "status": "DESCRIPTIVE_ONLY",
                "split_at": split.isoformat(),
                "n": len(oos_rows),
                "strategy": _series_metrics(oos_strategy),
                "buy_and_hold": _series_metrics(oos_asset),
                "benchmark": _series_metrics(oos_benchmark),
                "trend_following_baseline": _series_metrics(oos_trend),
                "statistical_significance_claimed": False,
            }
    return result
