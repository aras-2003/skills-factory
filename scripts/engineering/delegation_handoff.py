"""Validate the compact, source-bound handoff contract used by SDLC issue #748.

This module validates serialized references; it does not spawn agents or grant
permissions. The host remains responsible for actual child identity and access.
"""

from __future__ import annotations

import json
import re
from typing import Any


VERSION = "1"
MAX_HANDOFF_BYTES = 16_384
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
INPUT_FIELDS = {
    "issue_id", "role", "objective", "acceptance_criteria", "source_base_sha",
    "candidate_sha", "architecture_impact", "readonly_paths", "writable_paths",
    "dependencies", "selected_skill_refs", "tool_profile_ref", "test_case_ids",
    "stop_conditions", "context_budget", "output_contract_version",
}
RESULT_FIELDS = {
    "task_id", "role", "status", "candidate_sha", "changed_paths",
    "test_case_outcomes", "command_exit_codes", "evidence_refs",
    "material_findings", "residual_risks", "next_action", "usage",
}
FORBIDDEN_FIELDS = {
    "transcript", "tool_logs", "raw_tool_logs", "rubric", "evaluator_rubric",
    "held_out_fixtures", "heldout_fixtures", "permissions", "approval",
    "authorization", "credentials", "secret",
}
STATUSES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED"}
ARCHITECTURE_IMPACTS = {"A0", "A1", "A2", "A3", "A4", "UNKNOWN"}


def _bounded_json(value: Any) -> bytes:
    try:
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("handoff must be JSON serializable") from exc
    if len(encoded) > MAX_HANDOFF_BYTES:
        raise ValueError(f"handoff exceeds {MAX_HANDOFF_BYTES} byte context limit")
    return encoded


