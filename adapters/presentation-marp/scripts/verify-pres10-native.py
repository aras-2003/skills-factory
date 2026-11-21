#!/usr/bin/env python3
"""Inspect PRES-10 native PPTX, ODP source and layout manifest without trusting CLI success."""
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

deck_file, manifest_file, pptx_file, odp_file, report_file = map(Path,sys.argv[1:6])
deck=json.loads(deck_file.read_text())
manifest=json.loads(manifest_file.read_text())
expected=deck["slides"]
if len(expected)!=10 or len(manifest["slides"])!=10:
 raise SystemExit("Expected exactly ten slide and pattern records")
if any(x["status"]!="PLANNED_NOT_RENDERED" for x in manifest["slides"]):
 raise SystemExit("Source layout mapping is incomplete")
if len({x["layout_id"] for x in manifest["slides"]})<8:
 raise SystemExit("Less than eight distinct reference layouts were consumed")
if any(not x.get("reference_evidence") for x in manifest["slides"]):
 raise SystemExit("Missing reference evidence in layout plan")
if not pptx_file.exists() or pptx_file.stat().st_size<10000:
 raise SystemExit("PPTX absent or implausibly small")
if not odp_file.exists():
 raise SystemExit("Original editable ODP source missing")
ns={"p":"http://schemas.openxmlformats.org/presentationml/2006/main","a":"http://schemas.openxmlformats.org/drawingml/2006/main"}
stats=[]
with zipfile.ZipFile(pptx_file) as z:
 if z.testzip() is not None:
  raise SystemExit("PPTX ZIP corruption")
 slide_names=sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml",n)),key=lambda s:int(re.search(r"(\d+)\.xml$",s).group(1)))
 if len(slide_names)!=10:
  raise SystemExit(f"Expected 10 PPTX slide XMLs, found {len(slide_names)}")
 for idx,(name,expected_slide) in enumerate(zip(slide_names,expected),1):
  root=ET.fromstring(z.read(name))
  all_text=" ".join(x.text or "" for x in root.findall(".//a:t",ns))
  norm=lambda s:re.sub(r"\s+"," ",s).strip().lower()
  title=expected_slide["action_title"]
  if norm(title) not in norm(all_text):
   raise SystemExit(f"Slide {idx} native XML missing action title: {title!r}")
  user_copy=expected_slide.get("extensions",{}).get("executive",{}).get("copy",{})
  for key,val in user_copy.items():
   if norm(val) not in norm(all_text):
    raise SystemExit(f"Slide {idx} original content override not present: {key}")
  shapes=root.findall(".//p:sp",ns)
  if len(shapes)<8:
   raise SystemExit(f"Slide {idx} has only {len(shapes)} editable shapes")
  stats.append({"slide_id":expected_slide["slide_id"],"xml":name,"editable_shapes":len(shapes),
     "action_title_present":True,"reference_layout":manifest["slides"][idx-1]["layout_id"]})
with zipfile.ZipFile(odp_file) as z:
 if z.testzip() is not None: raise SystemExit("ODP ZIP corruption")
result={"status":"NATIVE_XML_VERIFIED","visual_quality":"NOT_RUN","independent_review":"NOT_RUN",
        "powerpoint_gui_roundtrip":"NOT_RUN","libreoffice_conversion":"VERIFIED_BY_OUTPUT",
        "slide_count":len(stats),"source_manifest":str(manifest_file),"slides":stats}
report_file.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"slide_count":len(stats),"min_shapes":min(s["editable_shapes"] for s in stats),
"status":"NATIVE_XML_VERIFIED"}))
