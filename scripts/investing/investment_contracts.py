"""Validation helpers for the versioned Investment OS specialist exchange."""
from __future__ import annotations

import copy
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


SCHEMAS = {
    "context": Path("schemas/investing/analysis-context-v1.schema.json"),
    "result": Path("schemas/investing/specialist-result-v1.schema.json"),
}
COMPARISON_FIELDS = (
    "metric_id", "definition", "unit", "period_start", "period_end",
    "accounting_basis", "adjustment_basis", "corporate_action_basis", "currency",
)


def _schema(root: Path, kind: str) -> dict[str, Any]:
    return json.loads((root / SCHEMAS[kind]).read_text(encoding="utf-8"))


def _schema_errors(value: object, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"schema {('/'.join(map(str, err.absolute_path)) or '$')}: {err.message}"
        for err in sorted(validator.iter_errors(value), key=lambda err: list(map(str, err.absolute_path)))
    ]


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def metric_comparability(left: dict[str, Any], right: dict[str, Any], *, as_of: str) -> dict[str, Any]:
    """Return whether two reported observations can be directly compared.

    This deliberately does not convert currency, accounting bases, periods, or
    corporate-action treatment. It preserves both measurements for a caller.
    """
    differences = [field for field in COMPARISON_FIELDS if left.get(field) != right.get(field)]
    missing = [field for field in COMPARISON_FIELDS if left.get(field) in (None, "") or right.get(field) in (None, "")]
    for basis, applicability in (
        ("currency", "currency_applicability"),
        ("corporate_action_basis", "corporate_action_applicability"),
    ):
        if left.get(applicability) != right.get(applicability):
            differences.append(applicability)
        if left.get(applicability) == right.get(applicability) == "NOT_APPLICABLE":
            missing = [field for field in missing if field != basis]
    if left.get("raw_value") is None or right.get("raw_value") is None:
        differences.append("missing_value")
    if not left.get("published_at") or not right.get("published_at"):
        differences.append("missing_publication_time")
    for label, metric in (("left", left), ("right", right)):
        source_ids = metric.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            differences.append(f"{label}_missing_source_ids")
        if not metric.get("observed_at"):
            differences.append(f"{label}_missing_observation_time")
        if metric.get("evidence_status") != "VERIFIED":
            differences.append(f"{label}_evidence_{metric.get('evidence_status', 'UNKNOWN').lower()}")
    cutoff = _instant(as_of)
    late = []
    for label, metric in (("left", left), ("right", right)):
        raw_value = metric.get("raw_value")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)) or not math.isfinite(raw_value):
            differences.append(f"{label}_invalid_value")
        published_at = metric.get("published_at")
        observed_at = metric.get("observed_at")
        try:
            if published_at and _instant(published_at) > cutoff:
                late.append(label)
            if observed_at and _instant(observed_at) > cutoff:
                late.append(f"{label}_observation")
            if metric.get("period_end") and date.fromisoformat(metric["period_end"]) > cutoff.date():
                late.append(f"{label}_period")
            if metric.get("period_start") and metric.get("period_end"):
                if date.fromisoformat(metric["period_start"]) > date.fromisoformat(metric["period_end"]):
                    differences.append(f"{label}_invalid_period")
            elif not metric.get("period_start") or not metric.get("period_end"):
                differences.append(f"{label}_missing_period")
        except (TypeError, ValueError):
            differences.append(f"{label}_invalid_time")
    if late:
        differences.append("time_after_as_of")
    if missing:
        differences.append("missing_comparison_basis")
    return {
        "status": "COMPARABLE" if not differences else "NOT_COMPARABLE",
        "reason_codes": sorted(set(differences)),
        "preserved_values": [left.get("raw_value"), right.get("raw_value")],
    }


