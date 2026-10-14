"""Verify native Site receipts without rewriting them into Lab attestations.

These checks prove correspondence only; all provider data remain unsigned.
"""
from __future__ import annotations

import hashlib
import json
import re


def canonical_sha(value: object) -> str:
    # The tested Site fixture surface uses integers and finite fractional JSON
    # numbers. Normalize integral floats to JS JSON.stringify's representation.
    def normalize(x):
        if isinstance(x, dict):
            return {k: normalize(v) for k, v in x.items()}
        if isinstance(x, list):
            return [normalize(v) for v in x]
        if isinstance(x, float) and x.is_integer():
            return int(x)
        return x
    raw = json.dumps(normalize(value), sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def unwrap(raw: dict) -> dict:
    if not isinstance(raw, dict) or raw.get("isError") is True:
        raise ValueError("native tool output unavailable or failed")
    if isinstance(raw.get("structuredContent"), dict):
        return raw["structuredContent"]
    if isinstance(raw.get("content"), list):
        blocks = [b for b in raw["content"] if isinstance(b, dict) and b.get("type") == "text"]
        if len(blocks) != 1:
            raise ValueError("ambiguous native text output")
        value = json.loads(blocks[0]["text"])
        if not isinstance(value, dict):
            raise ValueError("native output is not an object")
        return value
    return raw


def verify_identity(raw: dict, candidate: dict) -> dict:
    value = unwrap(raw)
    source = value.get("source_revision")
    if (value.get("channel") != "site" or value.get("attestation_status") != "verified"
            or value.get("identity_source") not in {"site_environment", "cloudflare_version_metadata"}
            or not isinstance(source, str) or not re.fullmatch(r"[a-f0-9]{40}", source)):
        raise ValueError("Site worker identity unavailable")
    lab = value.get("lab_release", {})
    for key in ("source_revision", "release_id", "payload_content_sha256"):
        if lab.get(key) != candidate.get(key) or not candidate.get(key):
            raise ValueError("embedded Lab identity mismatch: " + key)
    verify_call(value, "runtime_info", source)
    return value


def verify_call(raw: dict, tool: str, site_source: str) -> dict:
    output = unwrap(raw)
    receipt = output.get("tool_receipt", {})
    if (receipt.get("kind") != "unsigned_mcp_tool_call_receipt"
            or receipt.get("tool_name") != tool or receipt.get("status") != "SUCCESS"
            or receipt.get("execution_state") != "executed"
            or receipt.get("source_revision") != site_source):
        raise ValueError("native executed Site tool identity mismatch")
    body = {k: v for k, v in output.items() if k != "tool_receipt"}
    if receipt.get("output_sha256") != canonical_sha(body):
        raise ValueError("native canonical output digest mismatch")
    return output
