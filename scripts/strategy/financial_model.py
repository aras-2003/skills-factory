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
