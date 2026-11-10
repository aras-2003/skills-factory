#!/usr/bin/env python3
import json, re, subprocess, sys
from pathlib import Path
pdf=Path(sys.argv[1]); expected=int(sys.argv[2]); out=Path(sys.argv[3]); mode=sys.argv[4] if len(sys.argv)>4 else 'text'
out.mkdir(parents=True, exist_ok=True)
info=subprocess.run(['pdfinfo', str(pdf)],check=True,text=True,capture_output=True).stdout
pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))
if pages != expected: raise SystemExit(f'PDF page count mismatch: {pages} != {expected}')
size=re.search(r'^Page size:\s+([\d.]+) x ([\d.]+) pts',info,re.M)
w,h=map(float,size.groups()); ratio=w/h
if abs(ratio-16/9)>.01: raise SystemExit(f'PDF page is not 16:9: {w}x{h}')
text=''
if mode == 'text':
    text=subprocess.run(['pdftotext','-layout',str(pdf),'-'],check=True,text=True,capture_output=True).stdout
    normalized_text=re.sub(r'\s+', ' ', text).strip()
    for required in ['Three slides, one source model','Synthetic quarterly growth','Preserve meaning across modes','12','18','percent','src-synthetic']:
        if required.lower() not in normalized_text.lower(): raise SystemExit(f'PDF text extraction missing expected content: {required}')
subprocess.run(['pdftoppm','-png','-r','96',str(pdf),str(out/'reopened-slide')],check=True,capture_output=True)
report={'pages':pages,'width_points':w,'height_points':h,'ratio':ratio,'reopened_by':'poppler-pdftoppm','content_extraction':'pdftotext' if mode=='text' else 'OCR in reopened presentation evidence'}
if mode=='text': report['extracted_text']=text
print(json.dumps(report,indent=2))
