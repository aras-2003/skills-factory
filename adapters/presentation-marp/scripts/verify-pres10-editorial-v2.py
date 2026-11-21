#!/usr/bin/env python3
"""Fail-closed native PPTX editorial v2 inspection (structural, not visual acceptance)."""
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

deck_path, manifest_path, pptx_path, report_path = map(Path,sys.argv[1:5])
deck=json.loads(deck_path.read_text())
manifest=json.loads(manifest_path.read_text())
roles=["decision","options","architecture","roadmap"]
if [s.get("role") for s in deck.get("slides",[])]!=roles:
    raise SystemExit("Editorial stage one fixture role/order contract broken")
if len(manifest.get("slides",[]))!=4:
    raise SystemExit("Expected four source-pattern mappings")
expected_layouts={"LAYOUT-DECISION","LAYOUT-OPTIONS","LAYOUT-ARCHITECTURE","LAYOUT-ROADMAP"}
if {s.get("layout_id") for s in manifest["slides"]}!=expected_layouts:
    raise SystemExit("Source-to-layout mapping incomplete")
if any(s.get("status")!="PLANNED_NOT_RENDERED" or not s.get("reference_evidence") for s in manifest["slides"]):
    raise SystemExit("Reference evidence not connected")
NS={"p":"http://schemas.openxmlformats.org/presentationml/2006/main",
    "a":"http://schemas.openxmlformats.org/drawingml/2006/main"}
slide_receipts=[]
with zipfile.ZipFile(pptx_path) as z:
    if z.testzip() is not None: raise SystemExit("Broken PPTX zip")
    names=sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml",n)),
        key=lambda n:int(re.search(r"(\d+)\.xml$",n).group(1)))
    if len(names)!=4: raise SystemExit(f"Expected four slides: {len(names)}")
    for idx,name in enumerate(names):
        root=ET.fromstring(z.read(name))
        text=" ".join(e.text or "" for e in root.findall(".//a:t",NS))
        norm=lambda s:re.sub(r"\s+"," ",s).strip().lower()
        expected=deck["slides"][idx]
        needed=[expected["action_title"]]
        content=expected["extensions"]["executive"]["editorial_v2"]
        if expected["role"]=="decision":
            needed += [content["recommendation"],content["board_ask"]]
        elif expected["role"]=="options":
            needed += [content["criterion_rows"][0]["criterion"],content["decision_condition"]]
        elif expected["role"]=="architecture":
            needed += content["nodes"]
            needed += [content["markets"][0],content["platforms"][-1]]
        else:
            needed += [content["phases"][0]["name"],content["phases"][-1]["deliverable"],content["gates"][0]]
        missing=[v for v in needed if norm(v) not in norm(text)]
        if missing: raise SystemExit(f"{expected['slide_id']}: missing native editable text: {missing}")
        shapes=len(root.findall(".//p:sp",NS))
        if shapes<12: raise SystemExit(f"{expected['slide_id']}: too few native editable objects ({shapes})")
        pictures=len(root.findall(".//p:pic",NS))
        if pictures: raise SystemExit(f"{expected['slide_id']}: image-backed flattening not allowed")
        slide_receipts.append({"slide_id":expected["slide_id"],"role":expected["role"],
          "editable_shapes":shapes,"images":pictures,"all_required_text":True,
          "reference_pattern":manifest["slides"][idx]["layout_id"]})
report={"status":"NATIVE_STRUCTURE_PASS","human_visual_acceptance":"NOT_RUN",
   "powerpoint_gui_roundtrip":"NOT_RUN","number_of_slides":4,
   "source_fixture":str(deck_path),"slides":slide_receipts}
report_path.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":report["status"],"slides":4,
  "minimum_native_shapes":min(s["editable_shapes"] for s in slide_receipts)}))
