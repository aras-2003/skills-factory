"""Deterministic financial quality diagnostics (not valuation or an investment rating).

All inputs must use consistent units, accounting policies and reporting periods.
Metrics are descriptive; sector benchmarks and quality judgments are intentionally external.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Financials:
    period: str
    revenue: float
    cost_of_revenue: float | None = None
    sga: float | None = None
    research_development: float | None = None
    depreciation_amortization: float | None = None
    operating_income: float | None = None
    interest_expense: float | None = None
    pretax_income: float | None = None
    income_tax_expense: float | None = None
    net_income: float | None = None
    diluted_eps: float | None = None
    diluted_shares: float | None = None
    operating_cash_flow: float | None = None
    capital_expenditure: float | None = None
    invested_capital: float | None = None
    net_debt: float | None = None

    def __post_init__(self) -> None:
        if not self.period.strip() or not isfinite(self.revenue) or self.revenue <= 0:
            raise ValueError("period and positive, finite revenue required")
        for field, value in vars(self).items():
            if isinstance(value, (int, float)) and not isfinite(value):
                raise ValueError(f"{field} must be finite")
        for field in ("cost_of_revenue", "sga", "research_development",
                      "depreciation_amortization", "interest_expense",
                      "capital_expenditure", "diluted_shares", "invested_capital"):
            value = getattr(self, field)
            if value is not None and value < 0:
                raise ValueError(f"{field} must be nonnegative")


def ratio(n: float | None, d: float | None) -> float | None:
    if n is None or d is None or d <= 0:
        return None
    return round(n / d, 6)


def financial_quality(current: Financials, previous: Financials | None = None) -> dict:
    """Return source-data diagnostics and nulls for noncomparable/undefined ratios."""
    if previous is not None and previous.period == current.period:
        raise ValueError("Previous and current periods must differ")
    gp = (current.revenue - current.cost_of_revenue
          if current.cost_of_revenue is not None else None)
    fcf = (current.operating_cash_flow - current.capital_expenditure
           if current.operating_cash_flow is not None and current.capital_expenditure is not None else None)
    ebit = current.operating_income
    interest = current.interest_expense
    eps_growth = (round(current.diluted_eps / previous.diluted_eps - 1, 6)
                  if previous and previous.diluted_eps is not None
                  and previous.diluted_eps > 0 and current.diluted_eps is not None
                  and current.diluted_eps > 0 else None)
    metrics = {
        "gross_margin": ratio(gp, current.revenue),
        "sga_to_gross_profit": ratio(current.sga, gp),
        "rnd_to_gross_profit": ratio(current.research_development, gp),
        "depreciation_to_gross_profit": ratio(current.depreciation_amortization, gp),
        "interest_to_operating_income": ratio(interest, ebit),
        "interest_coverage_ebit": ratio(ebit, interest),
        "effective_tax_rate": ratio(current.income_tax_expense, current.pretax_income),
        "net_margin": ratio(current.net_income, current.revenue),
        "diluted_eps_growth": eps_growth,
        "operating_margin": ratio(ebit, current.revenue),
        "free_cash_flow": fcf,
        "fcf_margin": ratio(fcf, current.revenue),
        "fcf_to_net_income": ratio(fcf, current.net_income),
        "roic_proxy_ebit_over_invested_capital": ratio(ebit, current.invested_capital),
        "net_debt_to_operating_income": ratio(current.net_debt, ebit),
    }
    warnings = []
    if gp is not None and gp <= 0:
        warnings.append("Gross profit is nonpositive; expense-to-gross-profit ratios undefined.")
    if ebit is not None and ebit <= 0:
        warnings.append("EBIT is nonpositive; ratios with EBIT as denominator are undefined; interest coverage may be negative.")
    if current.pretax_income is not None and current.pretax_income <= 0:
        warnings.append("Pretax income is nonpositive; effective tax rate undefined.")
    if previous and (previous.diluted_eps is None or previous.diluted_eps <= 0):
        warnings.append("EPS growth undefined for nonpositive or missing base EPS.")
    if metrics["roic_proxy_ebit_over_invested_capital"] is not None:
        warnings.append("EBIT/invested capital is NOT tax-adjusted ROIC; NOPAT and average invested capital needed.")
    missing = [key for key, value in metrics.items() if value is None]
    return {
        "period": current.period,
        "metrics": metrics,
        "missing_or_undefined": missing,
        "warnings": warnings,
        "quality_score": None,
        "sector_comparison": "NOT_AVAILABLE",
        "valuation_or_trade_signal": False,
    }
