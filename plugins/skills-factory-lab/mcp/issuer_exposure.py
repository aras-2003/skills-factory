"""Read-only issuer look-through over explicit caller-supplied evidence."""

from __future__ import annotations

from datetime import date
from math import isfinite
from typing import Any


def _day(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("invalid calendar date")
    return parsed


def _pct(value: float) -> float:
    return round(value + 0.0, 6)


def _concentration(issuers: list[dict[str, Any]], complete: bool) -> dict[str, Any]:
    if not complete:
        return {"status": "BLOCKED_INCOMPLETE_ISSUER_DECOMPOSITION", "top_3_pct": None, "top_5_pct": None, "top_10_pct": None, "hhi_pct_squared": None, "effective_issuer_count": None}
    values = [row["known_minimum_total_pct"] for row in issuers]
    hhi = sum(value**2 for value in values)
    return {"status": "COMPLETE", "top_3_pct": _pct(sum(values[:3])), "top_5_pct": _pct(sum(values[:5])), "top_10_pct": _pct(sum(values[:10])), "hhi_pct_squared": _pct(hhi), "effective_issuer_count": _pct(10000 / hhi) if hhi else None}


def calculate_issuer_exposure(arguments: dict[str, Any]) -> dict[str, Any]:
    as_of = arguments["as_of"]
    as_of_day = _day(as_of)
    portfolio_id = str(arguments["portfolio_id"]).strip()
    base_currency = str(arguments["base_currency"]).strip()
    if not portfolio_id or not base_currency:
        raise ValueError("portfolio identity and base currency are required")
    positions = arguments["positions"]
    fund_snapshots = arguments["fund_snapshots"]
    if not isinstance(positions, list) or not 1 <= len(positions) <= 100:
        raise ValueError("positions must contain 1–100 rows")
    if not isinstance(fund_snapshots, list) or len(fund_snapshots) > 100:
        raise ValueError("fund_snapshots must contain at most 100 rows")
    total_pln = arguments.get("portfolio_value_pln")
    if total_pln is not None and (not isfinite(total_pln) or total_pln <= 0 or base_currency != "PLN"):
        raise ValueError("portfolio_value_pln requires a positive value and PLN currency")

    snapshots: dict[str, dict[str, Any]] = {}
    for snapshot in fund_snapshots:
        instrument_id = snapshot.get("instrument_id")
        if not instrument_id or instrument_id in snapshots:
            raise ValueError("fund snapshots require unique instrument_id")
        source_uri = snapshot.get("source_uri", "")
        if not source_uri.startswith("https://"):
            raise ValueError("fund source URI must use HTTPS")
        snapshot_day, published_day, retrieved_day = (_day(snapshot[key]) for key in ("as_of", "published_at", "retrieved_at"))
        if snapshot_day > as_of_day or published_day > as_of_day or retrieved_day > as_of_day or retrieved_day < published_day:
            raise ValueError("fund snapshot has invalid or future provenance date")
        coverage = snapshot.get("coverage_pct")
        constituents = snapshot.get("constituents")
        if not isinstance(coverage, (int, float)) or not 0 <= coverage <= 100 or not isinstance(constituents, list) or len(constituents) > 500:
            raise ValueError("invalid fund coverage or constituents")
        weights = [row.get("weight_pct") for row in constituents]
        if any(not isinstance(weight, (int, float)) or not isfinite(weight) or not 0 <= weight <= 100 for weight in weights):
            raise ValueError("constituent weights must be finite percentages")
        if sum(weights) > coverage + 1e-6:
            raise ValueError("constituent weights cannot exceed declared coverage")
        if snapshot.get("completeness") == "COMPLETE" and (coverage != 100 or abs(sum(weights) - 100) > 1e-4):
            raise ValueError("complete funds require constituent weights and coverage to total 100%")
        for row in constituents:
            if row.get("security_type") not in {"issuer", "fund"}:
                raise ValueError("constituent security_type must be issuer or fund")
            if row["security_type"] == "issuer" and (not row.get("issuer_id") or not row.get("issuer_name")):
                raise ValueError("issuer constituents require issuer_id and issuer_name")
            if row["security_type"] == "fund" and not row.get("instrument_id"):
                raise ValueError("fund constituents require instrument_id")
        snapshots[instrument_id] = snapshot

    seen_positions: set[str] = set()
    position_weight_total = 0.0
    for position in positions:
        position_id = position.get("position_id")
        if not position_id or position_id in seen_positions:
            raise ValueError("positions require unique position_id")
        seen_positions.add(position_id)
        for field in ("account_id", "instrument_id", "isin", "share_class", "source_id"):
            if not position.get(field):
                raise ValueError(f"position requires {field}")
        if not str(position.get("source_uri", "")).startswith("https://"):
            raise ValueError("position source URI must use HTTPS")
        published_day, retrieved_day = (_day(position[key]) for key in ("published_at", "retrieved_at"))
        if published_day > as_of_day or retrieved_day > as_of_day or retrieved_day < published_day:
            raise ValueError("position has invalid or future provenance date")
        weight = position.get("weight_pct")
        if not isinstance(weight, (int, float)) or not isfinite(weight) or not 0 <= weight <= 100:
            raise ValueError("position weight must be a finite percentage")
        value_pln = position.get("market_value_pln")
        if value_pln is not None and total_pln is None:
            raise ValueError("market_value_pln requires portfolio_value_pln for reconciliation")
        if total_pln is not None and (value_pln is None or not isfinite(value_pln) or abs(value_pln - total_pln * weight / 100) > max(1, total_pln * 0.0001)):
            raise ValueError("market_value_pln must reconcile with position weight and portfolio value")
        if position.get("instrument_type") not in {"equity", "fund"}:
            raise ValueError("instrument_type must be equity or fund")
        if position["instrument_type"] == "equity" and (not position.get("issuer_id") or not position.get("issuer_name")):
            raise ValueError("direct equities require explicit issuer_id and issuer_name")
        position_weight_total += weight
    if position_weight_total > 100 + 1e-6:
        raise ValueError("portfolio position weights cannot exceed 100%")

    def expand(fund_id: str, scale: float, path: tuple[str, ...] = ()) -> dict[str, Any]:
        snapshot = snapshots.get(fund_id)
        if snapshot is None or fund_id in path:
            return {"rows": [], "unknown": scale, "complete": False, "missing": True}
        rows = []
        complete = snapshot.get("completeness") == "COMPLETE"
        missing = False
        for constituent in snapshot["constituents"]:
            contribution = scale * constituent["weight_pct"] / 100
            if constituent["security_type"] == "issuer":
                rows.append({"issuer_id": constituent["issuer_id"], "issuer_name": constituent["issuer_name"], "weight_pct": contribution, "factors": constituent.get("factors", []), "source_id": snapshot["source_id"], "source_uri": snapshot["source_uri"], "leaf_instrument_id": fund_id, "isin": constituent["isin"], "share_class": constituent["share_class"], "fund_path": [*path, fund_id], "as_of": snapshot["as_of"], "published_at": snapshot["published_at"], "retrieved_at": snapshot["retrieved_at"]})
            else:
                nested = expand(constituent["instrument_id"], contribution, (*path, fund_id))
                rows.extend(nested["rows"])
                complete = complete and nested["complete"]
                missing = missing or nested["missing"]
        mapped = sum(row["weight_pct"] for row in rows)
        complete = complete and abs(mapped - scale) <= 1e-4
        return {"rows": rows, "unknown": max(0, scale - mapped), "complete": complete, "missing": missing}

    issuer_rows: dict[str, dict[str, Any]] = {}
    factor_weights: dict[str, float] = {}
    fund_rows = []
    source_coverage = 0.0
    decomposition_complete = abs(position_weight_total - 100) <= 1e-6
    reasons = set() if decomposition_complete else {"PORTFOLIO_POSITION_WEIGHT_UNDER_100"}

    def add(issuer_id: str, name: str, amount: float, basis: str, factors: list[str], source: str, uri: str, root_instrument: str, leaf_instrument: str, isin: str, share_class: str, account: str, as_of_value: str, published_at: str, retrieved_at: str, path: list[str]) -> None:
        row = issuer_rows.setdefault(issuer_id, {"issuer_id": issuer_id, "issuer_name": name, "direct_weight_pct": 0.0, "lookthrough_min_pct": 0.0, "factors": set(), "sources": set(), "instruments": set(), "weight_evidence": []})
        row["direct_weight_pct" if basis == "direct" else "lookthrough_min_pct"] += amount
        row["factors"].update(factors)
        row["sources"].add(source)
        row["instruments"].update((root_instrument, leaf_instrument))
        for factor in factors:
            factor_weights[factor] = factor_weights.get(factor, 0.0) + amount
        row["weight_evidence"].append({"contribution_pct": _pct(amount), "basis": basis, "account_id": account, "instrument_id": root_instrument, "source_instrument_id": leaf_instrument, "instrument_path": path, "isin": isin, "share_class": share_class, "as_of": as_of_value, "published_at": published_at, "retrieved_at": retrieved_at, "freshness": "STALE_BY_DATE" if as_of > retrieved_at else "CURRENT_AS_OF_DATE", "source_id": source, "source_uri": uri})

    for position in positions:
        if position["instrument_type"] == "equity":
            add(position["issuer_id"], position["issuer_name"], position["weight_pct"], "direct", position.get("factors", []), position["source_id"], position["source_uri"], position["instrument_id"], position["instrument_id"], position["isin"], position["share_class"], position["account_id"], as_of, position["published_at"], position["retrieved_at"], [position["instrument_id"]])
            source_coverage += position["weight_pct"]
            continue
        snapshot = snapshots.get(position["instrument_id"])
        if snapshot is None:
            decomposition_complete = False
            reasons.add("FUND_SNAPSHOT_MISSING")
            fund_rows.append({"instrument_id": position["instrument_id"], "account_id": position["account_id"], "isin": position["isin"], "share_class": position["share_class"], "source_coverage_pct": 0, "decomposition": "MISSING", "unknown_weight_pct": position["weight_pct"]})
            continue
        resolved = expand(position["instrument_id"], position["weight_pct"])
        partial = snapshot.get("completeness") != "COMPLETE"
        if partial:
            reasons.add("FUND_SNAPSHOT_PARTIAL")
        if not resolved["complete"] and not partial:
            reasons.add("NESTED_FUND_LOOKTHROUGH_INCOMPLETE")
        if resolved["missing"]:
            reasons.add("NESTED_FUND_SNAPSHOT_MISSING_OR_CYCLE")
        decomposition_complete = decomposition_complete and resolved["complete"]
        covered = position["weight_pct"] * snapshot["coverage_pct"] / 100
        source_coverage += covered
        for row in resolved["rows"]:
            add(row["issuer_id"], row["issuer_name"], row["weight_pct"], "fund", row["factors"], row["source_id"], row["source_uri"], position["instrument_id"], row["leaf_instrument_id"], row["isin"], row["share_class"], position["account_id"], row["as_of"], row["published_at"], row["retrieved_at"], row["fund_path"])
        mapped = sum(row["weight_pct"] for row in resolved["rows"])
        fund_rows.append({"instrument_id": position["instrument_id"], "account_id": position["account_id"], "isin": position["isin"], "share_class": position["share_class"], "market_value_pln": position.get("market_value_pln"), "source_id": snapshot["source_id"], "source_uri": snapshot["source_uri"], "source_as_of": snapshot["as_of"], "published_at": snapshot["published_at"], "retrieved_at": snapshot["retrieved_at"], "freshness": "STALE_BY_DATE" if as_of > snapshot["retrieved_at"] else "CURRENT_AS_OF_DATE", "source_coverage_pct": snapshot["coverage_pct"], "decomposition": "COMPLETE" if resolved["complete"] else "PARTIAL" if partial else "INCOMPLETE_NESTED", "covered_portfolio_weight_pct": _pct(covered), "unmapped_in_covered_portfolio_weight_pct": _pct(max(0, covered - mapped)), "unknown_weight_pct": _pct(resolved["unknown"])})

    issuers = []
    for row in issuer_rows.values():
        direct = _pct(row["direct_weight_pct"])
        lookthrough = _pct(row["lookthrough_min_pct"])
        total = _pct(direct + lookthrough)
        issuers.append({"issuer_id": row["issuer_id"], "issuer_name": row["issuer_name"], "direct_weight_pct": direct, "lookthrough_min_pct": lookthrough, "known_minimum_total_pct": total, "factors": sorted(row["factors"]), "source_ids": sorted(row["sources"]), "instrument_ids": sorted(row["instruments"]), "weight_evidence": row["weight_evidence"], "direct_pln": _pct(direct * total_pln / 100) if total_pln is not None else None, "lookthrough_min_pln": _pct(lookthrough * total_pln / 100) if total_pln is not None else None, "known_minimum_pln": _pct(total * total_pln / 100) if total_pln is not None else None})
    issuers.sort(key=lambda row: (-row["known_minimum_total_pct"], row["issuer_id"]))
    unique_funds = list({row["instrument_id"]: row for row in positions if row["instrument_type"] == "fund"}.values())
    overlaps = []
    for i, fund_a in enumerate(unique_funds):
        for fund_b in unique_funds[i + 1:]:
            resolved_a = expand(fund_a["instrument_id"], 100)
            resolved_b = expand(fund_b["instrument_id"], 100)
            weights_a: dict[str, float] = {}
            weights_b: dict[str, float] = {}
            for row in resolved_a["rows"]:
                weights_a[row["issuer_id"]] = weights_a.get(row["issuer_id"], 0) + row["weight_pct"]
            for row in resolved_b["rows"]:
                weights_b[row["issuer_id"]] = weights_b.get(row["issuer_id"], 0) + row["weight_pct"]
            shared = sorted(weights_a.keys() & weights_b.keys())
            minimum = sum(min(weights_a[key], weights_b[key]) for key in shared)
            overlaps.append({"instrument_a": fund_a["instrument_id"], "instrument_b": fund_b["instrument_id"], "status": "COMPLETE" if resolved_a["complete"] and resolved_b["complete"] else "PARTIAL_MINIMUM", "shared_issuer_count": len(shared), "shared_weight_pct_of_fund_a_min": _pct(minimum), "shared_weight_pct_of_fund_b_min": _pct(minimum), "shared_issuer_ids": shared})

    complete = decomposition_complete and source_coverage >= 100 - 1e-6
    if not complete and decomposition_complete:
        reasons.add("SOURCE_COVERAGE_UNDER_100")
    complete &= decomposition_complete
    hhi = sum(row["known_minimum_total_pct"] ** 2 for row in issuers) if complete else None
    concentration = {"top_3_issuer_weight_pct": _pct(sum(row["known_minimum_total_pct"] for row in issuers[:3])) if complete else None, "top_5_issuer_weight_pct": _pct(sum(row["known_minimum_total_pct"] for row in issuers[:5])) if complete else None, "top_10_issuer_weight_pct": _pct(sum(row["known_minimum_total_pct"] for row in issuers[:10])) if complete else None, "hhi_pct_squared": _pct(hhi) if hhi is not None else None, "effective_issuer_count": _pct(10000 / hhi) if hhi else None, "completeness": "COMPLETE_ISSUER_DECOMPOSITION" if complete else "BLOCKED_INCOMPLETE_ISSUER_DECOMPOSITION"}
    factor_views = [{"factor": factor, "exposure_pct": _pct(weight), "overlap_allowed": True} for factor, weight in sorted(factor_weights.items(), key=lambda item: (-item[1], item[0]))]

    previous = arguments.get("previous_snapshot")
    comparison: dict[str, Any] = {"status": "NOT_REQUESTED", "deltas": []}
    if previous is not None:
        previous_day = _day(previous["as_of"])
        compatibility_reasons = []
        if previous.get("method") != "issuer-lookthrough-v1": compatibility_reasons.append("METHOD_MISMATCH")
        if previous.get("portfolio_id") != portfolio_id: compatibility_reasons.append("PORTFOLIO_MISMATCH")
        if previous.get("base_currency") != base_currency: compatibility_reasons.append("CURRENCY_MISMATCH")
        if previous_day >= as_of_day: compatibility_reasons.append("INVALID_OR_NONPRIOR_AS_OF")
        if previous.get("status") != "COMPLETE" or not previous.get("decomposition_complete") or previous.get("source_coverage_pct") != 100 or not complete: compatibility_reasons.append("INCOMPLETE_DECOMPOSITION")
        if compatibility_reasons:
            comparison = {"status": "NOT_COMPARABLE", "reasons": compatibility_reasons, "deltas": []}
        else:
            previous_weights = {row["issuer_id"]: row["known_minimum_total_pct"] for row in previous["issuers"]}
            current_weights = {row["issuer_id"]: row["known_minimum_total_pct"] for row in issuers}
            comparison = {"status": "COMPARABLE", "previous_as_of": previous["as_of"], "method": "issuer-lookthrough-v1", "deltas": [{"issuer_id": key, "previous_weight_pct": _pct(previous_weights.get(key, 0)), "current_weight_pct": _pct(current_weights.get(key, 0)), "delta_pct_points": _pct(current_weights.get(key, 0) - previous_weights.get(key, 0))} for key in sorted(previous_weights.keys() | current_weights.keys())]}

    shocks = arguments.get("factor_shocks") or []
    if len({row["factor"] for row in shocks}) != len(shocks):
        raise ValueError("factor shocks require unique factors")
    stress_rows = []
    for shock in shocks:
        factor_weight = factor_weights.get(shock["factor"])
        if factor_weight is None or not isfinite(shock["shock_pct"]) or not -100 <= shock["shock_pct"] <= 100:
            stress_rows.append({"scenario_id": shock["scenario_id"], "factor": shock["factor"], "status": "NOT_COMPUTED_UNKNOWN_FACTOR", "impact_pct_points": None, "impact_pln": None})
            continue
        impact = factor_weight * shock["shock_pct"] / 100
        stress_rows.append({"scenario_id": shock["scenario_id"], "factor": shock["factor"], "status": "KNOWN_EXPOSURE_SCENARIO" if complete else "PARTIAL_MINIMUM_SCENARIO", "exposure_pct": _pct(factor_weight), "assumed_shock_pct": shock["shock_pct"], "impact_pct_points": _pct(impact), "impact_pln": _pct(impact * total_pln / 100) if total_pln is not None else None, "probabilities": None})

    preview: dict[str, Any] = {"status": "NOT_REQUESTED"}
    if arguments.get("scenario_positions"):
        scenario_args = {**arguments, "positions": arguments["scenario_positions"], "scenario_positions": None, "previous_snapshot": None, "factor_shocks": None}
        scenario = calculate_issuer_exposure(scenario_args)
        scenario_issuers = {row["issuer_id"]: row["known_minimum_total_pct"] for row in scenario["issuers"]}
        current_issuers = {row["issuer_id"]: row["known_minimum_total_pct"] for row in issuers}
        scenario_factors = {row["factor"]: row["exposure_pct"] for row in scenario["overlapping_factor_views"]}
        current_factors = {row["factor"]: row["exposure_pct"] for row in factor_views}
        preview = {"status": "COMPARABLE_PREVIEW" if complete and scenario["decomposition_complete"] else "PARTIAL_PREVIEW", "preview_basis": "CALLER_SUPPLIED_POST_TRADE_POSITIONS", "scenario_status": scenario["status"], "issuer_deltas": [{"issuer_id": key, "current_weight_pct": _pct(current_issuers.get(key, 0)), "scenario_weight_pct": _pct(scenario_issuers.get(key, 0)), "delta_pct_points": _pct(scenario_issuers.get(key, 0) - current_issuers.get(key, 0)), "delta_pln": _pct((scenario_issuers.get(key, 0) - current_issuers.get(key, 0)) * total_pln / 100) if total_pln is not None else None} for key in sorted(current_issuers.keys() | scenario_issuers.keys())], "factor_deltas": [{"factor": key, "current_exposure_pct": _pct(current_factors.get(key, 0)), "scenario_exposure_pct": _pct(scenario_factors.get(key, 0)), "delta_pct_points": _pct(scenario_factors.get(key, 0) - current_factors.get(key, 0)), "overlapping_non_additive": True} for key in sorted(current_factors.keys() | scenario_factors.keys())], "current_concentration": _concentration(issuers, complete), "scenario_concentration": scenario["concentration"], "position_review_threshold_pct": 8, "scenario_issuers_over_review_threshold": [row["issuer_id"] for row in scenario["issuers"] if row["known_minimum_total_pct"] > 8], "threshold_is_review_only": True, "threshold_check_is_minimum_only": not scenario["decomposition_complete"], "trades_executed": False}

    return {"method": "issuer-lookthrough-v1", "status": "COMPLETE" if decomposition_complete else "PARTIAL_MINIMUM", "as_of": as_of, "portfolio_id": portfolio_id, "base_currency": base_currency, "portfolio_value_pln": total_pln, "source_coverage_pct": _pct(min(100, source_coverage)), "decomposition_complete": decomposition_complete, "decomposition_reasons": sorted(reasons), "issuers": issuers, "funds": fund_rows, "etf_overlap": overlaps, "snapshot_comparison": comparison, "pre_trade_preview": preview, "overlapping_factor_views": factor_views, "stress": {"status": "SCENARIO_ONLY" if shocks else "NOT_REQUESTED", "results": stress_rows, "aggregate_result": "NOT_SUMMED_OVERLAPPING_FACTORS"}, "concentration": concentration, "limitations": ["Input-only preview; no portfolio retrieval or persistence.", "Issuer exposure is counted once per position and constituent; sector rows are not issuer constituents.", "Factor views overlap and must not be added together.", "No forecast, probability, recommendation, transaction or policy decision is produced."]}
