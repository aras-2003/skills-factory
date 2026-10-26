"""Run a real ARC-03 render from the exact current checkout."""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
from scripts.architecture.archify_adapter import render

ROOT=Path(__file__).resolve().parents[2]
SOURCE_PATH="docs/architecture/archify/ARC-02-IR.md"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--upstream",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    revision=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
    source={"uri":f"repo://{SOURCE_PATH}","revision":revision,"locator":"L1"}
    model={
        "schema_version":1,"model_id":"arc03-synthetic-adapter-smoke","source_revision":revision,
        "nodes":[
            {"id":"skill","type":"skill","label":"Synthetic architecture skill","state":"observed","evidence":[source]},
            {"id":"tool","type":"tool","label":"Synthetic renderer tool","state":"observed","evidence":[source]},
        ],
        "edges":[{"id":"calls","type":"calls","from":"skill","to":"tool","state":"observed","evidence":[source]}],
    }
    receipt=render(model,ROOT,args.upstream,args.output_dir)
    print(json.dumps(receipt,sort_keys=True,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
