#!/usr/bin/env python3
"""ARC-01 allowlisted synthetic fixture; NOT an Archify renderer/security audit."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

FIXTURE=Path(__file__).resolve().parents[1]/"fixtures"/"synthetic-architecture.json"

class UnsafeFixture(ValueError):
    """Reject unexpected content before invoking a third-party renderer."""

def validate(value: object) -> dict:
    if not isinstance(value,dict) or set(value)!={"schema_version","diagram_type","meta","components","connections"}:
        raise UnsafeFixture("unexpected diagram envelope")
    if type(value["schema_version"]) is not int or value["schema_version"]!=1 or value["diagram_type"]!="architecture":
        raise UnsafeFixture("unsupported version/diagram type")
    meta=value["meta"]
    if not isinstance(meta,dict) or set(meta)!={"title","output","quality_profile"}:
        raise UnsafeFixture("unexpected metadata")
    if meta["output"]!="synthetic-architecture.html" or meta["quality_profile"]!="showcase":
        raise UnsafeFixture("unapproved output path/profile")
    nodes,edges=value["components"],value["connections"]
    if not isinstance(nodes,list) or not isinstance(edges,list) or len(nodes)!=3 or len(edges)!=2:
        raise UnsafeFixture("unexpected graph size")
    ids=set()
    for node in nodes:
        if not isinstance(node,dict) or set(node)!={"id","type","label","pos","size"}:
            raise UnsafeFixture("unexpected node fields")
        if not isinstance(node["type"],str) or node["type"] not in {"backend","database"}:
            raise UnsafeFixture("unsupported node type")
        if not isinstance(node["id"],str) or not re.fullmatch("[a-z0-9_-]{1,40}",node["id"]) or node["id"] in ids:
            raise UnsafeFixture("invalid/duplicate node ID")
        ids.add(node["id"])
        for k in ("pos","size"):
            arr=node[k]
            if not isinstance(arr,list) or len(arr)!=2 or any(type(x) not in (int,float) or x<0 or x>2000 for x in arr):
                raise UnsafeFixture("invalid node geometry")
    for edge in edges:
        if not isinstance(edge,dict) or set(edge)!={"id","from","to","label"}:
            raise UnsafeFixture("unexpected edge fields")
        if not isinstance(edge["id"],str) or not re.fullmatch("[a-z0-9_-]{1,40}",edge["id"]):
            raise UnsafeFixture("invalid edge ID")
        if not isinstance(edge["from"],str) or not isinstance(edge["to"],str) or edge["from"] not in ids or edge["to"] not in ids:
            raise UnsafeFixture("dangling edge")
    if {edge["id"] for edge in edges}!={"route","receipt"}:
        raise UnsafeFixture("unexpected relationship IDs")
    for obj in [meta,*nodes,*edges]:
        for key,text in obj.items():
            if key in {"title","label"}:
                if not isinstance(text,str) or not text or len(text)>100 or not re.fullmatch(r"[\w \-]+",text,re.UNICODE):
                    raise UnsafeFixture("active HTML, URL or arbitrary markup not allowed")
    return value

def main() -> None:
    raw=FIXTURE.read_bytes()
    validate(json.loads(raw))
    print("fixture_static_check=PASS")
    print("fixture_sha256="+hashlib.sha256(raw).hexdigest())

if __name__=="__main__":
    main()
