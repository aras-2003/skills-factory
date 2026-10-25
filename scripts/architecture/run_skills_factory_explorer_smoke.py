"""Build exact-source ARC-04 graph and render readable representative views."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from scripts.architecture.archify_adapter import render
from scripts.architecture.skills_factory_explorer import (
    dependency_cycles, extract_model, gate_report, traverse,
)
from scripts.architecture.visualization_ir import model_digest, validate_model

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_ROOTS = ("workflow:investment-security-review", "workflow:investment-theme-discovery")


def sample_view(model: dict[str, Any], root_id: str) -> dict[str, Any]:
    """Keep one documented workflow, its direct skill/workflow/data lineage, and its gates."""
    by_id = {node["id"]: node for node in model["nodes"]}
    if root_id not in by_id:
        raise ValueError(f"sample root absent from source graph: {root_id}")
    selected = {root_id}
    for edge in model["edges"]:
        if edge["from"] == root_id:
            target = by_id[edge["to"]]
            if edge["state"] != "unknown" and target["type"] in {"skill", "workflow", "data"}:
                selected.add(target["id"])
            elif target["type"] == "process":
                selected.add(target["id"])
    nodes = [node for node in model["nodes"] if node["id"] in selected]
    edges = [edge for edge in model["edges"]
             if edge["from"] in selected and edge["to"] in selected]
    return validate_model({
        "schema_version": model["schema_version"],
        "model_id": f"{model['model_id']}:{root_id}",
        "source_revision": model["source_revision"],
        "nodes": nodes,
        "edges": edges,
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    model = extract_model(ROOT, revision)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "explorer-model.json").write_text(
        json.dumps(model, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    receipts = {}
    for root_id in SAMPLE_ROOTS:
        view = sample_view(model, root_id)
        name = root_id.removeprefix("workflow:")
        receipts[name] = {
            "model_digest": model_digest(view),
            "node_count": len(view["nodes"]),
            "edge_count": len(view["edges"]),
            "receipt": render(view, ROOT, args.upstream, args.output_dir / name),
        }
    summary = {
        "model_id": model["model_id"],
        "source_revision": revision,
        "model_digest": model_digest(model),
        "skill_nodes": sum(node["type"] == "skill" for node in model["nodes"]),
        "workflow_nodes": sum(node["type"] == "workflow" for node in model["nodes"]),
        "tool_nodes": sum(node["type"] == "tool" for node in model["nodes"]),
        "data_nodes": sum(node["type"] == "data" for node in model["nodes"]),
        "documented_gate_nodes": sum(
            node["type"] == "process" and node["state"] == "observed"
            for node in model["nodes"]
        ),
        "gate_status": gate_report(model),
        "dependency_cycles": dependency_cycles(model),
        "reachable_from_investment_os_review": traverse(
            model, "workflow:investment-os-review"
        ),
        "rendered_sample_views": receipts,
    }
    (args.output_dir / "explorer-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
