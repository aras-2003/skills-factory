#!/usr/bin/env python3
"""No-dependency negative-safe structural check for ARC-01 synthetic fixture.

This is NOT the Archify validator or browser execution.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic-architecture.json"


def main() -> None:
    raw = FIXTURE.read_bytes()
    data = json.loads(raw)
    assert data["diagram_type"] == "architecture"
    assert data["schema_version"] == 1
    assert data["meta"]["quality_profile"] == "showcase"
    assert data["meta"]["output"] == "synthetic-architecture.html"
    nodes = data["components"]
    edges = data["connections"]
    assert len(nodes) == 3 and len(edges) == 2
    ids = [node["id"] for node in nodes]
    assert len(ids) == len(set(ids))
    assert {edge["id"] for edge in edges} == {"route", "receipt"}
    for edge in edges:
        assert edge["from"] in ids and edge["to"] in ids
    for item in nodes + edges:
        for val in item.values():
            if isinstance(val, str):
                assert not any(x in val.lower() for x in ("<script", "javascript:", "data:text/html", "onerror="))
    print("fixture_static_check=PASS")
    print("fixture_sha256=" + hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
