"""Deterministic evidence-gated financial comparisons."""
from datetime import date
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Mapping
class Quality(str,Enum):
    VERIFIED="VERIFIED"; PROVISIONAL="PROVISIONAL"; BLOCKED="BLOCKED"
@dataclass(frozen=True)
class Metric:
    name:str; definition:str; value:Decimal|None; unit:str; published_at:str; source:str; quality:Quality
def valid_date(value):
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except (ValueError, TypeError):
        return False

def valid_inputs(metrics, as_of):
    return valid_date(as_of) and all(
        valid_date(x.published_at) and x.quality in (Quality.VERIFIED, Quality.PROVISIONAL)
        and x.name.strip() and x.definition.strip() for x in metrics)

def compare(company:Metric,industry:Metric,as_of:str):
    if not valid_inputs((company, industry), as_of):
        return {"status":"BLOCKED", "reason":"INVALID_METADATA", "delta":None}
    if any(x.value is None or not x.value.is_finite() or not x.source or x.quality==Quality.BLOCKED for x in (company,industry)):
        return {"status":"BLOCKED","reason":"MISSING_INPUT","delta":None}
    if any(x.published_at>as_of for x in (company,industry)):
        return {"status":"BLOCKED","reason":"LOOKAHEAD","delta":None}
    if any((x.name,x.definition,x.unit)!=(company.name,company.definition,company.unit) for x in (industry,)):
        return {"status":"BLOCKED","reason":"INCOMPATIBLE_DEFINITION","delta":None}
    status="PROVISIONAL" if any(x.quality==Quality.PROVISIONAL for x in (company,industry)) else "VERIFIED"
    return {"status":status,"delta":str(company.value-industry.value)}
def percentile(value:Decimal,peers:list[Decimal],higher_is_better=True):
    if len(peers)<5 or not value.is_finite() or any(not x.is_finite() for x in peers): return None
    result=(Decimal(sum(x<value for x in peers))+Decimal(sum(x==value for x in peers))/2)/len(peers)
    return result if higher_is_better else 1-result
def economic_spread(roic:Metric,wacc:Metric,as_of:str):
    if (not valid_inputs((roic, wacc), as_of)
            or roic.name != "roic" or wacc.name != "wacc"):
        return {"status":"BLOCKED", "value":None}
    if any(x.value is None or not x.value.is_finite() or x.quality==Quality.BLOCKED or not x.source or x.published_at>as_of or x.unit!="fraction" for x in (roic,wacc)):
        return {"status":"BLOCKED","value":None}
    status="PROVISIONAL" if any(x.quality==Quality.PROVISIONAL for x in (roic,wacc)) else "VERIFIED"
    return {"status":status,"value":str(roic.value-wacc.value)}


# These are transparent, provisional research-triage weights. The factors are
# separately derived from dated evidence upstream; this function only combines
# normalized 0..1 factor scores. A score is not a probability or a trade signal.
OPPORTUNITY_MODEL_VERSION = "opportunity-score-v0.1-provisional"
MIN_EVIDENCE_CONFIDENCE = Decimal("0.50")
SCORE_QUANTUM = Decimal("0.01")
RANK_GAP_QUANTUM = Decimal("0.001")

HORIZON_WEIGHTS: dict[str, dict[str, tuple[Decimal, int]]] = {
    "1-3m": {
        "catalyst_timing": (Decimal("0.22"), 45),
        "estimate_revisions": (Decimal("0.18"), 90),
        "valuation_expectations": (Decimal("0.15"), 90),
        "price_setup": (Decimal("0.15"), 30),
        "scenario_asymmetry": (Decimal("0.20"), 90),
        "cycle_resilience": (Decimal("0.10"), 180),
    },
    "6-12m": {
        "scenario_asymmetry": (Decimal("0.23"), 180),
        "valuation_expectations": (Decimal("0.22"), 180),
        "estimate_revisions": (Decimal("0.18"), 120),
        "business_quality": (Decimal("0.17"), 365),
        "risk_resilience": (Decimal("0.10"), 180),
        "cycle_resilience": (Decimal("0.10"), 365),
    },
    ">3y": {
        "growth_durability": (Decimal("0.24"), 365),
        "business_quality": (Decimal("0.22"), 365),
        "reinvestment_returns": (Decimal("0.18"), 365),
        "valuation_expectations": (Decimal("0.16"), 180),
        "balance_sheet_resilience": (Decimal("0.10"), 180),
        "cycle_resilience": (Decimal("0.10"), 730),
    },
}


