#!/usr/bin/env python3
"""Workflow-aware static audit of all registered Skills Factory Lab entrypoints."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

import yaml


def audit(root: Path) -> dict:
    registry_path = root / "workflows" / "runtime-registry.yaml"
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    items = data.get("workflows")
    if not isinstance(items, list):
        raise ValueError("runtime registry must have a workflows list")

    fixture_path = root / "evals" / "runtime-fixtures.yaml"
    fixture_data = yaml.safe_load(fixture_path.read_text(encoding="utf-8")) or {} if fixture_path.is_file() else {}
    central_targets = fixture_data.get("targets") or {}
    seen: set[str] = set()
    rows = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("workflow entry must be a mapping")
        name, source = item.get("name"), item.get("workflow")
        if not isinstance(name, str) or not isinstance(source, str) or name in seen:
            raise ValueError(f"invalid/duplicate workflow identity: {name!r}")
        seen.add(name)
        errors, warnings = [], []
        rel = Path(source)
        if rel.is_absolute() or ".." in rel.parts or rel.parts[:1] != ("workflows",) or rel.name != "WORKFLOW.md":
            errors.append("invalid registered source path")
            content = ""
        else:
            path = root / rel
            if not path.is_file():
                errors.append("registered WORKFLOW.md missing")
                content = ""
            else:
                content = path.read_text(encoding="utf-8")
        for label, cue in (("PURPOSE", "## Purpose"), ("OUTPUT_CONTRACT", "## Output contract")):
            if cue not in content:
                warnings.append(label)
        if not any(cue in content for cue in ("## Stages", "## Sequence", "## Stage 1", "## Routing", "## Gate sequence")):
            warnings.append("STAGE_OR_ROUTING_DISCLOSURE")
        if "## Stop conditions" not in content and "## Decision rules" not in content:
            warnings.append("STOP_OR_DECISION_BOUNDARY")
        if not any(cue in content for cue in ("## Preconditions", "## Entry criteria", "## Entry modes",
                                              "## Natural activation", "## Runtime routing preflight", "## Routing")):
            warnings.append("ENTRY_PRECONDITIONS_REVIEW")
        metadata = item.get("metadata")
        if not isinstance(metadata, dict) or any(not metadata.get(x) for x in
                                                 ("owner", "version", "maturity", "risk", "last_reviewed")):
            errors.append("incomplete version/maturity/owner metadata")
        desc = item.get("description")
        if not isinstance(desc, str) or len(desc.strip()) < 30:
            warnings.append("ROUTING_DESCRIPTION_REVIEW")
        deps = item.get("dependencies")
        if not isinstance(deps, dict) or "required" not in deps or "optional" not in deps:
            errors.append("required/optional dependency contract missing")
        channels = item.get("channels")
        if not isinstance(channels, dict) or not channels:
            errors.append("channel availability contract missing")
        local_tests = (root / rel.parent / "tests" / "cases.yaml").is_file()
        central_cases = central_targets.get(name) or []
        central_count = len(central_cases) if isinstance(central_cases, list) else 0
        if not local_tests and not central_count:
            warnings.append("NO_LOCAL_OR_CENTRAL_WORKFLOW_SUITE_CHECK_ALTERNATE_CAMPAIGNS")
        rows.append({
            "name": name, "source": source,
            "maturity": metadata.get("maturity") if isinstance(metadata, dict) else None,
            "local_test_suite_present": local_tests,
            "central_eval_case_count": central_count,
            "status": "STATIC_BLOCKER" if errors else "REVIEW_REQUIRED" if warnings else "STATIC_CHECKS_OK",
            "errors": errors, "review_signals": warnings,
            "semantic_review": "REQUIRED", "runtime_outcome": None, "runtime_evidence": "NOT_RUN",
        })

    counts = Counter(x["status"] for x in rows)
    signals = Counter(w for x in rows for w in x["review_signals"])
    return {
        "schema_version": "1.0",
        "scope": "registered_workflow_entrypoints",
        "source_revision": os.getenv("SOURCE_REVISION", "LOCAL_CHECKOUT_UNATTESTED"),
        "basis": "Skills Factory Cloud Next Lab 0.33.7, workflow-adapted specification, test design and validation",
        "total": len(rows), "statuses": dict(sorted(counts.items())),
        "review_signals": dict(sorted(signals.items())),
        "runtime": "NOT_RUN", "semantic_review": "REQUIRED",
        "workflows": rows,
        "limitations": [
            "A workflow registry and headings are source evidence, not model routing/behavior PASS.",
            "Missing local workflow suite may be covered by central isolated runtime fixtures: inspect both.",
            "Check runtime delegated tools, side effects and evidence through a separate version-bound campaign.",
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    report = audit(args.root.resolve())
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Workflow audit: {report['total']} registered; statuses={report['statuses']}; warnings={report['review_signals']}")
        for row in report["workflows"]:
            print(f"WORKFLOW {row['name']}: {row['status']}; signals={','.join(row['review_signals']) or 'none'}; runtime=NOT_RUN")
    else:
        print(payload, end="")
    return 1 if report["statuses"].get("STATIC_BLOCKER", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
