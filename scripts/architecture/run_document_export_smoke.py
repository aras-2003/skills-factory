"""Retain the same synthetic ARC-06 fixture in every actual output container."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from scripts.architecture.document_exports import build_document_exports


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--node", default="node")
    parser.add_argument("--upstream", type=Path, help="also render the same fixture with pinned Archify in its Docker sandbox")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    # Evaluator fixture remains outside runtime payloads; no private data used.
    sys.path.insert(0, str(root / "tests/architecture"))
    from test_export_bundle import fixture
    model = fixture()
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    model["source_revision"] = revision
    for item in model["nodes"] + model["edges"]:
        for ref in item["evidence"]:
            ref.update(uri="repo://tests/architecture/test_export_bundle.py", revision=revision, locator="L1")
    model["nodes"][1]["label"] = "Raport źródłowy i relacje"
    result = build_document_exports(model, args.output_dir, node_executable=args.node)
    html_receipt = None
    if args.upstream:
        from scripts.architecture.archify_adapter import render
        html_receipt = render(model, root, args.upstream, Path(args.output_dir) / "interactive-html")
        if html_receipt["model_digest"] != result["model_digest"]:
            raise RuntimeError("HTML and static containers did not consume the identical model")
    receipt = {"schema_version": 1, "implementation_revision": revision,
               "working_tree_dirty": bool(subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).strip()),
               "implementation_files_sha256": {
                   name: hashlib.sha256((root / "scripts/architecture" / name).read_bytes()).hexdigest()
                   for name in ("export_bundle.py", "document_exports.py", "rasterize-export.cjs")
               },
               "fixture_scope": "synthetic shared ARC-06 fixture, not source attestation",
               "interactive_html": html_receipt,
               "model_digest": result["model_digest"], "artifacts": result["artifacts"],
               "validation": "test_document_exports.py verifies exact container pixels/text/provenance",
               "consumer_visual_review": "separate rendered Office/PDF evidence required"}
    (Path(args.output_dir) / "export-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
