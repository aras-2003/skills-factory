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
import uuid
from pathlib import Path
from scripts.architecture.visualization_ir import verify_sources, model_digest, ModelValidationError

UPSTREAM_SHA="208acba8d412335185b2056fedf54b3405df43fb"
SANDBOX_IMAGE="mcr.microsoft.com/playwright@sha256:eff16c30e6f3f4af0a03fa4b706120d5e9b0891c344a27d64559aff5900a4a27"
BOUNDARY_MARKERS=("ARC03_BOUNDARY=network-denied","ARC03_BOUNDARY=rootfs-read-only","ARC03_BOUNDARY=source-read-only","ARC03_BOUNDARY=candidate-read-only","ARC03_BOUNDARY=output-separated")
SANDBOX_SCRIPT="""set -eu
node - <<'JS'
const fs=require('fs');
const https=require('https');
const lines=fs.readFileSync('/proc/mounts','utf8').trim().split('\\n');
function flagsAt(path){const row=lines.map(line=>line.split(' ')).find(fields=>fields[1]===path);return row?row[3].split(','):null;}
const root=flagsAt('/');
const source=flagsAt('/home/pwuser/archify');
const candidate=flagsAt('/home/pwuser/candidate.json');
const output=flagsAt('/home/pwuser/out');
if(!root||!root.includes('ro'))process.exit(81);
if(!source||!source.includes('ro'))process.exit(82);
if(!candidate||!candidate.includes('ro'))process.exit(83);
if(!output||!output.includes('rw'))process.exit(84);
console.error('ARC03_BOUNDARY=rootfs-read-only');
console.error('ARC03_BOUNDARY=source-read-only');
console.error('ARC03_BOUNDARY=candidate-read-only');
console.error('ARC03_BOUNDARY=output-separated');
const request=https.get('https://example.com',{timeout:3000},response=>{response.resume();console.error('ARC03_BOUNDARY=network-available');process.exit(85);});
request.on('timeout',()=>{request.destroy();console.error('ARC03_BOUNDARY=network-denied');});
request.on('error',()=>console.error('ARC03_BOUNDARY=network-denied'));
JS
CHROME="$(find /ms-playwright -type f -name chrome -perm -u+x -print -quit)"
test -n "$CHROME"
export HOME=/tmp
export TMPDIR=/tmp
export ARCHIFY_UPDATE_CHECK_DISABLED=1
export ARCHIFY_CHROME="$CHROME"
cd /home/pwuser/out
exec node /home/pwuser/archify/archify/bin/archify.mjs finalize architecture /home/pwuser/candidate.json diagram.html --quality standard --json
"""
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

def _fresh_output_dir(path: Path) -> tuple[Path,bool]:
    requested=Path(path).expanduser()
    if not requested.is_absolute():
        requested=Path.cwd()/requested
    absolute=Path(os.path.abspath(requested))
    current=Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current=current/part
        if current.is_symlink():
            raise RenderError("output path cannot contain a symlink")
    existed=absolute.exists()
    if existed and (not absolute.is_dir() or any(absolute.iterdir())):
        raise RenderError("output_dir must be a fresh empty directory")
    absolute.mkdir(parents=True,exist_ok=True)
    if absolute.is_symlink():
        raise RenderError("output_dir cannot be a symlink")
    return absolute,existed

def _sandbox_command(docker_binary:str,name:str,upstream:Path,candidate:Path,output_dir:Path,uid:int,gid:int)->list[str]:
    for item in (str(upstream),str(candidate),str(output_dir)):
        if "," in item:
            raise RenderError("sandbox paths cannot contain commas")
    return [
        docker_binary,"run","--rm","--init","--name",name,
        "--platform","linux/amd64","--network","none","--read-only",
        "--cap-drop","ALL","--security-opt","no-new-privileges:true",
        "--pids-limit","128","--memory","2g","--cpus","2","--shm-size","1g",
        "--user",f"{uid}:{gid}",
        "--tmpfs",f"/tmp:rw,noexec,nosuid,nodev,size=256m,uid={uid},gid={gid}",
        "--mount",f"type=bind,source={upstream},target=/home/pwuser/archify,readonly",
        "--mount",f"type=bind,source={candidate},target=/home/pwuser/candidate.json,readonly",
        "--mount",f"type=bind,source={output_dir},target=/home/pwuser/out",
        SANDBOX_IMAGE,"/bin/sh","-lc",SANDBOX_SCRIPT,
    ]

