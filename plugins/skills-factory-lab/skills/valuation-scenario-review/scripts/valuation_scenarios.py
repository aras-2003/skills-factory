"""Small deterministic valuation primitives for scenario review.

These functions calculate from already-verified, consistently defined inputs.
They do not select assumptions, infer probabilities, or issue investment actions.
"""
from __future__ import annotations

from math import isfinite


def _positive(name: str, value: float) -> float:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def margin_of_safety(fair_value: float, price: float) -> float:
    """Return (fair value - price) / fair value, as a fraction."""
    fair_value = _positive("fair_value", fair_value)
    _positive("price", price)
    return (fair_value - price) / fair_value


def upside(fair_value: float, price: float) -> float:
    """Return fair value / price - 1, as a fraction."""
    fair_value = _positive("fair_value", fair_value)
    _positive("price", price)
    return fair_value / price - 1


def dcf_per_share(
    cash_flows: list[float], discount_rate: float, terminal_growth: float,
    net_debt: float, diluted_shares: float,
) -> float:
    """Equity value/share from annual end-of-period unlevered enterprise FCF.

    `discount_rate` is WACC. `net_debt` must include supported debt-like claims;
    add non-operating assets to the present value before dividing by shares.
    Do not pass FCFE here, as that would double-count the debt bridge.
    """
    if not cash_flows or any(not isfinite(x) for x in cash_flows):
        raise ValueError("at least one finite annual cash flow is required")
    _positive("discount_rate", discount_rate)
    if not isfinite(terminal_growth) or terminal_growth <= -1 or terminal_growth >= discount_rate:
        raise ValueError("terminal_growth must be finite, above -100% and below discount_rate")
    if not isfinite(net_debt):
        raise ValueError("net_debt must be finite")
    shares = _positive("diluted_shares", diluted_shares)
    pv = sum(cf / (1 + discount_rate) ** year for year, cf in enumerate(cash_flows, 1))
    terminal = cash_flows[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    pv += terminal / (1 + discount_rate) ** len(cash_flows)
    return (pv - net_debt) / shares


def earnings_multiple_per_share(normalized_eps: float, exit_multiple: float) -> float:
    """Simple normalized EPS × exit multiple; no present-value adjustment."""
    if not isfinite(normalized_eps) or normalized_eps <= 0:
        raise ValueError("normalized_eps must be finite and positive")
    _positive("exit_multiple", exit_multiple)
    return normalized_eps * exit_multiple


def affo_multiple_per_share(affo_per_share: float, exit_multiple: float) -> float:
    """REIT value proxy from verified AFFO/share and a supported P/AFFO."""
    if not isfinite(affo_per_share) or affo_per_share <= 0:
        raise ValueError("affo_per_share must be finite and positive")
    _positive("exit_multiple", exit_multiple)
    return affo_per_share * exit_multiple


def nav_per_share(asset_value: float, liabilities: float, diluted_shares: float) -> float:
    """Net asset value per share from independently supported asset/liability values."""
    if not isfinite(asset_value) or asset_value < 0:
        raise ValueError("asset_value must be finite and nonnegative")
    if not isfinite(liabilities) or liabilities < 0:
        raise ValueError("liabilities must be finite and nonnegative")
    shares = _positive("diluted_shares", diluted_shares)
    value = (asset_value - liabilities) / shares
    if value <= 0:
        raise ValueError("net asset value per share must be positive")
    return value


def residual_income_per_share(
    book_value_per_share: float, return_on_equity: list[float],
    payout_ratios: list[float], cost_of_equity: float, terminal_growth: float,
) -> float:
    """Residual-income value for a financial, with annual book-value roll-forward."""
    book = _positive("book_value_per_share", book_value_per_share)
    if not return_on_equity or len(return_on_equity) != len(payout_ratios):
        raise ValueError("matching nonempty ROE and payout-ratio forecasts are required")
    _positive("cost_of_equity", cost_of_equity)
    if not isfinite(terminal_growth) or terminal_growth <= -1 or terminal_growth >= cost_of_equity:
        raise ValueError("terminal_growth must be finite, above -100% and below cost_of_equity")
    pv_ri = 0.0
    last_ri = 0.0
    for year, (roe, payout) in enumerate(zip(return_on_equity, payout_ratios), 1):
        if not isfinite(roe) or roe <= -1:
            raise ValueError("each ROE must be finite and above -100%")
        if not isfinite(payout) or not 0 <= payout <= 1:
            raise ValueError("each payout ratio must be between 0 and 1")
        last_ri = (roe - cost_of_equity) * book
        pv_ri += last_ri / (1 + cost_of_equity) ** year
        book *= 1 + roe * (1 - payout)
    terminal = last_ri * (1 + terminal_growth) / (cost_of_equity - terminal_growth)
    pv_ri += terminal / (1 + cost_of_equity) ** len(return_on_equity)
    return book_value_per_share + pv_ri


def dcf_sensitivity(
    cash_flows: list[float], discount_rate: float, terminal_growth: float,
    net_debt: float, diluted_shares: float, rate_shift: float = 0.02,
) -> dict[str, float]:
    """Recompute DCF for ±20% FCF and ±rate_shift discount-rate cases."""
    if not isfinite(rate_shift) or rate_shift <= 0:
        raise ValueError("rate_shift must be finite and positive")
    scenarios = {
        "base": (cash_flows, discount_rate),
        "fcf_down_20pct": ([x * 0.8 for x in cash_flows], discount_rate),
        "fcf_up_20pct": ([x * 1.2 for x in cash_flows], discount_rate),
        "discount_rate_up": (cash_flows, discount_rate + rate_shift),
        "discount_rate_down": (cash_flows, discount_rate - rate_shift),
    }
    return {
        name: dcf_per_share(flows, rate, terminal_growth, net_debt, diluted_shares)
        for name, (flows, rate) in scenarios.items()
    }


def earnings_multiple_sensitivity(normalized_eps: float, exit_multiple: float) -> dict[str, float]:
    """Show independent ±20% EPS and exit-multiple cases for an EPS-multiple model."""
    return {
        "base": earnings_multiple_per_share(normalized_eps, exit_multiple),
        "eps_down_20pct": earnings_multiple_per_share(normalized_eps * 0.8, exit_multiple),
        "eps_up_20pct": earnings_multiple_per_share(normalized_eps * 1.2, exit_multiple),
        "multiple_down_20pct": earnings_multiple_per_share(normalized_eps, exit_multiple * 0.8),
        "multiple_up_20pct": earnings_multiple_per_share(normalized_eps, exit_multiple * 1.2),
    }
