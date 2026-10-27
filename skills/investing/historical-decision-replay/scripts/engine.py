"""Small deterministic replay primitives; deliberately no data fetching or persistence."""

from datetime import datetime
from decimal import Decimal, InvalidOperation


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
