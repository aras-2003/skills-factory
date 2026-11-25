from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = Path(__file__).resolve().parent / "schemas" / "role-decision-record.schema.json"


def _timestamp(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value[:-1] + "+00:00" if value[-1:] in {"Z", "z"} else value)


def validate_record(data: Any) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(data), key=lambda error: list(map(str, error.absolute_path)))
    ]
    if errors:
        return errors

    # FormatChecker's date-time implementation is optional; always validate calendar values.
    def check_dates(value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else key
                if child is not None and (key in {"timestamp", "started_at", "ended_at", "assessed_at", "first_dependent_action_at", "captured_at", "earliest", "latest"}):
                    try:
                        _timestamp(child)
                    except (ValueError, TypeError, OverflowError):
                        errors.append(f"{child_path}: invalid calendar timestamp")
                else:
                    check_dates(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                check_dates(child, f"{path}.{index}")
    check_dates(data)
    if errors:
        return errors

    v11 = data["schema_version"] == "1.1"

    def require_reason(value: str, reason: str | None, field: str) -> None:
        if value == "UNKNOWN" and (not reason or not reason.strip()):
            errors.append(f"{field}=UNKNOWN requires a reason")

    for group in ("requested", "host_observed"):
        for name in ("model", "effort", "profile"):
            item = data[group][name]
            require_reason(item["value"], item["reason"], f"{group}.{name}")
    dispatch = data["dispatch"]
    execution = data["execution"]
    result = data["result"]
    disposition = data["coordinator_disposition"]
    timing = data["timing_assessment"]
    for field, item, key in (("dispatch.status", dispatch, "status"), ("execution.state", execution, "state"),
                             ("coordinator_disposition.value", disposition, "value"),
                             ("timing_assessment.value", timing, "value")):
        require_reason(item[key], item["reason"], field)

    decision_at = _timestamp(data["decision"]["timestamp"])
    dispatch_at = _timestamp(dispatch["timestamp"]) if dispatch["timestamp"] else None
    start = _timestamp(execution["started_at"]) if execution["started_at"] else None
    end = _timestamp(execution["ended_at"]) if execution["ended_at"] else None
    action = _timestamp(timing["first_dependent_action_at"]) if timing["first_dependent_action_at"] else None
    disposition_at = _timestamp(disposition["timestamp"])
    assessed_at = _timestamp(timing["assessed_at"])
    if dispatch["status"] == "NOT_ATTEMPTED":
        if dispatch_at is not None:
            errors.append("NOT_ATTEMPTED dispatch must not have a timestamp")
    elif dispatch_at is None:
        if not v11:
            errors.append("dispatch attempt requires a timestamp")
        elif not (dispatch["time_unknown_reason"] or "").strip():
            errors.append("unknown dispatch timestamp requires a reason")
    if dispatch["status"] == "NOT_ATTEMPTED" and data["attempt_id"] is not None:
        errors.append("NOT_ATTEMPTED cannot have an attempt_id")
    if dispatch["status"] != "NOT_ATTEMPTED" and data["attempt_id"] is None:
        errors.append("dispatch attempt requires attempt_id")
    if data["decision_id"] in {data["supersedes_decision_id"], data["parent_decision_id"]}:
        errors.append("a decision cannot link to itself")
    if data["retry_of"] is not None and data["attempt_id"] is None:
        errors.append("retry_of requires an actual dispatch attempt")
    if data["retry_of"] is not None and data["retry_of"] == data["attempt_id"]:
        errors.append("retry_of cannot refer to the same attempt_id")
    for index, signal in enumerate(data["signal_evidence"]):
        if _timestamp(signal["captured_at"]) > decision_at:
            errors.append(f"signal_evidence.{index} was captured after the decision")
    if dispatch_at and dispatch_at <= decision_at:
        errors.append("decision must precede dispatch")
    if data["decision"]["value"] == "SKIP" and dispatch["status"] != "NOT_ATTEMPTED":
        errors.append("SKIP cannot have a dispatch attempt")
    if execution["state"] != "NOT_STARTED" and dispatch["status"] not in {"ACCEPTED", "UNKNOWN"}:
        errors.append("execution requires an accepted or unknown dispatch")
    if execution["state"] in {"RUNNING", "COMPLETED", "FAILED", "CANCELLED"} and start is None:
        if not v11:
            errors.append("execution state requires started_at")
        elif not (execution["started_time_unknown_reason"] or "").strip():
            errors.append("unknown execution start requires a reason")
    if execution["state"] in {"COMPLETED", "FAILED", "CANCELLED"} and end is None:
        if not v11:
            errors.append("terminal execution state requires ended_at")
        elif not (execution["ended_time_unknown_reason"] or "").strip():
            errors.append("unknown execution end requires a reason")
    if execution["state"] in {"NOT_STARTED", "RUNNING"} and end is not None:
        errors.append("nonterminal execution cannot have ended_at")
    if execution["state"] == "NOT_STARTED" and start is not None:
        errors.append("NOT_STARTED cannot have started_at")
    if start and dispatch_at and start < dispatch_at:
        errors.append("execution cannot start before dispatch")
    if end and ((not start and not v11) or (start and end < start)):
        errors.append("execution cannot end before it starts")
    if bool(result["reference"]) != bool(result["sha256"]) or bool(result["reference"]) != bool(result["reference_kind"]):
        errors.append("result reference, reference_kind and sha256 must be supplied together")
    if result["reference_kind"] == "REPO_FILE" and result["reference"]:
        raw_path = Path(result["reference"])
        root = ROOT.resolve()
        resolved = (root / raw_path).resolve()
        if raw_path.is_absolute() or ".." in raw_path.parts or not resolved.is_relative_to(root):
            errors.append("REPO_FILE reference must be a safe repository-relative path")
        else:
            try:
                digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
                if digest != result["sha256"]:
                    errors.append("REPO_FILE result sha256 mismatch")
            except OSError as exc:
                errors.append(f"cannot read REPO_FILE result: {exc}")
    if result["reference"] and execution["state"] not in {"COMPLETED", "FAILED", "CANCELLED"}:
        errors.append("a result requires terminal execution")
    if execution["state"] == "COMPLETED" and not result["reference"]:
        errors.append("COMPLETED execution requires a result reference and sha256")
    if disposition["value"] in {"ACCEPTED", "ADAPTED"} and not result["reference"]:
        errors.append("ACCEPTED or ADAPTED disposition requires a result")
    if disposition_at < decision_at or (end and disposition["value"] != "PENDING" and disposition_at < end):
        errors.append("coordinator disposition cannot precede the decision or terminal execution")
    assessment = timing["value"]
    if (data["trigger_source"] == "NATURAL" and data["impact"] in {"A0", "A1"}
            and data["decision"]["value"] == "INVOKE"
            and assessment != "UNKNOWN"
            and (assessment != "UNNECESSARY" or not (timing["reason"] or "").strip())):
        errors.append("NATURAL A0/A1 INVOKE requires UNKNOWN or UNNECESSARY assessment with reviewer rationale")
    action_ref = timing["first_dependent_action_reference"]
    if not v11:
        if bool(action) != bool(action_ref):
            errors.append("first dependent action requires both timestamp and reference")
        if assessment in {"EARLY", "ON_TIME", "LATE", "MISSED"} and action is None:
            errors.append(f"{assessment} timing requires a first dependent action")
        if assessment in {"EARLY", "ON_TIME", "CORRECT_SKIP"} and action and decision_at >= action:
            errors.append(f"{assessment} requires the decision to precede the first dependent action")
        if assessment in {"EARLY", "ON_TIME"} and (dispatch_at is None or dispatch["status"] != "ACCEPTED" or (action and dispatch_at >= action)):
            errors.append(f"{assessment} requires accepted dispatch before the first dependent action")
        if assessment == "LATE" and action and decision_at < action and (dispatch_at is None or dispatch_at < action):
            errors.append("LATE requires the first dependent action to precede or coincide with the decision or dispatch")
    else:
        def interval(exact: dt.datetime | None, bounds: dict | None, field: str) -> tuple[dt.datetime, dt.datetime] | None:
            if bounds:
                earliest, latest = _timestamp(bounds["earliest"]), _timestamp(bounds["latest"])
                if earliest > latest:
                    errors.append(f"{field} bounds earliest must not exceed latest")
                if exact and not earliest <= exact <= latest:
                    errors.append(f"{field} exact timestamp must lie within bounds")
                if exact is None:
                    return earliest, latest
            return (exact, exact) if exact else None

        dispatch_interval = interval(dispatch_at, dispatch["coordinator_bounds"], "dispatch")
        interval(start, execution["started_coordinator_bounds"], "execution start")
        interval(end, execution["ended_coordinator_bounds"], "execution end")
        action_interval = interval(action, timing["first_dependent_action_coordinator_bounds"], "first dependent action")
        if dispatch["status"] == "NOT_ATTEMPTED" and dispatch_interval:
            errors.append("NOT_ATTEMPTED dispatch must not have bounds")
        if execution["state"] == "NOT_STARTED" and (execution["started_coordinator_bounds"] or execution["ended_coordinator_bounds"]):
            errors.append("NOT_STARTED execution must not have bounds")
        if execution["state"] == "RUNNING" and execution["ended_coordinator_bounds"]:
            errors.append("nonterminal execution must not have end bounds")
        if (action or action_interval) and not action_ref:
            errors.append("first dependent action occurrence requires a reference")
        if action_ref and not action and not (timing["first_dependent_action_time_unknown_reason"] or "").strip():
            errors.append("unknown first dependent action timestamp requires a reason")
        if assessment in {"EARLY", "ON_TIME", "LATE", "MISSED"} and not (action_ref and action_interval):
            errors.append(f"{assessment} timing requires a first dependent action with timing evidence")
        if assessment in {"EARLY", "ON_TIME"} and (dispatch["status"] != "ACCEPTED" or not dispatch_interval or not action_interval or dispatch_interval[1] >= action_interval[0] or decision_at >= action_interval[0]):
            errors.append(f"{assessment} requires accepted dispatch before the first dependent action")
        # The lower bound of dispatch is the request; a late acknowledgment alone is not proof.
        request_at = _timestamp(dispatch["coordinator_bounds"]["earliest"]) if dispatch["coordinator_bounds"] else None
        if assessment == "LATE" and (not action_interval or not (action_interval[1] < decision_at or (request_at and action_interval[1] < request_at))):
            errors.append("LATE requires action proven before decision or dispatch request")
        if assessment == "MISSED" and (not action_interval or decision_at >= action_interval[0]):
            errors.append("MISSED requires a qualifying action after SKIP")
        if assessment == "CORRECT_SKIP" and (action_ref or action or action_interval):
            errors.append("CORRECT_SKIP forbids action occurrence evidence")
    if assessment == "CORRECT_SKIP" and timing["no_qualifying_action_confirmed"] is not True:
        errors.append("CORRECT_SKIP requires reviewer confirmation of no qualifying action")
    if assessment == "CORRECT_SKIP" and not (timing["reason"] or "").strip():
        errors.append("CORRECT_SKIP requires reviewer evidence rationale")
    if assessment in {"MISSED", "CORRECT_SKIP"} and data["decision"]["value"] != "SKIP":
        errors.append(f"{assessment} requires a SKIP decision")
    if assessment in {"EARLY", "ON_TIME", "LATE", "UNNECESSARY"} and data["decision"]["value"] != "INVOKE":
        errors.append(f"{assessment} requires an INVOKE decision")
    if assessment == "CORRECT_SKIP" and data["impact"] in {"A2", "A3", "A4"}:
        errors.append("CORRECT_SKIP is inconsistent with impact A2-A4")
    if assessment == "UNNECESSARY" and data["impact"] in {"A2", "A3", "A4"} and not (timing["reason"] or "").strip():
        errors.append("UNNECESSARY for impact A2-A4 requires reviewer rationale")
    if data["decision"]["value"] == "SKIP" and data["impact"] in {"A2", "A3", "A4"} and assessment not in {"MISSED", "UNKNOWN"}:
        errors.append("SKIP for impact A2-A4 requires MISSED or UNKNOWN timing assessment")
    if assessed_at < decision_at or (action and assessed_at < action):
        errors.append("timing assessment cannot precede the events it assesses")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a structured role decision record")
    parser.add_argument("command", choices=["validate"])
    parser.add_argument("records", nargs="*", type=Path)
    args = parser.parse_args()
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaError) as exc:
        print(f"{SCHEMA}: {exc}", file=sys.stderr)
        return 1
    default_dir = ROOT / "evals" / "results" / "role-decisions"
    records = args.records or sorted(default_dir.rglob("*.json"))
    failed = False
    seen_attempts: dict[str, tuple[Path, dict[str, Any]]] = {}
    retries: list[tuple[Path, dict[str, Any]]] = []
    decisions: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for record in records:
        try:
            data = json.loads(record.read_text(encoding="utf-8"))
            errors = validate_record(data)
            if not errors:
                if data["result"]["reference_kind"] in {"EXTERNAL", "PRIVATE"}:
                    print(f"{record}: {data['result']['reference_kind']} result content NOT VERIFIED")
                decisions.setdefault(data["decision_id"], []).append((record, data))
                attempt_id = data["attempt_id"]
                if attempt_id is not None:
                    if attempt_id in seen_attempts:
                        errors.append(f"duplicate or conflicting attempt_id also found in {seen_attempts[attempt_id][0]}")
                    else:
                        seen_attempts[attempt_id] = (record, data)
                if data["retry_of"] is not None:
                    retries.append((record, data))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError, OverflowError) as exc:
            print(f"{record}: {exc}", file=sys.stderr)
            failed = True
            continue
        for error in errors:
            print(f"{record}: {error}", file=sys.stderr)
            failed = True
    immutable_fields = ("decision_id", "task_reference", "role", "impact", "trigger_source", "policy_revision", "source_revision")
    for decision_id, group in decisions.items():
        if len(group) <= 1:
            continue
        first = group[0][1]
        if any(data["attempt_id"] is None for _, data in group):
            print(f"{decision_id}: multiple records cannot include a no-attempt snapshot", file=sys.stderr)
            failed = True
        roots = sum(data["retry_of"] is None for _, data in group)
        if roots > 1 or (not args.records and roots != 1):
            print(f"{decision_id}: attempt chain requires exactly one root", file=sys.stderr)
            failed = True
        for record, data in group[1:]:
            differences = [field for field in immutable_fields if data[field] != first[field]]
            if data["decision"]["value"] != first["decision"]["value"]:
                differences.append("decision.value")
            if _timestamp(data["decision"]["timestamp"]) != _timestamp(first["decision"]["timestamp"]):
                differences.append("decision.timestamp")
            if data["schema_version"] == "1.1" or first["schema_version"] == "1.1":
                differences.extend(field for field in ("decision", "signal_evidence", "parent_decision_id", "supersedes_decision_id") if data[field] != first[field])
            if differences:
                print(f"{record}: decision group differs in {', '.join(differences)}", file=sys.stderr)
                failed = True
    for record, data in retries:
        target = data["retry_of"]
        reason = data["retry_resolution_reason"]
        if target not in seen_attempts:
            if not args.records or not reason or not reason.strip():
                print(f"{record}: retry target {target!r} unavailable; partial scans require a reason", file=sys.stderr)
                failed = True
            else:
                print(f"{record}: retry target {target!r} UNKNOWN in partial scan: {reason}")
            continue
        original = seen_attempts[target][1]
        differences = [field for field in immutable_fields if data[field] != original[field]]
        if data["decision"]["value"] != original["decision"]["value"]:
            differences.append("decision.value")
        if _timestamp(data["decision"]["timestamp"]) != _timestamp(original["decision"]["timestamp"]):
            differences.append("decision.timestamp")
        if data["schema_version"] == "1.1" or original["schema_version"] == "1.1":
            differences.extend(field for field in ("decision", "signal_evidence", "parent_decision_id", "supersedes_decision_id") if data[field] != original[field])
        if differences:
            print(f"{record}: retry differs from target in {', '.join(differences)}", file=sys.stderr)
            failed = True
        old_at, new_at = original["dispatch"]["timestamp"], data["dispatch"]["timestamp"]
        if old_at and new_at:
            if _timestamp(old_at) >= _timestamp(new_at):
                print(f"{record}: retry target dispatch must be earlier", file=sys.stderr)
                failed = True
        else:
            print(f"{record}: retry chronology UNKNOWN: exact dispatch times unavailable")
    # Check graph topology independently of timestamps and input order.
    for attempt_id, (record, data) in seen_attempts.items():
        visited: set[str] = set()
        current = attempt_id
        while current in seen_attempts:
            if current in visited:
                print(f"{record}: retry cycle detected", file=sys.stderr)
                failed = True
                break
            visited.add(current)
            current = seen_attempts[current][1]["retry_of"]
            if current is None:
                break
    if not records:
        print(f"No role decision records found in {default_dir}")
    elif not failed:
        print(f"Validated {len(records)} role decision record(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
