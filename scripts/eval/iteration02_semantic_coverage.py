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
import subprocess
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/engineering"))
from audit_skill_lifecycle import audit as audit_skills  # noqa: E402
from audit_workflow_lifecycle import audit as audit_workflows  # noqa: E402

HEX40 = re.compile(r"^[0-9a-f]{40}$")
SAFE_CASE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,120}$")
REF = re.compile(r"\b(?:skills|workflows)/[A-Za-z0-9_./-]+\b")


def _read_yaml(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _safe_existing_file(root: Path, relative: str) -> Path | None:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        return None
    path = Path(relative)
    if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
        return None
    candidate = root / path
    if candidate.is_symlink() or not candidate.is_file() or not candidate.resolve().is_relative_to(root.resolve()):
        return None
    return candidate


def _catalog_drift(root: Path, skills: list[dict], workflows: list[dict]) -> dict:
    path = _safe_existing_file(root, "docs/catalog.json")
    if path is None:
        return {"status": "UNKNOWN", "missing": [], "extra": [], "errors": ["canonical catalog unavailable"]}
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"status": "BLOCKED", "missing": [], "extra": [], "errors": ["canonical catalog invalid"]}
    drift = {}
    for kind, lifecycle_rows in (("skill", skills), ("workflow", workflows)):
        catalog_rows = catalog.get("skills" if kind == "skill" else "workflows") if isinstance(catalog, dict) else None
        if not isinstance(catalog_rows, list):
            return {"status": "BLOCKED", "missing": [], "extra": [], "errors": [f"catalog {kind} inventory missing"]}
        actual = {(row.get("name"), row.get("source")) for row in lifecycle_rows if isinstance(row, dict)}
        projected = {(row.get("name"), row.get("source")) for row in catalog_rows if isinstance(row, dict)}
        drift[kind] = {"missing": sorted(f"{name}:{source}" for name, source in actual - projected),
                       "extra": sorted(f"{name}:{source}" for name, source in projected - actual)}
    has_drift = any(row["missing"] or row["extra"] for row in drift.values())
    return {"status": "DRIFT" if has_drift else "MATCH", "inventories": drift, "errors": []}


def _campaign_reference_candidates(root: Path, component_names: set[str]) -> dict[str, list[dict]]:
    result = {name: [] for name in component_names}
    campaign_root = root / "evals/campaigns"
    for path in sorted([*campaign_root.rglob("*.yaml"), *campaign_root.rglob("*.yml"), *campaign_root.rglob("*.json")]):
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        for name in component_names:
            if name in text:
                result[name].append({"path": rel, "sha256": digest, "basis": "LEXICAL_REFERENCE_CANDIDATE"})
    return {name: sorted(rows, key=lambda item: item["path"]) for name, rows in result.items()}


def _fixture_summary(root: Path, source: str, kind: str, registry: dict) -> dict:
    if _safe_existing_file(root, source) is None:
        return {"case_ids": [], "local_case_ids": [], "central_case_ids": [],
                "negative_case_ids": [], "competing_routes": [],
                "fixture_paths": [], "central_fixture_paths": [], "declared": False}
    parent = (root / source).parent
    local = parent / "tests" / "cases.yaml"
    ids: list[str] = []
    local_ids: list[str] = []
    central_ids: list[str] = []
    negatives: list[str] = []
    competitors: set[str] = set()
    fixture_paths: list[str] = []
    central_paths: list[str] = []
    local_rel = local.relative_to(root).as_posix()
    safe_local = _safe_existing_file(root, local_rel)
    if safe_local:
        data = _read_yaml(safe_local)
        for case in data.get("cases", []) if isinstance(data.get("cases"), list) else []:
            if not isinstance(case, dict):
                continue
            ident = case.get("id")
            if isinstance(ident, str) and SAFE_CASE.fullmatch(ident):
                ids.append(ident)
                local_ids.append(ident)
                expected = case.get("expected")
                if isinstance(expected, dict) and expected.get("should_trigger") is False:
                    negatives.append(ident)
                tags = expected.get("tags", []) if isinstance(expected, dict) else []
                if isinstance(tags, list):
                    competitors.update(tag.removeprefix("route-to-") for tag in tags
                                       if isinstance(tag, str) and tag.startswith("route-to-") and len(tag) > 9)
        fixture_paths.append(local_rel)
    if kind == "workflow":
        central = _read_yaml(root / "evals/runtime-fixtures.yaml").get("targets", {})
        target_name = registry.get("name") if isinstance(registry, dict) else None
        targets = central.get(target_name or Path(source).parent.name, []) if isinstance(central, dict) else []
        if isinstance(targets, list):
            for item in targets:
                if isinstance(item, dict) and isinstance(item.get("id"), str) and SAFE_CASE.fullmatch(item["id"]):
                    ids.append(item["id"])
                    central_ids.append(item["id"])
                    if isinstance(item.get("input"), str) and _safe_existing_file(root, item["input"]):
                        fixture_paths.append(item["input"])
                        central_paths.append(item["input"])
                    if isinstance(item.get("rubric"), str) and _safe_existing_file(root, item["rubric"]):
                        fixture_paths.append(item["rubric"])
                        central_paths.append(item["rubric"])
    return {"case_ids": sorted(set(ids)), "local_case_ids": sorted(set(local_ids)),
            "central_case_ids": sorted(set(central_ids)), "negative_case_ids": sorted(set(negatives)),
            "competing_routes": sorted(competitors),
            "fixture_paths": sorted(set(fixture_paths)), "central_fixture_paths": sorted(set(central_paths)),
            "declared": bool(ids)}