def validate_exchange(context: object, results: object, *, root: Path) -> list[str]:
    """Validate shape and cross-document invariants without fetching evidence."""
    errors: list[str] = []
    if not isinstance(context, dict):
        return ["context must be an object"]
    if not isinstance(results, list):
        return ["results must be an array"]
    context_errors = _schema_errors(context, _schema(root, "context"))
    result_schema = _schema(root, "result")
    errors.extend(f"context {error}" for error in context_errors)
    for index, result in enumerate(results):
        errors.extend(f"results/{index} {error}" for error in _schema_errors(result, result_schema))
    if errors:
        return errors

    cutoff = _instant(context["as_of"])
    if cutoff.utcoffset() != timezone.utc.utcoffset(cutoff):
        errors.append("context as_of must be expressed in UTC")
    horizon = context["horizon"]
    if horizon["min_months"] > horizon["max_months"]:
        errors.append("horizon min_months must not exceed max_months")
    scope = context["write_scope"]
    if context["execution_mode"] in {"TEST", "HISTORICAL_REPLAY"} and scope["mode"] != "NONE":
        errors.append("test and historical replay contexts must have write_scope NONE")
    if scope["mode"] == "EXPLICIT_OPERATION" and context["context_mode"] != "CANONICAL":
        errors.append("explicit write scope requires canonical context")

    result_ids: set[str] = set()
    claim_ids: set[str] = set()
    evidence: dict[str, dict[str, Any]] = {}
    if set(context["requested_skills"]) & {"position-sizing-review", "portfolio-state-review"}:
        if context["context_mode"] == "CANONICAL" and not context.get("policy_version_ref"):
            errors.append("portfolio analysis requires an explicit policy_version_ref")
        if context["context_mode"] == "CANONICAL" and not context.get("portfolio_snapshot_ref"):
            errors.append("portfolio analysis requires an explicit portfolio_snapshot_ref")
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            continue
        result_id = result["result_id"]
        if result_id in result_ids:
            errors.append(f"duplicate result_id: {result_id}")
        result_ids.add(result_id)
        if result["producer"]["skill_id"] not in context["requested_skills"]:
            errors.append(f"results/{index} producer was not requested: {result['producer']['skill_id']}")
        if result["analysis_id"] != context["analysis_id"]:
            errors.append(f"results/{index} analysis_id mismatch")
        if result["instrument_id"] != context["instrument"]["canonical_id"]:
            errors.append(f"results/{index} instrument_id mismatch")
        if _instant(result["as_of"]) != cutoff:
            errors.append(f"results/{index} as_of mismatch")
        local_evidence: set[str] = set()
        local_metric_ids: set[str] = set()
        for ref in result["evidence_refs"]:
            source_id = ref["source_id"]
            if source_id in local_evidence:
                errors.append(f"duplicate evidence source_id within result: {source_id}")
            if source_id in evidence and evidence[source_id] != ref:
                errors.append(f"conflicting definitions for evidence source_id: {source_id}")
            local_evidence.add(source_id)
            evidence[source_id] = ref
            if _instant(ref["published_at"]) > cutoff:
                errors.append(f"evidence published after as_of: {source_id}")
            if _instant(ref["allowed_as_of"]) < cutoff:
                errors.append(f"evidence is not allowed at context as_of: {source_id}")
        for finding in result["findings"]:
            claim_id = finding["claim_id"]
            if claim_id in claim_ids:
                errors.append(f"duplicate claim_id: {claim_id}")
            claim_ids.add(claim_id)
            if finding["horizon"] != context["horizon"]:
                errors.append(f"finding {claim_id} horizon differs from AnalysisContext")
            if finding["evidence_status"] in {"VERIFIED", "PROVISIONAL"} and not finding["evidence_ids"]:
                errors.append(f"finding {claim_id} has evidence status but no evidence ids")
            for source_id in finding["evidence_ids"] + finding["counterevidence_ids"]:
                if source_id not in local_evidence:
                    errors.append(f"unresolved finding evidence id: {source_id}")
                elif finding["evidence_status"] == "VERIFIED" and not _immutable_source(evidence[source_id]):
                    errors.append(f"verified finding lacks immutable source locator: {claim_id}")
        for metric in result["metrics"]:
            if metric["metric_id"] in local_metric_ids:
                errors.append(f"duplicate metric_id within result: {metric['metric_id']}")
            local_metric_ids.add(metric["metric_id"])
            for source_id in metric["source_ids"]:
                if source_id not in local_evidence:
                    errors.append(f"unresolved metric source id: {source_id}")
                elif metric["evidence_status"] == "VERIFIED" and not _immutable_source(evidence[source_id]):
                    errors.append(f"verified metric lacks immutable source locator: {metric['metric_id']}")
            if metric["evidence_status"] == "VERIFIED":
                for field, applicability_field in (
                    ("currency", "currency_applicability"),
                    ("corporate_action_basis", "corporate_action_applicability"),
                ):
                    applicability = metric[applicability_field]
                    value = metric[field]
                    if applicability == "REQUIRED" and value in (None, ""):
                        errors.append(f"verified metric missing required {field}: {metric['metric_id']}")
                    if applicability == "NOT_APPLICABLE" and value not in (None, ""):
                        errors.append(f"verified metric has inapplicable {field}: {metric['metric_id']}")
                    if applicability == "UNKNOWN":
                        errors.append(f"verified metric has unknown {field} applicability: {metric['metric_id']}")
            if metric["published_at"] and _instant(metric["published_at"]) > cutoff:
                errors.append(f"metric published after as_of: {metric['metric_id']}")
            if metric["observed_at"] and _instant(metric["observed_at"]) > cutoff:
                errors.append(f"metric observed after as_of: {metric['metric_id']}")
            if metric["period_start"] and metric["period_end"]:
                period_start = date.fromisoformat(metric["period_start"])
                period_end = date.fromisoformat(metric["period_end"])
                if period_start > period_end:
                    errors.append(f"metric period starts after it ends: {metric['metric_id']}")
                if period_end > cutoff.date():
                    errors.append(f"metric period ends after as_of: {metric['metric_id']}")
            if metric.get("raw_value") is not None and not math.isfinite(metric["raw_value"]):
                errors.append(f"metric raw_value must be finite: {metric['metric_id']}")
        if result["execution_status"] in {"BLOCKED", "FAILED", "NOT_RUN"} and (result["findings"] or result["metrics"]):
            errors.append(f"{result['execution_status']} result cannot carry findings or metrics")
    graph = {item["result_id"]: set(item["source_result_refs"]) for item in results}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(result_id: str) -> None:
        if result_id in visiting:
            errors.append(f"source_result_refs contain a cycle at: {result_id}")
            return
        if result_id in visited:
            return
        visiting.add(result_id)
        for parent_id in graph.get(result_id, set()):
            visit(parent_id)
        visiting.remove(result_id)
        visited.add(result_id)

    for result_id in graph:
        visit(result_id)
    for result in results:
        if not isinstance(result, dict):
            continue
        if result["result_id"] in result["source_result_refs"]:
            errors.append(f"result cannot reference itself: {result['result_id']}")
        for ref in result["source_result_refs"]:
            if ref not in result_ids:
                errors.append(f"unresolved source_result_ref: {ref}")
    for source_id in context["evidence_snapshot_refs"]:
        if source_id not in evidence:
            errors.append(f"unresolved context evidence snapshot: {source_id}")
    return errors


