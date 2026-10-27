"""Small deterministic business-case calculations; decimal inputs are required."""
from decimal import Decimal, localcontext


def _d(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def npv(rate, cash_flows):
    """NPV for equally spaced flows, with the first element at period zero."""
    rate = _d(rate)
    flows = [_d(x) for x in cash_flows]
    if not flows:
        raise ValueError("cash_flows must not be empty")
    if rate <= -1:
        raise ValueError("rate must be greater than -1")
    with localcontext() as ctx:
        ctx.prec = 28
        return sum((cf / ((Decimal(1) + rate) ** t) for t, cf in enumerate(flows)), Decimal(0))


def payback(cash_flows, discounted_rate=None):
    """Return fractional periods from time zero, or None if never recovered."""
    flows = [_d(x) for x in cash_flows]
    if not flows:
        raise ValueError("cash_flows must not be empty")
    if discounted_rate is not None:
        rate = _d(discounted_rate)
        if rate <= -1:
            raise ValueError("rate must be greater than -1")
        flows = [cf / ((Decimal(1) + rate) ** t) for t, cf in enumerate(flows)]
    cumulative = flows[0]
    if cumulative >= 0:
        return Decimal(0)
    for period, flow in enumerate(flows[1:], start=1):
        previous = cumulative
        cumulative += flow
        if cumulative >= 0 and flow > 0:
            return Decimal(period - 1) + (-previous / flow)
    return None


def irr(cash_flows, *, tolerance=Decimal("1e-12"), max_iterations=256):
    """Find one IRR in [-0.999999, 10] by bisection; None if unbracketed.

    Multiple sign changes can imply multiple IRRs. This routine returns only a
    root bracketed over the stated interval; callers must disclose that limit.
    """
    flows = [_d(x) for x in cash_flows]
    tol = _d(tolerance)
    if len(flows) < 2 or not (any(x < 0 for x in flows) and any(x > 0 for x in flows)):
        return None
    lo, hi = Decimal("-0.999999"), Decimal(10)
    flo, fhi = npv(lo, flows), npv(hi, flows)
    if flo == 0:
        return lo
    if fhi == 0:
        return hi
    if (flo > 0) == (fhi > 0):
        return None
    for _ in range(max_iterations):
        mid = (lo + hi) / 2
        fm = npv(mid, flows)
        if abs(fm) <= tol or hi - lo <= tol:
            return mid
        if (flo > 0) == (fm > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def profit_bridge(baseline, target):
    """Exact price-volume-mix/unit-cost bridge for keyed product segments.

    Each mapping is segment -> (volume, unit_price, unit_variable_cost). The
    decomposition order is total volume at baseline mix, mix at target total
    volume, price, then unit variable cost. A residual is returned and should
    be zero within Decimal precision; no missing segment is silently imputed.
    """
    if not baseline or set(baseline) != set(target):
        raise ValueError("baseline and target must contain the same non-empty segments")
    def rows(source):
        normalized = {}
        for key, values in source.items():
            if len(values) != 3:
                raise ValueError("each segment requires volume, price, and unit variable cost")
            volume, price, cost = map(_d, values)
            if volume < 0 or price < 0 or cost < 0:
                raise ValueError("volume, price, and unit variable cost must be non-negative")
            normalized[key] = (volume, price, cost)
        return normalized
    base, actual = rows(baseline), rows(target)
    q0, q1 = sum(v[0] for v in base.values()), sum(v[0] for v in actual.values())
    if q0 <= 0 or q1 <= 0:
        raise ValueError("baseline and target total volume must be positive")
    baseline_profit = sum(q * (p - c) for q, p, c in base.values())
    target_profit = sum(q * (p - c) for q, p, c in actual.values())
    volume_effect = (q1 - q0) * sum(base[k][0] / q0 * (base[k][1] - base[k][2]) for k in base)
    mix_effect = sum(
        (actual[k][0] / q1 - base[k][0] / q0) * q1 * (base[k][1] - base[k][2])
        for k in base
    )
    price_effect = sum(actual[k][0] * (actual[k][1] - base[k][1]) for k in base)
    unit_cost_effect = sum(-actual[k][0] * (actual[k][2] - base[k][2]) for k in base)
    change = target_profit - baseline_profit
    residual = change - volume_effect - mix_effect - price_effect - unit_cost_effect
    return {
        "baseline_profit": baseline_profit,
        "target_profit": target_profit,
        "volume_effect": volume_effect,
        "mix_effect": mix_effect,
        "price_effect": price_effect,
        "unit_cost_effect": unit_cost_effect,
        "residual": residual,
    }