def _source_metadata(root: Path, source: str, kind: str) -> dict:
    path = _safe_existing_file(root, source)
    text = path.read_text(encoding="utf-8") if path else ""
    metadata: dict = {}
    if kind == "skill" and text.startswith("---\n") and "\n---\n" in text[4:]:
        try:
            frontmatter = yaml.safe_load(text[4:].split("\n---\n", 1)[0])
            if isinstance(frontmatter, dict):
                raw = frontmatter.get("metadata")
                metadata = raw if isinstance(raw, dict) else {}
        except yaml.YAMLError:
            pass
    return {"text": text, "metadata": metadata}


def _task_owner(metadata: object) -> str:
    owner = metadata.get("owner") if isinstance(metadata, dict) else None
    return owner if isinstance(owner, str) and owner.strip() else "UNKNOWN"


def _receipt_rows(root: Path) -> list[dict]:
    # Reuse the existing public-safe projection. Never read prompt/trace bodies here.
    sys.path.insert(0, str(root / "scripts/eval"))
    from evidence_index import build_index  # noqa: E402
    return build_index(root).get("receipts", [])


def _workflow_reconciliation_design(root: Path, components: list[dict], nodes: dict) -> tuple[list[dict], dict | None, list[str]]:
    """Validate the declarative workflow-gap campaign against current files."""
    rel = "evals/campaigns/workflow-case-reconciliation-2026-11/campaign.yaml"
    path = _safe_existing_file(root, rel)
    if path is None:
        return [], None, []
    campaign = _read_yaml(path)
    errors: list[str] = []
    if campaign.get("kind") != "TEST_DESIGN" or campaign.get("runtime_execution") != "NOT_RUN":
        errors.append("workflow reconciliation campaign must remain TEST_DESIGN / NOT_RUN")
    if not isinstance(campaign.get("design_base_sha"), str) or not HEX40.fullmatch(campaign["design_base_sha"]):
        errors.append("workflow reconciliation campaign must pin a full lowercase 40-character design_base_sha")
    by_id = {row["stable_id"]: row for row in components if row["kind"] == "workflow"}
    reconciliation = []
    cases = campaign.get("cases", [])
    if not isinstance(cases, list):
        return [], campaign, ["workflow reconciliation campaign cases malformed"]
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("workflow reconciliation campaign contains malformed case")
            continue
        workflow_id = case.get("workflow_id")
        stable_id = f"workflow:{workflow_id}"
        if case.get("stable_id") != stable_id:
            errors.append(f"workflow reconciliation stable ID mismatch: {workflow_id}")
        component = by_id.get(stable_id)
        if not component or workflow_id in seen:
            errors.append(f"workflow reconciliation campaign has unknown/duplicate workflow {workflow_id}")
            continue
        seen.add(workflow_id)
        for key, digest_key in (("workflow_source", "workflow_source_sha256"),
                                ("case_file", "case_file_sha256"),
                                ("input", "input_sha256"), ("rubric", "rubric_sha256")):
            file = _safe_existing_file(root, case.get(key))
            actual = hashlib.sha256(file.read_bytes()).hexdigest() if file else None
            if not actual or actual != case.get(digest_key):
                errors.append(f"workflow reconciliation pin mismatch: {workflow_id}:{key}")
        if case.get("workflow_source") != component["source_path"] or case.get("workflow_source_sha256") != component["source_sha256"]:
            errors.append(f"workflow source identity mismatch: {workflow_id}")
        metadata = nodes.get(stable_id, {}).get("registry", {}).get("metadata", {})
        owner = _task_owner(metadata)
        if case.get("owner") != owner:
            errors.append(f"workflow reconciliation owner mismatch: {workflow_id}")
        suite = _read_yaml(root / case.get("case_file", ""))
        suite_cases = [row for row in suite.get("cases", []) if isinstance(row, dict)]
        local_case_ids = [row.get("id") for row in suite_cases if isinstance(row.get("id"), str)]
        negative_case_ids = [row.get("id") for row in suite_cases
                             if isinstance(row.get("id"), str) and
                             isinstance(row.get("expected"), dict) and
                             row["expected"].get("should_trigger") is False]
        if case.get("case_ids") != local_case_ids or case.get("negative_case_ids") != negative_case_ids:
            errors.append(f"workflow reconciliation case ID inventory mismatch: {workflow_id}")
        local = next((row for row in suite_cases if row.get("id") == case.get("case_id")), None)
        if local is None:
            errors.append(f"workflow local case absent from suite: {workflow_id}")
        input_file = _safe_existing_file(root, case.get("input"))
        if local and input_file and local.get("input", "").rstrip() != input_file.read_text(encoding="utf-8").rstrip():
            errors.append(f"workflow case input differs from pinned input: {workflow_id}")
        reused_cases = case.get("reused_central_cases", [])
        for reused in reused_cases if isinstance(reused_cases, list) else []:
            for key, digest_key in (("input", "input_sha256"), ("rubric", "rubric_sha256")):
                file = _safe_existing_file(root, reused.get(key) if isinstance(reused, dict) else None)
                actual = hashlib.sha256(file.read_bytes()).hexdigest() if file else None
                if not actual or actual != reused.get(digest_key):
                    errors.append(f"reused central fixture pin mismatch: {workflow_id}:{reused.get('case_id')}:{key}")
        if case.get("execution_state") != "NOT_RUN" or case.get("runtime_pass") is not False:
            errors.append(f"workflow reconciliation case has runtime claim: {workflow_id}")
        reconciliation.append({
            "stable_id": stable_id, "workflow_id": workflow_id,
            "workflow_source": case.get("workflow_source"),
            "workflow_source_sha256": case.get("workflow_source_sha256"),
            "local_cases_yaml": "PRESENT", "local_case_file": case.get("case_file"),
            "local_case_file_sha256": case.get("case_file_sha256"),
            "local_case_ids": local_case_ids, "negative_case_ids": negative_case_ids,
            "new_design_case_ids": local_case_ids,
            "central_fixture_case_ids": component["central_fixture_case_ids"],
            "reused_central_case_ids": [item.get("case_id") for item in reused_cases if isinstance(item, dict)],
            "coverage_limit": case.get("coverage_limit"), "owner": owner,
            "follow_up_state": "RECONCILED_CASE_DESIGNED", "execution_state": "NOT_RUN",
            "runtime_pass": False,
        })
    return reconciliation, campaign, errors


