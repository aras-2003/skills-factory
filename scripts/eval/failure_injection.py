#!/usr/bin/env python3
"""Deterministic TEST-only failure injection for MCP-style tool adapters.

Does not contact the Site, production MCP, databases, or browser. A returned
simulated outcome is never a provider/runtime receipt and never a campaign PASS.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

FAILURES = ("timeout", "permission_denied", "tool_unavailable", "incompatible_schema", "renderer_unavailable")


class InjectedUnavailable(RuntimeError):
    pass


def failure_probe(case: str, action: Callable[[], Any] | None = None) -> dict:
    """Use only isolated stub actions. Failure meaning stays explicit."""
    if case not in FAILURES:
        raise ValueError("unsupported injected failure case")
    if action is not None:
        raise ValueError("live action is prohibited; failures are simulated by this contract")
    errors = {
        "timeout": ("TimeoutError", "BLOCKED", "awaiting_runner"),
        "permission_denied": ("PermissionError", "BLOCKED", "blocked"),
        "tool_unavailable": ("InjectedUnavailable", "BLOCKED", "blocked"),
        "incompatible_schema": ("ValueError", "FAIL", "executed"),
        "renderer_unavailable": ("InjectedUnavailable", "BLOCKED", "blocked"),
    }
    name, verdict, execution = errors[case]
    return {
        "schema_version": "1.0", "kind": "synthetic_tool_failure_fixture",
        "case": case, "simulated_exception": name,
        "simulated_expected_status": verdict,
        "simulated_expected_execution_state": execution,
        "provider_calls_executed": False, "external_side_effects": "NONE_BY_HARNESS",
        "tool_receipt": None, "client_display_state": "not_observed",
        "real_execution_state": "NOT_RUN",
        "real_outcome": None,
        "test_mode": "OFFLINE_SIMULATION_ONLY",
    }


def evaluate_observed_failure(case: str, observation: dict) -> dict:
    """Check evidence structure, not provider authenticity; no false PASS."""
    if case not in FAILURES:
        raise ValueError("unsupported failure case")
    if not isinstance(observation, dict):
        return {"status": "BLOCKED", "reason": "no observation", "release_approved": False}
    status = observation.get("execution_state")
    if status not in ("executed", "blocked", "awaiting_runner", "no_steps", "not_executed"):
        return {"status": "BLOCKED", "reason": "invalid execution state", "release_approved": False}
    # Any test that did not run cannot be assigned FAIL.
    if status != "executed":
        return {"status": "NOT_RUN", "reason": "no executed runtime path", "release_approved": False}
    if observation.get("tool_receipt") is None or not observation.get("actual_exception"):
        return {"status": "REVIEW_REQUIRED", "reason": "actual tool trace/exception evidence missing", "release_approved": False}
    return {"status": "REVIEW_REQUIRED", "reason": "assess real trace against independent rubric", "release_approved": False}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=FAILURES, required=True)
    args = parser.parse_args()
    print(json.dumps(failure_probe(args.case), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
