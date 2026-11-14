"""Validate and calculate the versioned Evaluation Report Contract v1.

This is a pure report-layer contract over existing per-case evidence receipts.
It never executes evaluations, edits receipts, or authorizes releases.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "scripts/eval/schemas/evaluation-report-v1.schema.json"
CALCULATION_VERSION = "weighted-assertions-v1"
GRADE_VALUES = {Decimal("0"), Decimal("0.5"), Decimal("1")}


def _decimal(value: Any, where: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{where}: expected a number")
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{where}: invalid decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{where}: value must be finite")
    return result


def _profile_contract(profile: dict[str, Any]) -> tuple[list[dict[str, Any]], Decimal, Decimal, Decimal]:
    dimensions = profile["dimensions"]
    names = [item["name"] for item in dimensions]
    if len(set(names)) != len(names):
        raise ValueError("evaluation_profile: duplicate dimension name")
    excluded = profile.get("excluded_dimensions", [])
    excluded_names = [item["name"] for item in excluded]
    if len(set(excluded_names)) != len(excluded_names) or set(names) & set(excluded_names):
        raise ValueError("evaluation_profile: duplicate or both included/excluded dimension")
    total = sum((_decimal(item["weight"], "dimension.weight") for item in dimensions), Decimal(0))
    if total != Decimal(100):
        raise ValueError(f"evaluation_profile: dimension weights must sum to 100; found {total}")
    thresholds = profile["thresholds"]
    pass_min = _decimal(thresholds["pass_minimum"], "thresholds.pass_minimum")
    critical_min = _decimal(thresholds["critical_dimension_minimum"], "thresholds.critical_dimension_minimum")
    reject_below = _decimal(thresholds["reject_below"], "thresholds.reject_below")
    if reject_below >= pass_min or critical_min > pass_min:
        raise ValueError("evaluation_profile: thresholds are inconsistent")
    return dimensions, pass_min, critical_min, reject_below


def calculate_score(
    profile: dict[str, Any],
    assertions: list[dict[str, Any]],
    *,
    blocking_gates: list[str] | None = None,
) -> dict[str, Any]:
    """Return the reproducible score, coverage and decision for frozen assertions.

    A required assertion without executed evidence makes the headline score
    NOT_SCORABLE. A failed blocking assertion or explicit blocker can never PASS.
    Proposed, uncalibrated thresholds only yield a PROVISIONAL score/ITERATE.
    """
    dimensions, pass_min, critical_min, reject_below = _profile_contract(profile)
    names = {item["name"] for item in dimensions}
    unknown = sorted({item.get("dimension") for item in assertions} - names)
    if unknown:
        raise ValueError(f"assertions: dimensions absent from profile: {unknown}")

    output_dimensions: list[dict[str, Any]] = []
    missing: list[str] = []
    required_total = 0
    executed_total = 0
    raw_total = Decimal(0)
    scorable = True
    critical_dimension_values: list[Decimal] = []
    failed_assertion_gates: list[str] = []

    for dimension in dimensions:
        name = dimension["name"]
        required = [a for a in assertions if a.get("dimension") == name and a.get("required") is True]
        dimension_all = [a for a in assertions if a.get("dimension") == name]
        if not required:
            scorable = False
            missing.append(f"dimension:{name}:no-required-assertions")
        required_total += len(required)
        valid: list[dict[str, Any]] = []
        for assertion in required:
            assertion_id = assertion.get("id", "<unknown>")
            state = assertion.get("execution_state")
            grade = assertion.get("grade")
            if state != "executed" or grade is None:
                scorable = False
                missing.append(f"assertion:{assertion_id}:not-executed-or-unscored")
                continue
            score = _decimal(grade, f"assertion:{assertion_id}.grade")
            if score not in GRADE_VALUES:
                raise ValueError(f"assertion:{assertion_id}.grade: must be 0, 0.5 or 1")
            if not assertion.get("evidence_refs"):
                scorable = False
                missing.append(f"assertion:{assertion_id}:evidence-missing")
                continue
            importance = int(assertion["importance"])
            valid.append({"grade": score, "importance": importance})
            executed_total += 1
            if assertion.get("blocking_gate") and score < Decimal(1):
                failed_assertion_gates.append(f"assertion:{assertion_id}")

        complete = bool(required) and len(valid) == len(required)
        dimension_value: Decimal | None = None
        if complete:
            denominator = sum((Decimal(item["importance"]) for item in valid), Decimal(0))
            numerator = sum((Decimal(item["importance"]) * item["grade"] for item in valid), Decimal(0))
            dimension_value = Decimal(10) * numerator / denominator
            raw_total += _decimal(dimension["weight"], "dimension.weight") * dimension_value / Decimal(100)
            if dimension.get("critical"):
                critical_dimension_values.append(dimension_value)
        else:
            scorable = False
        output_dimensions.append({
            "name": name,
            "weight": float(_decimal(dimension["weight"], "dimension.weight")),
            "value": None if dimension_value is None else float(dimension_value),
            "required_assertions": len(required),
            "executed_assertions": len(valid),
            "case_count": len({a["case_id"] for a in dimension_all}),
            "evidence_refs": sorted({ref for a in dimension_all for ref in a.get("evidence_refs", [])}),
        })

    coverage_ratio = Decimal(0) if required_total == 0 else Decimal(executed_total) / Decimal(required_total)
    gates = sorted(set(blocking_gates or []) | set(failed_assertion_gates))
    value: float | None = None
    unrounded: float | None = None
    if scorable:
        unrounded = float(raw_total)
        value = float(raw_total.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

    if gates:
        decision = "REJECT"
    elif not scorable:
        decision = "ITERATE"
    elif profile["calibration_status"] != "VALIDATED":
        decision = "ITERATE"
    elif raw_total < reject_below:
        decision = "REJECT"
    elif raw_total >= pass_min and all(v >= critical_min for v in critical_dimension_values):
        decision = "PASS"
    else:
        decision = "ITERATE"

    status = "NOT_SCORABLE" if not scorable else (
        "FINAL" if profile["calibration_status"] == "VALIDATED" else "PROVISIONAL"
    )
    return {
        "value": value,
        "unrounded_value": unrounded,
        "scale": "0-10",
        "status": status,
        "profile": f"{profile['profile_id']}@{profile['version']}",
        "dimensions": output_dimensions,
        "calculation_version": CALCULATION_VERSION,
        "coverage": {
            "required_assertions": required_total,
            "executed_assertions": executed_total,
            "ratio": float(coverage_ratio),
        },
        "missing_evidence": sorted(missing),
        "decision": {
            "status": decision,
            "blocking_gates": gates,
        },
    }


def _expected_delta(report: dict[str, Any], calculated_score: dict[str, Any]) -> dict[str, Any]:
    comparator = report["comparator"]
    actual_profile = report["evaluation_profile"]
    null_reason: str | None = None
    value: float | None = None
    if comparator["id"] is None:
        null_reason = comparator["not_applicable_reason"]
    elif calculated_score["status"] != "FINAL":
        null_reason = "Candidate score is not final and comparable."
    elif comparator["profile_id"] != actual_profile["profile_id"] or comparator["profile_version"] != actual_profile["version"]:
        null_reason = "Evaluation profiles differ."
    elif comparator["evalset_id"] != report["evalset"]["id"] or comparator["evalset_version"] != report["evalset"]["version"]:
        null_reason = "EvalSet identity differs."
    elif sorted(comparator["case_ids"]) != sorted(case["case_id"] for case in report["cases"]):
        null_reason = "Evaluation case identities differ."
    elif sorted(comparator["assertion_ids"]) != sorted(assertion["id"] for assertion in report["assertions"]):
        null_reason = "Evaluation assertion identities differ."
    elif comparator["runtime_identity"] != report["runtime"]:
        null_reason = "Runtime/model/tool identity differs."
    elif comparator["score"] is None:
        null_reason = "Comparator score is missing."
    else:
        delta = _decimal(calculated_score["value"], "score.value") - _decimal(comparator["score"], "comparator.score")
        value = float(delta.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    return {"value": value, "reason": null_reason}


def calculate_report(report: dict[str, Any]) -> dict[str, Any]:
    """Build fields derived from a report's profile, assertions and blockers."""
    external_gates = list(report.get("decision", {}).get("blocking_gates", []))
    external_gates.extend(
        f"weakness:{idx}" for idx, weakness in enumerate(report.get("weaknesses", []), 1)
        if weakness.get("severity") in {"critical", "high"}
    )
    result = calculate_score(report["evaluation_profile"], report["assertions"], blocking_gates=external_gates)
    comparator = _expected_delta(report, result)
    return {"score": {k: v for k, v in result.items() if k != "decision"},
            "decision": {**result["decision"], "next_actions": report.get("decision", {}).get("next_actions", [])},
            "comparison_delta": comparator}