def _declared_graph(root: Path) -> tuple[dict[str, list[dict]], dict[str, dict]]:
    registry = _read_yaml(root / "workflows/runtime-registry.yaml")
    nodes: dict[str, dict] = {}
    graph: dict[str, list[dict]] = {}
    skills = sorted(path for path in (root / "skills").rglob("SKILL.md")
                    if not path.is_symlink() and path.resolve().is_relative_to(root.resolve()))
    for path in skills:
        rel = path.relative_to(root).as_posix()
        name = path.parent.name
        nodes[f"skill:{name}"] = {"kind": "skill", "name": name, "source": rel}
    workflow_rows = registry.get("workflows", [])
    if isinstance(workflow_rows, list):
        for row in workflow_rows:
            if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not isinstance(row.get("workflow"), str):
                continue
            nodes[f"workflow:{row['name']}"] = {"kind": "workflow", "name": row["name"], "source": row["workflow"], "registry": row}
    names: dict[str, list[str]] = {}
    for ident, node in nodes.items():
        names.setdefault(node["name"], []).append(ident)
    for ident, node in nodes.items():
        edges = []
        if node["kind"] == "workflow":
            declared_targets: set[str] = set()
            deps = (node.get("registry") or {}).get("dependencies", {})
            for bucket in ("required", "optional"):
                items = deps.get(bucket) if isinstance(deps, dict) else None
                if not isinstance(items, list):
                    edges.append({"target": None, "target_name": None, "dependency": bucket,
                                  "evidence": "workflows/runtime-registry.yaml#/workflows/dependencies/" + bucket,
                                  "edge_status": "MALFORMED_BUCKET"})
                    continue
                for item in items:
                    target = item.get("name") if isinstance(item, dict) else item
                    if not isinstance(target, str):
                        edges.append({"target": None, "target_name": None, "dependency": bucket,
                                      "evidence": "workflows/runtime-registry.yaml#/workflows/dependencies/" + bucket,
                                      "edge_status": "MALFORMED_REFERENCE"})
                        continue
                    declared_targets.add(target)
                    matches = names.get(target, [])
                    if len(matches) == 1 and matches[0] != ident:
                        edges.append({"target": matches[0], "target_name": target, "dependency": bucket,
                                      "evidence": "workflows/runtime-registry.yaml#/workflows/dependencies/" + bucket,
                                      "edge_status": "RESOLVED"})
                    elif target == node["name"]:
                        edges.append({"target": None, "target_name": target, "dependency": bucket,
                                      "evidence": "workflows/runtime-registry.yaml#/workflows/dependencies/" + bucket,
                                      "edge_status": "SELF_REFERENCE"})
                    else:
                        edges.append({"target": None, "target_name": target, "dependency": bucket,
                                      "evidence": "workflows/runtime-registry.yaml#/workflows/dependencies/" + bucket,
                                      "edge_status": "UNKNOWN_TARGET"})
            # Runtime registry edges are authoritative when declared. Also retain
            # exact skill-name references from workflow source as unverified
            # candidates; prose alone cannot establish an executable dependency,
            # so these edges must block impact claims until reviewed.
            source_path = _safe_existing_file(root, node["source"])
            if source_path:
                source_text = source_path.read_text(encoding="utf-8")
                candidate_lines: dict[str, int] = {}
                skill_names = sorted(name for name, matches in names.items()
                                     if len(matches) == 1 and matches[0].startswith("skill:"))
                if skill_names:
                    names_pattern = re.compile(
                        r"(?<![A-Za-z0-9_-])(" + "|".join(re.escape(name) for name in skill_names)
                        + r")(?![A-Za-z0-9_-])")
                    for line_number, line in enumerate(source_text.splitlines(), start=1):
                        for match in names_pattern.finditer(line):
                            candidate = match.group(1)
                            if candidate not in declared_targets:
                                candidate_lines.setdefault(candidate, line_number)
                for candidate, line_number in candidate_lines.items():
                    edges.append({"target": None, "target_name": candidate,
                                  "dependency": "source_reference_candidate",
                                  "evidence": f"{node['source']}#L{line_number}",
                                  "edge_status": "UNVERIFIED_SOURCE_REFERENCE"})
        graph[ident] = sorted(edges, key=lambda e: (e["target"] or "", e["target_name"] or "", e["dependency"]))
    return graph, nodes


