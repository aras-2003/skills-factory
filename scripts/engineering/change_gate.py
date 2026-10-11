#!/usr/bin/env python3
"""Risk-scoped test planning for Skills Factory changes (no model execution)."""
from __future__ import annotations

import argparse
import json
from pathlib import PurePosixPath, Path

CHANGE_CLASSES = ("NEW", "ROUTING", "BEHAVIOR", "RESOURCE", "DOCS")
GATES = {
    "NEW": (
        "specification_and_reuse_check",
        "early_test_design",
        "static_package_validation",
        "positive_indirect_near_miss_competing_routing",
        "behavioral_evals_and_regressions",
        "resource_security_review",
        "release_readiness",
    ),
    "ROUTING": (
        "static_package_validation",
        "positive_indirect_near_miss_competing_routing",
        "routing_regression_review",
        "release_readiness",
    ),
    "BEHAVIOR": (
        "static_package_validation",
        "behavioral_evals_and_regressions",
        "side_effect_and_security_review",
        "release_readiness",
    ),
    "RESOURCE": (
        "resource_helper_unit_tests",
        "dependent_skill_workflow_regressions",
        "side_effect_and_security_review",
        "release_readiness",
    ),
    "DOCS": ("documentation_diff_review", "static_document_validation"),
}


def safe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value and not path.is_absolute() and
                "\\" not in value and ".." not in path.parts and
                path.as_posix() == value and value not in {".", ".."})


def docs_only_path(path: str) -> bool:
    """Allow only obviously non-executable, non-contract editorial sources."""
    if path in {"README.md", "CHANGELOG.md"}:
        return True
    return path.startswith("docs/") and path.endswith(".md")


def plan(change_class: str, changed_files: list[str]) -> dict:
    if change_class not in GATES:
        raise ValueError(f"unknown change class: {change_class}")
    errors = []
    if not changed_files:
        errors.append("changed file list is required; do not guess DOCS-only scope")
    for name in changed_files:
        if not safe_path(name):
            errors.append(f"unsafe or noncanonical changed file path: {name!r}")
    if change_class == "DOCS":
        for name in changed_files:
            if safe_path(name) and not docs_only_path(name):
                errors.append(f"DOCS class cannot omit behavioral/resource tests for: {name}")
    checks = list(GATES[change_class])
    return {
        "schema_version": "1.0",
        "scope": "static_change_planning_only",
        "change_class": change_class,
        "changed_files": sorted(set(changed_files)),
        "status": "BLOCKED" if errors else "PLAN_READY",
        "blockers": errors,
        "required_checks": checks,
        "early_test_design_required": change_class == "NEW",
        "runtime_case_execution": "NOT_RUN",
        "runtime_pass_claim": False,
        "release_authorized": False,
        "handoff": {
            "implementation": "record exact changed files and source revision",
            "evidence": "link static validation and any executed scoped eval receipts; keep unexecuted cases NOT_RUN",
            "next_step": "run required scoped gates; obtain release review separately if applicable",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--change-class", choices=CHANGE_CLASSES, required=True)
    parser.add_argument("--path", action="append", dest="paths", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = plan(args.change_class, args.paths)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
