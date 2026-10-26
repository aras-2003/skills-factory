#!/usr/bin/env python3
"""Deterministic advisory style selector for Presentation OS. stdlib only."""
import argparse, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def select(brief, catalog=None):
    data=catalog or json.loads((ROOT/"templates.json").read_text(encoding="utf-8"))
    audience=str(brief.get("audience","")).lower()
    purpose=str(brief.get("purpose","")).lower()
    density=str(brief.get("density","medium")).lower()
    medium=str(brief.get("medium","pptx")).lower()
    brand=brief.get("brand_style_id")
    if medium not in ("pptx","pdf","canva","figma","google-slides","web"):
        raise ValueError("Unsupported target medium")
    if density not in ("low","medium","high"):
        raise ValueError("Density must be low, medium or high")
    if brand and not any(s["id"]==brand for s in data["styles"]):
        raise ValueError("Unknown brand_style_id; do not silently ignore brand")
    query=f"{audience} {purpose}"
    tokens=set(query.replace("-"," ").split())
    scored=[]
    for style in data["styles"]:
        matched=sorted(set(style["tags"]) & tokens)
        score=3*len(matched)+(2 if density in style["density"] else -3)
        if "board" in tokens or "decision" in tokens:
            score-=style["novelty"]
        if brand:
            if style["id"]!=brand:
                continue
            score+=100
        scored.append({"style_id":style["id"],"score":score,"matched_tags":matched,
                       "density_fit":density in style["density"],
                       "fonts":{"heading":style["heading_font"],"body":style["body_font"],"data":style["data_font"]},
                       "palette":style["palette"],"layout_ids":style["layouts"],
                       "rights":"original_recipe","status":"ADVISORY_NOT_RENDER_VERIFIED"})
    return {"catalog_version":data["schema_version"],"brief":brief,
            "recommendations":sorted(scored,key=lambda x:(-x["score"],x["style_id"])),
            "warnings":["Confirm font installation, Polish glyphs and license in target.",
                        "Run actual renderer preflight, slide review and export parity before PASS."]}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--brief",required=True,help="JSON brief path")
    args=ap.parse_args()
    brief=json.loads(Path(args.brief).read_text(encoding="utf-8"))
    print(json.dumps(select(brief),ensure_ascii=False,indent=2))
