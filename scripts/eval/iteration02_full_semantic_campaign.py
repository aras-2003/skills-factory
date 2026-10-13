#!/usr/bin/env python3
"""Freeze full source-fixture campaign for every current skill/workflow.

This is a PREPARATION step only: it does not call a model, run a provider,
certify fixtures as good, or decide PASS. Executor gets only inputs, evaluator
rubrics live in a separate output root; immutable source SHA and hashes bind both.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

import yaml

HEX40 = re.compile(r"^[a-f0-9]{40}$")
RISK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def _suite(path: Path) -> list[dict]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing/unsafe fixture: {path}")
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = content.get("cases") if isinstance(content, dict) else None
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"empty/malformed suite: {path}")
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"]:
            raise ValueError(f"unnamed case: {path}")
        if case["id"] in seen:
            raise ValueError(f"duplicate case ID: {path}")
        seen.add(case["id"])
        if not isinstance(case.get("input"), str) or not case["input"].strip():
            raise ValueError(f"missing input: {path} {case['id']}")
        expected = case.get("expected")
        if not isinstance(expected, dict) or type(expected.get("should_trigger")) is not bool:
            raise ValueError(f"missing evaluator polarity: {path} {case['id']}")
    return cases


def _sources(root: Path) -> list[tuple[str, str, Path]]:
    skills = sorted((root / "skills").rglob("SKILL.md"))
    workflows_file = root / "workflows/runtime-registry.yaml"
    if not workflows_file.is_file():
        raise ValueError("canonical workflow registry missing")
    registry = yaml.safe_load(workflows_file.read_text(encoding="utf-8"))
    registered = registry.get("workflows") if isinstance(registry, dict) else None
    if not isinstance(registered, list):
        raise ValueError("malformed registered workflow inventory")
    all_items = [("skill", path.parent.name, path) for path in skills]
    for item in registered:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("malformed workflow registration")
        rel = item.get("workflow")
        if not isinstance(rel, str) or Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise ValueError("unsafe registered workflow source path")
        path = root / rel
        if not path.is_file() or path.name != "WORKFLOW.md":
            raise ValueError(f"registered workflow missing: {item['name']}")
        all_items.append(("workflow", item["name"], path))
    identities = [(kind, name) for kind, name, _ in all_items]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate component identity")
    if not skills or not registered:
        raise ValueError("empty canonical component inventory")
    return all_items


def freeze(root: Path, executor: Path, evaluator: Path, source_revision: str, *,
           min_positive: int = 1, min_negative: int = 1) -> dict:
    if not HEX40.fullmatch(source_revision):
        raise ValueError("exact 40-digit source revision required")
    if executor.exists() or evaluator.exists():
        raise ValueError("refuse overwrite: executor/evaluator output already exists")
    if executor.resolve() == evaluator.resolve() or executor.resolve().is_relative_to(evaluator.resolve()) or evaluator.resolve().is_relative_to(executor.resolve()):
        raise ValueError("executor and evaluator outputs require separate roots")
    if executor.resolve().is_relative_to(root.resolve()) and "skills" in executor.parts:
        raise ValueError("do not place exported fixture inputs within source skills")
    records = []
    coverage = []
    for kind, name, path in _sources(root):
        cases_path = path.parent / "tests/cases.yaml"
        source_rel = path.relative_to(root).as_posix()
        data_sha = digest(path.read_bytes())
        if not cases_path.is_file():
            coverage.append({"kind": kind, "name": name, "source": source_rel,
                             "state": "MISSING_LOCAL_SUITE_REQUIRES_REVIEW", "case_count": 0})
            continue
        cases = _suite(cases_path)
        pos = sum(case["expected"]["should_trigger"] for case in cases)
        neg = len(cases) - pos
        coverage.append({"kind": kind, "name": name, "source": source_rel,
                         "source_sha256": data_sha,
                         "state": "FIXTURES_PRESENT_REVIEW_REQUIRED" if pos >= min_positive and neg >= min_negative else "INSUFFICIENT_POLARITY",
                         "positive": pos, "negative": neg, "case_count": len(cases)})
        for case in cases:
            raw_input = case["input"].encode("utf-8")
            raw_rubric = stable(case["expected"])
            identifier = digest(stable([kind, name, case["id"]]))[:20]
            records.append({
                "case_id": identifier,
                "local_case_id": case["id"],
                "component_kind": kind, "component_name": name,
                "source": source_rel, "source_sha256": data_sha,
                "input_sha256": digest(raw_input),
                "rubric_sha256": digest(raw_rubric),
                "input_data": raw_input, "rubric_data": raw_rubric,
                "expected_trigger": case["expected"]["should_trigger"],
            })
    if not records:
        raise ValueError("no source fixtures available")
    manifest_rows = []
    executor.mkdir(parents=True, mode=0o700)
    evaluator.mkdir(parents=True, mode=0o700)
    (executor / "inputs").mkdir(mode=0o700)
    (evaluator / "rubrics").mkdir(mode=0o700)
    for row in records:
        identifier = row["case_id"]
        (executor / "inputs" / f"{identifier}.txt").write_bytes(row.pop("input_data"))
        (evaluator / "rubrics" / f"{identifier}.json").write_bytes(row.pop("rubric_data"))
        row["input_path"] = "inputs/" + identifier + ".txt"
        row["rubric_path"] = "rubrics/" + identifier + ".json"
        manifest_rows.append(row)
    missing = [x for x in coverage if x["state"] != "FIXTURES_PRESENT_REVIEW_REQUIRED"]
    report = {
        "schema_version": "1.0", "kind": "iteration02_full_component_fixture_campaign",
        "source_revision": source_revision,
        "skills": sum(x["kind"] == "skill" for x in coverage),
        "workflows": sum(x["kind"] == "workflow" for x in coverage),
        "fixtures": len(manifest_rows), "missing_or_insufficient": missing,
        "executor_runtime_state": "NOT_RUN", "independent_evaluator": "NOT_RUN",
        "model_behavior_verdict": "NOT_EVALUATED", "release_approved": False,
        "cases": [{k: v for k, v in x.items() if k != "rubric_path"} for x in manifest_rows],
    }
    if missing:
        report["status"] = "SOURCE_FIXTURE_COVERAGE_INCOMPLETE"
    else:
        report["status"] = "INPUTS_PREPARED_INDEPENDENT_REVIEW_REQUIRED"
    # Rubrics and their details NEVER appear in executor pack.
    (executor / "lock.json").write_bytes(stable(report) + b"\n")
    (evaluator / "lock.json").write_bytes(stable({
        "schema_version": "1.0", "kind": "independent_evaluator_only",
        "source_revision": source_revision, "model_behavior_verdict": "NOT_EVALUATED",
        "cases": [{"case_id": x["case_id"], "rubric_path": x["rubric_path"],
                   "rubric_sha256": x["rubric_sha256"]} for x in manifest_rows],
    }) + b"\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--executor-output", type=Path, required=True)
    parser.add_argument("--evaluator-output", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    try:
        report = freeze(args.root.resolve(), args.executor_output,
                        args.evaluator_output, args.source_revision)
        print(json.dumps({"status": report["status"], "skills": report["skills"],
                          "workflows": report["workflows"], "fixtures": report["fixtures"],
                          "missing_or_insufficient": len(report["missing_or_insufficient"])}))
        return int(report["status"] != "INPUTS_PREPARED_INDEPENDENT_REVIEW_REQUIRED")
    except (ValueError, OSError, TypeError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "BLOCKED", "error_class": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
