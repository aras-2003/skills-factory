#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
reference=Path(sys.argv[1]); target_dir=Path(sys.argv[2]); out=Path(sys.argv[3]); threshold=float(sys.argv[4])
reference_files=sorted(reference.glob('html-slide-*.png'))
records=[]
for i, ref in enumerate(reference_files,1):
    candidates=[target_dir/f'reopened-slide-{i}.png',target_dir/f'reopened-slide-{i:02}.png',target_dir/f'reopened-slide-{i:03}.png']
    target=next((p for p in candidates if p.exists()),None)
    if target is None: raise SystemExit(f'missing reopened screenshot for slide {i}')
    if not target.exists(): raise SystemExit(f'missing reopened screenshot: {target}')
    proc=subprocess.run(['compare','-metric','MAE','-resize','1280x720!',str(ref),'-resize','1280x720!',str(target),'null:'],capture_output=True,text=True)
    metric=(proc.stderr or proc.stdout).strip().split()
    normalized=None
    for token in reversed(metric):
        if token.startswith('(') and token.endswith(')'):
            try: normalized=float(token.strip('()')); break
            except ValueError: pass
    if normalized is None: raise SystemExit(f'could not parse ImageMagick MAE for slide {i}: {proc.stderr}')
    records.append({'slide':i,'normalized_mae':normalized,'threshold':threshold,'state':'PASS' if normalized<=threshold else 'FAIL'})
    if normalized>threshold: raise SystemExit(f'visual drift over threshold on slide {i}: {normalized} > {threshold}')
out.write_text(json.dumps({'metric':'ImageMagick normalized mean absolute error','records':records},indent=2)+'\n')
print(json.dumps({'records':records},indent=2))
