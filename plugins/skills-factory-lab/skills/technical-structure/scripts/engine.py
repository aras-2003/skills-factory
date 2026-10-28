"""Deterministic swing-structure primitives for supplied adjusted OHLCV only."""

from datetime import datetime
from decimal import Decimal, InvalidOperation


class StructureInputError(ValueError):
    pass


def _timestamp(value):
    if not isinstance(value, str):
        raise StructureInputError("timestamp must be an ISO-8601 string")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StructureInputError("invalid ISO-8601 timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise StructureInputError("timestamp must include a timezone")
    return result


def analyze_structure(bars, *, as_of, source_id, adjusted, adjustment_id=None, left=2, right=2, max_gap_days=5):
    if (not isinstance(source_id, str) or not source_id.strip() or adjusted is not True
            or not isinstance(adjustment_id, str) or not adjustment_id.strip()):
        return {"status": "UNKNOWN", "reason": "MISSING_SOURCE_OR_ADJUSTMENT"}
    if not isinstance(left, int) or not isinstance(right, int) or min(left, right) < 1:
        raise StructureInputError("left and right pivot windows must be positive integers")
    cutoff = _timestamp(as_of)
    if not isinstance(bars, list) or len(bars) < left + right + 3:
        return {"status": "UNKNOWN", "reason": "INSUFFICIENT_BARS"}

    rows = []
    try:
        for bar in bars:
            stamp = _timestamp(bar["timestamp"])
            published = _timestamp(bar["published_at"])
            if stamp > cutoff or published > cutoff:
                return {"status": "UNKNOWN", "reason": "FUTURE_DATED_BAR"}
            values = {key: Decimal(str(bar[key])) for key in ("open", "high", "low", "close", "volume")}
            if any(not value.is_finite() for value in values.values()) or any(values[key] <= 0 for key in ("open", "high", "low", "close")) or values["volume"] < 0:
                raise StructureInputError("OHLC prices must be positive and volume non-negative")
            if values["high"] < max(values["open"], values["low"], values["close"]) or values["low"] > min(values["open"], values["high"], values["close"]):
                raise StructureInputError("invalid high/low/close relationship")
            if not bar.get("source_id"):
                raise StructureInputError("each bar needs a source_id")
            rows.append({**values, "timestamp": stamp, "source_id": bar["source_id"]})
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise StructureInputError("bar is missing a valid timestamp, source or price") from exc

    rows.sort(key=lambda row: row["timestamp"])
    if len({row["timestamp"] for row in rows}) != len(rows):
        raise StructureInputError("duplicate bar timestamps")
    if any((b["timestamp"] - a["timestamp"]).days > max_gap_days for a, b in zip(rows, rows[1:])):
        return {"status": "UNKNOWN", "reason": "DATA_GAP_EXCEEDS_LIMIT"}

    pivots = []
    for i in range(left, len(rows) - right):
        window = rows[i - left:i + right + 1]
        bar = rows[i]
        confirmed_at = rows[i + right]["timestamp"]
        if bar["high"] == max(row["high"] for row in window) and sum(row["high"] == bar["high"] for row in window) == 1:
            pivots.append({"kind": "HIGH", "price": bar["high"], "timestamp": bar["timestamp"], "confirmed_at": confirmed_at, "source_id": bar["source_id"]})
        if bar["low"] == min(row["low"] for row in window) and sum(row["low"] == bar["low"] for row in window) == 1:
            pivots.append({"kind": "LOW", "price": bar["low"], "timestamp": bar["timestamp"], "confirmed_at": confirmed_at, "source_id": bar["source_id"]})
    pivots.sort(key=lambda item: (item["confirmed_at"], item["timestamp"], item["kind"]))
    highs = [p for p in pivots if p["kind"] == "HIGH" and p["confirmed_at"] <= cutoff]
    lows = [p for p in pivots if p["kind"] == "LOW" and p["confirmed_at"] <= cutoff]
    if len(highs) < 2 or len(lows) < 2:
        return {"status": "UNKNOWN", "reason": "INSUFFICIENT_CONFIRMED_PIVOTS", "confirmed_pivots": len(pivots), "source_id": source_id}

    higher_high = highs[-1]["price"] > highs[-2]["price"]
    higher_low = lows[-1]["price"] > lows[-2]["price"]
    lower_high = highs[-1]["price"] < highs[-2]["price"]
    lower_low = lows[-1]["price"] < lows[-2]["price"]
    if higher_high and higher_low:
        trend, score = "UPTREND", 100
    elif lower_high and lower_low:
        trend, score = "DOWNTREND", 0
    else:
        trend, score = "RANGE_OR_MIXED", 50 + 25 * int(higher_high) + 25 * int(higher_low)

    close = rows[-1]["close"]
    ops, opd = highs[-1], lows[-1]
    distance = lambda level: str(((level - close) / close * Decimal(100)).quantize(Decimal("0.01")))
    return {
        "status": "OBSERVED",
        "as_of": as_of,
        "source_id": source_id,
        "adjustment_id": adjustment_id,
        "trend": trend,
        "score": score,
        "score_is_probability": False,
        "score_components": {"higher_high": higher_high, "higher_low": higher_low},
        "current_close": str(close),
        "ops": {"price": str(ops["price"]), "confirmed_at": ops["confirmed_at"].isoformat(), "source_id": ops["source_id"], "distance_pct": distance(ops["price"])},
        "opd": {"price": str(opd["price"]), "confirmed_at": opd["confirmed_at"].isoformat(), "source_id": opd["source_id"], "distance_pct": distance(opd["price"])},
        "breakout_condition": f"adjusted close above {ops['price']}",
        "invalidation_condition": f"adjusted close below {opd['price']}",
        "confirmed_pivots": len(pivots),
        "window": {"left_bars": left, "right_bars": right},
    }
