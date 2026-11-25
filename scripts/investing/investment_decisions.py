"""Pure, read-only Investment OS decision synthesis for typed evidence projections."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from scripts.investing.investment_contracts import _schema_errors, validate_exchange

INPUT_SCHEMA = Path("schemas/investing/investment-decision-input-v1.schema.json")
OUTPUT_SCHEMA = Path("schemas/investing/investment-decision-v1.schema.json")
EXPECTED_PRODUCERS = {
    "quality": "security-underwriting",
    "eligibility": "investment-policy-design",
    "thesis": "thesis-challenge",
    "valuation": "valuation-scenario-review",
    "portfolio": "portfolio-state-review",
    "timing": "technical-structure",
}
EXPECTED_PRODUCER_VERSIONS = {
    "security-underwriting": "0.6.0",
    "investment-policy-design": "0.1.0",
    "thesis-challenge": "0.1.2",
    "valuation-scenario-review": "0.4.0",
    "portfolio-state-review": "0.7.2",
    "technical-structure": "0.1.1",
}


def _load_schema(root: Path, path: Path) -> dict[str, Any]:
    return json.loads((root / path).read_text(encoding="utf-8"))


def _gate(gate_id: str, status: str, reason: str, signal: dict[str, Any] | None = None) -> dict[str, Any]:
    signal = signal or {}
    return {
        "gate_id": gate_id,
        "status": status,
        "reason_codes": [reason] if reason else [],
        "source_result_refs": [signal["result_id"]] if signal.get("result_id") else [],
        "claim_ids": signal.get("claim_ids", []),
        "evidence_ids": signal.get("evidence_ids", []),
        "conflict_ids": signal.get("conflict_ids", []),
        "policy_rule_ref": signal.get("policy_rule_ref"),
    }


def _reference_errors(context: dict[str, Any], results: list[dict[str, Any]], signals: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    by_id = {result.get("result_id"): result for result in results if isinstance(result, dict)}
    for name, signal in signals.items():
        expected = EXPECTED_PRODUCERS[name]
        result = by_id.get(signal["result_id"])
        if result is None:
            errors.append(f"{name} signal references an unknown result")
            continue
        if signal["producer_skill_id"] != expected or result["producer"]["skill_id"] != expected:
            errors.append(f"{name} signal has an unapproved producer")
        if result["producer"]["version"] != EXPECTED_PRODUCER_VERSIONS[expected]:
            errors.append(f"{name} signal uses an unsupported producer version")
        if signal["producer_skill_id"] not in context["requested_skills"]:
            errors.append(f"{name} producer was not requested by AnalysisContext")
        claims = {finding["claim_id"]: finding for finding in result["findings"]}
        evidence = {ref["source_id"] for ref in result["evidence_refs"]}
        if not signal["claim_ids"] or any(claim_id not in claims for claim_id in signal["claim_ids"]):
            errors.append(f"{name} signal has missing or dangling claim references")
        if not signal["evidence_ids"] or any(source_id not in evidence for source_id in signal["evidence_ids"]):
            errors.append(f"{name} signal has missing or dangling evidence references")
        claim_evidence = {
            evidence_id
            for claim_id in signal["claim_ids"]
            if claim_id in claims
            for evidence_id in claims[claim_id]["evidence_ids"] + claims[claim_id]["counterevidence_ids"]
        }
        if any(source_id not in claim_evidence for source_id in signal["evidence_ids"]):
            errors.append(f"{name} signal evidence is not linked to its referenced claims")
        for claim_id in signal["claim_ids"]:
            if claim_id in claims:
                claim_sources = set(claims[claim_id]["evidence_ids"] + claims[claim_id]["counterevidence_ids"])
                if not claim_sources.intersection(signal["evidence_ids"]):
                    errors.append(f"{name} signal does not cite evidence for claim {claim_id}")
        if result["execution_status"] not in {"SUCCESS", "PARTIAL"}:
            errors.append(f"{name} signal producer did not return an executable result")
        if result["payload_type"] == "LEGACY_OPAQUE":
            errors.append(f"{name} signal cannot be inferred from an opaque legacy payload")
        if result["payload_type"] != "INVESTMENT_DECISION_SIGNAL" or result["payload_schema_version"] != "1.0":
            errors.append(f"{name} signal does not use the supported decision-signal payload version")
        payload = result["payload"].get("decision_signal_v1") if isinstance(result["payload"], dict) else None
        compared_fields = ["state", "claim_ids", "evidence_ids"] + (["security_attractiveness"] if name == "valuation" else [])
        if name == "quality" and signal["state"] == "CONFLICTED":
            compared_fields.append("conflict_ids")
        if name == "valuation":
            compared_fields.append("asset_path")
        if name == "portfolio":
            compared_fields.extend(["position_state", "position_snapshot_complete", "policy_rule_ref", "continuation_rule_ref"])
        if name == "eligibility":
            compared_fields.append("policy_rule_ref")
        if not isinstance(payload, dict) or payload.get("signal_type") != name or any(payload.get(field) != signal.get(field) for field in compared_fields):
            errors.append(f"{name} typed signal does not match the producer-owned result payload")
        verified_required = {
            "quality": signal["state"] in {"PASS", "WARN", "BLOCK"},
            "eligibility": signal["state"] in {"ELIGIBLE", "INELIGIBLE"},
            "thesis": signal["state"] in {"SURVIVES", "WEAKENED", "INVALIDATED"},
            "valuation": signal["state"] == "READY" and signal["security_attractiveness"] != "UNRESOLVED",
            "portfolio": signal["state"] in {"IN_POLICY", "REVIEW_THRESHOLD", "HARD_CAP_BREACH"},
            "timing": signal["state"] in {"SUPPORTIVE", "ADVERSE", "NEUTRAL"},
        }[name]
        if verified_required and any(claims[cid]["evidence_status"] != "VERIFIED" for cid in signal["claim_ids"] if cid in claims):
            errors.append(f"{name} decision-critical signal is not backed by VERIFIED claim evidence")
        if name in {"eligibility", "portfolio"} and not context.get("policy_version_ref"):
            errors.append(f"{name} signal requires the context policy_version_ref")
    if signals["portfolio"]["state"] != "NOT_APPLICABLE" and not context.get("portfolio_snapshot_ref"):
        errors.append("portfolio signal requires a context portfolio_snapshot_ref")
    if signals["portfolio"]["state"] != "NOT_APPLICABLE" and signals["portfolio"].get("policy_rule_ref") is None:
        errors.append("portfolio signal requires a policy rule reference")
    if signals["portfolio"].get("continuation_rule_ref") and signals["portfolio"]["state"] != "IN_POLICY":
        errors.append("continuation rule is only applicable to an IN_POLICY portfolio state")
    if signals["portfolio"].get("continuation_rule_ref") and not context.get("policy_version_ref"):
        errors.append("continuation rule requires the context policy version")
    instrument = context["instrument"]
    industry = (instrument.get("industry") or "").lower()
    expected_path = "ETF" if instrument["type"] == "ETF" else ("BANK" if "bank" in industry else ("EQUITY" if instrument["type"] == "EQUITY" else "GENERAL"))
    if signals["valuation"]["asset_path"] != expected_path:
        errors.append("valuation signal does not use the instrument-specific analysis path")
    return errors


def _identity_output(context: dict[str, Any], position_state: str) -> dict[str, Any]:
    horizon = context.get("horizon")
    if (
        not isinstance(horizon, dict)
        or not isinstance(horizon.get("min_months"), int)
        or isinstance(horizon.get("min_months"), bool)
        or not isinstance(horizon.get("max_months"), int)
        or isinstance(horizon.get("max_months"), bool)
        or not isinstance(horizon.get("objective"), str)
        or not horizon.get("objective", "").strip()
        or horizon.get("min_months", -1) < 0
        or horizon.get("max_months", -1) < 0
        or horizon.get("min_months", 0) > horizon.get("max_months", 0)
    ):
        horizon = {"min_months": 0, "max_months": 0, "objective": "unresolved"}
    as_of = context.get("as_of", "1970-01-01T00:00:00Z")
    if not isinstance(as_of, str):
        as_of = "1970-01-01T00:00:00Z"
    else:
        try:
            parsed_as_of = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
            if parsed_as_of.tzinfo is None:
                raise ValueError("timezone required")
        except ValueError:
            as_of = "1970-01-01T00:00:00Z"
    analysis_id = context.get("analysis_id")
    if not isinstance(analysis_id, str) or not analysis_id.strip():
        analysis_id = "UNKNOWN"
    instrument = context.get("instrument")
    instrument_id = instrument.get("canonical_id") if isinstance(instrument, dict) else None
    if not isinstance(instrument_id, str) or not instrument_id.strip():
        instrument_id = "UNKNOWN"
    policy_version_ref = context.get("policy_version_ref")
    if not isinstance(policy_version_ref, str):
        policy_version_ref = None
    return {
        "schema_version": "1.0",
        "analysis_id": analysis_id,
        "instrument_id": instrument_id,
        "policy_version_ref": policy_version_ref,
        "as_of": as_of,
        "horizon": horizon,
        "decision_rule_version": "1.0",
        "position_state": position_state if isinstance(position_state, str) and position_state in {"HELD", "NOT_HELD", "UNKNOWN"} else "UNKNOWN",
        "research_state": "VERIFY",
        "thesis_state": "UNRESOLVED",
        "business_quality_state": "UNRESOLVED",
        "valuation_state": "UNRESOLVED",
        "security_attractiveness_state": "UNRESOLVED",
        "portfolio_fit_state": "UNRESOLVED",
        "portfolio_action": "UNRESOLVED",
        "timing_state": "N/A",
        "gate_results": [],
        "advisory_recommendation": None,
        "reason_codes": [],
        "uncertainties": [],
        "conditions_to_upgrade": [],
        "conditions_to_downgrade": [],
        "owner_approval_required": True,
        "owner_decision": None,
        "execution_authorized": False,
        "source_result_refs": [],
        "numeric_sizing_blocked": True,
    }


def _validate_and_trace(decision_input: object, root: Path) -> tuple[dict[str, Any], list[str]]:
    context = decision_input.get("context", {}) if isinstance(decision_input, dict) else {}
    results = decision_input.get("results", []) if isinstance(decision_input, dict) else []
    safe_context = context if isinstance(context, dict) else {}
    position = decision_input.get("position_state", "UNKNOWN") if isinstance(decision_input, dict) else "UNKNOWN"
    output = _identity_output(safe_context, position)
    errors: list[str] = []
    if not isinstance(decision_input, dict):
        errors.append("decision input must be an object")
        return output, errors
    errors.extend(f"input {e}" for e in _schema_errors(decision_input, _load_schema(root, INPUT_SCHEMA)))
    if not isinstance(results, list):
        errors.append("results must be an array")
        return output, errors
    errors.extend(validate_exchange(context, results, root=root))
    if errors:
        return output, errors
    signals = decision_input["signals"]
    errors.extend(_reference_errors(context, results, signals))
    position = decision_input["position_state"]
    if signals["portfolio"]["position_state"] != position:
        errors.append("position state must match the portfolio producer result")
    if position in {"HELD", "NOT_HELD"} and not context.get("portfolio_snapshot_ref"):
        errors.append("known position state requires a context portfolio snapshot")
    return output, errors


def synthesize_decision(decision_input: object, *, root: Path) -> dict[str, Any]:
    """Return deterministic advisory synthesis; never retrieves, writes, sizes, or trades."""
    output, errors = _validate_and_trace(decision_input, root)
    if errors:
        output["gate_results"] = [_gate("G0", "BLOCK", "INVALID_CONTEXT_OR_REFERENCES")]
        output["gate_results"].extend(_gate(f"G{i}", "UNRESOLVED", "PREREQUISITE_BLOCKED") for i in range(1, 7))
        output["reason_codes"] = sorted(set(errors))
        output["uncertainties"] = ["decision input or source references failed validation"]
        Draft202012Validator(_load_schema(root, OUTPUT_SCHEMA), format_checker=FormatChecker()).validate(output)
        return output

    # All source documents have passed the #753 contract before this point.
    signals = decision_input["signals"]
    position = decision_input["position_state"]
    quality = signals["quality"]["state"]
    eligibility = signals["eligibility"]["state"]
    thesis = signals["thesis"]["state"]
    valuation_state = signals["valuation"]["state"]
    attractiveness = signals["valuation"]["security_attractiveness"]
    portfolio = signals["portfolio"]["state"]
    timing = signals.get("timing")

    g0 = _gate("G0", "PASS", "IDENTITY_CUTOFF_AND_LINEAGE_VALID")
    g1_status = {"PASS": "PASS", "WARN": "WARN", "BLOCK": "BLOCK", "VERIFY": "UNRESOLVED", "CONFLICTED": "UNRESOLVED", "UNRESOLVED": "UNRESOLVED"}[quality]
    g1_reason = {"PASS": "CRITICAL_EVIDENCE_VERIFIED", "WARN": "EVIDENCE_LIMITATIONS", "BLOCK": "FINANCIAL_QUALITY_BLOCK", "VERIFY": "DECISION_CRITICAL_EVIDENCE_UNVERIFIED", "CONFLICTED": "DECISION_CRITICAL_EVIDENCE_CONFLICT", "UNRESOLVED": "EVIDENCE_STATE_UNRESOLVED"}[quality]
    g1 = _gate("G1", g1_status, g1_reason, signals["quality"])
    g2_status = {"ELIGIBLE": "PASS", "INELIGIBLE": "BLOCK", "UNRESOLVED": "UNRESOLVED"}[eligibility]
    g2_reason = {"ELIGIBLE": "POLICY_ELIGIBILITY_CONFIRMED", "INELIGIBLE": "POLICY_OR_INVESTABILITY_BLOCK", "UNRESOLVED": "ELIGIBILITY_UNKNOWN"}[eligibility]
    g2 = _gate("G2", g2_status, g2_reason, signals["eligibility"])
    thesis_state = "UNRESOLVED" if thesis == "INSUFFICIENT_EVIDENCE" else thesis
    g3_status = "UNRESOLVED" if thesis == "INSUFFICIENT_EVIDENCE" else "PASS"
    g3 = _gate("G3", g3_status, "THESIS_CHALLENGE_INSUFFICIENT" if thesis == "INSUFFICIENT_EVIDENCE" else f"THESIS_{thesis}", signals["thesis"])
    if g1_status in {"BLOCK", "UNRESOLVED"}:
        g4_status, g4_reason = "UNRESOLVED", "VALUATION_PREREQUISITE_BLOCKED_BY_G1"
    else:
        g4_status = {"READY": "PASS", "BLOCKED": "BLOCK", "UNRESOLVED": "UNRESOLVED"}[valuation_state]
        g4_reason = {"READY": f"SECURITY_ATTRACTIVENESS_{attractiveness}", "BLOCKED": "VALUATION_METHOD_BLOCK", "UNRESOLVED": "VALUATION_UNRESOLVED"}[valuation_state]
    g4 = _gate("G4", g4_status, g4_reason, signals["valuation"])
    g5_status = {"IN_POLICY": "PASS", "REVIEW_THRESHOLD": "WARN", "HARD_CAP_BREACH": "BLOCK", "UNRESOLVED": "UNRESOLVED", "NOT_APPLICABLE": "N/A"}[portfolio]
    g5_reason = {"IN_POLICY": "POLICY_IN_RANGE", "REVIEW_THRESHOLD": "POLICY_REVIEW_THRESHOLD", "HARD_CAP_BREACH": "POLICY_BREACH_REDUCTION_REVIEW", "UNRESOLVED": "PORTFOLIO_FIT_UNKNOWN", "NOT_APPLICABLE": "PORTFOLIO_NOT_APPLICABLE"}[portfolio]
    if position == "UNKNOWN" or not signals["portfolio"]["position_snapshot_complete"]:
        g5_status = "UNRESOLVED"
        g5_reason = "POSITION_STATE_UNKNOWN" if position == "UNKNOWN" else "POSITION_SNAPSHOT_INCOMPLETE"
    g5 = _gate("G5", g5_status, g5_reason, signals["portfolio"])
    if timing is None:
        g6 = _gate("G6", "N/A", "NO_TIMING_SIGNAL_REQUESTED")
    else:
        g6_status = "UNRESOLVED" if timing["state"] == "UNRESOLVED" else ("N/A" if timing["state"] == "NOT_APPLICABLE" else "PASS")
        g6 = _gate("G6", g6_status, f"TIMING_{timing['state']}", timing)
    gates = [g0, g1, g2, g3, g4, g5, g6]
    output["gate_results"] = gates
    output["thesis_state"] = thesis_state
    output["business_quality_state"] = quality
    output["valuation_state"] = valuation_state if g4["status"] == "PASS" else ("BLOCKED" if g4["status"] == "BLOCK" else "UNRESOLVED")
    output["security_attractiveness_state"] = attractiveness if g4["status"] == "PASS" else "UNRESOLVED"
    output["portfolio_fit_state"] = "UNRESOLVED" if g5_status == "UNRESOLVED" else portfolio
    output["timing_state"] = timing["state"] if timing else "N/A"
    output["source_result_refs"] = sorted({ref for gate in gates for ref in gate["source_result_refs"]})
    output["numeric_sizing_blocked"] = True
    if g1_status == "UNRESOLVED":
        output["research_state"] = "VERIFY"
    elif g2_status == "BLOCK" or (thesis == "INVALIDATED" and position == "NOT_HELD"):
        output["research_state"] = "REJECT"
    elif g1_status != "PASS" or g2_status != "PASS" or g3_status != "PASS" or g4_status != "PASS" or g5_status in {"BLOCK", "UNRESOLVED"}:
        output["research_state"] = "RESEARCH"
    else:
        output["research_state"] = "RESEARCHED"
    reasons = [code for gate in gates for code in gate["reason_codes"]]
    recommendation = None
    if g0["status"] == "PASS" and g1["status"] == "PASS":
        if g2["status"] == "BLOCK":
            output["research_state"] = "REJECT"
            recommendation = "AVOID" if position == "NOT_HELD" else None
        elif g2["status"] == "PASS" and g3["status"] == "PASS":
            if thesis == "INVALIDATED":
                recommendation = "AVOID" if position == "NOT_HELD" else "SELL_REVIEW"
            elif position == "NOT_HELD" and attractiveness == "UNFAVORABLE" and portfolio == "IN_POLICY" and g4["status"] == "PASS" and g5["status"] == "PASS":
                recommendation = "WAIT"
            elif position == "HELD" and thesis in {"SURVIVES", "WEAKENED"} and attractiveness in {"ATTRACTIVE", "FAIR"} and portfolio == "IN_POLICY" and g4["status"] == "PASS" and g5["status"] == "PASS" and signals["portfolio"].get("continuation_rule_ref"):
                recommendation = "HOLD"
            elif position == "HELD" and portfolio == "REVIEW_THRESHOLD" and thesis != "INVALIDATED" and g5["status"] == "WARN":
                recommendation = "TRIM_REVIEW"
    if portfolio == "HARD_CAP_BREACH" and g5_status == "BLOCK":
        recommendation = None
        reasons.append("POLICY_BREACH_REDUCTION_REVIEW")
    if quality != "PASS":
        recommendation = None
    if eligibility == "UNRESOLVED" or thesis == "INSUFFICIENT_EVIDENCE" or valuation_state == "UNRESOLVED" or portfolio == "UNRESOLVED":
        recommendation = None
    if position == "UNKNOWN":
        recommendation = None
    if position == "HELD" and g5["status"] not in {"PASS", "WARN", "BLOCK"}:
        recommendation = None
    if recommendation is None and g1["status"] == "PASS" and g2["status"] == "PASS" and g3["status"] == "PASS" and g4["status"] == "PASS" and g5["status"] == "PASS":
        if attractiveness in {"ATTRACTIVE", "FAIR"} and position == "NOT_HELD":
            reasons.append("BUY_ACCUMULATE_MAPPING_NOT_APPROVED")
        elif attractiveness in {"ATTRACTIVE", "FAIR"} and position == "HELD" and not signals["portfolio"].get("continuation_rule_ref"):
            reasons.append("HOLD_REQUIRES_APPROVED_CONTINUATION_RULE")
    output["advisory_recommendation"] = recommendation
    output["portfolio_action"] = {
        "TRIM_REVIEW": "TRIM_REVIEW",
        "SELL_REVIEW": "SELL_REVIEW",
        "AVOID": "AVOID",
    }.get(recommendation, "REDUCTION_REVIEW" if portfolio == "HARD_CAP_BREACH" and g5["status"] == "BLOCK" else ("UNRESOLVED" if g5["status"] == "UNRESOLVED" else "NONE"))
    output["reason_codes"] = sorted(set(reasons))
    if recommendation in {"WAIT", "HOLD", "TRIM_REVIEW", "SELL_REVIEW"} or output["portfolio_action"] == "REDUCTION_REVIEW" or "BUY_ACCUMULATE_MAPPING_NOT_APPROVED" in reasons or "HOLD_REQUIRES_APPROVED_CONTINUATION_RULE" in reasons:
        output["research_state"] = "WATCH"
    if recommendation is None:
        output["uncertainties"] = sorted(set(reasons))
    if recommendation == "WAIT":
        output["conditions_to_upgrade"] = ["valuation specialist supplies an approved favorable valuation state at a later eligible as_of"]
    if recommendation in {"HOLD", "TRIM_REVIEW", "SELL_REVIEW"}:
        output["conditions_to_downgrade"] = ["policy or thesis owner review changes the referenced state"]
    schema = _load_schema(root, OUTPUT_SCHEMA)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(output)
    return output
