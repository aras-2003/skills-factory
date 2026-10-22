"""Canonical evidence-bearing diagram IR v1.

Transport-neutral: it never renders, fetches, or infers relationships.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


class ModelValidationError(ValueError):
    """Invalid or unsupported source-backed visualization model."""


NODE_TYPES = frozenset({"skill", "workflow", "tool", "capability", "process", "application", "data", "owner", "unknown"})
EDGE_TYPES = frozenset({"requires", "calls", "produces", "supports", "owns", "depends_on", "flows_to", "unknown"})
STATES = frozenset({"observed", "proposed", "unknown"})


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ModelValidationError(f"{path}: expected nonempty trimmed string")
    if len(value) > 512 or any(ord(ch) < 32 for ch in value):
        raise ModelValidationError(f"{path}: invalid characters or length")
    return value


def _source(value: Any, path: str, revision: str) -> dict:
    if not isinstance(value, dict) or set(value) != {"uri", "revision", "locator"}:
        raise ModelValidationError(f"{path}: exact uri/revision/locator required")
    source = {k: _text(value[k], f"{path}.{k}") for k in ("uri", "revision", "locator")}
    if source["revision"] != revision:
        raise ModelValidationError(f"{path}: stale or mismatched source revision")
    if not (source["uri"].startswith("repo://") or source["uri"].startswith("evidence://")):
        raise ModelValidationError(f"{path}: disallowed source URI scheme")
    return source


def validate_model(value: Any) -> dict:
    """Return ordered validated normalized model. No implicit edges and no mutations."""
    if not isinstance(value, dict) or set(value) != {"schema_version", "model_id", "source_revision", "nodes", "edges"}:
        raise ModelValidationError("model: required top-level keys differ")
    if value["schema_version"] != 1 or isinstance(value["schema_version"], bool):
        raise ModelValidationError("schema_version: only integer 1 supported")
    model_id = _text(value["model_id"], "model_id")
    revision = _text(value["source_revision"], "source_revision")
    for field in ("nodes", "edges"):
        if not isinstance(value[field], list):
            raise ModelValidationError(f"{field}: expected list")
    nodes = {}
    for raw in value["nodes"]:
        if not isinstance(raw, dict) or set(raw) != {"id", "type", "label", "state", "evidence"}:
            raise ModelValidationError("node: unexpected/missing keys")
        key = _text(raw["id"], "node.id")
        if key in nodes:
            raise ModelValidationError(f"duplicate node: {key}")
        if raw["type"] not in NODE_TYPES or raw["state"] not in STATES:
            raise ModelValidationError(f"node {key}: unsupported type/state")
        evidence = raw["evidence"]
        if not isinstance(evidence, list) or (not evidence and raw["state"] != "unknown"):
            raise ModelValidationError(f"node {key}: evidence required except unknown")
        if raw["state"] == "unknown" and evidence:
            raise ModelValidationError(f"node {key}: unknown must not masquerade as evidenced")
        nodes[key] = {"id": key, "type": raw["type"], "label": _text(raw["label"], "node.label"),
                      "state": raw["state"], "evidence": [_source(s, f"node {key}.evidence", revision) for s in evidence]}
    edges = {}
    for raw in value["edges"]:
        if not isinstance(raw, dict) or set(raw) != {"id", "type", "from", "to", "state", "evidence"}:
            raise ModelValidationError("edge: unexpected/missing keys")
        key = _text(raw["id"], "edge.id")
        if key in edges:
            raise ModelValidationError(f"duplicate edge: {key}")
        if raw["type"] not in EDGE_TYPES or raw["state"] not in STATES:
            raise ModelValidationError(f"edge {key}: unsupported type/state")
        left, right = _text(raw["from"], "edge.from"), _text(raw["to"], "edge.to")
        if left not in nodes or right not in nodes:
            raise ModelValidationError(f"edge {key}: dangling reference")
        evidence = raw["evidence"]
        if not isinstance(evidence, list) or (not evidence and raw["state"] != "unknown"):
            raise ModelValidationError(f"edge {key}: evidence required except unknown")
        if raw["state"] == "unknown" and evidence:
            raise ModelValidationError(f"edge {key}: unknown must not masquerade as evidenced")
        if raw["state"] != "unknown" and (nodes[left]["state"] == "unknown" or nodes[right]["state"] == "unknown"):
            raise ModelValidationError(f"edge {key}: evidenced edge linked to unknown node")
        edges[key] = {"id": key, "type": raw["type"], "from": left, "to": right, "state": raw["state"],
                      "evidence": [_source(s, f"edge {key}.evidence", revision) for s in evidence]}
    return {"schema_version": 1, "model_id": model_id, "source_revision": revision,
            "nodes": [nodes[k] for k in sorted(nodes)], "edges": [edges[k] for k in sorted(edges)]}


def canonical_json(model: Any) -> str:
    return json.dumps(validate_model(model), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def model_digest(model: Any) -> str:
    return hashlib.sha256(canonical_json(model).encode("utf-8")).hexdigest()