def validate_report(
    report: dict[str, Any],
    *,
    schema_path: Path = SCHEMA_PATH,
    root: Path = ROOT,
) -> list[str]:
    """Validate schema, cross-field references, score arithmetic and fail-closed gates."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = [f"schema: {error.message}" for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report)]
    if errors:
        return sorted(errors)

    try:
        profile = report["evaluation_profile"]
        _profile_contract(profile)
        cases = report["cases"]
        case_ids = [item["case_id"] for item in cases]
        if len(set(case_ids)) != len(case_ids):
            errors.append("cases: duplicate case_id")
        case_by_id = {item["case_id"]: item for item in cases}
        expected_outcomes = {"PASS": "passed", "FAIL": "failed", "REVIEW_REQUIRED": None, "NOT_RUN": None}
        for case in cases:
            status = case["evaluation_status"]
            state = case["execution_state"]
            if status == "NOT_RUN":
                if state == "executed" or case["outcome"] is not None or not case["execution_reason"]:
                    errors.append(f"case:{case['case_id']}: NOT_RUN requires non-executed state, null outcome, and reason")
            elif state != "executed" or case["outcome"] != expected_outcomes[status]:
                errors.append(f"case:{case['case_id']}: evaluation status/outcome contradict execution state")

        evidence = report["evidence_receipts"]
        evidence_refs: set[str] = set()
        for item in evidence:
            if item["sha256"] in evidence_refs or item["ref"] in evidence_refs:
                errors.append("evidence_receipts: duplicate ref or sha256")
            evidence_refs.add(item["sha256"])
            evidence_refs.add(item["ref"])
            ref_path = Path(item["ref"])
            if ref_path.is_absolute() or ".." in ref_path.parts:
                errors.append(f"evidence:{item['ref']}: reference must be a repository-relative path")
                continue
            resolved = (root / ref_path).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"evidence:{item['ref']}: reference escapes repository root")
                continue
            if not resolved.is_file():
                errors.append(f"evidence:{item['ref']}: referenced evidence file is missing")
            elif hashlib.sha256(resolved.read_bytes()).hexdigest() != item["sha256"]:
                errors.append(f"evidence:{item['ref']}: SHA-256 does not match file content")

        dimensions, _, _, _ = _profile_contract(profile)
        dimension_names = {item["name"] for item in dimensions}
        assertion_ids: set[str] = set()
        for assertion in report["assertions"]:
            aid = assertion["id"]
            if aid in assertion_ids:
                errors.append(f"assertion:{aid}: duplicate id")
            assertion_ids.add(aid)
            if assertion["case_id"] not in case_by_id:
                errors.append(f"assertion:{aid}: unknown case_id")
            if assertion["dimension"] not in dimension_names:
                errors.append(f"assertion:{aid}: dimension not in profile")
            case = case_by_id.get(assertion["case_id"])
            if case and ((assertion["execution_state"] == "executed") != (case["execution_state"] == "executed")):
                errors.append(f"assertion:{aid}: execution state contradicts case")
            if assertion["execution_state"] == "executed":
                if assertion["grade"] is None or not assertion["evidence_refs"]:
                    errors.append(f"assertion:{aid}: executed assertion requires a grade and evidence")
            elif assertion["grade"] is not None:
                errors.append(f"assertion:{aid}: unexecuted assertion must have null grade")
            for ref in assertion["evidence_refs"]:
                if ref not in evidence_refs:
                    errors.append(f"assertion:{aid}: unknown evidence ref {ref}")

        for label in ("strengths", "weaknesses"):
            rows = report[label]
            empty_reason = report[f"{label}_empty_reason"]
            if not rows and not (isinstance(empty_reason, str) and empty_reason.strip()):
                errors.append(f"{label}: empty list requires an explicit explanation")
            if rows and empty_reason is not None:
                errors.append(f"{label}: empty explanation must be null when findings exist")
            for row in rows:
                if row["dimension"] not in dimension_names:
                    errors.append(f"{label}: unknown dimension {row['dimension']}")
                for case_id in row["case_ids"]:
                    if case_id not in case_by_id:
                        errors.append(f"{label}: unknown case_id {case_id}")
                for ref in row["evidence_refs"]:
                    if ref not in evidence_refs:
                        errors.append(f"{label}: unknown evidence ref {ref}")

        critical_weaknesses = [w for w in report["weaknesses"] if w["severity"] in {"critical", "high"}]
        external_gates = list(report["decision"]["blocking_gates"])
        external_gates.extend(f"weakness:{idx}" for idx, _ in enumerate(critical_weaknesses, 1))
        computed = calculate_score(profile, report["assertions"], blocking_gates=external_gates)
        _compare_score(report["score"], {k: v for k, v in computed.items() if k != "decision"}, errors)
        expected_decision = {**computed["decision"], "next_actions": report["decision"]["next_actions"]}
        if report["decision"] != expected_decision:
            errors.append("decision: status or blocking gates do not match deterministic calculation")
        if report["decision"]["status"] != "PASS" and not report["decision"]["next_actions"]:
            errors.append("decision: non-PASS status requires at least one next action")
        expected_delta = _expected_delta(report, {k: v for k, v in computed.items() if k != "decision"})
        if report["comparison_delta"] != expected_delta:
            errors.append("comparison_delta: does not match comparator identity/score or explicit null reason")
    except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
        errors.append(f"semantic: {exc}")
    return sorted(set(errors))


def _compare_score(actual: dict[str, Any], expected: dict[str, Any], errors: list[str]) -> None:
    for key in ("scale", "status", "profile", "calculation_version", "coverage", "missing_evidence"):
        if actual.get(key) != expected.get(key):
            errors.append(f"score.{key}: does not match deterministic calculation")
    for key in ("value", "unrounded_value"):
        if actual.get(key) is None or expected.get(key) is None:
            if actual.get(key) is not expected.get(key):
                errors.append(f"score.{key}: does not match deterministic calculation")
        elif _decimal(actual[key], f"score.{key}") != _decimal(expected[key], f"score.{key}"):
            errors.append(f"score.{key}: does not match deterministic calculation")
    if len(actual.get("dimensions", [])) != len(expected["dimensions"]):
        errors.append("score.dimensions: count does not match profile")
        return
    for idx, (got, want) in enumerate(zip(actual["dimensions"], expected["dimensions"])):
        if got != want:
            errors.append(f"score.dimensions[{idx}]: does not match deterministic calculation")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="path to an Evaluation Report JSON document")
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        errors = validate_report(report)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID {exc}", file=sys.stderr)
        return 1
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID Evaluation Report v1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
