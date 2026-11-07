"""Deterministic evidence checks for peer tables and forward-PEG eligibility."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import Mapping, Sequence
from urllib.parse import urlparse


class EvidenceState(str, Enum):
    VERIFIED = "VERIFIED"
    PROVISIONAL = "PROVISIONAL"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTED = "CONFLICTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class PeerMetric:
    name: str
    value: Decimal | None
    unit: str
    definition: str
    period: str
    basis: str
    published_at: str
    source_url: str
    status: EvidenceState = EvidenceState.VERIFIED
    horizon: str = ""
    currency: str = "USD"
    period_alignment_group: str = ""
    basis_group: str = ""


@dataclass(frozen=True)
class IssuerSnapshot:
    ticker: str
    sector: str
    industry: str
    business_model: str
    as_of: str
    metrics: Mapping[str, PeerMetric]
    cyclical: bool = False
    comparison_group: str = ""
    inclusion_rationale: str = ""
    peer_tier: str = ""


_MULTIPLE_METRICS = {"ev_sales", "ev_ebitda", "forward_pe", "price_sales", "price_to_sales", "ev_fcf"}
_FRACTION_METRICS = {"revenue_growth", "fcf_growth", "eps_cagr", "fcf_yield", "operating_margin", "gross_margin", "fcf_margin", "roic", "eps_revision_90d"}
_FORWARD_METRICS = {"forward_pe", "eps_cagr"}
_FRESH_METRICS = _FORWARD_METRICS | {"eps_revision_90d"}
_MAX_FORWARD_AGE_DAYS = 90
_MIN_TABLE_PEERS = 3
_MIN_PERCENTILE_PEERS = 5
_MAX_PEERS = 15
_NON_RANKED_METRICS = {"ps_growth_heuristic"}
_CORE_VALUATION_METRICS = {"ev_sales", "ev_ebitda", "forward_pe"}


def _valid_date(value: str) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except (TypeError, ValueError):
        return False


def _valid_url(value: str) -> bool:
    parsed = urlparse(value) if isinstance(value, str) else None
    return bool(parsed and parsed.scheme == "https" and parsed.netloc)


def _nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _metric_reason(metric: PeerMetric | None, name: str, as_of: str, *, compare_to: PeerMetric | None = None) -> str | None:
    if metric is None:
        return "MISSING"
    try:
        state = EvidenceState(metric.status)
    except (ValueError, TypeError):
        return "INVALID_EVIDENCE_STATE"
    if state not in {EvidenceState.VERIFIED, EvidenceState.PROVISIONAL}:
        return state.value
    if metric.value is None or not isinstance(metric.value, Decimal) or not metric.value.is_finite():
        return "MISSING_OR_NONFINITE"
    if not _valid_date(metric.published_at) or not _valid_date(as_of):
        return "INVALID_DATE"
    if metric.published_at > as_of:
        return "LOOKAHEAD"
    if not _valid_url(metric.source_url):
        return "INVALID_SOURCE_URL"
    if not all(_nonblank(value) for value in (metric.name, metric.unit, metric.definition, metric.period, metric.basis, metric.currency)):
        return "INCOMPLETE_DEFINITION"
    if (name in _MULTIPLE_METRICS or metric.unit == "multiple") and (metric.unit != "multiple" or metric.value <= 0):
        return "NOT_MEANINGFUL"
    if name in _FRACTION_METRICS and metric.unit != "fraction":
        return "INCOMPATIBLE_UNIT"
    if name in _FRESH_METRICS:
        age = (date.fromisoformat(as_of) - date.fromisoformat(metric.published_at)).days
        if age > _MAX_FORWARD_AGE_DAYS:
            return "STALE_FORWARD_OR_REVISION_DATA"
    if name in _FORWARD_METRICS:
        if not metric.horizon:
            return "MISSING_FORECAST_HORIZON"
        if name == "forward_pe" and metric.horizon not in {"12M", "NTM"}:
            return "INCOMPATIBLE_FORWARD_PE_HORIZON"
        if name == "eps_cagr" and metric.horizon not in {"3Y", "5Y", "3–5Y"}:
            return "INCOMPATIBLE_EPS_GROWTH_HORIZON"
    if compare_to is not None and (
        metric.name != compare_to.name
        or metric.unit != compare_to.unit
        or metric.definition != compare_to.definition
        or metric.horizon != compare_to.horizon
        or (
            metric.period != compare_to.period
            and not (
                _nonblank(metric.period_alignment_group)
                and metric.period_alignment_group == compare_to.period_alignment_group
            )
        )
        or (
            metric.basis != compare_to.basis
            and not (_nonblank(metric.basis_group) and metric.basis_group == compare_to.basis_group)
        )
        or (
            metric.currency.upper() != compare_to.currency.upper()
            and metric.unit not in {"fraction", "multiple", "heuristic"}
        )
    ):
        return "INCOMPATIBLE_DEFINITION_PERIOD_BASIS_OR_HORIZON"
    return None


def _fingerprint(target: IssuerSnapshot, peers: Sequence[IssuerSnapshot], rows: Sequence[dict], as_of: str) -> str:
    material = {
        "target": target.ticker,
        "as_of": as_of,
        "target_classification": (target.sector, target.industry, target.business_model, target.cyclical,
                                  target.comparison_group, target.inclusion_rationale, target.peer_tier),
        "target_metrics": {
            k: (str(v.value) if v.value is not None else None, v.unit, v.definition, v.period,
                v.basis, v.horizon, v.published_at, v.source_url, v.currency,
                v.period_alignment_group, v.basis_group, str(v.status))
            for k, v in sorted(target.metrics.items())
        },
        "peer_classifications": {
            peer.ticker: {
                "classification": (peer.sector, peer.industry, peer.business_model, peer.as_of, peer.cyclical,
                                   peer.comparison_group, peer.inclusion_rationale, peer.peer_tier),
                "metrics": {
                    key: (str(value.value) if value.value is not None else None, value.unit,
                          value.definition, value.period, value.basis, value.horizon,
                          value.published_at, value.source_url, value.currency,
                          value.period_alignment_group, value.basis_group, str(value.status))
                    for key, value in sorted(peer.metrics.items())
                },
            }
            for peer in sorted(peers, key=lambda item: str(item.ticker))
        },
        "rows": [
            (r["ticker"], r["eligibility"], r["reason"], {
                k: (v.get("value"), v.get("status"), v.get("reason"), v.get("source_url"))
                for k, v in sorted(r.get("metrics", {}).items())
            }) for r in rows
        ],
    }
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def compare_peer_set(target: IssuerSnapshot, peers: Sequence[IssuerSnapshot], as_of: str) -> dict:
    """Build a reproducible comparison without a recommendation or automatic rank.

    Peer eligibility is explicit. Metric rows remain N/M when values, source
    timing, definitions, periods, units, accounting bases or forecast horizons
    cannot be compared. Percentiles are descriptive and require five valid
    peer observations; they are never converted to a cross-industry score.
    """
    if (
        not _valid_date(as_of)
        or not _nonblank(target.ticker)
        or target.as_of != as_of
        or not _nonblank(target.sector)
        or not _nonblank(target.industry)
        or not _nonblank(target.business_model)
        or not _nonblank(target.comparison_group)
        or not isinstance(target.metrics, Mapping)
        or any(not isinstance(metric, PeerMetric) for metric in target.metrics.values())
        or not isinstance(peers, Sequence)
        or any(not isinstance(peer, IssuerSnapshot) for peer in peers)
        or len(peers) > _MAX_PEERS
    ):
        return {"status": "NOT_COMPARABLE", "reason": "INVALID_TARGET_SNAPSHOT_OR_PEER_COUNT", "as_of": as_of,
                "peers": [], "recommendation": None, "ranked": False}
    if any(key != metric.name for key, metric in target.metrics.items()):
        return {"status": "NOT_COMPARABLE", "reason": "TARGET_METRIC_KEY_MISMATCH", "as_of": as_of,
                "peers": [], "recommendation": None, "ranked": False}
    if len({str(p.ticker) for p in peers}) != len(peers) or target.ticker in {str(p.ticker) for p in peers}:
        return {"status": "NOT_COMPARABLE", "reason": "DUPLICATE_OR_TARGET_PEER", "as_of": as_of,
                "peers": [], "recommendation": None, "ranked": False}

    rows: list[dict] = []
    for peer in sorted(peers, key=lambda item: str(item.ticker)):
        reason = None
        if peer.as_of != as_of:
            reason = "AS_OF_MISMATCH"
        elif peer.sector != target.sector or peer.industry != target.industry:
            reason = "SECTOR_OR_INDUSTRY_MISMATCH"
        elif not _nonblank(peer.ticker) or not _nonblank(peer.sector) or not _nonblank(peer.industry) or not _nonblank(peer.business_model):
            reason = "MISSING_PEER_IDENTITY"
        elif peer.peer_tier not in {"DIRECT", "ADJACENT"}:
            reason = "INVALID_COMPARABILITY_TIER"
        elif not _nonblank(peer.comparison_group) or peer.comparison_group != target.comparison_group:
            reason = "COMPARISON_GROUP_MISMATCH"
        elif not _nonblank(peer.inclusion_rationale):
            reason = "MISSING_INCLUSION_RATIONALE"
        row = {
            "ticker": peer.ticker,
            "eligibility": "INCLUDED" if reason is None else "EXCLUDED",
            "reason": reason,
            "exclusion_rationale": {
                "AS_OF_MISMATCH": "Peer snapshot date differs from target snapshot.",
                "SECTOR_OR_INDUSTRY_MISMATCH": "Peer is outside the target sector or industry.",
                "MISSING_PEER_IDENTITY": "Peer identity or business-model classification is missing.",
                "INVALID_COMPARABILITY_TIER": "Reviewer must assign DIRECT or ADJACENT explicitly.",
                "COMPARISON_GROUP_MISMATCH": "Peer is not assigned to the target's reviewed comparison group.",
                "MISSING_INCLUSION_RATIONALE": "A reviewer must explain the economic basis for including this peer.",
            }.get(reason),
            "business_model": peer.business_model,
            "comparison_group": peer.comparison_group,
            "comparability_tier": peer.peer_tier if reason is None else "EXCLUDED",
            "inclusion_rationale": peer.inclusion_rationale if reason is None else None,
            "cycle_normalization_required": peer.cyclical,
            "metrics": {},
        }
        if reason is not None:
            rows.append(row)
            continue
        if any(key != metric.name for key, metric in peer.metrics.items()):
            row["eligibility"] = "EXCLUDED"
            row["reason"] = "PEER_METRIC_KEY_MISMATCH"
            rows.append(row)
            continue

        for name, target_metric in sorted(target.metrics.items()):
            peer_metric = peer.metrics.get(name)
            target_reason = _metric_reason(target_metric, name, as_of)
            peer_reason = _metric_reason(peer_metric, name, as_of, compare_to=target_metric)
            metric_reason = target_reason or peer_reason
            if metric_reason:
                row["metrics"][name] = {
                    "value": "N/M", "unit": target_metric.unit,
                    "status": "NOT_MEANINGFUL", "reason": metric_reason,
                    "definition": target_metric.definition, "period": target_metric.period,
                    "horizon": target_metric.horizon, "basis": target_metric.basis,
                    "target_currency": target_metric.currency,
                    "target_source_url": target_metric.source_url,
                    "target_published_at": target_metric.published_at,
                    "peer_basis": peer_metric.basis if peer_metric else None,
                    "peer_period": peer_metric.period if peer_metric else None,
                    "peer_period_alignment_group": peer_metric.period_alignment_group if peer_metric else None,
                    "target_period_alignment_group": target_metric.period_alignment_group,
                    "peer_basis_group": peer_metric.basis_group if peer_metric else None,
                    "target_basis_group": target_metric.basis_group,
                    "peer_source_url": peer_metric.source_url if peer_metric else None,
                    "peer_published_at": peer_metric.published_at if peer_metric else None,
                }
            else:
                row["metrics"][name] = {
                    "value": str(peer_metric.value), "unit": peer_metric.unit,
                    "status": "VERIFIED" if EvidenceState(peer_metric.status) == EvidenceState.VERIFIED and EvidenceState(target_metric.status) == EvidenceState.VERIFIED else "PROVISIONAL",
                    "reason": None, "definition": peer_metric.definition,
                    "period": peer_metric.period, "horizon": peer_metric.horizon, "basis": peer_metric.basis,
                    "target_period": target_metric.period, "target_basis": target_metric.basis,
                    "peer_period_alignment_group": peer_metric.period_alignment_group,
                    "target_period_alignment_group": target_metric.period_alignment_group,
                    "peer_basis_group": peer_metric.basis_group, "target_basis_group": target_metric.basis_group,
                    "peer_currency": peer_metric.currency, "target_currency": target_metric.currency,
                    "target_value": str(target_metric.value),
                    "target_source_url": target_metric.source_url,
                    "target_published_at": target_metric.published_at,
                    "source_url": peer_metric.source_url, "published_at": peer_metric.published_at,
                }

        price_sales = peer.metrics.get("price_sales") or peer.metrics.get("price_to_sales")
        target_price_sales = target.metrics.get("price_sales") or target.metrics.get("price_to_sales")
        peer_revenue_growth = peer.metrics.get("revenue_growth")
        target_revenue_growth = target.metrics.get("revenue_growth")
        ps_reasons = []
        if target_price_sales is None or target_revenue_growth is None:
            ps_reasons.append("MISSING_TARGET_P_S_OR_REVENUE_GROWTH")
        if price_sales is None or peer_revenue_growth is None:
            ps_reasons.append("MISSING_PEER_P_S_OR_REVENUE_GROWTH")
        if peer.peer_tier != "DIRECT":
            ps_reasons.append("BUSINESS_MODEL_MISMATCH")
        if not ps_reasons:
            for metric, reference in ((target_price_sales, None), (target_revenue_growth, None),
                                      (price_sales, target_price_sales), (peer_revenue_growth, target_revenue_growth)):
                reason = _metric_reason(metric, metric.name, as_of, compare_to=reference)
                if reason:
                    ps_reasons.append(reason)
            if peer_revenue_growth.value <= 0 or target_revenue_growth.value <= 0:
                ps_reasons.append("NONPOSITIVE_REVENUE_GROWTH")
        if ps_reasons:
            row["metrics"]["ps_growth_heuristic"] = {"value": "N/M", "unit": "heuristic",
                "status": "NOT_MEANINGFUL", "reason": sorted(set(ps_reasons))[0],
                "recommendation": None, "primary_rank": False}
        else:
            ps_growth_value = price_sales.value / (peer_revenue_growth.value * Decimal("100"))
            ps_state = "PROVISIONAL" if any(EvidenceState(metric.status) == EvidenceState.PROVISIONAL
                for metric in (price_sales, peer_revenue_growth, target_price_sales, target_revenue_growth)) else "VERIFIED"
            row["metrics"]["ps_growth_heuristic"] = {"value": str(ps_growth_value), "unit": "heuristic",
                "status": ps_state, "reason": None,
                "definition": "P/S divided by revenue growth expressed in percentage points; descriptive heuristic only",
                "source_url": price_sales.source_url, "published_at": price_sales.published_at,
                "growth_source_url": peer_revenue_growth.source_url,
                "growth_published_at": peer_revenue_growth.published_at,
                "target_p_s_source_url": target_price_sales.source_url,
                "target_p_s_published_at": target_price_sales.published_at,
                "target_growth_source_url": target_revenue_growth.source_url,
                "target_growth_published_at": target_revenue_growth.published_at,
                "recommendation": None, "primary_rank": False}

        forward_pe = peer.metrics.get("forward_pe")
        eps_growth = peer.metrics.get("eps_cagr")
        growth_reason = "BUSINESS_MODEL_MISMATCH" if peer.peer_tier != "DIRECT" else _metric_reason(eps_growth, "eps_cagr", as_of,
                                       compare_to=target.metrics.get("eps_cagr")) if target.metrics.get("eps_cagr") else "MISSING_TARGET_GROWTH_DEFINITION"
        pe_reason = "BUSINESS_MODEL_MISMATCH" if peer.peer_tier != "DIRECT" else _metric_reason(forward_pe, "forward_pe", as_of,
                                   compare_to=target.metrics.get("forward_pe")) if target.metrics.get("forward_pe") else "MISSING_TARGET_FORWARD_PE_DEFINITION"
        target_growth = target.metrics.get("eps_cagr")
        if (growth_reason or pe_reason or eps_growth is None or forward_pe is None or target_growth is None
                or eps_growth.value <= 0 or target_growth.value <= 0):
            row["metrics"]["peg"] = {"value": "N/M", "unit": "multiple", "status": "NOT_MEANINGFUL",
                                      "reason": growth_reason or pe_reason or "NONPOSITIVE_EPS_GROWTH"}
        else:
            peg = forward_pe.value / (eps_growth.value * Decimal("100"))
            peg_status = "PROVISIONAL" if EvidenceState(forward_pe.status) == EvidenceState.PROVISIONAL or EvidenceState(eps_growth.status) == EvidenceState.PROVISIONAL else "VERIFIED"
            row["metrics"]["peg"] = {"value": str(peg), "unit": "multiple", "status": peg_status,
                                      "reason": None, "definition": "forward P/E / EPS CAGR expressed in percentage points",
                                      "horizon": eps_growth.horizon, "peg_reference": "1",
                                      "forward_pe_source_url": forward_pe.source_url,
                                      "forward_pe_published_at": forward_pe.published_at,
                                      "eps_cagr_source_url": eps_growth.source_url,
                                      "eps_cagr_published_at": eps_growth.published_at}
        rows.append(row)

    included = [row for row in rows if row["eligibility"] == "INCLUDED"]
    direct_included = [row for row in included if row["comparability_tier"] == "DIRECT"]
    summaries: dict[str, dict] = {}
    all_names = sorted({name for row in direct_included for name in row["metrics"] if name not in _NON_RANKED_METRICS})
    for name in all_names:
        values = [Decimal(row["metrics"][name]["value"]) for row in direct_included
                  if row["metrics"].get(name, {}).get("status") in {"VERIFIED", "PROVISIONAL"}]
        verified_count = sum(row["metrics"].get(name, {}).get("status") == "VERIFIED" for row in direct_included)
        provisional_count = sum(row["metrics"].get(name, {}).get("status") == "PROVISIONAL" for row in direct_included)
        summary = {"valid_peer_count": len(values), "unit": next(
            (row["metrics"][name].get("unit") for row in direct_included if name in row["metrics"]), None),
            "verified_peer_count": verified_count, "provisional_peer_count": provisional_count}
        if values:
            ordered = sorted(values)
            summary["median"] = str(ordered[len(ordered) // 2]) if len(ordered) % 2 else str((ordered[len(ordered)//2 - 1] + ordered[len(ordered)//2]) / 2)
        if len(values) >= _MIN_PERCENTILE_PEERS:
            target_metric = target.metrics.get(name)
            if name == "peg":
                target_pe = target.metrics.get("forward_pe")
                target_growth = target.metrics.get("eps_cagr")
                target_reason = _metric_reason(target_pe, "forward_pe", as_of) if target_pe else "MISSING_TARGET_FORWARD_PE"
                target_reason = target_reason or (_metric_reason(target_growth, "eps_cagr", as_of) if target_growth else "MISSING_TARGET_EPS_GROWTH")
                if not target_reason and target_growth and target_growth.value <= 0:
                    target_reason = "NONPOSITIVE_EPS_GROWTH"
                target_value = (target_pe.value / (target_growth.value * Decimal("100"))) if not target_reason and target_pe and target_growth and target_growth.value > 0 else None
            else:
                target_reason = _metric_reason(target_metric, name, as_of) if target_metric else "MISSING_TARGET_METRIC"
                target_value = target_metric.value if not target_reason and target_metric else None
            if target_reason is None:
                summary["target_percentile"] = str(
                    (Decimal(sum(x < target_value for x in values)) + Decimal(sum(x == target_value for x in values)) / 2)
                    / Decimal(len(values))
                )
                summary["percentile_evidence_status"] = "PROVISIONAL" if provisional_count else "VERIFIED"
            else:
                summary["target_percentile"] = "N/M"
                summary["target_percentile_reason"] = target_reason
        else:
            summary["percentile_status"] = (
                "N/M; descriptive percentiles require at least five compatible peers in the reviewed direct cohort"
                if len(values) >= _MIN_PERCENTILE_PEERS else "N/M; at least five compatible peer values required"
            )
        summaries[name] = summary

    snapshot_id = _fingerprint(target, peers, rows, as_of)
    plot_points = []
    target_pe = target.metrics.get("forward_pe")
    target_growth = target.metrics.get("eps_cagr")
    if target_pe and target_growth:
        pe_reason = _metric_reason(target_pe, "forward_pe", as_of)
        growth_reason = _metric_reason(target_growth, "eps_cagr", as_of)
        if not pe_reason and not growth_reason and target_pe.value > 0 and target_growth.value > 0:
            plot_points.append({
                "ticker": target.ticker, "role": "TARGET",
                "status": "PROVISIONAL" if EvidenceState(target_growth.status) == EvidenceState.PROVISIONAL or EvidenceState(target_pe.status) == EvidenceState.PROVISIONAL else "VERIFIED",
                "eps_growth_pct": str(target_growth.value * 100), "forward_pe": str(target_pe.value),
                "peg": str(target_pe.value / (target_growth.value * Decimal("100"))),
                "eps_growth_source_url": target_growth.source_url, "eps_growth_published_at": target_growth.published_at,
                "forward_pe_source_url": target_pe.source_url, "forward_pe_published_at": target_pe.published_at,
                "eps_growth_definition": target_growth.definition, "forward_pe_definition": target_pe.definition,
                "horizon": target_growth.horizon,
                "cycle_normalization_required": target.cyclical,
            })
    for row in included:
        pe = row["metrics"].get("forward_pe", {})
        growth = row["metrics"].get("eps_cagr", {})
        peg = row["metrics"].get("peg", {})
        if pe.get("status") in {"VERIFIED", "PROVISIONAL"} and growth.get("status") in {"VERIFIED", "PROVISIONAL"} and peg.get("status") in {"VERIFIED", "PROVISIONAL"}:
            peer_metric = next(p for p in peers if p.ticker == row["ticker"])
            peer_pe = peer_metric.metrics["forward_pe"]
            peer_growth = peer_metric.metrics["eps_cagr"]
            plot_points.append({
                "ticker": row["ticker"], "role": "PEER",
                "status": peg["status"],
                "eps_growth_pct": str(Decimal(growth["value"]) * 100), "forward_pe": pe["value"], "peg": peg["value"],
                "eps_growth_source_url": peer_growth.source_url, "eps_growth_published_at": peer_growth.published_at,
                "forward_pe_source_url": peer_pe.source_url, "forward_pe_published_at": peer_pe.published_at,
                "eps_growth_definition": peer_growth.definition, "forward_pe_definition": peer_pe.definition,
                "horizon": peer_growth.horizon,
                "cycle_normalization_required": peer.cyclical,
            })

    core_metric_peer_counts = {
        name: int(summaries.get(name, {}).get("valid_peer_count", 0))
        for name in sorted(_CORE_VALUATION_METRICS)
    }
    has_minimum_compatible_metric = any(count >= _MIN_TABLE_PEERS for count in core_metric_peer_counts.values())
    comparability_reason = (
        "FEWER_THAN_THREE_DIRECT_PEERS" if len(direct_included) < _MIN_TABLE_PEERS
        else "NO_CORE_METRIC_HAS_THREE_COMPATIBLE_DIRECT_PEERS" if not has_minimum_compatible_metric
        else None
    )
    return {
        "status": "COMPARABLE" if comparability_reason is None else "INSUFFICIENT_COMPARABLE_PEERS",
        "comparability_reason": comparability_reason,
        "as_of": as_of, "target": target.ticker, "sector": target.sector, "industry": target.industry,
        "business_model": target.business_model, "comparison_group": target.comparison_group,
        "included_peer_count": len(included), "direct_peer_count": len(direct_included),
        "core_metric_peer_counts": core_metric_peer_counts,
        "cycle_normalization_required": target.cyclical,
        "required_peer_range": "3–5 for a compact table; expand to 5–15 only when economically valid",
        "peers": rows, "metric_summaries": summaries,
        "peg_reference": {"value": "1", "x_axis": "EPS growth in percentage points", "y_axis": "forward P/E",
                          "interpretation": "descriptive heuristic only; not a buy signal or cross-sector ranking"},
        "plot": {"snapshot_id": snapshot_id, "as_of": as_of,
                 "forecast_horizon": (target.metrics.get("eps_cagr").horizon if target.metrics.get("eps_cagr") else None),
                 "filter": {"sector": target.sector, "industry": target.industry, "business_model": target.business_model},
                 "points": plot_points, "same_input_as_table": True,
                 "peg_one_line": "forward P/E = EPS growth percentage points"},
        "recommendation": None, "ranked": False, "cross_sector_ranking": False,
    }