@dataclass(frozen=True)
class FactorEvidence:
    """One normalized factor with the provenance needed for score gating."""

    value: Decimal
    confidence: Decimal
    as_of_date: str
    source_ids: tuple[str, ...]
    definition: str
    normalization_profile: str
    quality: Quality = Quality.VERIFIED


def _score_band(score: Decimal) -> str:
    if score >= Decimal("0.80"):
        return "VERY_ATTRACTIVE"
    if score >= Decimal("0.65"):
        return "ATTRACTIVE"
    if score >= Decimal("0.45"):
        return "NEUTRAL_WATCH"
    if score >= Decimal("0.25"):
        return "WEAK"
    return "UNFAVORABLE"


def _research_action(score: Decimal) -> str:
    if score >= Decimal("0.65"):
        return "PRIORITIZE"
    if score >= Decimal("0.45"):
        return "WATCH"
    if score >= Decimal("0.25"):
        return "DEPRIORITIZE"
    return "REJECT"


def score_opportunity(
    candidate_id: str,
    horizon: str,
    evidence: Mapping[str, FactorEvidence],
    as_of: str,
    *,
    model_version: str = OPPORTUNITY_MODEL_VERSION,
    weights: Mapping[str, tuple[Decimal, int]] | None = None,
) -> dict:
    """Score a research candidate for one horizon, failing closed on weak inputs.

    `value` and `confidence` must be precomputed by a provenance-aware upstream
    analysis. Missing, future-dated, stale, incompatible, or low-confidence
    factors block the score; they are never filled from the other horizons.
    `weights` exists for explicit sensitivity tests; callers must use a new
    `model_version` for any non-default profile.
    """
    profile = weights if weights is not None else HORIZON_WEIGHTS.get(horizon)
    if (not isinstance(candidate_id, str) or not candidate_id.strip()
            or not isinstance(model_version, str) or not model_version.strip()
            or not valid_date(as_of) or horizon not in HORIZON_WEIGHTS
            or not isinstance(evidence, Mapping) or not isinstance(profile, Mapping)):
        return {"candidate_id": candidate_id, "horizon": horizon, "model_version": model_version,
                "status": "NOT_SCORED", "reason": "INVALID_PROFILE_OR_AS_OF", "score": None}
    if (set(profile) != set(HORIZON_WEIGHTS[horizon]) or any(
        not isinstance(weight, Decimal) or not weight.is_finite() or weight <= 0
        or not isinstance(max_age, int) or max_age < 0
        for weight, max_age in profile.values()
    ) or sum((item[0] for item in profile.values()), Decimal("0")) != Decimal("1")
            or (weights is not None and profile != HORIZON_WEIGHTS[horizon]
                and model_version == OPPORTUNITY_MODEL_VERSION)):
        return {"candidate_id": candidate_id, "horizon": horizon, "model_version": model_version,
                "status": "NOT_SCORED", "reason": "INVALID_WEIGHT_PROFILE", "score": None}

    target_date = date.fromisoformat(as_of)
    missing: list[str] = []
    stale: list[str] = []
    future: list[str] = []
    weak: list[str] = []
    invalid: list[str] = []
    valid: dict[str, FactorEvidence] = {}
    for name, (weight, max_age) in profile.items():
        item = evidence.get(name)
        if item is None:
            missing.append(name)
            continue
        if not isinstance(item, FactorEvidence):
            invalid.append(name)
            continue
        try:
            item_quality = Quality(item.quality)
        except (ValueError, TypeError):
            invalid.append(name)
            continue
        if (not isinstance(item.as_of_date, str) or not valid_date(item.as_of_date)
                or not isinstance(item.definition, str) or not item.definition.strip()
                or not isinstance(item.normalization_profile, str) or not item.normalization_profile.strip()
                or not isinstance(item.source_ids, tuple) or not item.source_ids
                or any(not isinstance(source_id, str) or not source_id.strip() for source_id in item.source_ids)
                or not isinstance(item.value, Decimal) or not isinstance(item.confidence, Decimal)
                or not item.value.is_finite() or not Decimal("0") <= item.value <= Decimal("1")
                or not item.confidence.is_finite() or not Decimal("0") <= item.confidence <= Decimal("1")
                or item_quality == Quality.BLOCKED):
            invalid.append(name)
            continue
        observed = date.fromisoformat(item.as_of_date)
        age_days = (target_date - observed).days
        if age_days < 0:
            future.append(name)
            continue
        if age_days > max_age:
            stale.append(name)
            continue
        if item.confidence < MIN_EVIDENCE_CONFIDENCE:
            weak.append(name)
            continue
        valid[name] = item

    completeness = sum((profile[name][0] for name in valid), Decimal("0"))
    confidence = None
    if valid and completeness > 0:
        confidence = sum(
            (profile[name][0] * item.confidence * (Decimal("1") if Quality(item.quality) == Quality.VERIFIED else Decimal("0.70"))
             for name, item in valid.items()), Decimal("0")
        ) / completeness
    reasons = {
        "missing_factors": missing,
        "stale_factors": stale,
        "future_dated_factors": future,
        "weak_evidence_factors": weak,
        "invalid_factors": invalid,
    }
    if missing or stale or future or weak or invalid:
        return {"candidate_id": candidate_id, "horizon": horizon, "model_version": model_version,
                "status": "NOT_SCORED", "reason": "EVIDENCE_GATE", "score": None,
                "completeness": str(completeness.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_UP)),
                "confidence": (str(confidence.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_UP)) if confidence is not None else None),
                **reasons}

    raw = sum((profile[name][0] * item.value for name, item in valid.items()), Decimal("0"))
    score = raw.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_UP)
    status = "PROVISIONAL" if any(Quality(item.quality) == Quality.PROVISIONAL for item in valid.values()) else "SCORED"
    return {
        "candidate_id": candidate_id,
        "horizon": horizon,
        "model_version": model_version,
        "status": status,
        "score": str(score),
        "unrounded_score": format(raw, "f"),
        "score_is_probability": False,
        "score_band": _score_band(raw),
        "research_action": _research_action(raw) if status == "SCORED" else "REVIEW_PROVISIONAL",
        "confidence": str(confidence.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_UP)),
        "completeness": "1.00",
        "factor_contributions": {
            name: format(profile[name][0] * item.value, "f")
            for name, item in valid.items()
        },
        "factor_weights": {name: format(profile[name][0], "f") for name in profile},
        "factor_evidence": {
            name: {
                "value": format(item.value, "f"),
                "confidence": format(item.confidence, "f"),
                "quality": Quality(item.quality).value,
                "as_of_date": item.as_of_date,
                "source_ids": list(item.source_ids),
                "definition": item.definition,
            }
            for name, item in valid.items()
        },
        "normalization_profiles": {name: item.normalization_profile for name, item in valid.items()},
        "factor_source_ids": {name: list(item.source_ids) for name, item in valid.items()},
        "as_of": as_of,
    }


