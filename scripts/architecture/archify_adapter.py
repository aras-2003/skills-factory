"""ARC-03: evidence-gated Archify renderer (offline output, never published to Site).

Caller supplies a *trusted* local canonical Git checkout and pinned Archify source.
This process does not provide an OS sandbox: production execution requires one.
"""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from scripts.architecture.visualization_ir import verify_sources, model_digest, ModelValidationError

UPSTREAM_SHA="208acba8d412335185b2056fedf54b3405df43fb"
TYPE_MAP={"skill":"backend","workflow":"backend","tool":"cloud",
          "capability":"backend","process":"backend","application":"cloud",
          "data":"database","owner":"external","unknown":"external"}

class RenderError(RuntimeError):
    pass

def archify_candidate(model: dict) -> dict:
    """Deterministic layout and metadata. Evidence passed separately, not disguised as source claims."""
    from scripts.architecture.visualization_ir import validate_model
    obj=validate_model(model)
    nodes=obj["nodes"]
    by_id={n["id"]:n for n in nodes}
    components=[{"id":f"n{i}","type":TYPE_MAP[n["type"]],
                 "label":n["label"][:80],"pos":[50+(i%3)*350,70+(i//3)*210],
                 "size":[180,76]} for i,n in enumerate(nodes)]
    ids={n["id"]:f"n{i}" for i,n in enumerate(nodes)}
    edges=[{"id":f"e{i}","from":ids[e["from"]],"to":ids[e["to"]],
            "label":e["type"].replace("_"," ")[:50],
            **({"variant":"dashed"} if e["state"]=="unknown" else {})}
           for i,e in enumerate(obj["edges"])]
    return {"schema_version":1,"diagram_type":"architecture",
            "meta":{"title":"Evidence-backed architecture view","output":"diagram.html","quality_profile":"standard"},
            "components":components,"connections":edges}

def _git_sha(root: Path) -> str:
    r=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],
                     capture_output=True,text=True,timeout=15,check=False)
    if r.returncode:
        raise RenderError("Archify checkout is not a trusted Git checkout")
    return r.stdout.strip()

def render(model:dict, repo_root:Path, archify_root:Path, output_dir:Path,
           *, node_binary:str="node", timeout:int=120) -> dict:
    """Fail closed; no host/same-origin HTML embedding, and no implicit network sandbox claim."""
    validated=verify_sources(model,repo_root)
    upstream=Path(archify_root).resolve(strict=True)
    if _git_sha(upstream)!=UPSTREAM_SHA:
        raise RenderError("Archify source SHA mismatch")
    cli=upstream/"archify"/"bin"/"archify.mjs"
    if not cli.is_file():
        raise RenderError("pinned Archify CLI missing")
    dest=Path(output_dir).resolve()
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise RenderError("output_dir must be a fresh empty directory")
    dest.mkdir(parents=True,exist_ok=True)
    if dest.is_symlink():
        raise RenderError("symlink destination disallowed")
    candidate=archify_candidate(validated)
    raw=json.dumps(candidate,ensure_ascii=False,sort_keys=True,indent=2)
    (dest/"candidate.json").write_text(raw,encoding="utf-8")
    env={**os.environ,"ARCHIFY_UPDATE_CHECK_DISABLED":"1"}
    command=[node_binary,str(cli),"finalize","architecture","candidate.json","diagram.html",
             "--quality","standard","--json"]
    try:
        proc=subprocess.run(command,cwd=dest,env=env,text=True,capture_output=True,
                            timeout=timeout,check=False)
    except (OSError,subprocess.TimeoutExpired) as e:
        raise RenderError("Archify execution failed or timed out") from e
    (dest/"finalize-receipt.json").write_text(proc.stdout,encoding="utf-8")
    try:
        receipt=json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RenderError("Archify did not emit valid JSON evidence") from e
    gates=receipt.get("gates",{})
    if proc.returncode or receipt.get("ok") is not True or any(
        gates.get(g)!="pass" for g in ("validate","deliver","check","browser-check")
    ):
        raise RenderError("Archify failed one or more mandatory gates")
    html=dest/"diagram.html"
    if not html.is_file() or html.is_symlink():
        raise RenderError("expected HTML artifact absent or unsafe")
    data=html.read_bytes()
    if len(data)<1000:
        raise RenderError("HTML artifact unexpectedly short")
    return {"source_revision":validated["source_revision"],"model_digest":model_digest(validated),
            "upstream_sha":UPSTREAM_SHA,"html_sha256":hashlib.sha256(data).hexdigest(),
            "html_bytes":len(data),"gates":gates,"publication":"forbidden; sandboxed viewer required"}

def offline_svg_fallback(model:dict) -> str:
    """Safe noninteractive static fallback: no scripts/links/external resources."""
    import html
    data=archify_candidate(model)
    nodes=data["components"]
    w=1050
    h=max(320,110+((len(nodes)+2)//3)*210)
    body=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="Architecture overview">']
    for n in nodes:
        x,y=n["pos"]
        body.append(f'<rect x="{x}" y="{y}" width="180" height="76" rx="8" fill="#edf2f7" stroke="#334155"/>')
        body.append(f'<text x="{x+12}" y="{y+42}" font-size="14" fill="#1e293b">{html.escape(n["label"],quote=True)}</text>')
    positions={n["id"]:(n["pos"][0],n["pos"][1]) for n in nodes}
    for edge in data["connections"]:
        x1,y1=positions[edge["from"]]
        x2,y2=positions[edge["to"]]
        body.append(f'<line x1="{x1+90}" y1="{y1+76}" x2="{x2+90}" y2="{y2}" stroke="#475569" stroke-width="2"{" stroke-dasharray="+chr(34)+"5 4"+chr(34) if edge.get("variant")=="dashed" else ""}/>')
        body.append(f'<text x="{(x1+x2)/2+90}" y="{(y1+y2+76)/2-6}" font-size="11" fill="#334155">{html.escape(edge["label"])}</text>')
    body.append("</svg>")
    return "\n".join(body)
