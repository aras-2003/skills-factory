"""Evidence-aware canonical visualization IR. No rendering, implicit edges or network calls."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

class ModelValidationError(ValueError):
    """Invalid, unsupported, or unverified diagram input."""

NODES = frozenset({"skill","workflow","tool","capability","process","application","data","owner","unknown"})
EDGES = frozenset({"requires","calls","produces","supports","owns","contains","depends_on","flows_to","unknown"})
STATES = frozenset({"observed","proposed","unknown"})
SHA = re.compile(r"[0-9a-f]{40}\Z")
LINES = re.compile(r"L([1-9]\d*)(?:-L?([1-9]\d*))?\Z")
POLICY = {
 "requires": {("workflow","skill"),("workflow","workflow"),("skill","skill"),("skill","tool")},
 "calls": {("workflow","skill"),("workflow","workflow"),("workflow","tool"),("skill","tool"),("application","application")},
 "produces": {("skill","data"),("workflow","data"),("process","data"),("application","data")},
 "supports": {("application","capability"),("application","process"),("process","capability")},
 "owns": {("owner",target) for target in ("capability","process","application","data")},
 "contains": {("capability",target) for target in ("capability","process","application","owner")},
 "depends_on": {(type_,type_) for type_ in ("skill","workflow","tool","capability","process","application","data")} | {("workflow","process"),("workflow","data"),("skill","data"),("skill","workflow")},
 "flows_to": {(type_,type_) for type_ in ("process","application","data","tool")},
 "unknown": set(),
}

def _text(v: Any, field: str) -> str:
    if not isinstance(v,str) or not v or v != v.strip() or len(v)>512 or any(ord(c)<32 or ord(c)==127 for c in v):
        raise ModelValidationError(f"{field}: nonempty trimmed text without controls required")
    return v

def _enum(v: Any, choices: frozenset, field: str) -> str:
    if not isinstance(v,str) or v not in choices:
        raise ModelValidationError(f"{field}: unsupported value")
    return v

def _path(uri: str) -> str:
    if not uri.startswith("repo://"):
        raise ModelValidationError("source: only repo:// source URIs supported")
    path=uri[7:]
    parts=path.split("/")
    if not path or len(path)>400 or path.startswith("/") or "\\" in path or any(p in ("",".","..") for p in parts) or any(not re.fullmatch(r"[a-zA-Z0-9_.@+-]+",p) for p in parts):
        raise ModelValidationError("source: unsafe repository-relative path")
    return path

def _evidence(v: Any, state: str, rev: str, field: str) -> list[dict]:
    if not isinstance(v,list) or (state=="unknown" and v) or (state!="unknown" and not v):
        raise ModelValidationError(f"{field}: evidence inconsistent with state")
    found=[]
    for ref in v:
        if not isinstance(ref,dict) or set(ref)!={"uri","revision","locator"}:
            raise ModelValidationError(f"{field}: exact uri/revision/locator required")
        item={k:_text(ref[k],f"{field}.{k}") for k in ("uri","revision","locator")}
        if item["revision"]!=rev:
            raise ModelValidationError(f"{field}: stale evidence revision")
        _path(item["uri"])
        m=LINES.fullmatch(item["locator"])
        if not m or int(m.group(2) or m.group(1))<int(m.group(1)):
            raise ModelValidationError(f"{field}: invalid line locator")
        found.append(item)
    return sorted(found,key=lambda x:(x["uri"],x["revision"],x["locator"]))

def validate_model(raw: Any) -> dict:
    """Deterministically normalize a structurally and semantically legal model; does not attest sources."""
    if not isinstance(raw,dict) or set(raw)!={"schema_version","model_id","source_revision","nodes","edges"}:
        raise ModelValidationError("model: unexpected or missing keys")
    if type(raw["schema_version"]) is not int or raw["schema_version"]!=1:
        raise ModelValidationError("schema_version: only integer 1 accepted")
    model_id=_text(raw["model_id"],"model_id")
    revision=_text(raw["source_revision"],"source_revision")
    if not SHA.fullmatch(revision):
        raise ModelValidationError("source_revision: full immutable lowercase Git SHA required")
    if not isinstance(raw["nodes"],list) or not isinstance(raw["edges"],list):
        raise ModelValidationError("nodes/edges must be arrays")
    nodes={}
    for obj in raw["nodes"]:
        if not isinstance(obj,dict) or set(obj)!={"id","type","label","state","evidence"}:
            raise ModelValidationError("node: unexpected or missing keys")
        id_=_text(obj["id"],"node.id")
        if id_ in nodes:
            raise ModelValidationError(f"duplicate node: {id_}")
        kind=_enum(obj["type"],NODES,"node.type")
        state=_enum(obj["state"],STATES,"node.state")
        nodes[id_]={"id":id_,"type":kind,"label":_text(obj["label"],"node.label"),"state":state,
                    "evidence":_evidence(obj["evidence"],state,revision,f"node {id_}")}
    edges={}
    for obj in raw["edges"]:
        if not isinstance(obj,dict) or set(obj)!={"id","type","from","to","state","evidence"}:
            raise ModelValidationError("edge: unexpected or missing keys")
        id_=_text(obj["id"],"edge.id")
        if id_ in edges:
            raise ModelValidationError(f"duplicate edge: {id_}")
        kind=_enum(obj["type"],EDGES,"edge.type")
        state=_enum(obj["state"],STATES,"edge.state")
        start,end=_text(obj["from"],"edge.from"),_text(obj["to"],"edge.to")
        if start not in nodes or end not in nodes:
            raise ModelValidationError(f"edge {id_}: dangling node reference")
        if state=="unknown":
            if kind!="unknown":
                raise ModelValidationError(f"edge {id_}: unknown state requires unknown type")
        else:
            if kind=="unknown" or (nodes[start]["type"],nodes[end]["type"]) not in POLICY[kind]:
                raise ModelValidationError(f"edge {id_}: relation not allowed for endpoint types")
            if nodes[start]["state"]=="unknown" or nodes[end]["state"]=="unknown":
                raise ModelValidationError(f"edge {id_}: asserted relation to unknown node")
        edges[id_]={"id":id_,"type":kind,"from":start,"to":end,"state":state,
                    "evidence":_evidence(obj["evidence"],state,revision,f"edge {id_}")}
    return {"schema_version":1,"model_id":model_id,"source_revision":revision,
            "nodes":[nodes[k] for k in sorted(nodes)],"edges":[edges[k] for k in sorted(edges)]}

def _git(root: Path,*args: str) -> bytes:
    try:
        r=subprocess.run(["git","-C",str(root),*args],capture_output=True,check=False,timeout=10)
    except (OSError,subprocess.TimeoutExpired) as e:
        raise ModelValidationError("source: Git unavailable") from e
    if r.returncode:
        raise ModelValidationError("source: Git revision or blob missing")
    return r.stdout

def verify_sources(model: Any,repo_root: str|Path) -> dict:
    """Verify line anchors at exact Git commit in a caller-provided trusted local repo.

    Existence of source text does not prove that the model claim is logically entailed.
    """
    obj=validate_model(model)
    root=Path(repo_root).resolve(strict=True)
    if not root.is_dir() or _git(root,"rev-parse","--is-inside-work-tree").strip()!=b"true":
        raise ModelValidationError("repo_root: trusted Git working tree required")
    rev=obj["source_revision"]
    if _git(root,"cat-file","-t",rev).strip()!=b"commit":
        raise ModelValidationError("source_revision: not a Git commit")
    cache={}
    for item in obj["nodes"]+obj["edges"]:
        for ref in item["evidence"]:
            name=_path(ref["uri"])
            if name not in cache:
                content=_git(root,"show",f"{rev}:{name}")
                if b"\0" in content:
                    raise ModelValidationError("source: binary blob cannot use line anchors")
                try:
                    cache[name]=content.decode("utf-8").splitlines()
                except UnicodeDecodeError as e:
                    raise ModelValidationError("source: non-UTF8 source") from e
            m=LINES.fullmatch(ref["locator"])
            assert m is not None
            if int(m.group(2) or m.group(1))>len(cache[name]):
                raise ModelValidationError(f"source: line locator beyond file end: {name}")
    return obj

def canonical_json(model: Any) -> str:
    return json.dumps(validate_model(model),sort_keys=True,ensure_ascii=False,separators=(",",":"))

def model_digest(model: Any) -> str:
    return hashlib.sha256(canonical_json(model).encode("utf-8")).hexdigest()
