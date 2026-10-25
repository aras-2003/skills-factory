"""Source-derived Skills Factory Explorer graph with explicit provenance and uncertainty.

The graph describes documented references in a pinned Git revision. It does not
claim that a workflow or child skill executed at runtime.
"""
from __future__ import annotations

import re
import subprocess
from collections import deque
from pathlib import Path
from typing import Any

from scripts.architecture.visualization_ir import ModelValidationError, validate_model

SKILLS = (
    "decision-journal-update", "investment-attention-triage",
    "investment-policy-design", "investment-record-store",
    "investor-pattern-research", "market-opportunity-scan",
    "portfolio-state-review", "position-sizing-review",
    "security-underwriting", "thesis-challenge", "thesis-monitor",
    "trend-theme-research", "valuation-scenario-review",
)
WORKFLOWS = (
    "investment-attention-review", "investment-opportunity-hunter",
    "investment-os-review", "investment-portfolio-observation",
    "investment-portfolio-review", "investment-security-review",
    "investment-theme-discovery",
)
DATA_FIELDS = (
    "as_of_date", "current_positions", "current_theses", "draft_theses",
    "holding_weight", "instrument_exposures", "latest_valid_snapshot_pair",
    "portfolio_exposure_source_coverage", "portfolio_position_changes",
    "sector_weight", "source_date", "system_config",
)
TOOL_TOKEN = re.compile(r"\b(?:route|render|load|list|search|fetch|write|save|read|retrieve)_[a-z][a-z0-9_]*\b")
GATE_LINE = re.compile(
    r"\b(?:must stop|stop before|stop condition|stop routing|fail closed|"
    r"BLOCKED_[A-Z_]+|do not proceed|must not proceed)\b", re.IGNORECASE
)
TOKEN_EDGE = r"(?<![A-Za-z0-9_-]){}(?![A-Za-z0-9_-])"


class ExplorerError(ValueError):
    """Required source is unavailable or the source graph is invalid."""


def _git_text(repo_root: Path, revision: str, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{revision}:{path}"],
        capture_output=True, text=True, timeout=20, check=False,
    )
    if result.returncode:
        raise ExplorerError(f"required source missing at pinned revision: {path}")
    return result.stdout


def _evidence(revision: str, path: str, line: int) -> dict[str, str]:
    return {"uri": f"repo://{path}", "revision": revision, "locator": f"L{line}"}


def _clean_label(value: str, limit: int = 180) -> str:
    value = re.sub(r"[\x00-\x1f\x7f]", " ", value)
    value = value.replace("<", "‹").replace(">", "›").replace("&", "and")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit].rstrip() or "Unlabelled source item"


def _token_present(line: str, token: str) -> bool:
    return re.search(TOKEN_EDGE.format(re.escape(token)), line, re.IGNORECASE) is not None


