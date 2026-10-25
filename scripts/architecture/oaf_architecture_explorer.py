"""Source-derived OAF architecture slice with explicit unknowns and provenance."""
from __future__ import annotations

import re
import subprocess
from collections import deque
from pathlib import Path
from typing import Any

from scripts.architecture.visualization_ir import ModelValidationError, validate_model

SOURCE = "evals/oaf/wave4/case-capability-map-001.md"
SECTION_START = "Extract:"
SECTION_END = "Leadership wants"
KNOWN_TYPES = {
    "CRM Team": "owner",
    "Customer Service Process": "process",
    "Customer Data Platform": "application",
    "Power BI": "application",
}


class OAFExplorerError(ValueError):
    """Required OAF fixture source is absent or malformed."""


def _git_text(repo_root: Path, revision: str, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{revision}:{path}"],
        capture_output=True, text=True, timeout=20, check=False,
    )
    if result.returncode:
        raise OAFExplorerError(f"required source missing at pinned revision: {path}")
    return result.stdout


def _slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")


def extract_model(repo_root: Path, revision: str) -> dict[str, Any]:
    """Extract the explicitly nested case-map entities from immutable Git objects."""
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise OAFExplorerError("revision must be a full immutable lowercase Git SHA")
    text = _git_text(repo_root, revision, SOURCE)
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == SECTION_START)
        end = next(i for i in range(start + 1, len(lines))
                   if lines[i].strip().startswith(SECTION_END))
    except StopIteration as error:
        raise OAFExplorerError("capability-map extraction section is malformed") from error

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    ids: dict[str, str] = {}
    parents: dict[int, str] = {}
    entity_types: dict[str, str] = {}

    def evidence(line_number: int) -> list[dict[str, str]]:
        return [{"uri": f"repo://{SOURCE}", "revision": revision,
                 "locator": f"L{line_number}"}]

    def add_node(node_id: str, kind: str, label: str, state: str,
                 refs: list[dict[str, str]]) -> None:
        nodes.append({"id": node_id, "type": kind, "label": label,
                      "state": state, "evidence": refs})

    for index in range(start + 1, end):
        match = re.match(r"^( *)(?:- )([^\n]+?)\s*$", lines[index])
        if not match:
            continue
        indent, label = len(match.group(1)), match.group(2).strip()
        if indent == 0:
            kind = "capability"
            node_id = f"capability:{_slug(label)}"
            parents[0] = node_id
        elif indent == 2 and 0 in parents:
            kind = KNOWN_TYPES.get(label, "capability")
            node_id = f"{kind}:{_slug(label)}"
        else:
            raise OAFExplorerError(f"unsupported hierarchy at {SOURCE}:L{index + 1}")
        if label in ids:
            raise OAFExplorerError(f"duplicate entity label in source map: {label}")
        ids[label] = node_id
        entity_types[label] = kind
        add_node(node_id, kind, label, "observed", evidence(index + 1))
        if indent == 2:
            parent_id = parents[0]
            edges.append({
                "id": f"contains:{parent_id}:{node_id}",
                "type": "contains", "from": parent_id, "to": node_id,
                "state": "observed", "evidence": evidence(index + 1),
            })

    if not nodes:
        raise OAFExplorerError("capability map contains no explicit entities")

    owner_gap_line = next(
        (i + 1 for i, line in enumerate(lines) if "ownership is incomplete" in line.lower()),
        None,
    )
    if owner_gap_line is None:
        raise OAFExplorerError("source no longer documents incomplete ownership")
    gap_id = "unknown:application-owners"
    add_node(gap_id, "unknown", "Some application owners not supplied", "unknown", [])
    for label, node_id in sorted(ids.items()):
        if entity_types[label] == "application":
            edges.append({
                "id": f"unknown-owner:{node_id}", "type": "unknown",
                "from": node_id, "to": gap_id, "state": "unknown", "evidence": [],
            })

    add_node("unknown:data-lineage", "unknown",
             "Data lineage not represented in this map", "unknown", [])
    add_node("unknown:to-be", "unknown", "TO-BE model not supplied", "unknown", [])

    model = {
        "schema_version": 1,
        "model_id": "oaf-capability-map-case-001",
        "source_revision": revision,
        "nodes": sorted(nodes, key=lambda node: node["id"]),
        "edges": sorted(edges, key=lambda edge: edge["id"]),
    }
    try:
        return validate_model(model)
    except ModelValidationError as error:
        raise OAFExplorerError(f"extracted OAF model violates canonical IR: {error}") from error


def traverse(model: dict[str, Any], start_id: str) -> list[str]:
    """Return deterministic impact reachability across evidenced relationships only."""
    graph = {node["id"]: [] for node in model["nodes"]}
    for edge in model["edges"]:
        if edge["state"] != "unknown":
            graph[edge["from"]].append(edge["to"])
    if start_id not in graph:
        raise OAFExplorerError(f"unknown traversal start: {start_id}")
    seen = {start_id}
    queue = deque([start_id])
    while queue:
        current = queue.popleft()
        for target in sorted(graph[current]):
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return sorted(seen)


def coverage(model: dict[str, Any]) -> dict[str, Any]:
    """Summarize source coverage without treating absent layers as verified facts."""
    counts = {kind: sum(node["type"] == kind for node in model["nodes"])
              for kind in ("capability", "process", "application", "data", "owner")}
    unknowns = sorted(node["id"] for node in model["nodes"] if node["state"] == "unknown")
    return {
        "source_kind": "synthetic evaluation fixture, not an organization's verified EA repository",
        "as_is": "capability-map fixture contents only",
        "to_be": "NOT_SUPPLIED",
        "entity_counts": counts,
        "unresolved": unknowns,
    }
