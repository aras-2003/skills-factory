"""Deterministic, safe static export bundle for evidence-aware architecture models.

The bundle contains one accessible SVG, a complete text equivalent, and a
format matrix. It does not claim to render DOCX/PDF/PPTX containers or PNG.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
from pathlib import Path
from typing import Any

from scripts.architecture.visualization_ir import model_digest, validate_model


class ExportError(ValueError):
    """Unsafe destination or invalid export request."""


FORMAT_MATRIX = {
    "html": {
        "mode": "interactive",
        "diagram_semantics": "interactive source artifact; retain the original model",
        "embedding": "embed as a self-contained HTML attachment where supported",
        "accessible_equivalent": "include architecture.txt alongside the embed",
        "generated_here": False,
    },
    "svg": {
        "mode": "static-vector",
        "diagram_semantics": "all model nodes and directed relations are listed",
        "embedding": "embed architecture.svg",
        "accessible_equivalent": "architecture.svg has title/description; include architecture.txt",
        "generated_here": True,
    },
    "png": {
        "mode": "static-raster",
        "diagram_semantics": "rasterize the generated SVG; preserve architecture.txt and manifest",
        "embedding": "downstream rasterization required; do not substitute an unrelated preview",
        "accessible_equivalent": "attach architecture.txt as alt/long description",
        "generated_here": False,
    },
    "docx": {
        "mode": "flattened-embed",
        "diagram_semantics": "embed SVG or a rasterized derivative; retain text equivalent and manifest",
        "embedding": "static media only; no interactive HTML",
        "accessible_equivalent": "set image alt text and include architecture.txt in document",
        "generated_here": False,
    },
    "pdf": {
        "mode": "flattened-embed",
        "diagram_semantics": "embed SVG or a rasterized derivative; retain text equivalent and manifest",
        "embedding": "static media only; no interactive HTML",
        "accessible_equivalent": "tag the figure and include architecture.txt as accessible description",
        "generated_here": False,
    },
    "pptx": {
        "mode": "flattened-embed",
        "diagram_semantics": "embed SVG or a rasterized derivative; retain text equivalent and manifest",
        "embedding": "static media only; editable native shapes are not generated",
        "accessible_equivalent": "set image alt text and include architecture.txt in speaker notes or appendix",
        "generated_here": False,
    },
}


def _fresh_directory(path: str | Path) -> Path:
    requested = Path(path).expanduser()
    if not requested.is_absolute():
        requested = Path.cwd() / requested
    target = Path(os.path.abspath(requested))
    current = Path(target.anchor)
    for part in target.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ExportError("output path cannot contain a symlink")
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ExportError("output_dir must be a fresh empty directory")
    target.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise ExportError("output_dir cannot be a symlink")
    return target


def _svg(model: dict[str, Any], digest: str) -> str:
    """Produce a script-free SVG. Nodes and relations are explicit, never inferred."""
    nodes = model["nodes"]
    edges = model["edges"]
    width = 1100
    row_height = 48
    node_top = 100
    node_rows = max(1, len(nodes))
    edge_top = node_top + node_rows * row_height + 72
    edge_rows = max(1, len(edges))
    height = edge_top + edge_rows * row_height + 100
    title = "Evidence-backed architecture export"
    description = (
        f"{len(nodes)} nodes and {len(edges)} directed relations. "
        "The text equivalent lists every node, relation, state, evidence anchor, "
        f"source revision {model['source_revision']}, and model digest {digest}."
    )
    metadata = {
        "schema_version": 1,
        "model_id": model["model_id"],
        "source_revision": model["source_revision"],
        "model_digest": digest,
        "node_ids": [item["id"] for item in nodes],
        "edge_ids": [item["id"] for item in edges],
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">',
        f"<title>{html.escape(title)}</title>",
        f"<desc>{html.escape(description)}</desc>",
        f"<metadata>{html.escape(json.dumps(metadata, sort_keys=True), quote=False)}</metadata>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="32" y="46" font-size="24" font-weight="700" fill="#0f172a">{html.escape(title)}</text>',
        f'<text x="32" y="76" font-size="13" fill="#475569">{len(nodes)} nodes · {len(edges)} relations · revision {model["source_revision"]}</text>',
        '<text x="32" y="104" font-size="16" font-weight="700" fill="#0f172a">Nodes</text>',
    ]
    for index, node in enumerate(nodes):
        y = node_top + index * row_height
        parts.extend([
            f'<g id="node-{index}" data-model-id="{html.escape(node["id"], quote=True)}">',
            f'<rect x="32" y="{y}" width="1036" height="38" rx="5" fill="#f1f5f9" stroke="#64748b"/>',
            f'<text x="44" y="{y + 16}" font-size="12" font-weight="700" fill="#0f172a">{html.escape(node["id"])} · {html.escape(node["type"])} · {html.escape(node["state"])}</text>',
            f'<text x="44" y="{y + 31}" font-size="12" fill="#334155">{html.escape(node["label"])}</text>',
            "</g>",
        ])
    parts.append(f'<text x="32" y="{edge_top - 20}" font-size="16" font-weight="700" fill="#0f172a">Directed relations</text>')
    node_by_id = {item["id"]: item for item in nodes}
    for index, edge in enumerate(edges):
        y = edge_top + index * row_height
        start = node_by_id[edge["from"]]
        end = node_by_id[edge["to"]]
        state_label = "UNKNOWN" if edge["state"] == "unknown" else edge["state"].upper()
        relation = f'{edge["from"]} → {edge["type"]} → {edge["to"]}'
        parts.extend([
            f'<g id="edge-{index}" data-model-id="{html.escape(edge["id"], quote=True)}">',
            f'<rect x="32" y="{y}" width="1036" height="38" rx="5" fill="#fff" stroke="#94a3b8"/>',
            f'<text x="44" y="{y + 16}" font-size="12" font-weight="700" fill="#0f172a">{html.escape(edge["id"])} · {html.escape(state_label)} · {html.escape(relation)}</text>',
            f'<text x="44" y="{y + 31}" font-size="11" fill="#475569">from {html.escape(start["label"])} to {html.escape(end["label"])}</text>',
            "</g>",
        ])
    parts.extend([
        f'<text x="32" y="{height - 44}" font-size="11" fill="#475569">Source revision: {model["source_revision"]}</text>',
        f'<text x="32" y="{height - 24}" font-size="11" fill="#475569">Model digest: {digest}</text>',
        "</svg>",
    ])
    return "\n".join(parts) + "\n"


def _text_equivalent(model: dict[str, Any], digest: str) -> str:
    lines = [
        f"Architecture model: {model['model_id']}",
        f"Source revision: {model['source_revision']}",
        f"Model digest: {digest}",
        f"Nodes: {len(model['nodes'])}; directed relations: {len(model['edges'])}",
        "",
        "Nodes:",
    ]
    for node in model["nodes"]:
        lines.append(f"- {node['id']} [{node['type']}; {node['state']}]: {node['label']}")
        for ref in node["evidence"]:
            lines.append(f"  Evidence: {ref['uri']}@{ref['revision']} {ref['locator']}")
    lines.extend(["", "Directed relations:"])
    for edge in model["edges"]:
        state = "UNKNOWN" if edge["state"] == "unknown" else edge["state"]
        lines.append(f"- {edge['id']} [{state}]: {edge['from']} --{edge['type']}--> {edge['to']}")
        for ref in edge["evidence"]:
            lines.append(f"  Evidence: {ref['uri']}@{ref['revision']} {ref['locator']}")
    return "\n".join(lines) + "\n"


def build_export_bundle(model: Any, output_dir: str | Path) -> dict[str, Any]:
    """Write SVG, full text equivalent, and a truthful cross-format embedding matrix."""
    validated = validate_model(model)
    target = _fresh_directory(output_dir)
    digest = model_digest(validated)
    svg = _svg(validated, digest).encode("utf-8")
    text_equivalent = _text_equivalent(validated, digest).encode("utf-8")
    (target / "architecture.svg").write_bytes(svg)
    (target / "architecture.txt").write_bytes(text_equivalent)
    manifest = {
        "schema_version": 1,
        "model_id": validated["model_id"],
        "source_revision": validated["source_revision"],
        "model_digest": digest,
        "node_ids": [item["id"] for item in validated["nodes"]],
        "edge_ids": [item["id"] for item in validated["edges"]],
        "node_count": len(validated["nodes"]),
        "edge_count": len(validated["edges"]),
        "artifacts": {
            "svg": {"path": "architecture.svg", "sha256": hashlib.sha256(svg).hexdigest()},
            "text_equivalent": {"path": "architecture.txt", "sha256": hashlib.sha256(text_equivalent).hexdigest()},
        },
        "formats": FORMAT_MATRIX,
        "limitations": [
            "This adapter does not rasterize PNG.",
            "This adapter does not generate DOCX, PDF, or PPTX containers.",
            "PPTX native editable shapes are not implemented.",
            "Interactive HTML remains the separately generated source artifact.",
        ],
    }
    encoded = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (target / "export-manifest.json").write_bytes(encoded)
    return {**manifest, "manifest_sha256": hashlib.sha256(encoded).hexdigest()}