def extract_model(repo_root: Path, revision: str) -> dict[str, Any]:
    """Extract the fixed 13-skill / 7-workflow investment slice from exact Git objects."""
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ExplorerError("revision must be a full immutable lowercase Git SHA")

    sources: list[dict[str, Any]] = []
    for kind, names in (("skill", SKILLS), ("workflow", WORKFLOWS)):
        for name in names:
            path = (
                f"skills/investing/{name}/SKILL.md" if kind == "skill"
                else f"workflows/{name}/WORKFLOW.md"
            )
            lines = _git_text(repo_root, revision, path).splitlines()
            if not lines:
                raise ExplorerError(f"empty required source: {path}")
            title_line = next((i for i, line in enumerate(lines, 1) if line.startswith("# ")), None)
            name_line = next((i for i, line in enumerate(lines, 1)
                              if re.match(rf"^name:\s*{re.escape(name)}\s*$", line)), None)
            evidence_line = name_line if kind == "skill" and name_line else title_line
            if evidence_line is None:
                raise ExplorerError(f"no explicit title/name in required source: {path}")
            label_source = lines[evidence_line - 1]
            label = _clean_label(label_source.removeprefix("# ").removeprefix("name:").strip())
            sources.append({
                "kind": kind, "name": name, "path": path, "lines": lines,
                "id": f"{kind}:{name}", "label": label, "line": evidence_line,
            })

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    edge_ids: set[str] = set()

    def add_node(node_id: str, kind: str, label: str, state: str,
                 evidence: list[dict[str, str]]) -> None:
        if node_id in node_ids:
            return
        node_ids.add(node_id)
        nodes.append({"id": node_id, "type": kind, "label": _clean_label(label),
                      "state": state, "evidence": evidence})

    def add_edge(source_id: str, target_id: str, relation: str, state: str,
                 evidence: list[dict[str, str]], suffix: str) -> None:
        edge_id = f"edge:{source_id}:{relation}:{target_id}:{suffix}"
        if edge_id in edge_ids:
            return
        edge_ids.add(edge_id)
        edges.append({"id": edge_id, "type": relation, "from": source_id, "to": target_id,
                      "state": state, "evidence": evidence})

    for source in sources:
        add_node(source["id"], source["kind"], source["label"], "observed",
                 [_evidence(revision, source["path"], source["line"])])

    names_by_id = {source["id"]: source for source in sources}
    references: dict[tuple[str, str], tuple[str, int]] = {}
    tool_references: dict[str, tuple[str, int, str]] = {}
    data_references: dict[str, tuple[str, int, str]] = {}
    gates_by_workflow: dict[str, list[tuple[int, str]]] = {}

    for source in sources:
        for line_number, line in enumerate(source["lines"], 1):
            for target in sources:
                if target["id"] == source["id"] or not _token_present(line, target["name"]):
                    continue
                key = (source["id"], target["id"])
                references.setdefault(key, (line, line_number))
            for match in TOOL_TOKEN.finditer(line):
                token = match.group(0)
                tool_references.setdefault(token, (source["path"], line_number, line))
            for token in DATA_FIELDS:
                if _token_present(line, token):
                    data_references.setdefault(token, (source["path"], line_number, line))
            if source["kind"] == "workflow" and GATE_LINE.search(line):
                gates_by_workflow.setdefault(source["id"], []).append((line_number, line))

    for (source_id, target_id), (line, line_number) in sorted(references.items()):
        source = names_by_id[source_id]
        target = names_by_id[target_id]
        relation = "calls" if source["kind"] == "workflow" else "depends_on"
        evidence = [_evidence(revision, source["path"], line_number)]
        add_edge(source_id, target_id, relation, "observed", evidence, f"L{line_number}")

    for token, (path, line_number, line) in sorted(tool_references.items()):
        tool_id = f"tool:{token}"
        add_node(tool_id, "tool", token, "observed",
                 [_evidence(revision, path, line_number)])
        source_id = next(s["id"] for s in sources if s["path"] == path)
        add_edge(source_id, tool_id, "calls", "observed",
                 [_evidence(revision, path, line_number)], f"L{line_number}")

    for token, (path, line_number, line) in sorted(data_references.items()):
        data_id = f"data:{token}"
        add_node(data_id, "data", token.replace("_", " "), "observed",
                 [_evidence(revision, path, line_number)])
        source_id = next(s["id"] for s in sources if s["path"] == path)
        add_edge(source_id, data_id, "depends_on", "observed",
                 [_evidence(revision, path, line_number)], f"L{line_number}")

    for source in (item for item in sources if item["kind"] == "workflow"):
        gates = gates_by_workflow.get(source["id"], [])
        if gates:
            for line_number, line in gates:
                gate_id = f"gate:{source['name']}:L{line_number}"
                add_node(gate_id, "process", f"Failure gate, source line {line_number}: {line}",
                         "observed", [_evidence(revision, source["path"], line_number)])
                add_edge(source["id"], gate_id, "depends_on", "observed",
                         [_evidence(revision, source["path"], line_number)], f"L{line_number}")
        else:
            gate_id = f"gate:{source['name']}:undocumented"
            add_node(gate_id, "process", "Failure-gate documentation missing", "unknown", [])
            add_edge(source["id"], gate_id, "unknown", "unknown", [], "missing-gate")

        run_id = f"run:{source['name']}:not-run"
        add_node(run_id, "process", "Runtime gate execution: NOT_RUN (no run receipt supplied)",
                 "unknown", [])
        add_edge(source["id"], run_id, "unknown", "unknown", [], "no-run-receipt")

    model = {
        "schema_version": 1,
        "model_id": "skills-factory-investment-explorer",
        "source_revision": revision,
        "nodes": sorted(nodes, key=lambda n: n["id"]),
        "edges": sorted(edges, key=lambda e: e["id"]),
    }
    try:
        return validate_model(model)
    except ModelValidationError as error:
        raise ExplorerError(f"extracted model violates canonical IR: {error}") from error


def traverse(model: dict[str, Any], start_id: str) -> list[str]:
    """Return deterministic forward reachability across documented relations."""
    graph = {node["id"]: [] for node in model["nodes"]}
    for edge in model["edges"]:
        if edge["state"] != "unknown":
            graph[edge["from"]].append(edge["to"])
    if start_id not in graph:
        raise ExplorerError(f"unknown traversal start: {start_id}")
    seen = {start_id}
    queue = deque([start_id])
    while queue:
        current = queue.popleft()
        for target in sorted(graph[current]):
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return sorted(seen)


def dependency_cycles(model: dict[str, Any]) -> list[list[str]]:
    """Report cycles among source skill/workflow nodes; never invent an execution order."""
    eligible = {node["id"] for node in model["nodes"] if node["type"] in {"skill", "workflow"}}
    graph = {node_id: [] for node_id in eligible}
    for edge in model["edges"]:
        if edge["state"] != "unknown" and edge["from"] in eligible and edge["to"] in eligible:
            graph[edge["from"]].append(edge["to"])

    cycles: set[tuple[str, ...]] = set()
    active: list[str] = []
    active_set: set[str] = set()
    done: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in active_set:
            cycle = active[active.index(node_id):]
            rotations = [tuple(cycle[i:] + cycle[:i]) for i in range(len(cycle))]
            cycles.add(min(rotations))
            return
        if node_id in done:
            return
        active.append(node_id)
        active_set.add(node_id)
        for target in sorted(graph[node_id]):
            visit(target)
        active.pop()
        active_set.remove(node_id)
        done.add(node_id)

    for node_id in sorted(graph):
        visit(node_id)
    return [list(cycle) for cycle in sorted(cycles)]


def gate_report(model: dict[str, Any]) -> dict[str, list[str]]:
    """Separate missing documentation and unexecuted runtime gates from observed gates."""
    return {
        "missing_gate_documentation": sorted(
            n["id"] for n in model["nodes"]
            if n["type"] == "process" and n["state"] == "unknown"
            and n["label"] == "Failure-gate documentation missing"
        ),
        "runtime_not_run": sorted(
            n["id"] for n in model["nodes"]
            if n["type"] == "process" and n["state"] == "unknown"
            and n["label"].startswith("Runtime gate execution: NOT_RUN")
        ),
    }
