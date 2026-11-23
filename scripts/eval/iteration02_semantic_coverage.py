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
        return {"case_ids": [], "negative_case_ids": [], "competing_routes": [],
                "fixture_paths": [], "declared": False}
    parent = (root / source).parent
    local = parent / "tests" / "cases.yaml"
    ids: list[str] = []
    negatives: list[str] = []
    competitors: set[str] = set()
    fixture_paths: list[str] = []
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
        targets = central.get(Path(source).parent.name, []) if isinstance(central, dict) else []
        if isinstance(targets, list):
            for item in targets:
                if isinstance(item, dict) and isinstance(item.get("id"), str) and SAFE_CASE.fullmatch(item["id"]):
                    ids.append(item["id"])
                    if isinstance(item.get("input"), str) and _safe_existing_file(root, item["input"]):
                        fixture_paths.append(item["input"])
                    if isinstance(item.get("rubric"), str) and _safe_existing_file(root, item["rubric"]):
                        fixture_paths.append(item["rubric"])
    return {"case_ids": sorted(set(ids)), "negative_case_ids": sorted(set(negatives)),
            "competing_routes": sorted(competitors),
            "fixture_paths": sorted(set(fixture_paths)), "declared": bool(ids)}


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


def _receipt_rows(root: Path) -> list[dict]:
    # Reuse the existing public-safe projection. Never read prompt/trace bodies here.
    sys.path.insert(0, str(root / "scripts/eval"))
    from evidence_index import build_index  # noqa: E402
    return build_index(root).get("receipts", [])


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
    names = {name: ident for ident, node in nodes.items() for name in (node["name"],)}
    for ident, node in nodes.items():
        edges = []
        if node["kind"] == "workflow":
            deps = (node.get("registry") or {}).get("dependencies", {})
            for bucket in ("required", "optional"):
                items = deps.get(bucket, []) if isinstance(deps, dict) else []
                if not isinstance(items, list):
                    continue
                for item in items:
                    target = item.get("name") if isinstance(item, dict) else item
                    if isinstance(target, str) and target in names and names[target] != ident:
                        edges.append({"target": names[target], "dependency": bucket, "evidence": "runtime-registry.yaml"})
        graph[ident] = sorted(edges, key=lambda e: (e["target"], e["dependency"]))
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
            fixture = _fixture_summary(root, source, kind, {})
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
                "direct_consumers": direct, "transitive_consumers": transitive_consumers.get(node_id, []),
                "competing_routes": {"explicit_refs": fixture["competing_routes"],
                                     "status": "EXPLICIT_FIXTURE_BOUNDARIES" if fixture["competing_routes"] else "NOT_MAPPED"},
                "tool_dependencies": tool_dependencies,
                "dependency_edges": graph.get(node_id, []),
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
                "priority": priority, "review_signals": sorted(set(signals)),
                "evidence_gap": sorted(set(signals)),
                "next_test_action": "RUN_VERSION_BOUND_INDEPENDENT_SEMANTIC_CAMPAIGN",
                "model_execution": "NOT_RUN", "runtime_behavioral_acceptance": "NOT_VERIFIED",
                "independent_evaluator": "NOT_RUN", "task_owner": "UNASSIGNED",
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
    return {
        "schema_version": "2.0", "kind": "skill_workflow_consumer_test_crosswalk",
        "status": "BLOCKED_SOURCE" if errors else "SOURCE_INVENTORY_REVIEW_REQUIRED",
        "errors": sorted(set(errors)), "source_revision": source_revision, "worktree_state": worktree_state,
        "input_digests": input_digests,
        "crosswalk_sha256": hashlib.sha256(rows_projection).hexdigest(),
        "catalog_drift": catalog_state,
        "skill_count": len([c for c in components if c["kind"] == "skill"]),
        "registered_workflow_count": len([c for c in components if c["kind"] == "workflow"]),
        "unregistered_source_workflow_count": len(sources_w) - len(w_rows),
        "routing_fixture_signals": dict(sorted(signal_counter.items())),
        "components": sorted(components, key=lambda x: (x["kind"], x["name"])),
        "runtime_execution": "NOT_RUN", "model_behavior_verified": False,
        "independent_evaluation": "NOT_RUN", "release_approved": False,
        "gap_prioritization": {"dimensions": ["risk", "impact", "execution_frequency"],
                               "frequency_source": "No reliable per-component execution telemetry in the existing public-safe evidence projection.",
                               "policy": "Do not rank a numeric risk×impact×frequency score while any factor is UNKNOWN; prioritize only after frequency evidence is supplied."},
        "note": "Generated source crosswalk. Defined cases are not executed tests; recorded receipts do not prove compatible runtime without verified environment, fixture and channel identity. No overall coverage percentage is computed.",
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
