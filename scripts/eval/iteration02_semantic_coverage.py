#!/usr/bin/env python3
"""Source-only coverage matrix for all current skills and registered workflows.

Reuses lifecycle audits as its *single* inventory authority. Does NOT execute
a model, generate invented semantic verdicts or replace independent campaigns.
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/engineering"))
from audit_skill_lifecycle import audit as audit_skills  # noqa: E402
from audit_workflow_lifecycle import audit as audit_workflows  # noqa: E402

HEX40 = re.compile(r"^[0-9a-f]{40}$")


def assess(skills: object, workflows: object, root: Path) -> dict:
    errors: list[str] = []
    if not isinstance(skills, dict) or not isinstance(workflows, dict):
        return {"status": "BLOCKED_SOURCE", "errors": ["malformed lifecycle audit inputs"],
                "runtime_execution": "NOT_RUN", "model_behavior_verified": False}
    s_rows, w_rows = skills.get("skills"), workflows.get("workflows")
    if not isinstance(s_rows, list) or not isinstance(w_rows, list):
        return {"status": "BLOCKED_SOURCE", "errors": ["missing component arrays"],
                "runtime_execution": "NOT_RUN", "model_behavior_verified": False}
    sources_s = {x.relative_to(root).as_posix() for x in (root / "skills").rglob("SKILL.md")}
    sources_w = {x.relative_to(root).as_posix() for x in (root / "workflows").rglob("WORKFLOW.md")}
    if skills.get("total_skills") != len(s_rows) or workflows.get("total") != len(w_rows):
        errors.append("lifecycle source counts disagree with row counts")
    if len(s_rows) != len(sources_s):
        errors.append("skill lifecycle inventory incomplete")
    # Source workflows also include unregistered ones. The workflow lifecycle
    # report deliberately covers only registered runtime entrypoints.
    components, seen = [], set()
    for kind, rows in (("skill", s_rows), ("workflow", w_rows)):
        for row in rows:
            if not isinstance(row, dict):
                errors.append(f"{kind}: malformed lifecycle row")
                continue
            name, source = row.get("name"), row.get("source")
            if not isinstance(name, str) or not name or not isinstance(source, str):
                errors.append(f"{kind}: invalid component name/source")
                continue
            identity = (kind, name)
            if identity in seen:
                errors.append(f"{kind}: duplicate {name}")
            seen.add(identity)
            permitted_sources = sources_s if kind == "skill" else sources_w
            if source not in permitted_sources:
                errors.append(f"{kind}: source absent or untrusted {name}")
                file_digest = None
            else:
                original = root / source
                file_digest = hashlib.sha256(original.read_bytes()).hexdigest() if original.is_file() else None
            signals = []
            if kind == "skill":
                count = row.get("case_count")
                positive, negative = row.get("positive_cases"), row.get("negative_cases")
                if any(type(n) is not int or n < 0 for n in (count, positive, negative)):
                    errors.append(f"{name}: malformed routing fixture counts")
                    continue
                if positive + negative > count:
                    errors.append(f"{name}: polarity exceeds number of test cases")
                if positive == 0:
                    signals.append("NO_POSITIVE_ROUTING_FIXTURE")
                if negative == 0:
                    signals.append("NO_NEGATIVE_ROUTING_FIXTURE")
                if positive < 2 or negative < 2:
                    signals.append("INSUFFICIENT_NEAR_MISS_DIVERSITY")
                if row.get("static_robustness_signal") is not True:
                    signals.append("EDGE_CASE_REVIEW_REQUIRED")
                suite = row.get("test_source")
                if not isinstance(suite, str) or not (root / suite).is_file():
                    signals.append("TEST_SOURCE_MISSING")
                case_count = count
            else:
                local = row.get("local_test_suite_present")
                central = row.get("central_eval_case_count")
                if type(local) is not bool or type(central) is not int or central < 0:
                    errors.append(f"{name}: invalid workflow fixture declaration")
                    continue
                case_count = central
                if not local and central == 0:
                    signals.append("WORKFLOW_TEST_COVERAGE_NOT_LOCATED")
                if not local:
                    signals.append("NO_LOCAL_WORKFLOW_SUITE")
                if central == 0:
                    signals.append("NO_CENTRAL_WORKFLOW_FIXTURE")
            status = row.get("status")
            if status not in {"STATIC_BLOCKER", "REVIEW_REQUIRED", "STATIC_CHECKS_OK"}:
                errors.append(f"{name}: invalid static audit status")
            if status == "STATIC_BLOCKER":
                signals.append("SOURCE_STATIC_BLOCKER")
            # Existing local suites are not equivalent to independent tool/model
            # behavior traces. No row is ever made acceptance-ready here.
            components.append({
                "kind": kind, "name": name, "source": source,
                "source_sha256": file_digest, "static_status": status,
                "lifecycle_case_count": case_count,
                "routing_positive_cases": positive if kind == "skill" else None,
                "routing_negative_cases": negative if kind == "skill" else None,
                "review_signals": sorted(set(signals)),
                "next_test_action": "RUN_VERSION_BOUND_INDEPENDENT_SEMANTIC_CAMPAIGN",
                "model_execution": "NOT_RUN",
                "runtime_behavioral_acceptance": "NOT_VERIFIED",
                "independent_evaluator": "NOT_RUN",
            })
    source_revision = os.getenv("SOURCE_REVISION", "")
    if not HEX40.fullmatch(source_revision):
        source_revision = "LOCAL_CHECKOUT_UNATTESTED"
    signal_counter = Counter(x for c in components for x in c["review_signals"])
    return {
        "schema_version": "1.0", "kind": "iteration02_static_semantic_coverage",
        "status": "BLOCKED_SOURCE" if errors else "SOURCE_INVENTORY_REVIEW_REQUIRED",
        "errors": sorted(set(errors)), "source_revision": source_revision,
        "skill_count": len([c for c in components if c["kind"] == "skill"]),
        "registered_workflow_count": len([c for c in components if c["kind"] == "workflow"]),
        "unregistered_source_workflow_count": len(sources_w) - len(w_rows),
        "routing_fixture_signals": dict(sorted(signal_counter.items())),
        "components": sorted(components, key=lambda x: (x["kind"], x["name"])),
        "runtime_execution": "NOT_RUN", "model_behavior_verified": False,
        "independent_evaluation": "NOT_RUN", "release_approved": False,
        "note": "Static fixture counts are NOT pass results. Previous 54/16 coverage must never silently certify current 64/19.",
    }


def build(root: Path = ROOT) -> dict:
    return assess(audit_skills(root), audit_workflows(root), root)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        report = build(args.root)
    except (OSError, ValueError, TypeError) as error:
        report = {"status": "BLOCKED_SOURCE", "errors": [type(error).__name__],
                  "runtime_execution": "NOT_RUN", "release_approved": False}
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return int(report["status"] != "SOURCE_INVENTORY_REVIEW_REQUIRED")


if __name__ == "__main__":
    raise SystemExit(main())
