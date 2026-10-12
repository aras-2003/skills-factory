"""Fail-closed capability preflight for a host-supplied channel manifest.

This library compares reviewed repository-side declarations with externally
supplied availability. It does not discover a host, approve an action, or execute
any skill. Integrators must still verify actual runtime identity and authorization.
"""
from __future__ import annotations

from collections.abc import Mapping

from contract import DIMENSIONS, assessment_for, load_dimensions


def preflight(contract: dict, component: str, availability: Mapping[str, str]) -> dict:
    """Return a deterministic, non-executing routing gate result.

    "supported" means only that the *caller claims* the capability is available.
    It is never evidence that a provider call succeeded or that a side effect
    was authorized. Unknown requirements fail closed.
    """
    if not isinstance(component, str) or not component:
        raise ValueError("component name is required")
    if not isinstance(availability, Mapping):
        raise ValueError("channel availability must be a mapping")

    assessment = assessment_for(contract, component)
    requirements = assessment["requirements"]
    allowed_states = contract.get("availability_states")
    if not isinstance(allowed_states, list):
        raise ValueError("capability contract must define availability states")

    unexpected = set(availability) - set(DIMENSIONS)
    if unexpected:
        raise ValueError(f"unknown availability dimensions: {', '.join(sorted(unexpected))}")
    for dimension, state in availability.items():
        if not isinstance(state, str) or state not in allowed_states:
            raise ValueError(f"invalid availability for {dimension}: {state!r}")
    # Validate the source-side capability schema separately from a host assertion.
    load_dimensions(contract)

    unavailable: list[str] = []
    unresolved: list[str] = []
    approval: list[str] = []
    host_view: dict[str, str] = {}

    for dimension in DIMENSIONS:
        required = requirements[dimension]
        provided = availability.get(dimension, "unknown")
        host_view[dimension] = provided
        if required == "none":
            continue
        if required == "unassessed":
            unresolved.append(f"{dimension}:unassessed")
            continue
        if required == "named_classes":
            # A generic class requirement is not proof that the correct secrets
            # or connector-specific scopes exist in this particular channel.
            unresolved.append(f"{dimension}:credential_classes_not_verified")
        if provided == "unavailable":
            unavailable.append(dimension)
        elif provided == "unknown":
            unresolved.append(f"{dimension}:availability_unknown")
        elif provided == "requiring_approval":
            approval.append(dimension)
        if required == "approval_required" or required == "write":
            approval.append(dimension)

    if unavailable:
        state = "BLOCKED_UNAVAILABLE"
    elif unresolved:
        state = "BLOCKED_UNVERIFIED"
    elif approval:
        state = "REQUIRES_APPROVAL"
    else:
        state = "STATIC_CAPABILITY_MATCH_ONLY"

    return {
        "component": component,
        "decision": state,
        "requirements_assessment": assessment["status"],
        "requirements": dict(requirements),
        "channel_availability": host_view,
        "unavailable": sorted(set(unavailable)),
        "unresolved": sorted(set(unresolved)),
        "approval_gates": sorted(set(approval)),
        "execution_authorized": False,
        "provider_calls_executed": False,
        "runtime_evidence": "NOT_RUN",
        "source": "repository-declared requirements + caller-supplied availability; not an attestation",
    }
