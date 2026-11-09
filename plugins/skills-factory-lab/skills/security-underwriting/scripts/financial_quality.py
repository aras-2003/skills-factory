"""Evidence-gated, deterministic multi-period financial-quality calculations.

This module consumes source-reviewed facts. It does not fetch filings or certify
that a URL supports the supplied value; that review stays with the caller.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Iterable
from urllib.parse import urlparse


class FactStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTED = "CONFLICTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class PeriodType(str, Enum):
    FY = "FY"
    YTD = "YTD"


@dataclass(frozen=True)
class FinancialFact:
    metric: str
    value: Decimal | None
    period_type: PeriodType
    period_label: str
    period_start: str
    period_end: str
    fiscal_year: int
    currency: str
    unit: str
    basis: str
    source_url: str
    published_at: str
    status: FactStatus = FactStatus.VERIFIED
    fiscal_quarter: int | None = None
    capex_sign: str | None = None
    definition: str = ""


_MONEY_UNITS = {
    "currency": Decimal("1"),
    "currency_thousands": Decimal("1000"),
    "currency_millions": Decimal("1000000"),
    "currency_billions": Decimal("1000000000"),
}
_SHARE_UNITS = {
    "shares": Decimal("1"),
    "shares_thousands": Decimal("1000"),
    "shares_millions": Decimal("1000000"),
}
_MONEY_METRICS = {
    "gross_profit", "net_debt", "total_debt", "debt_due_12m", "cash",
    "stock_compensation", "working_capital_change", "one_off_adjustments",
    "recurring_adjustments", "adjusted_ebitda",
}
_SHARE_METRICS = {"shares_diluted"}
_FRACTION_OPTIONAL_METRICS = {"gross_margin", "revenue_growth"}
_CORE_METRICS = ("revenue", "operating_income", "net_income", "cfo", "capex")
_OPTIONAL_METRICS = (
    "gross_profit", "gross_margin", "revenue_growth", "net_debt", "total_debt",
    "debt_due_12m", "cash", "shares_diluted", "stock_compensation",
    "working_capital_change", "cash_conversion_cycle", "one_off_adjustments",
    "recurring_adjustments", "adjusted_ebitda",
)
_INDUSTRY_ALTERNATIVES = {
    "bank", "banks", "insurer", "insurance", "etf", "fund", "reit",
    "real estate investment trust",
}


def _valid_date(value: str) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except (TypeError, ValueError):
        return False


def _valid_url(value: str) -> bool:
    parsed = urlparse(value) if isinstance(value, str) else None
    return bool(parsed and parsed.scheme == "https" and parsed.netloc)


def _normalized_value(fact: FinancialFact) -> tuple[Decimal | None, str]:
    if fact.value is None or not isinstance(fact.value, Decimal) or not fact.value.is_finite():
        return None, "MISSING_OR_NONFINITE_VALUE"
    if fact.unit in _MONEY_UNITS:
        if not isinstance(fact.currency, str) or not fact.currency.strip():
            return None, "MISSING_CURRENCY"
        return fact.value * _MONEY_UNITS[fact.unit], fact.currency.upper()
    if fact.unit in _SHARE_UNITS:
        return fact.value * _SHARE_UNITS[fact.unit], "shares"
    if fact.unit == "percent" and fact.metric in _FRACTION_OPTIONAL_METRICS:
        return fact.value / Decimal("100"), "fraction"
    if fact.unit in {"fraction", "percent", "multiple", "per_share", "days"}:
        return fact.value, fact.unit
    return None, "UNSUPPORTED_UNIT"


def _fact_problems(fact: FinancialFact, as_of: str) -> list[str]:
    problems: list[str] = []
    metric_name = fact.metric if isinstance(fact.metric, str) else ""
    unit_name = fact.unit if isinstance(fact.unit, str) else ""
    if any(not isinstance(value, str) or not value.strip() for value in (fact.metric, fact.period_label, fact.basis, fact.unit)):
        problems.append("INCOMPLETE_FACT_IDENTITY")
    if not _valid_date(fact.period_start) or not _valid_date(fact.period_end) or fact.period_start > fact.period_end:
        problems.append("INVALID_PERIOD")
    elif _valid_date(as_of) and fact.period_end > as_of:
        problems.append("PERIOD_AFTER_AS_OF")
    if not isinstance(fact.fiscal_year, int) or fact.fiscal_year < 1900:
        problems.append("INVALID_FISCAL_YEAR")
    if fact.period_type == PeriodType.YTD and fact.fiscal_quarter not in {1, 2, 3}:
        problems.append("INVALID_YTD_QUARTER")
    if fact.period_type == PeriodType.FY and fact.fiscal_quarter is not None:
        problems.append("ANNUAL_FACT_HAS_QUARTER")
    if not _valid_date(fact.published_at) or not _valid_date(as_of):
        problems.append("INVALID_PUBLICATION_OR_AS_OF_DATE")
    elif fact.published_at > as_of:
        problems.append("LOOKAHEAD")
    if not _valid_url(fact.source_url):
        problems.append("INVALID_SOURCE_URL")
    if not isinstance(fact.definition, str) or not fact.definition.strip():
        problems.append("MISSING_METRIC_DEFINITION")
    if metric_name in (*_CORE_METRICS, "nopat", "average_invested_capital", *_MONEY_METRICS) and unit_name not in _MONEY_UNITS:
        problems.append("INCOMPATIBLE_MONEY_UNIT")
    if metric_name in _SHARE_METRICS and unit_name not in _SHARE_UNITS:
        problems.append("INCOMPATIBLE_SHARE_UNIT")
    if metric_name in _FRACTION_OPTIONAL_METRICS and unit_name not in {"fraction", "percent"}:
        problems.append("INCOMPATIBLE_FRACTION_UNIT")
    if metric_name == "cash_conversion_cycle" and unit_name != "days":
        problems.append("INCOMPATIBLE_DAYS_UNIT")
    try:
        FactStatus(fact.status)
        PeriodType(fact.period_type)
    except (ValueError, TypeError):
        problems.append("INVALID_STATUS_OR_PERIOD_TYPE")
    if metric_name == "capex" and (
        not isinstance(fact.capex_sign, str)
        or fact.capex_sign not in {"spend_positive", "cashflow_signed"}
    ):
        problems.append("CAPEX_SIGN_CONVENTION_REQUIRED")
    return problems


def _select_facts(
    facts: Iterable[FinancialFact], as_of: str
) -> tuple[dict[tuple[str, str], FinancialFact], list[str], dict[tuple[str, str], list[dict]]]:
    eligible: dict[tuple[str, str], list[FinancialFact]] = {}
    problems: list[str] = []
    for fact in facts:
        fact_problems = _fact_problems(fact, as_of)
        if fact_problems:
            problems.extend(f"{fact.period_label}/{fact.metric}:{problem}" for problem in fact_problems)
            continue
        status = FactStatus(fact.status)
        if status == FactStatus.CONFLICTED:
            problems.append(f"{fact.period_label}/{fact.metric}:CONFLICTED_SOURCE")
            continue
        if status != FactStatus.VERIFIED:
            problems.append(f"{fact.period_label}/{fact.metric}:UNVERIFIED_SOURCE")
            continue
        eligible.setdefault((fact.period_label, fact.metric), []).append(fact)

    selected: dict[tuple[str, str], FinancialFact] = {}
    revisions: dict[tuple[str, str], list[dict]] = {}
    for key, candidates in eligible.items():
        latest_date = max(f.published_at for f in candidates)
        latest = [f for f in candidates if f.published_at == latest_date]
        normalized = {_normalized_value(f)[0] for f in latest}
        normalized_kinds = {
            "money" if f.unit in _MONEY_UNITS else
            "shares" if f.unit in _SHARE_UNITS else f.unit
            for f in latest
        }
        if key[1] in _FRACTION_OPTIONAL_METRICS and all(f.unit in {"fraction", "percent"} for f in latest):
            normalized_kinds = {"fraction"}
        metadata = {
            (f.currency.upper() if isinstance(f.currency, str) else "", f.basis, f.definition,
             PeriodType(f.period_type), f.fiscal_year, f.fiscal_quarter, f.period_start, f.period_end)
            for f in latest
        }
        if len(normalized) != 1 or len(metadata) != 1 or len(normalized_kinds) != 1:
            problems.append(f"{key[0]}/{key[1]}:CONFLICTED_DUPLICATE_FACTS")
            continue
        selected[key] = latest[0]
        older = sorted((f for f in candidates if f.published_at < latest_date), key=lambda f: f.published_at)
        if older:
            revisions[key] = [{"published_at": f.published_at, "source_url": f.source_url,
                               "value": str(_normalized_value(f)[0]), "basis": f.basis,
                               "definition": f.definition} for f in older]
    return selected, problems, revisions


def _get_period_value(
    facts: dict[tuple[str, str], FinancialFact], period: str, metric: str
) -> tuple[Decimal | None, str | None, str | None]:
    fact = facts.get((period, metric))
    if fact is None:
        return None, None, "MISSING"
    value, unit_or_error = _normalized_value(fact)
    if value is None:
        return None, None, unit_or_error
    return value, unit_or_error, None


def audit_financial_quality(
    facts: Iterable[FinancialFact],
    as_of: str,
    *,
    industry_path: str = "general",
    cyclical: bool = False,
    required_fy_count: int = 3,
) -> dict:
    """Audit source-reviewed FY/YTD facts and derive comparable quality metrics.

    Values are normalized to base currency units for supported same-currency
    arithmetic. Foreign-exchange conversion is intentionally not performed.
    """
    if (not _valid_date(as_of) or not isinstance(required_fy_count, int)
            or isinstance(required_fy_count, bool) or required_fy_count < 3 or required_fy_count > 5
            or not isinstance(industry_path, str)):
        return {"status": "UNVERIFIED", "reason": "INVALID_AS_OF_OR_PERIOD_REQUIREMENT", "periods": []}
    fact_list = list(facts)
    selected, problems, revisions = _select_facts(fact_list, as_of)
    if not selected:
        return {"status": "UNVERIFIED", "reason": "NO_VERIFIED_FACTS", "problems": sorted(set(problems)), "periods": []}

    fy_labels = sorted(
        {f.period_label for f in selected.values() if PeriodType(f.period_type) == PeriodType.FY},
        key=lambda label: next(f.fiscal_year for f in selected.values() if f.period_label == label),
    )
    fiscal_years = [next(f.fiscal_year for f in selected.values() if f.period_label == label) for label in fy_labels]
    if len(fy_labels) < required_fy_count:
        problems.append("INSUFFICIENT_FY_HISTORY")
    if fiscal_years and any(b - a != 1 for a, b in zip(fiscal_years, fiscal_years[1:])):
        problems.append("NONCONTIGUOUS_FY_HISTORY")

    ytd_facts = [f for f in selected.values() if PeriodType(f.period_type) == PeriodType.YTD]
    ytd_by_quarter: dict[int, set[int]] = {}
    ytd_labels_by_period: dict[tuple[int, int], set[str]] = {}
    for fact in ytd_facts:
        ytd_by_quarter.setdefault(fact.fiscal_quarter or 0, set()).add(fact.fiscal_year)
        ytd_labels_by_period.setdefault((fact.fiscal_year, fact.fiscal_quarter or 0), set()).add(fact.period_label)
    latest_ytd: tuple[int, int] | None = None
    if ytd_by_quarter:
        candidates = [(year, quarter) for quarter, years in ytd_by_quarter.items() for year in years]
        latest_ytd = max(candidates)
        year, quarter = latest_ytd
        if year - 1 not in ytd_by_quarter.get(quarter, set()):
            problems.append("COMPARABLE_YTD_MISSING")
        elif ytd_by_quarter[quarter] != {year, year - 1}:
            problems.append("NONCOMPARABLE_YTD_SET")
        else:
            current_labels = ytd_labels_by_period.get((year, quarter), set())
            prior_labels = ytd_labels_by_period.get((year - 1, quarter), set())
            current_lengths = {(date.fromisoformat(f.period_end) - date.fromisoformat(f.period_start)).days
                               for f in ytd_facts if f.period_label in current_labels}
            prior_lengths = {(date.fromisoformat(f.period_end) - date.fromisoformat(f.period_start)).days
                             for f in ytd_facts if f.period_label in prior_labels}
            if len(current_labels) != 1 or len(prior_labels) != 1 or len(current_lengths) != 1 or len(prior_lengths) != 1:
                problems.append("AMBIGUOUS_YTD_PERIOD_IDENTITY")
            elif abs(next(iter(current_lengths)) - next(iter(prior_lengths))) > 2:
                problems.append("YTD_PERIOD_LENGTH_MISMATCH")
    else:
        problems.append("YTD_NOT_SUPPLIED")

    path = industry_path.strip().lower()
    alternative = path in _INDUSTRY_ALTERNATIVES
    labels_to_summarize = fy_labels[-required_fy_count:]
    if latest_ytd:
        ytd_year, ytd_quarter = latest_ytd
        labels_to_summarize.extend(sorted(
            {f.period_label for f in ytd_facts if f.fiscal_quarter == ytd_quarter and f.fiscal_year in {ytd_year - 1, ytd_year}},
            key=lambda label: next(f.fiscal_year for f in ytd_facts if f.period_label == label),
        ))

    cross_period_comparability_problems: set[str] = set()
    for metric in _CORE_METRICS:
        definitions = {selected[(label, metric)].definition for label in labels_to_summarize if (label, metric) in selected}
        if len(definitions) > 1:
            cross_period_comparability_problems.add(f"METRIC_DEFINITION_CHANGED:{metric}")
    core_bases_across_periods = {selected[(label, metric)].basis for label in labels_to_summarize
                                 for metric in _CORE_METRICS if (label, metric) in selected}
    if len(core_bases_across_periods) > 1:
        cross_period_comparability_problems.add("CORE_BASIS_CHANGED_ACROSS_PERIODS")
    problems.extend(sorted(cross_period_comparability_problems))

    periods: list[dict] = []
    currencies_by_period: dict[str, set[str]] = {}
    for label in labels_to_summarize:
        record: dict[str, str | None | list[str]] = {"period": label, "status": "VERIFIED", "flags": []}
        raw: dict[str, tuple[Decimal | None, str | None, str | None]] = {}
        for metric in (*_CORE_METRICS, "nopat", "average_invested_capital", *_OPTIONAL_METRICS):
            raw[metric] = _get_period_value(selected, label, metric)
        if alternative:
            record["standard_industrial_fcf"] = "NOT_APPLICABLE"
            record["industry_path"] = "ALTERNATIVE_REQUIRED"
            record["status"] = "NOT_APPLICABLE"
            record["flags"] = ["USE_INDUSTRY_SPECIFIC_CAPITAL_OR_PROVIDER_METRICS"]
            periods.append(record)
            continue

        missing_core = [m for m in _CORE_METRICS if raw[m][0] is None]
        if missing_core:
            record["status"] = "UNVERIFIED"
            record["flags"] = [f"MISSING_CRITICAL:{m}" for m in missing_core]
            problems.extend(f"{label}/{m}:MISSING_CRITICAL" for m in missing_core)
            periods.append(record)
            continue
        currency_set = {raw[m][1] for m in _CORE_METRICS if m in {"revenue", "operating_income", "net_income", "cfo", "capex"}}
        currencies_by_period[label] = {str(x) for x in currency_set if x}
        if len(currency_set) != 1:
            record["status"] = "UNVERIFIED"
            record["flags"] = ["MIXED_CURRENCY_REQUIRES_CONVERSION"]
            problems.append(f"{label}:MIXED_CURRENCY_REQUIRES_CONVERSION")
            periods.append(record)
            continue
        core_bases = {selected[(label, metric)].basis for metric in _CORE_METRICS}
        if len(core_bases) != 1:
            record["status"] = "UNVERIFIED"
            record["flags"] = ["MIXED_GAAP_OR_ADJUSTED_BASIS"]
            problems.append(f"{label}:MIXED_GAAP_OR_ADJUSTED_BASIS")
            periods.append(record)
            continue

        revenue, _, _ = raw["revenue"]
        op_income, _, _ = raw["operating_income"]
        net_income, _, _ = raw["net_income"]
        cfo, _, _ = raw["cfo"]
        capex_fact = selected[(label, "capex")]
        capex, _, _ = raw["capex"]
        capex_sign_mismatch = (
            (capex_fact.capex_sign == "cashflow_signed" and capex > 0)
            or (capex_fact.capex_sign == "spend_positive" and capex < 0)
        )
        capex_spend = -capex if capex_fact.capex_sign == "cashflow_signed" else capex
        if capex_sign_mismatch:
            record["status"] = "UNVERIFIED"
            record["flags"] = ["CAPEX_CASHFLOW_SIGN_MISMATCH"]
            problems.append(f"{label}:CAPEX_CASHFLOW_SIGN_MISMATCH")
            periods.append(record)
            continue

        fcf = cfo - capex_spend
        record.update({
            "currency": next(iter(currency_set)),
            "revenue": str(revenue),
            "operating_income": str(op_income),
            "net_income": str(net_income),
            "cfo": str(cfo),
            "capex_spend": str(capex_spend),
            "fcf": str(fcf),
            "fcf_definition": "cash_from_operations - capital_expenditures",
            "operating_margin": str(op_income / revenue) if revenue > 0 else "N/M",
            "fcf_conversion": str(fcf / net_income) if net_income > 0 else "N/M",
            "fcf_conversion_definition": "free_cash_flow / positive_net_income",
            "evidence": {
                metric: {"source_url": selected[(label, metric)].source_url,
                         "published_at": selected[(label, metric)].published_at,
                         "basis": selected[(label, metric)].basis,
                         "definition": selected[(label, metric)].definition,
                         "reported_unit": selected[(label, metric)].unit,
                         "currency": selected[(label, metric)].currency,
                         "prior_revisions": revisions.get((label, metric), [])}
                for metric in _CORE_METRICS
            },
        })
        optional_values: dict[str, dict] = {}
        for metric in _OPTIONAL_METRICS:
            value, value_unit, error = raw[metric]
            if error:
                optional_values[metric] = {"value": "N/M", "status": "UNVERIFIED", "reason": error}
                continue
            fact = selected[(label, metric)]
            expected_units = (_MONEY_UNITS if metric in _MONEY_METRICS else
                              _SHARE_UNITS if metric in _SHARE_METRICS else
                              {"days"} if metric == "cash_conversion_cycle" else
                              {"fraction", "percent", "multiple", "per_share"})
            unit_compatible = fact.unit in expected_units
            compatible_currency = fact.unit not in _MONEY_UNITS or value_unit == record["currency"]
            compatible_basis = fact.basis == next(iter(core_bases))
            basis_independent = metric in {"one_off_adjustments", "recurring_adjustments", "adjusted_ebitda"}
            accepted = unit_compatible and compatible_currency and (compatible_basis or basis_independent)
            optional_values[metric] = {
                "value": str(value) if accepted else "N/M",
                "unit": value_unit,
                "status": "VERIFIED" if accepted else "UNVERIFIED",
                "reason": None if accepted else "INCOMPATIBLE_UNIT_OR_CURRENCY_OR_BASIS",
                "basis_compatible": compatible_basis,
                "source_url": fact.source_url,
                "published_at": fact.published_at,
                "definition": fact.definition,
                "reported_unit": fact.unit,
                "basis": fact.basis,
                "prior_revisions": revisions.get((label, metric), []),
            }
        record["optional_metrics"] = optional_values
        gross_profit = optional_values.get("gross_profit", {}).get("value")
        reported_gross_margin = optional_values.get("gross_margin", {}).get("value")
        if gross_profit not in {None, "N/M"} and revenue > 0:
            record["gross_margin"] = str(Decimal(gross_profit) / revenue)
            record["gross_margin_method"] = "gross_profit / revenue"
        elif reported_gross_margin not in {None, "N/M"}:
            record["gross_margin"] = reported_gross_margin
            record["gross_margin_method"] = "source-reported gross_margin"
        else:
            record["gross_margin"] = "N/M"
            record["gross_margin_reason"] = "MISSING_GROSS_PROFIT_OR_NONPOSITIVE_REVENUE"
        debt = optional_values.get("total_debt", {}).get("value")
        cash_value = optional_values.get("cash", {}).get("value")
        if debt not in {None, "N/M"} and cash_value not in {None, "N/M"}:
            record["net_debt"] = str(Decimal(debt) - Decimal(cash_value))
            record["net_debt_method"] = "total_debt - cash"
        elif optional_values.get("net_debt", {}).get("value") not in {None, "N/M"}:
            record["net_debt"] = optional_values["net_debt"]["value"]
            record["net_debt_method"] = "source-reported net_debt"
        else:
            record["net_debt"] = "N/M"
            record["net_debt_reason"] = "MISSING_OR_INCOMPATIBLE_DEBT_OR_CASH"
        if revenue > 0 and optional_values.get("stock_compensation", {}).get("value") not in {None, "N/M"}:
            record["stock_compensation_to_revenue"] = str(Decimal(optional_values["stock_compensation"]["value"]) / revenue)
        else:
            record["stock_compensation_to_revenue"] = "N/M"
        if debt not in {None, "N/M"} and Decimal(debt) > 0 and optional_values.get("debt_due_12m", {}).get("value") not in {None, "N/M"}:
            record["debt_due_12m_share"] = str(Decimal(optional_values["debt_due_12m"]["value"]) / Decimal(debt))
        else:
            record["debt_due_12m_share"] = "N/M"
        nopat, nopat_unit, nopat_error = raw["nopat"]
        invested, invested_unit, invested_error = raw["average_invested_capital"]
        if nopat_error or invested_error:
            record["roic"] = "UNVERIFIED"
            record["roic_method"] = "NOPAT / average invested capital; source-derived inputs required"
        elif (nopat_unit != invested_unit or invested == 0
              or selected[(label, "nopat")].basis != selected[(label, "average_invested_capital")].basis):
            record["roic"] = "UNVERIFIED"
            record["roic_method"] = "INCOMPATIBLE_INPUTS"
        else:
            record["roic"] = str(nopat / invested)
            record["roic_method"] = "NOPAT / average invested capital"
        if (label, "nopat") in selected and (label, "average_invested_capital") in selected:
            record["roic_evidence"] = {
                metric: {"source_url": selected[(label, metric)].source_url,
                         "published_at": selected[(label, metric)].published_at,
                         "basis": selected[(label, metric)].basis,
                         "prior_revisions": revisions.get((label, metric), [])}
                for metric in ("nopat", "average_invested_capital")
            }
        periods.append(record)

    comparable_currencies = {tuple(sorted(v)) for v in currencies_by_period.values()}
    period_currency_mismatch = len(comparable_currencies) > 1
    if period_currency_mismatch:
        problems.append("PERIOD_CURRENCY_MISMATCH")
        for period in periods:
            period["revenue_growth_yoy"] = "N/M"
            period["revenue_growth_reason"] = "PERIOD_CURRENCY_MISMATCH"
            period["fcf_growth_yoy"] = "N/M"
            period["fcf_growth_reason"] = "PERIOD_CURRENCY_MISMATCH"

    verified_periods = [p for p in periods if p.get("status") == "VERIFIED"]
    # Deterioration is descriptive and requires three ordered annual observations.
    annual = [p for p in periods if str(p.get("period", "")).startswith("FY") and p.get("status") == "VERIFIED"]
    annual.sort(key=lambda p: p["period"])
    for previous, current in zip(annual, annual[1:]):
        current_year = int(current["period"][2:])
        previous_year = int(previous["period"][2:])
        if current_year - previous_year != 1:
            continue
        previous_revenue = Decimal(previous["revenue"])
        previous_fcf = Decimal(previous["fcf"])
        previous_shares = previous.get("optional_metrics", {}).get("shares_diluted", {}).get("value")
        current_shares = current.get("optional_metrics", {}).get("shares_diluted", {}).get("value")
        current["revenue_growth_yoy"] = str(Decimal(current["revenue"]) / previous_revenue - 1) if previous_revenue > 0 else "N/M"
        current["fcf_growth_yoy"] = str(Decimal(current["fcf"]) / previous_fcf - 1) if previous_fcf > 0 else "N/M"
        current["shares_dilution_yoy"] = (
            str(Decimal(current_shares) / Decimal(previous_shares) - 1)
            if previous_shares not in {None, "N/M"} and current_shares not in {None, "N/M"} and Decimal(previous_shares) > 0
            else "N/M"
        )
    if (latest_ytd and year - 1 in ytd_by_quarter.get(quarter, set())
            and len(ytd_labels_by_period.get((year, quarter), set())) == 1
            and len(ytd_labels_by_period.get((year - 1, quarter), set())) == 1
            and "YTD_PERIOD_LENGTH_MISMATCH" not in problems
            and "AMBIGUOUS_YTD_PERIOD_IDENTITY" not in problems
            and not cross_period_comparability_problems):
        current_label = next(iter(ytd_labels_by_period.get((year, quarter), set())))
        prior_label = next(iter(ytd_labels_by_period.get((year - 1, quarter), set())))
        by_label = {item.get("period"): item for item in periods}
        current_period, prior_period = by_label.get(current_label), by_label.get(prior_label)
        if current_period and prior_period and current_period.get("status") == "VERIFIED" and prior_period.get("status") == "VERIFIED":
            prior_revenue = Decimal(prior_period["revenue"])
            prior_fcf = Decimal(prior_period["fcf"])
            current_period["revenue_growth_yoy"] = str(Decimal(current_period["revenue"]) / prior_revenue - 1) if prior_revenue > 0 else "N/M"
            current_period["fcf_growth_yoy"] = str(Decimal(current_period["fcf"]) / prior_fcf - 1) if prior_fcf > 0 else "N/M"
    deterioration: list[str] = []
    annual_years = [int(str(p["period"])[2:]) for p in annual]
    annual_comparable = (len(annual) >= 3 and all(b - a == 1 for a, b in zip(annual_years, annual_years[1:]))
                         and not period_currency_mismatch and not cross_period_comparability_problems)
    if annual_comparable:
        revenues = [Decimal(str(p["revenue"])) for p in annual[-3:]]
        margins = [Decimal(str(p["operating_margin"])) for p in annual[-3:] if p["operating_margin"] != "N/M"]
        fcfs = [Decimal(str(p["fcf"])) for p in annual[-3:]]
        if len(revenues) == 3 and revenues[0] > revenues[1] > revenues[2]:
            deterioration.append("REVENUE_DECLINED_TWO_CONSECUTIVE_PERIODS")
        if len(margins) == 3 and margins[0] > margins[1] > margins[2]:
            deterioration.append("OPERATING_MARGIN_DECLINED_TWO_CONSECUTIVE_PERIODS")
        if len(fcfs) == 3 and fcfs[0] > fcfs[1] > fcfs[2]:
            deterioration.append("FCF_DECLINED_TWO_CONSECUTIVE_PERIODS")
    if cyclical:
        deterioration.append("CYCLE_NORMALIZATION_REQUIRED_NO_PEAK_EXTRAPOLATION")

    critical_errors = any(
        item.endswith(":LOOKAHEAD") or "CONFLICTED" in item or "MISSING_CRITICAL" in item
        or item in {"INSUFFICIENT_FY_HISTORY", "NONCONTIGUOUS_FY_HISTORY", "COMPARABLE_YTD_MISSING", "YTD_NOT_SUPPLIED", "PERIOD_CURRENCY_MISMATCH", "YTD_PERIOD_LENGTH_MISMATCH", "AMBIGUOUS_YTD_PERIOD_IDENTITY", "CORE_BASIS_CHANGED_ACROSS_PERIODS"}
        or item.endswith(":CAPEX_CASHFLOW_SIGN_MISMATCH")
        or item.endswith(":MIXED_GAAP_OR_ADJUSTED_BASIS")
        or item.endswith(":MIXED_CURRENCY_REQUIRES_CONVERSION")
        or item.startswith("METRIC_DEFINITION_CHANGED:")
        for item in problems
    )
    status = "UNVERIFIED" if problems or len(verified_periods) < len(periods) else "VERIFIED"
    if critical_errors:
        status = "BLOCKED"
    if alternative:
        status = "ALTERNATIVE_INDUSTRY_PATH"
    return {
        "status": status,
        "as_of": as_of,
        "industry_path": "ALTERNATIVE_REQUIRED" if alternative else "GENERAL",
        "period_count_fy": len(fy_labels),
        "required_fy_count": required_fy_count,
        "comparable_ytd": bool(latest_ytd and not any(problem in problems for problem in (
            "COMPARABLE_YTD_MISSING", "NONCOMPARABLE_YTD_SET", "AMBIGUOUS_YTD_PERIOD_IDENTITY", "YTD_PERIOD_LENGTH_MISMATCH",
            "CORE_BASIS_CHANGED_ACROSS_PERIODS"
        )) and not any(problem.startswith("METRIC_DEFINITION_CHANGED:") for problem in problems)),
        "periods": periods,
        "deterioration_flags": deterioration,
        "problems": sorted(set(problems)),
        "write_attempted": False,
    }
