"""Render the exact-source OAF capability-map sample with pinned Archify."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from scripts.architecture.archify_adapter import render
from scripts.architecture.oaf_architecture_explorer import coverage, extract_model, traverse
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
        **coverage(model),
        "model_id": model["model_id"],
        "source_revision": revision,
        "model_digest": model_digest(model),
        "capability_management_impact": traverse(model, "capability:customer-management"),
        "unresolved_edge_count": sum(edge["state"] == "unknown" for edge in model["edges"]),
        "render_receipt": receipt,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "oaf-explorer-model.json").write_text(
        json.dumps(model, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "oaf-explorer-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