def _check_forbidden(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError("handoff object keys must be strings")
            if key.lower() in FORBIDDEN_FIELDS:
                raise ValueError(f"forbidden field: {key}")
            _check_forbidden(nested)
    elif isinstance(value, list):
        for nested in value:
            _check_forbidden(nested)


def _required_object(value: Any, required: set[str], optional: set[str], name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    _check_forbidden(value)
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing:
        raise ValueError(f"{name} missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{name} has unknown fields: {', '.join(sorted(unknown))}")
    return value


def _text(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _string_list(value: Any, field: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field} must be a list of non-empty strings")


def _sha(value: Any, field: str, optional: bool = False) -> None:
    if optional and value is None:
        return
    if not isinstance(value, str) or not SHA1.fullmatch(value):
        raise ValueError(f"{field} must be a full lowercase 40-character Git SHA")


def validate_input(payload: Any) -> dict:
    required = INPUT_FIELDS - {"candidate_sha"}
    item = _required_object(payload, required, {"candidate_sha"}, "handoff input")
    if type(item["issue_id"]) is not int or item["issue_id"] < 1:
        raise ValueError("issue_id must be a positive integer")
    for field in ("role", "objective", "architecture_impact", "tool_profile_ref", "output_contract_version"):
        _text(item[field], field)
    if item["architecture_impact"] not in ARCHITECTURE_IMPACTS:
        raise ValueError("architecture_impact must be A0-A4 or UNKNOWN")
    if item["output_contract_version"] != VERSION:
        raise ValueError("unsupported output_contract_version")
    if not isinstance(item["acceptance_criteria"], list) or not item["acceptance_criteria"]:
        raise ValueError("acceptance_criteria must be a non-empty numbered list")
    for criterion in item["acceptance_criteria"]:
        if not isinstance(criterion, str) or not re.match(r"^\d+\.", criterion.strip()):
            raise ValueError("acceptance_criteria entries must be numbered strings")
    _sha(item["source_base_sha"], "source_base_sha")
    _sha(item.get("candidate_sha"), "candidate_sha", optional=True)
    for field in ("readonly_paths", "writable_paths", "selected_skill_refs", "test_case_ids", "stop_conditions"):
        _string_list(item[field], field)
    if len(set(item["test_case_ids"])) != len(item["test_case_ids"]):
        raise ValueError("test_case_ids must contain unique case IDs")
    if item["role"] == "sf-test-executor" and not item["test_case_ids"]:
        raise ValueError("Test Executor handoff requires at least one test_case_id")
    if not isinstance(item["dependencies"], list) or any(type(dep) is not int or dep < 1 for dep in item["dependencies"]):
        raise ValueError("dependencies must be positive issue numbers")
    if type(item["context_budget"]) is not int or not 128 <= item["context_budget"] <= 16_384:
        raise ValueError("context_budget must be between 128 and 16384 bytes")
    if item["context_budget"] > MAX_HANDOFF_BYTES:
        raise ValueError("context_budget exceeds maximum handoff size")
    encoded = _bounded_json(item)
    if len(encoded) > item["context_budget"]:
        raise ValueError("serialized input exceeds declared context_budget")
    return item


def serialize_input(payload: Any) -> bytes:
    return _bounded_json(validate_input(payload))


def read_input(data: bytes | str) -> dict:
    if isinstance(data, bytes):
        if len(data) > MAX_HANDOFF_BYTES:
            raise ValueError(f"handoff exceeds {MAX_HANDOFF_BYTES} byte context limit")
        data = data.decode("utf-8")
    if not isinstance(data, str):
        raise ValueError("serialized handoff must be bytes or text")
    try:
        payload = json.loads(data)
    except (ValueError, TypeError) as exc:
        raise ValueError("serialized handoff is not valid JSON") from exc
    return validate_input(payload)


def validate_result(
    payload: Any,
    *,
    expected_task_id: str,
    expected_role: str,
    expected_test_case_ids: list[str],
    expected_candidate_sha: str,
) -> dict:
    _text(expected_task_id, "expected_task_id")
    _text(expected_role, "expected_role")
    _string_list(expected_test_case_ids, "expected_test_case_ids")
    if expected_role == "sf-test-executor" and not expected_test_case_ids:
        raise ValueError("Test Executor result requires at least one expected test case")
    if len(set(expected_test_case_ids)) != len(expected_test_case_ids):
        raise ValueError("expected_test_case_ids must contain unique case IDs")
    _sha(expected_candidate_sha, "expected_candidate_sha")
    required = RESULT_FIELDS - {"usage"}
    item = _required_object(payload, required, {"usage"}, "handoff result")
    for field in ("task_id", "role", "next_action"):
        _text(item[field], field)
    if item["task_id"] != expected_task_id:
        raise ValueError("task ID mismatch; result belongs to a different delegation")
    if item["role"] != expected_role:
        raise ValueError("role mismatch; result does not match the delegated role")
    if not isinstance(item["status"], str) or item["status"] not in STATUSES:
        raise ValueError("status must be PASS, FAIL, NOT_RUN or BLOCKED")
    _sha(item["candidate_sha"], "candidate_sha")
    if item["candidate_sha"] != expected_candidate_sha:
        raise ValueError("candidate SHA mismatch; result is stale")
    for field in ("changed_paths", "evidence_refs", "material_findings", "residual_risks"):
        _string_list(item[field], field)
    if not isinstance(item["test_case_outcomes"], list):
        raise ValueError("test_case_outcomes must be a list")
    case_ids = set()
    for outcome in item["test_case_outcomes"]:
        entry = _required_object(
            outcome,
            {"case_id", "status"},
            {"fixture_sha256", "evidence_refs"},
            "test case outcome",
        )
        _text(entry["case_id"], "test_case_outcomes.case_id")
        if entry["case_id"] in case_ids:
            raise ValueError("test_case_outcomes must contain unique case IDs")
        case_ids.add(entry["case_id"])
        if not isinstance(entry["status"], str) or entry["status"] not in STATUSES:
            raise ValueError("test_case_outcomes.status must be PASS, FAIL, NOT_RUN or BLOCKED")
        if "fixture_sha256" in entry and (
            not isinstance(entry["fixture_sha256"], str)
            or not SHA256.fullmatch(entry["fixture_sha256"])
        ):
            raise ValueError("test_case_outcomes.fixture_sha256 must be a lowercase SHA-256 digest")
        if "evidence_refs" in entry:
            _string_list(entry["evidence_refs"], "test_case_outcomes.evidence_refs")
    if case_ids != set(expected_test_case_ids):
        raise ValueError("test case IDs do not match the delegated test_case_ids")
    if not isinstance(item["command_exit_codes"], list):
        raise ValueError("command_exit_codes must be a list")
    for execution in item["command_exit_codes"]:
        entry = _required_object(execution, {"command", "exit_code"}, set(), "command exit record")
        _text(entry["command"], "command_exit_codes.command")
        if type(entry["exit_code"]) is not int:
            raise ValueError("command_exit_codes.exit_code must be an integer")
    if item["status"] == "PASS":
        if not item["evidence_refs"]:
            raise ValueError("PASS requires at least one evidence reference")
        if any(outcome["status"] != "PASS" for outcome in item["test_case_outcomes"]):
            raise ValueError("PASS cannot contain a non-PASS test case outcome")
        if any(execution["exit_code"] != 0 for execution in item["command_exit_codes"]):
            raise ValueError("PASS cannot contain a nonzero command exit code")
        if expected_role == "sf-test-executor" and not item["command_exit_codes"]:
            raise ValueError("Test Executor PASS requires at least one command exit record")
    usage = item.get("usage")
    if usage is not None:
        if not isinstance(usage, dict) or set(usage) - {"input_tokens", "output_tokens", "tool_calls"}:
            raise ValueError("usage may contain only observed input_tokens, output_tokens and tool_calls")
        for key, count in usage.items():
            if type(count) is not int or count < 0:
                raise ValueError(f"usage.{key} must be an observed non-negative integer")
    result = dict(item)
    result.setdefault("usage", None)
    _bounded_json(result)
    return result