def _consumer_maps(graph: dict[str, list[dict]]) -> tuple[dict[str, list[dict]], dict[str, list[str]]]:
    reverse: dict[str, list[dict]] = {node: [] for node in graph}
    for consumer, edges in graph.items():
        for edge in edges:
            reverse.setdefault(edge["target"], []).append({"consumer": consumer, "basis": edge["evidence"], "dependency": edge["dependency"]})
    transitive = {}
    for node in graph:
        seen, pending = set(), [x["consumer"] for x in reverse.get(node, [])]
        while pending:
            consumer = pending.pop()
            if consumer in seen:
                continue
            seen.add(consumer)
            pending.extend(x["consumer"] for x in reverse.get(consumer, []))
        transitive[node] = sorted(seen)
    return reverse, transitive


def _affected_query(report: dict, stable_id: str) -> dict:
    report_identity = {"source_revision": report.get("source_revision"),
                       "crosswalk_sha256": report.get("crosswalk_sha256"),
                       "worktree_state": report.get("worktree_state")}
    rows = {row.get("stable_id"): row for row in report.get("components", []) if isinstance(row, dict)}
    source_errors = report.get("errors", [])
    global_unresolved = [{"consumer": row["stable_id"], "edge": edge, "scope": "GLOBAL_GRAPH"}
                         for row in rows.values() for edge in row.get("dependency_edges", [])
                         if edge.get("edge_status") != "RESOLVED"]
    if report.get("status") == "BLOCKED_SOURCE" or source_errors:
        return {**report_identity, "status": "BLOCKED_SOURCE", "requested_stable_id": stable_id,
                "source_errors": source_errors, "regression_neighbors": [],
                "unresolved_edges": global_unresolved, "runtime_execution": "NOT_RUN"}
    if report.get("worktree_state") != "CLEAN_CHECKOUT":
        return {**report_identity, "status": "BLOCKED_WORKTREE_STATE", "requested_stable_id": stable_id,
                "block_reason": "Impact queries require a clean, revision-attested checkout.",
                "regression_neighbors": [], "unresolved_edges": global_unresolved,
                "runtime_execution": "NOT_RUN"}
    changed = rows.get(stable_id)
    if changed is None:
        return {**report_identity, "status": "BLOCKED_UNKNOWN_COMPONENT", "requested_stable_id": stable_id,
                "regression_neighbors": [], "unresolved_edges": [], "runtime_execution": "NOT_RUN"}
    direct_ids = {edge.get("consumer") for edge in changed.get("direct_consumers", []) if isinstance(edge, dict)}
    transitive_ids = set(changed.get("transitive_consumers", []))
    changed_name = changed.get("name") or stable_id.split(":", 1)[-1]
    candidate_consumers = [{"stable_id": row["stable_id"], "edge": edge}
                           for row in rows.values()
                           for edge in row.get("dependency_edges", [])
                           if edge.get("edge_status") != "RESOLVED"
                           and edge.get("target_name") == changed_name]
    neighbors = []
    for neighbor_id in sorted((direct_ids | transitive_ids) - {None}):
        neighbor = rows.get(neighbor_id)
        if neighbor is None:
            continue
        neighbors.append({"stable_id": neighbor_id,
                          "relation": "DIRECT_AND_TRANSITIVE" if neighbor_id in direct_ids and neighbor_id in transitive_ids else
                                     "DIRECT" if neighbor_id in direct_ids else "TRANSITIVE",
                          "fixture_case_ids": neighbor.get("fixture_case_ids", []),
                          "evidence_gap": neighbor.get("evidence_gap", [])})
    status = "BLOCKED_UNKNOWN_EDGES" if global_unresolved else "QUERY_COMPLETE"
    return {**report_identity, "status": status, "requested_stable_id": stable_id,
            "changed_node": {"stable_id": stable_id, "source_path": changed.get("source_path"),
                             "source_sha256": changed.get("source_sha256"),
                             "fixture_case_ids": changed.get("fixture_case_ids", []),
                             "evidence_gap": changed.get("evidence_gap", [])},
            "regression_neighbors": neighbors,
            "unverified_consumer_candidates": sorted(candidate_consumers,
                                                       key=lambda item: (item["stable_id"], item["edge"]["evidence"])),
            "unresolved_edges": global_unresolved,
            "runtime_execution": "NOT_RUN"}


