"""Build and render the exact-source ARC-04 Skills Factory investment explorer."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from scripts.architecture.archify_adapter import render
from scripts.architecture.skills_factory_explorer import (
    dependency_cycles, extract_model, gate_report, traverse,
)
from scripts.architecture.visualization_ir import model_digest

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    model = extract_model(ROOT, revision)
    receipt = render(model, ROOT, args.upstream, args.output_dir)
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
        "render_receipt": receipt,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "explorer-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
