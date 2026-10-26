"""Deterministic, explainable five-phase business lifecycle classifier.

Research support only. Shares are heuristic affinity weights, NOT calibrated probabilities.
No market price is used and no investment recommendation is produced.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional

PHASES = ("startup", "hyper_growth", "operating_leverage", "capital_return", "decline")


@dataclass(frozen=True)
class FinancialPeriod:
    """Comparable annual or trailing-twelve-month USD/local-currency observations."""
    period: str
    revenue: float
    operating_profit: float
    free_cash_flow: Optional[float] = None
    shareholder_returns: Optional[float] = None

    def __post_init__(self) -> None:
        values = (self.revenue, self.operating_profit, self.free_cash_flow, self.shareholder_returns)
        if any(v is not None and not isfinite(v) for v in values):
            raise ValueError("Financial values must be finite")
        if self.revenue <= 0:
            raise ValueError("Revenue must be positive")
        if self.shareholder_returns is not None and self.shareholder_returns < 0:
            raise ValueError("Shareholder returns must be nonnegative")


def classify_lifecycle(periods: list[FinancialPeriod]) -> dict:
    """Classify chronological, equally spaced periods; requires >=3 observations.

    Annualize inputs first; never mix quarterly observations with TTM/annual values.
    Latest change is a year-on-year change only when input frequency is annual.
    """
    if len(periods) < 3:
        return {"status": "INSUFFICIENT_DATA", "required_periods": 3,
                "observed_periods": len(periods), "probabilities_calibrated": False}
    if len({p.period for p in periods}) != len(periods):
        raise ValueError("Period labels must be unique")
    a, b, c = periods[-3:]
    growth = c.revenue / b.revenue - 1
    prior_growth = b.revenue / a.revenue - 1
    margin = c.operating_profit / c.revenue
    prev_margin = b.operating_profit / b.revenue
    margin_change_pp = 100 * (margin - prev_margin)
    profit_growth = ((c.operating_profit / b.operating_profit) - 1
                     if b.operating_profit > 0 and c.operating_profit > 0 else None)
    fcf_margin = c.free_cash_flow / c.revenue if c.free_cash_flow is not None else None
    returns_ratio = (c.shareholder_returns / c.free_cash_flow
                     if c.shareholder_returns is not None and c.free_cash_flow is not None
                     and c.free_cash_flow > 0 else None)

    scores = dict.fromkeys(PHASES, 1.0)
    if c.operating_profit <= 0:
        scores["startup"] += 4 if growth < 0.15 else 2
        scores["hyper_growth"] += 6 if growth >= 0.20 else 2
    else:
        scores["operating_leverage"] += 2
        scores["capital_return"] += 1
        if margin_change_pp >= 1:
            scores["operating_leverage"] += 5
        elif margin_change_pp > 0:
            scores["operating_leverage"] += 3
        if profit_growth is not None and profit_growth > growth and growth > 0:
            scores["operating_leverage"] += 3
        if growth >= 0.25:
            scores["hyper_growth"] += 4
        if 0 <= growth < 0.10 and margin_change_pp >= -1:
            scores["capital_return"] += 3
        if fcf_margin is not None and fcf_margin > 0.08:
            scores["capital_return"] += 2
        if returns_ratio is not None and returns_ratio > 0.2:
            scores["capital_return"] += 4
    if growth < -0.05 and prior_growth < 0:
        scores["decline"] += 8
    if margin_change_pp < -2:
        scores["decline"] += 4
    if fcf_margin is not None and fcf_margin < 0:
        scores["capital_return"] = 1.0

    total = sum(scores.values())
    affinities = {phase: round(100 * score / total, 1) for phase, score in scores.items()}
    phase = max(PHASES, key=lambda p: scores[p])
    missing = [name for name, value in (
        ("free_cash_flow", c.free_cash_flow), ("shareholder_returns", c.shareholder_returns)
    ) if value is None]
    return {
        "status": "CLASSIFIED",
        "phase": phase,
        "phase_affinity_pct": affinities,
        "probabilities_calibrated": False,
        "confidence": "LOW" if missing else "MEDIUM",
        "data_gaps": missing,
        "metrics": {
            "revenue_growth": round(growth, 5),
            "prior_revenue_growth": round(prior_growth, 5),
            "operating_margin": round(margin, 5),
            "operating_margin_change_pp": round(margin_change_pp, 3),
            "operating_profit_growth": round(profit_growth, 5) if profit_growth is not None else None,
            "fcf_margin": round(fcf_margin, 5) if fcf_margin is not None else None,
            "shareholder_returns_to_fcf": round(returns_ratio, 5) if returns_ratio is not None else None,
        },
        "limitations": [
            "Affinities are uncalibrated heuristic scores, not event probabilities.",
            "Business segments can be in different phases.",
            "Business phase is not a stock valuation, forecast or BUY/SELL signal.",
            "Cross-sector thresholds require separate validation before use for decisions.",
        ],
    }