def rank_opportunities(results: list[dict]) -> list[dict]:
    """Rank scoreable rows, preserving blocked rows without assigning ranks."""
    rows = [row for row in results if row.get("status") in {"SCORED", "PROVISIONAL"} and row.get("score") is not None]
    ranked: list[dict] = [
        {**row, "rank_within_horizon": None, "score_difference_to_next": None,
         "ranking_status": "NOT_RANKED", "ranking_reason": row.get("reason", "NOT_SCOREABLE")}
        for row in results if row not in rows
    ]
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for row in rows:
        groups.setdefault((row["horizon"], row["model_version"], row["as_of"]), []).append(row)
    for (horizon, model_version, as_of), group in sorted(groups.items()):
        fingerprints = {
            (
                tuple(sorted(row.get("normalization_profiles", {}).items())),
                tuple(sorted(
                    (name, value.get("definition"))
                    for name, value in row.get("factor_evidence", {}).items()
                )),
            )
            for row in group
        }
        candidate_ids = [row["candidate_id"] for row in group]
        if len(candidate_ids) != len(set(candidate_ids)):
            ranked.extend({**row, "rank_within_horizon": None,
                           "ranking_status": "NOT_COMPARABLE",
                           "ranking_reason": "DUPLICATE_CANDIDATE_ID"}
                          for row in group)
            continue
        if len(fingerprints) > 1:
            ranked.extend({**row, "rank_within_horizon": None,
                           "ranking_status": "NOT_COMPARABLE",
                           "ranking_reason": "INCOMPATIBLE_NORMALIZATION_OR_FACTOR_DEFINITION"}
                          for row in group)
            continue
        group.sort(key=lambda row: (-Decimal(row.get("unrounded_score", row["score"])), row["candidate_id"]))
        for rank, row in enumerate(group, 1):
            score = Decimal(row.get("unrounded_score", row["score"]))
            next_score = Decimal(group[rank]["unrounded_score"]) if rank < len(group) else None
            difference = (str((score - next_score).quantize(RANK_GAP_QUANTUM, rounding=ROUND_HALF_UP))
                          if next_score is not None else None)
            ranked.append({**row, "rank_within_horizon": rank,
                           "score_difference_to_next": difference,
                           "ranking_status": "COMPARABLE"})
    return ranked
