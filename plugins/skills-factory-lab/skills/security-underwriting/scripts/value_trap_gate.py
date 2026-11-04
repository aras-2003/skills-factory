"""Deterministic gates for source quality and explicitly assessed risks.

This helper applies no universal financial thresholds. Inputs are evidence
statuses/flags established by the underwriting workflow, not raw claims inferred
from missing data. Unknown risk flags remain WARN; critical cash-flow defects
fail closed.
"""
from __future__ import annotations

from collections.abc import Mapping


VALID_STATUS = {"VERIFIED", "UNVERIFIED", "CONFLICTED", "SUPPORTED", "UNSUPPORTED", "UNKNOWN"}


def value_trap_gate(evidence: Mapping[str, object]) -> dict[str, object]:
    required_statuses = {
        "primary_cashflow": {"VERIFIED", "UNVERIFIED", "CONFLICTED"},
        "cashflow_normalization": {"SUPPORTED", "UNSUPPORTED", "UNKNOWN"},
    }
    for field, allowed in required_statuses.items():
        value = evidence.get(field)
        if not isinstance(value, str) or value not in VALID_STATUS or value not in allowed:
            raise ValueError(f"{field} must be one of {sorted(allowed)}")

    gates: dict[str, dict[str, object]] = {}
    source_status = str(evidence["primary_cashflow"])
    normalization = str(evidence["cashflow_normalization"])
    if source_status != "VERIFIED":
        gates["cashflow_evidence"] = {
            "status": "BLOCK",
            "reason": f"Critical cash-flow evidence is {source_status}; primary-source verification is required.",
        }
    elif normalization == "UNSUPPORTED":
        gates["cashflow_evidence"] = {
            "status": "BLOCK",
            "reason": "Cash-flow normalization is unsupported; FCF-based valuation is blocked.",
        }
    elif normalization == "UNKNOWN":
        gates["cashflow_evidence"] = {
            "status": "WARN",
            "reason": "Cash-flow normalization is not established; do not use normalized FCF as a decisive signal.",
        }
    else:
        gates["cashflow_evidence"] = {"status": "PASS", "reason": "Primary cash-flow evidence and normalization are verified."}

    for gate_name, evidence_key in (
        ("leverage_refinancing", "leverage_or_refinancing_concern"),
        ("structural_decline", "structural_decline_or_concentration_concern"),
        ("cash_conversion", "cash_conversion_or_working_capital_concern"),
    ):
        flag = evidence.get(evidence_key)
        if flag is True:
            status, reason = "WARN", f"{gate_name.replace('_', ' ').capitalize()} concern is supported by evidence."
        elif flag is False:
            status, reason = "PASS", f"No material {gate_name.replace('_', ' ')} concern was identified in the reviewed evidence."
        elif flag is None:
            status, reason = "WARN", f"{gate_name.replace('_', ' ').capitalize()} has not been assessed; unknown is not neutral."
        else:
            raise ValueError(f"{evidence_key} must be true, false, or null")
        gates[gate_name] = {"status": status, "reason": reason}

    statuses = {str(item["status"]) for item in gates.values()}
    overall = "BLOCK" if "BLOCK" in statuses else "WARN" if "WARN" in statuses else "PASS"
    triggers = evidence.get("invalidation_triggers")
    if not isinstance(triggers, list) or any(not isinstance(x, str) or not x.strip() for x in triggers):
        raise ValueError("invalidation_triggers must be a list of concrete, nonempty strings")
    if overall != "PASS" and not triggers:
        raise ValueError("WARN/BLOCK requires at least one explicit invalidation or verification trigger")
    return {
        "overall": overall,
        "gates": gates,
        "attractive_rating_allowed": overall == "PASS",
        "fcf_valuation_allowed": gates["cashflow_evidence"]["status"] == "PASS",
        "invalidation_triggers": triggers,
        "thresholds": "No universal numeric thresholds are applied; sector/cycle context must be evidenced.",
    }
