#!/usr/bin/env python3
"""Generate source-locked evaluator-isolated campaign for *all* current skills/workflows.

Uses actual existing cases.yaml / runtime-fixtures.yaml, never generated case
prompts, inferred expected answers, live clients or production data. Executor
bundle contains only input prompts + digests, separate evaluator plan contains
rubrics. Not equivalent to model runtime execution or release certification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/engineering"))
from audit_skill_lifecycle import audit as audit_skills  # noqa: E402
from audit_workflow_lifecycle import audit as audit_workflows  # noqa: E402

HEX40 = re.compile(r"^[0-9a-f]{40}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,120}$")
MAX_CASE_BYTES = 192_000


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(root: Path, rel: str, prefix: str) -> Path:
    if not isinstance(rel, str) or not rel or "\\" in rel:
        raise ValueError("path missing/backslash")
    p = Path(rel)
    if p.is_absolute() or any(part in {"..", "."} for part in p.parts) or p.parts[0] != prefix:
        raise ValueError(f"unsafe path in {prefix}: {rel}")
    full = root / p
    if not full.resolve().is_relative_to(root.resolve()) or not full.is_file() or full.is_symlink():
        raise ValueError(f"missing/unsafe source: {rel}")
    return full


def _load_yaml(file: Path) -> object:
    raw = file.read_bytes()
    if not raw or len(raw) > MAX_CASE_BYTES:
        raise ValueError(f"empty/oversized fixture: {file.name}")
    return yaml.safe_load(raw)


def _local_cases(root: Path, source: str, kind: str) -> list[dict]:
    p = safe_path(root, source, "skills" if kind == "skill" else "workflows")
    suite = p.parent / "tests/cases.yaml"
    if not suite.is_file():
        return []
    if suite.is_symlink() or not suite.resolve().is_relative_to(root.resolve()):
        raise ValueError("untrusted suite path")
    data = _load_yaml(suite)
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        raise ValueError("suite must provide cases list")
    cases: list[dict] = []
    seen = set()
    for c in data["cases"]:
        if not isinstance(c, dict):
            raise ValueError("nonmapping test fixture")
        ident, prompt, expected = c.get("id"), c.get("input"), c.get("expected")
        if not isinstance(ident, str) or not SAFE_ID.fullmatch(ident) or ident in seen:
            raise ValueError(f"invalid/duplicate case id {ident!r}")
        seen.add(ident)
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt.encode()) > MAX_CASE_BYTES:
            raise ValueError(f"{ident}: missing/oversized prompt")
        if not isinstance(expected, dict) or not expected:
            raise ValueError(f"{ident}: evaluator expected map missing")
        cases.append({"id": ident, "input": prompt, "expected": expected,
                      "source": suite.relative_to(root).as_posix(), "fixture_kind": "local"})
    return cases


def _central_cases(root: Path, name: str, targets: dict) -> list[dict]:
    rows = targets.get(name, [])
    if not isinstance(rows, list):
        raise ValueError("central fixture list malformed")
    selected = []
    for item in rows:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not SAFE_ID.fullmatch(item["id"]):
            raise ValueError("central fixture ID malformed")
        pin, rubric = item.get("input"), item.get("rubric")
        pin_file = safe_path(root, pin, "evals")
        rubric_file = safe_path(root, rubric, "evals")
        prompt = pin_file.read_text(encoding="utf-8")
        rubric_bytes = rubric_file.read_bytes()
        if not prompt.strip() or len(prompt.encode()) > MAX_CASE_BYTES or not rubric_bytes or len(rubric_bytes) > MAX_CASE_BYTES:
            raise ValueError("central fixture input/rubric oversized or empty")
        expected = _load_yaml(rubric_file)
        if not isinstance(expected, dict) or not expected:
            raise ValueError("central fixture rubric must be mapping")
        selected.append({"id": item["id"], "input": prompt, "expected": expected,
                         "source": pin_file.relative_to(root).as_posix(),
                         "rubric_source": rubric_file.relative_to(root).as_posix(),
                         "fixture_kind": "central"})
    return selected


def build(root: Path, source_revision: str) -> tuple[dict, list[dict], list[dict]]:
    if not isinstance(source_revision, str) or not HEX40.fullmatch(source_revision):
        raise ValueError("exact 40-hex source revision required")
    root = root.resolve()
    audit_s, audit_w = audit_skills(root), audit_workflows(root)
    src_s = audit_s.get("skills")
    src_w = audit_w.get("workflows")
    if not isinstance(src_s, list) or not isinstance(src_w, list) or not src_s or not src_w:
        raise ValueError("malformed/incomplete lifecycle inventories")
    if len(src_s) != len(list((root / "skills").rglob("SKILL.md"))):
        raise ValueError("skills inventory drift")
    registry = _load_yaml(root / "workflows/runtime-registry.yaml")
    names = [x.get("name") for x in registry.get("workflows", [])]
    if len(src_w) != len(names) or len(names) != len(set(names)):
        raise ValueError("workflow registry drift")
    fixture_sources = _load_yaml(root / "evals/runtime-fixtures.yaml")
    targets = fixture_sources.get("targets")
    if not isinstance(targets, dict):
        raise ValueError("central runtime targets absent")
    manifest, executor, evaluator, errors = [], [], [], []
    counts = Counter()
    observed = set()
    for kind, rows in (("skill", src_s), ("workflow", src_w)):
        for row in rows:
            name, src = row.get("name"), row.get("source")
            if not isinstance(name, str) or not SAFE_ID.fullmatch(name) or (kind, name) in observed:
                errors.append(f"{kind}: invalid/duplicate {name}")
                continue
            observed.add((kind, name))
            try:
                path = safe_path(root, src, "skills" if kind == "skill" else "workflows")
                cases = _local_cases(root, src, kind) + _central_cases(root, name, targets)
                case_ids = set()
                selected = []
                polarity = Counter()
                for c in cases:
                    if c["id"] in case_ids:
                        raise ValueError("duplicate case ID across local/central fixture")
                    case_ids.add(c["id"])
                    polarity["positive" if c["expected"].get("should_trigger") is True else
                             "negative" if c["expected"].get("should_trigger") is False else "unclassified"] += 1
                    case_key = f"{kind}--{name}--{c['id']}"
                    if len(case_key) > 250:
                        raise ValueError("case key too long")
                    prompt_bytes = c["input"].encode("utf-8")
                    rubric_bytes = canonical(c["expected"])
                    pin, rubric_pin = digest(prompt_bytes), digest(rubric_bytes)
                    selected.append(case_key)
                    executor.append({
                        "key": case_key, "kind": kind, "component": name,
                        "source_revision": source_revision,
                        "input_sha256": pin, "rubric_sha256": rubric_pin,
                        "input": c["input"], "execution_state": "NOT_RUN",
                        "result": None, "channel": "LAB_TEST_ONLY_PENDING_APPROVAL",
                    })
                    evaluator.append({
                        "key": case_key, "source_revision": source_revision,
                        "input_sha256": pin, "rubric_sha256": rubric_pin,
                        "expected": c["expected"], "rubric_source": c.get("rubric_source") or c["source"],
                        "evaluator_result": "NOT_RUN",
                    })
                if not selected:
                    errors.append(f"{kind}/{name}: no reusable input/expected fixtures")
                if kind == "skill" and (polarity["positive"] < 2 or polarity["negative"] < 2):
                    errors.append(f"skill/{name}: insufficient explicit positive/negative fixture polarity")
                manifest.append({
                    "kind": kind, "name": name, "source": src,
                    "source_sha256": digest(path.read_bytes()),
                    "case_count": len(selected), "case_keys": selected,
                    "local_or_central_fixtures": dict(polarity),
                    "semantic_status": "NEEDS_INDEPENDENT_REVIEW",
                    "runtime_execution": "NOT_RUN",
                })
                counts[kind] += 1
            except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
                errors.append(f"{kind}/{name}: {type(exc).__name__}: {exc}")
    report = {
        "schema_version": "1.0", "kind": "source_bound_full_behavior_test_handoff",
        "source_revision": source_revision,
        "skill_count": counts["skill"], "registered_workflow_count": counts["workflow"],
        "case_count": len(executor), "evaluator_case_count": len(evaluator),
        "status": "BLOCKED_SOURCE" if errors else "INPUTS_READY_RUNTIME_NOT_RUN",
        "errors": errors, "components": manifest,
        "source_inventory": "lifecycle_audit+runtime_registry+actual_cases.yaml",
        "executor_rubrics_included": False, "provider_model_execution": "NOT_RUN",
        "independent_evaluator": "NOT_RUN", "release_approved": False,
        "note": "A source fixture is not a runtime tool trace. Missing cases block; never synthesize prompts, behavioral outcomes, or write permissions.",
    }
    if len(executor) != len({x["key"] for x in executor}) or len(evaluator) != len(executor):
        report["errors"].append("case collision/incomplete evaluator mapping")
        report["status"] = "BLOCKED_SOURCE"
    return report, executor, evaluator


def write_outputs(root: Path, source_revision: str, out: Path) -> dict:
    report, executor, evaluator = build(root, source_revision)
    if out.exists():
        raise ValueError("output directory exists; will not replace or rewrite evidence")
    out.mkdir(parents=True)
    (out / "source-audit.json").write_text(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if report["status"] != "INPUTS_READY_RUNTIME_NOT_RUN":
        # No runnable prompt package from an incomplete source campaign.
        return report
    (out / "executor-inputs.json").write_text(json.dumps({
        "source_revision": source_revision, "cases": executor, "runtime_execution": "NOT_RUN",
        "provider_authentication": "NOT_VERIFIED", "evaluator_rubric_content": "EXCLUDED",
        "writes_authorized": False,
    }, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Isolated evaluator folder must NOT be shipped as executor artifact.
    separate = out / "evaluator-only"
    separate.mkdir()
    (separate / "rubrics.json").write_text(json.dumps({
        "source_revision": source_revision, "cases": evaluator, "evaluation": "NOT_RUN",
    }, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--source-revision", default=os.getenv("SOURCE_REVISION", ""))
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        report = write_outputs(args.root, args.source_revision, args.output)
    except (OSError, ValueError, UnicodeError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "BLOCKED_SOURCE", "errors": [str(exc)],
                          "provider_model_execution": "NOT_RUN", "release_approved": False}))
        return 1
    print(json.dumps({k: report[k] for k in ("status", "skill_count", "registered_workflow_count", "case_count", "errors")}))
    return 0 if report["status"] == "INPUTS_READY_RUNTIME_NOT_RUN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