def render(model:dict,repo_root:Path,archify_root:Path,output_dir:Path,*,docker_binary:str="docker",timeout:int=180)->dict:
    """Verify canonical sources and run pinned Archify inside a network/filesystem-bounded container."""
    if type(timeout) is not int or not 1<=timeout<=600:
        raise RenderError("timeout must be an integer between 1 and 600 seconds")
    dest,existed=_fresh_output_dir(Path(output_dir))
    validated=verify_sources(model,repo_root)
    upstream=Path(archify_root).resolve(strict=True)
    if _git_sha(upstream)!=UPSTREAM_SHA:
        raise RenderError("Archify source SHA mismatch")
    cli=upstream/"archify"/"bin"/"archify.mjs"
    if not cli.is_file():
        raise RenderError("pinned Archify CLI missing")
    try:
        image=subprocess.run([docker_binary,"image","inspect",SANDBOX_IMAGE],capture_output=True,text=True,timeout=15,check=False)
    except (OSError,subprocess.TimeoutExpired) as e:
        raise RenderError("pinned sandbox image must be pulled before rendering") from e
    if image.returncode:
        raise RenderError("pinned Playwright sandbox image is not present locally")
    candidate=archify_candidate(validated)
    candidate_json=json.dumps(candidate,ensure_ascii=False,sort_keys=True,indent=2)
    name=f"archify-{uuid.uuid4().hex[:16]}"
    with tempfile.TemporaryDirectory(prefix="archify-candidate-") as stage:
        candidate_path=Path(stage)/"candidate.json"
        candidate_path.write_text(candidate_json,encoding="utf-8")
        command=_sandbox_command(docker_binary,name,upstream,candidate_path,dest,os.getuid(),os.getgid())
        try:
            proc=subprocess.run(command,capture_output=True,text=True,timeout=timeout,check=False)
        except subprocess.TimeoutExpired as e:
            subprocess.run([docker_binary,"rm","--force",name],capture_output=True,text=True,timeout=15,check=False)
            raise RenderError("isolated Archify execution timed out") from e
        except OSError as e:
            raise RenderError("Docker sandbox execution failed") from e
    if proc.returncode:
        raise RenderError(f"isolated Archify execution failed with exit {proc.returncode}")
    missing=[marker for marker in BOUNDARY_MARKERS if marker not in proc.stderr]
    if missing:
        raise RenderError("sandbox boundary receipt incomplete: "+", ".join(missing))
    try:
        receipt=json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RenderError("Archify did not emit valid JSON evidence") from e
    gates=receipt.get("gates",{})
    if receipt.get("ok") is not True or any(gates.get(g)!="pass" for g in ("validate","deliver","check","browser-check")) or receipt.get("browserCheck",{}).get("ran") is not True:
        raise RenderError("Archify failed one or more mandatory gates")
    html=dest/"diagram.html"
    if not html.is_file() or html.is_symlink():
        raise RenderError("expected HTML artifact absent or unsafe")
    data=html.read_bytes()
    if len(data)<1000:
        raise RenderError("HTML artifact unexpectedly short")
    digest=model_digest(validated)
    provenance={
        "nodes":[{"renderer_id":f"n{i}","model_id":node["id"],"state":node["state"],"evidence":node["evidence"]} for i,node in enumerate(validated["nodes"])],
        "edges":[{"renderer_id":f"e{i}","model_id":edge["id"],"state":edge["state"],"evidence":edge["evidence"]} for i,edge in enumerate(validated["edges"])],
    }
    sandbox_receipt={
        "sandbox_image":SANDBOX_IMAGE,
        "platform":"linux/amd64",
        "network":"none; external HTTPS probe failed inside the render container",
        "filesystem":"read-only root; source/candidate read-only; output separately writable",
        "capabilities":"all dropped; no-new-privileges; non-root uid; resource limits applied",
        "host_environment_forwarded":False,
        "source_revision":validated["source_revision"],
        "model_digest":digest,
        "upstream_sha":UPSTREAM_SHA,
        "html_sha256":hashlib.sha256(data).hexdigest(),
        "html_bytes":len(data),
        "browser_check_ran":True,
        "output_directory_preexisted_empty":existed,
    }
    (dest/"finalize-receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\\n",encoding="utf-8")
    (dest/"sandbox-receipt.json").write_text(json.dumps(sandbox_receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\\n",encoding="utf-8")
    (dest/"provenance-index.json").write_text(json.dumps(provenance,ensure_ascii=False,sort_keys=True,indent=2)+"\\n",encoding="utf-8")
    return sandbox_receipt

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