def _immutable_source(ref: dict[str, Any]) -> bool:
    return bool(ref.get("source_sha256") and ref.get("locator") and ref.get("archive_snapshot_ref"))


def wrap_legacy_result(
    *, context: dict[str, Any], skill_id: str, version: str, source_sha: str,
    payload_schema_version: str, payload: dict[str, Any], result_id: str,
    execution_status: str, applicability: str,
    evidence_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Wrap, but never rewrite, one existing specialist output as opaque v1 data."""
    supported = {"security-underwriting", "technical-structure", "valuation-scenario-review"}
    if skill_id not in supported:
        raise ValueError(f"unsupported legacy producer: {skill_id}")
    if skill_id not in context.get("requested_skills", []):
        raise ValueError(f"legacy producer was not requested: {skill_id}")
    return {
        "contract_version": "1.0", "result_id": result_id,
        "analysis_id": context["analysis_id"],
        "producer": {"skill_id": skill_id, "version": version, "source_sha": source_sha},
        "instrument_id": context["instrument"]["canonical_id"], "as_of": context["as_of"],
        "execution_status": execution_status, "applicability": applicability,
        "payload_type": f"LEGACY_OPAQUE:{skill_id}",
        "payload_schema_version": payload_schema_version, "payload": copy.deepcopy(payload),
        "evidence_refs": copy.deepcopy(evidence_refs or []), "findings": [], "metrics": [], "blockers": [],
        "handoff": [], "source_result_refs": [],
    }


def validate_files(context_path: Path, results_path: Path, *, root: Path) -> list[str]:
    try:
        context = json.loads(context_path.read_text(encoding="utf-8"))
        results = json.loads(results_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"cannot read JSON input: {exc}"]
    return validate_exchange(context, results, root=root)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", type=Path)
    parser.add_argument("results", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    failures = validate_files(args.context, args.results, root=args.root)
    if failures:
        print("\n".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print("Investment specialist exchange valid (source identity not independently verified).")