def _source_revision(root: Path) -> tuple[str, str]:
    try:
        revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        status = subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL)
        if not HEX40.fullmatch(revision):
            return "LOCAL_CHECKOUT_UNATTESTED", "REVISION_INVALID"
        supplied = os.getenv("SOURCE_REVISION", "")
        if supplied and supplied != revision:
            return revision, "SOURCE_REVISION_MISMATCH"
        return revision, "WORKTREE_DIRTY" if status else "CLEAN_CHECKOUT"
    except (OSError, subprocess.CalledProcessError):
        return "LOCAL_CHECKOUT_UNATTESTED", "REVISION_UNAVAILABLE"


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
    graph, nodes = _declared_graph(root)
    direct_consumers, transitive_consumers = _consumer_maps(graph)
    receipts = _receipt_rows(root)
    receipts_by_component: dict[str, list[dict]] = {}
    for receipt_row in receipts:
        component_name = receipt_row.get("component")
        if isinstance(component_name, str):
            receipts_by_component.setdefault(component_name, []).append(receipt_row)
    campaign_refs = _campaign_reference_candidates(root, {node["name"] for node in nodes.values()})
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
                original = _safe_existing_file(root, source)
                file_digest = hashlib.sha256(original.read_bytes()).hexdigest() if original else None
            signals = []
            node_id = f"{kind}:{name}"
            source_info = _source_metadata(root, source, kind)
            fixture = _fixture_summary(root, source, kind, {"name": name})
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
                case_count = len(fixture["case_ids"])
                if not local and central == 0:
                    signals.append("WORKFLOW_TEST_COVERAGE_NOT_LOCATED")
                if not local:
                    signals.append("NO_LOCAL_WORKFLOW_SUITE")
                if central == 0:
                    signals.append("NO_CENTRAL_WORKFLOW_FIXTURE")
                if not local and central == 0:
                    if campaign_refs.get(name):
                        signals.append("ALTERNATIVE_CAMPAIGN_REFERENCE_REVIEW_REQUIRED")
                    else:
                        signals.append("NO_ALTERNATIVE_CAMPAIGN_REFERENCE_FOUND")
            unresolved_dependencies = [edge for edge in graph.get(node_id, [])
                                       if edge.get("edge_status") != "RESOLVED"]
            if unresolved_dependencies:
                signals.append("DEPENDENCY_TARGET_UNRESOLVED")
            status = row.get("status")
            if status not in {"STATIC_BLOCKER", "REVIEW_REQUIRED", "STATIC_CHECKS_OK"}:
                errors.append(f"{name}: invalid static audit status")
            if status == "STATIC_BLOCKER":
                signals.append("SOURCE_STATIC_BLOCKER")
            # Existing local suites are not equivalent to independent tool/model
            # behavior traces. No row is ever made acceptance-ready here.
            if not fixture["declared"]:
                signals.append("NO_RESOLVABLE_CASE_IDS")
            if not fixture["competing_routes"]:
                signals.append("COMPETING_ROUTES_NOT_MAPPED")
            direct = direct_consumers.get(node_id, [])
            consumers = [x["consumer"] for x in direct]
            registry_node = nodes.get(node_id, {})
            registry_row = registry_node.get("registry", {})
            channels = registry_row.get("channels", {}) if isinstance(registry_row, dict) else {}
            declared_channels = {str(k): str(v) for k, v in channels.items()} if isinstance(channels, dict) else {}
            metadata = source_info["metadata"]
            if not declared_channels and isinstance(metadata.get("channels"), dict):
                declared_channels = {str(k): str(v) for k, v in metadata["channels"].items()}
            if kind == "workflow" and isinstance(registry_row.get("metadata"), dict):
                metadata = registry_row["metadata"]
            evidence = receipts_by_component.get(name, [])
            historical_receipt_count = sum(1 for x in evidence
                                           if x.get("receipt_validation") == "PASS" and x.get("case_id"))
            compatible_receipts = [x for x in evidence if x.get("receipt_validation") == "PASS" and
                                   x.get("component_identity_matches") is True]
            if any(x.get("recorded_status") == "FAIL" for x in evidence):
                signals.append("RECORDED_FAILURE_EVIDENCE_PRESERVED")
            if any(x.get("receipt_validation") == "FAIL" for x in evidence):
                signals.append("INVALID_RECEIPT_EVIDENCE_PRESERVED")
            if not compatible_receipts:
                signals.append("NO_CURRENT_IDENTITY_MATCHED_RECEIPT")
            if evidence and any(x.get("compatibility") == "NOT_VERIFIED" for x in evidence):
                signals.append("FIXTURE_ENVIRONMENT_CHANNEL_COMPATIBILITY_UNKNOWN")
            if not declared_channels:
                signals.append("CHANNEL_DECLARATION_NOT_FOUND")
            signals.append("RUNTIME_CHANNEL_NOT_VERIFIED")
            signals.append("EXECUTION_FREQUENCY_UNKNOWN")
            if source_info["text"] and not re.search(r"\b(?:tool|tools|MCP|connector)\b", source_info["text"], re.I):
                tool_dependencies = {"state": "NO_DECLARATION_FOUND", "refs": []}
                signals.append("TOOL_DEPENDENCY_NOT_LOCATED")
            else:
                tool_refs = sorted(set(re.findall(r"`([A-Za-z][A-Za-z0-9_.-]{1,80})`", source_info["text"])
                                       if re.search(r"\b(?:tool|tools|MCP|connector)\b", source_info["text"], re.I) else []))
                tool_dependencies = {"state": "REFERENCE_CANDIDATES_REVIEW_REQUIRED" if tool_refs else "DECLARATION_UNRESOLVED",
                                     "refs": tool_refs, "basis": "inline-code tokens near tool/MCP/connector terms"}
                if not tool_refs:
                    signals.append("TOOL_DEPENDENCY_UNRESOLVED")
            risk = str(metadata.get("risk", "UNKNOWN")).upper()
            impact = "HIGH" if len(transitive_consumers.get(node_id, [])) >= 5 else "MODERATE" if consumers or transitive_consumers.get(node_id) else "LOW"
            priority = "UNRANKED_FREQUENCY_UNKNOWN"
            components.append({
                "stable_id": node_id, "kind": kind, "name": name, "source_path": source,
                "source_sha256": file_digest, "type": kind, "static_status": status,
                "structural_status": "DEFINED" if fixture["declared"] else "UNKNOWN",
                "routing_status": "FIXTURES_DEFINED" if fixture["declared"] else "UNKNOWN",
                "behavior_status": "NOT_RUN", "integration_status": "NOT_RUN",
                "runtime_status": "NOT_VERIFIED", "quality_status": "NOT_SCORED", "cost_status": "UNKNOWN",
                "fixture_case_ids": fixture["case_ids"], "negative_cases": fixture["negative_case_ids"],
                "fixture_paths": fixture["fixture_paths"], "fixture_sha256": {p: hashlib.sha256(file.read_bytes()).hexdigest() for p in fixture["fixture_paths"] if (file := _safe_existing_file(root, p))},
                "central_fixture_paths": fixture["central_fixture_paths"],
                "local_fixture_case_ids": fixture["local_case_ids"],
                "central_fixture_case_ids": fixture["central_case_ids"],
                "direct_consumers": direct, "transitive_consumers": transitive_consumers.get(node_id, []),
                "competing_routes": {"explicit_refs": fixture["competing_routes"],
                                     "status": "EXPLICIT_FIXTURE_BOUNDARIES" if fixture["competing_routes"] else "NOT_MAPPED"},
                "tool_dependencies": tool_dependencies,
                "dependency_edges": graph.get(node_id, []),
                "dependency_status": "UNKNOWN" if unresolved_dependencies else "DECLARED_RESOLVED",
                "alternative_test_refs": campaign_refs.get(name, []),
                "deterministic_owner_ref": sorted(set(REF.findall(source_info["text"]))),
                "declared_channels": declared_channels, "verified_runtime_channels": [],
                "evaluation_receipts": [{k: x.get(k) for k in ("receipt_path", "receipt_sha256", "case_id", "recorded_status", "receipt_validation", "component_identity_matches", "compatibility")} for x in evidence],
                "evidence_freshness": ("INVALID_RECEIPT_PRESENT" if any(x.get("receipt_validation") == "FAIL" for x in evidence) else
                                        "NOT_VERIFIABLE_FROM_PUBLIC_INDEX" if compatible_receipts else
                                        "STALE_COMPONENT_IDENTITY" if evidence else "NO_RECEIPT"),
                "lifecycle_case_count": case_count,
                "routing_positive_cases": positive if kind == "skill" else None,
                "routing_negative_cases": negative if kind == "skill" else None,
                "risk": risk, "impact": impact, "execution_frequency": "UNKNOWN",
                "historical_receipt_count_lower_bound": historical_receipt_count,
                "historical_receipt_count_basis": "VALID_PUBLIC_SAFE_INDEXED_RECEIPTS" if historical_receipt_count else "NO_VALID_INDEXED_RECEIPT_FOUND",
                "priority": priority, "review_signals": sorted(set(signals)),
                "evidence_gap": sorted(set(signals)),
                "next_test_action": "RUN_VERSION_BOUND_INDEPENDENT_SEMANTIC_CAMPAIGN",
                "model_execution": "NOT_RUN", "runtime_behavioral_acceptance": "NOT_VERIFIED",
                "independent_evaluator": "NOT_RUN", "task_owner": _task_owner(metadata),
            })
    catalog_state = _catalog_drift(root, s_rows, w_rows)
    if catalog_state["status"] in {"BLOCKED", "DRIFT"}:
        errors.extend(catalog_state.get("errors", []))
        if catalog_state["status"] == "DRIFT":
            errors.append("canonical catalog differs from lifecycle source inventory")
    source_revision, worktree_state = _source_revision(root)
    if worktree_state == "SOURCE_REVISION_MISMATCH":
        errors.append("SOURCE_REVISION environment value disagrees with actual Git HEAD")
    signal_counter = Counter(x for c in components for x in c["review_signals"])
    input_digests = {}
    for rel in ("docs/catalog.json", "workflows/runtime-registry.yaml", "evals/runtime-fixtures.yaml"):
        file = _safe_existing_file(root, rel)
        input_digests[rel] = hashlib.sha256(file.read_bytes()).hexdigest() if file else None
    receipt_projection = json.dumps(receipts, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    input_digests["public_safe_receipt_index"] = hashlib.sha256(receipt_projection).hexdigest()
    rows_projection = json.dumps(components, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    workflow_reconciliation, reconciliation_campaign, design_errors = _workflow_reconciliation_design(root, components, nodes)
    errors.extend(design_errors)
    reconciled_ids = {f"workflow:{item['workflow_id']}" for item in workflow_reconciliation}
    for row in components:
        if row["kind"] != "workflow" or row["local_fixture_case_ids"] or row["stable_id"] in reconciled_ids:
            continue
        request = {"status": "CASE_DESIGN_REQUIRED", "owner": row["task_owner"],
                   "workflow_source": row["source_path"], "workflow_source_sha256": row["source_sha256"],
                   "case_file": f"{Path(row['source_path']).parent.as_posix()}/tests/cases.yaml",
                   "max_case_ids": 3, "case_ids": [],
                   "required_scenarios": ["PRIMARY_PATH", "HIGHEST_RISK_NEGATIVE_OR_MISSING_EVIDENCE"],
                   "execution_state": "NOT_RUN", "defined_cases_are_not_executed": True}
        workflow_reconciliation.append({"workflow_id": row["stable_id"],
            "workflow_source": row["source_path"], "workflow_source_sha256": row["source_sha256"],
            "local_cases_yaml": "MISSING", "central_fixture_case_ids": row["central_fixture_case_ids"],
            "owner": row["task_owner"], "follow_up_state": "CASE_DESIGN_REQUIRED",
            "follow_up_action": "ADD_VERSIONED_WORKFLOW_CASES", "case_design_request": request,
            "execution_state": "NOT_RUN", "runtime_pass": False})
    return {
        "schema_version": "2.0", "kind": "skill_workflow_consumer_test_crosswalk",
        "status": "BLOCKED_SOURCE" if errors else "SOURCE_INVENTORY_REVIEW_REQUIRED",
        "errors": sorted(set(errors)), "source_revision": source_revision, "worktree_state": worktree_state,
        "input_digests": input_digests,
        "crosswalk_sha256": hashlib.sha256(rows_projection).hexdigest(),
        "catalog_drift": catalog_state,
        "workflow_fixture_reconciliation": sorted(workflow_reconciliation, key=lambda item: item["workflow_id"]),
        "workflow_reconciliation_campaign": reconciliation_campaign,
        "skill_count": len([c for c in components if c["kind"] == "skill"]),
        "registered_workflow_count": len([c for c in components if c["kind"] == "workflow"]),
        "unregistered_source_workflow_count": len(sources_w) - len(w_rows),
        "routing_fixture_signals": dict(sorted(signal_counter.items())),
        "components": sorted(components, key=lambda x: (x["kind"], x["name"])),
        "runtime_execution": "NOT_RUN", "model_behavior_verified": False,
        "independent_evaluation": "NOT_RUN", "release_approved": False,
        "gap_prioritization": {"dimensions": ["risk", "impact", "execution_frequency"],
                               "frequency_source": "Overall frequency remains unavailable; historical_receipt_count_lower_bound counts only valid public-safe indexed receipt records and is not a usage denominator.",
                               "policy": "Do not rank a numeric risk×impact×frequency score while execution_frequency is UNKNOWN.",
                               "historical_receipt_count_field": "historical_receipt_count_lower_bound",
                               "residual_blocker": "EXECUTION_FREQUENCY_TELEMETRY_UNAVAILABLE"},
        "note": "Generated source crosswalk. Defined cases are not executed tests; recorded receipts do not prove compatible runtime without verified environment, fixture and channel identity. No overall coverage percentage is computed.",
    }


def build(root: Path = ROOT) -> dict:
    return assess(audit_skills(root), audit_workflows(root), root)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path)
    p.add_argument("--affected", help="Return change-impact query for one stable ID, e.g. skill:skill-name")
    args = p.parse_args()
    try:
        report = build(args.root)
    except (OSError, ValueError, TypeError) as error:
        report = {"status": "BLOCKED_SOURCE", "errors": [type(error).__name__],
                  "runtime_execution": "NOT_RUN", "release_approved": False}
    if args.affected:
        report = _affected_query(report, args.affected)
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return int(report["status"] not in {"SOURCE_INVENTORY_REVIEW_REQUIRED", "QUERY_COMPLETE"})


if __name__ == "__main__":
    raise SystemExit(main())
