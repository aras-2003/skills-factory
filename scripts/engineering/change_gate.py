#!/usr/bin/env python3
"""Risk-scoped test planning for Skills Factory changes (no model execution)."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import PurePosixPath, Path

CHANGE_CLASSES = ("NEW", "ROUTING", "BEHAVIOR", "RESOURCE", "TEST_DESIGN", "DOCS")
DOCS_ONLY_ALLOWLIST = {"README.md", "CHANGELOG.md", "docs/roadmap/README.md"}
TEST_DESIGN_ROOT = "evals/campaigns/"
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
    "TEST_DESIGN": (
        "case_ids_and_expected_results_review",
        "coverage_and_channel_mapping_review",
        "evidence_identity_and_state_review",
    ),
    "DOCS": ("documentation_diff_review", "static_document_validation"),
}


def safe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value and not path.is_absolute() and
                "\\" not in value and "\x00" not in value and ".." not in path.parts and
                path.as_posix() == value and value not in {".", ".."})


def docs_only_path(path: str) -> bool:
    """Allow only explicitly reviewed editorial paths; other docs can define contracts."""
    return path in DOCS_ONLY_ALLOWLIST


def test_design_path(path: str) -> bool:
    """Keep standalone campaign designs separate from product and executable tests."""
    return path.startswith(TEST_DESIGN_ROOT) and path.endswith((".md", ".yaml", ".yml", ".json"))


def plan(change_class: str, changed_files: list[str], *, architecture_impact: str = "UNKNOWN",
         consumers: list[str] | None = None, graph_reviewed: bool = False,
         security_sensitive: bool = False) -> dict:
    if change_class not in GATES:
        raise ValueError(f"unknown change class: {change_class}")
    errors = []
    if architecture_impact is None:
        errors.append("Architecture Impact is required; use UNKNOWN when it is not assessed")
    if not changed_files:
        errors.append("changed file list is required; do not guess DOCS-only scope")
    for name in changed_files:
        if not safe_path(name):
            errors.append(f"unsafe or noncanonical changed file path: {name!r}")
    if change_class == "DOCS":
        for name in changed_files:
            if safe_path(name) and not docs_only_path(name):
                errors.append(f"DOCS class cannot omit behavioral/resource tests for: {name}")
    if change_class == "TEST_DESIGN":
        for name in changed_files:
            if safe_path(name) and not test_design_path(name):
                errors.append(f"TEST_DESIGN class is limited to versioned eval campaign definitions: {name}")
    checks = list(GATES[change_class])
    consumers = sorted(set(consumers or []))
    if architecture_impact is not None:
        if architecture_impact not in {"A0", "A1", "A2", "A3", "A4", "UNKNOWN"}:
            errors.append("Architecture Impact must use the native A0-A4 field or UNKNOWN")
        if architecture_impact == "A0" and change_class not in {"DOCS", "TEST_DESIGN"}:
            errors.append("A0 cannot describe a runtime/contract change")
        if any(not safe_path(path) for path in consumers):
            errors.append("consumer paths must be canonical repository paths")
        if architecture_impact in {"A3", "A4"} or security_sensitive:
            checks += ["architecture_approval", "consumer_contract_regressions", "migration_rollback_review"]
        elif architecture_impact == "A2":
            checks += ["extension_boundary_review", "consumer_contract_regressions"]
        elif architecture_impact == "A1":
            checks += ["preserved_interface_regression"]
        # Caller review and tracked path presence cannot establish graph completeness.
        if architecture_impact in {"UNKNOWN", "A4"} or change_class not in {"DOCS", "TEST_DESIGN"}:
            checks += ["full_affected_channel_baseline"]
        if security_sensitive:
            checks += ["negative_authorization_and_data_safety_tests", "reviewer_other_than_author"]
    return {
        "schema_version": "1.0",
        "scope": "static_change_planning_only",
        "change_class": change_class,
        "architecture_impact": architecture_impact,
        "consumer_paths": consumers,
        "dependency_graph_reviewed": False,
        "dependency_graph_review_claimed": graph_reviewed,
        "dependency_graph_status": "UNKNOWN",
        "changed_files": sorted(set(changed_files)),
        "status": "BLOCKED" if errors else "PLAN_READY",
        "blockers": errors,
        "required_checks": list(dict.fromkeys(checks)),
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


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", "--no-replace-objects", *args], stderr=subprocess.DEVNULL)


def resolve_commit(revision: str, label: str, blockers: list[str]) -> str | None:
    try:
        return git_output("rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}").decode("ascii").strip()
    except (OSError, subprocess.CalledProcessError):
        blockers.append(f"{label} revision does not resolve to an available Git commit: {revision!r}")
        return None


def source_tree(revision: str) -> dict[str, dict[str, str]]:
    entries = {}
    for record in git_output("ls-tree", "-rtz", "--full-tree", revision).split(b"\0"):
        if record:
            object_info, path = record.split(b"\t", 1)
            mode, object_type, object_id = object_info.decode("ascii").split()
            entries[path.decode("utf-8", errors="surrogateescape")] = {
                "status": "PRESENT",
                "git_object_id": object_id,
                "git_object_type": object_type,
                "git_mode": mode,
            }
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--change-class", choices=CHANGE_CLASSES, required=True)
    parser.add_argument("--path", action="append", dest="paths", default=[])
    parser.add_argument("--architecture-impact", choices=("A0", "A1", "A2", "A3", "A4", "UNKNOWN"), required=True)
    parser.add_argument("--consumer", action="append", default=[], help="Consumer path tracked at the source revision")
    parser.add_argument("--graph-reviewed", action="store_true", help="Record a review claim without narrowing test scope")
    parser.add_argument("--security-sensitive", action="store_true")
    parser.add_argument("--base-revision", help="Compute actual changed paths instead of a caller-supplied list")
    parser.add_argument("--source-revision", default="HEAD")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.base_revision is not None and args.paths:
        parser.error("Use either actual Git diff or explicit --path inputs")

    blockers = []
    source_revision = resolve_commit(args.source_revision, "source", blockers)
    base_revision = None if args.base_revision is None else resolve_commit(args.base_revision, "base", blockers)
    consumer_evidence = {}
    if source_revision is not None:
        try:
            tree = source_tree(source_revision) if args.consumer or base_revision == source_revision else {}
            for path in sorted(set(args.consumer)):
                if not safe_path(path):
                    continue
                if path in tree:
                    consumer_evidence[path] = tree[path]
                else:
                    consumer_evidence[path] = {"status": "MISSING"}
                    blockers.append(f"consumer path {path!r} is absent at source revision {source_revision}")
            if base_revision == source_revision:
                # Manual dispatch: a conservative full-source plan from the commit, independent of the index.
                args.paths = [path for path, entry in tree.items() if entry["git_object_type"] != "tree"]
            elif base_revision is not None:
                diff = git_output("diff", "--no-relative", "--name-only", "-z", base_revision, source_revision, "--")
                args.paths = [path for path in diff.decode("utf-8", errors="surrogateescape").split("\0") if path]
        except (OSError, subprocess.CalledProcessError):
            blockers.append(f"cannot read the Git tree or diff at source revision {source_revision}")

    report = plan(args.change_class, args.paths, architecture_impact=args.architecture_impact,
                  consumers=args.consumer, graph_reviewed=args.graph_reviewed,
                  security_sensitive=args.security_sensitive)
    report.update(source_revision=source_revision, base_revision=base_revision, consumer_path_evidence=consumer_evidence)
    if blockers:
        report["blockers"] = blockers + report["blockers"]
        report["status"] = "BLOCKED"
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
