#!/bin/sh
set -eu
pptx=$2
out=$3
expected=$4
mode=$5
mkdir -p "$out"
libreoffice -env:UserInstallation=file:///tmp/lo-profile-$$ --headless --convert-to pdf --outdir "$out" "$pptx" >/tmp/lo-output.txt 2>/tmp/lo-error.txt || { cat /tmp/lo-error.txt >&2; exit 1; }
pdf=$(find "$out" -maxdepth 1 -name '*.pdf' -type f | head -n1)
[ -n "$pdf" ] || { echo 'LibreOffice did not reopen the PPTX' >&2; exit 1; }
pdfinfo "$pdf" > "$out/pdfinfo.txt"
pages=$(sed -n 's/^Pages:[[:space:]]*//p' "$out/pdfinfo.txt")
[ "$pages" = "$expected" ] || { echo "reopened page count $pages != $expected" >&2; exit 1; }
ratio=$(awk '/^Page size:/ { printf "%.6f", $3/$5 }' "$out/pdfinfo.txt")
awk -v r="$ratio" 'BEGIN { exit !(r > 1.77 && r < 1.78) }' || { echo "reopened page size not 16:9: $ratio" >&2; exit 1; }
pdftoppm -png -r 96 "$pdf" "$out/reopened-slide" >/dev/null 2>&1
for image in "$out"/reopened-slide-*.png; do tesseract "$image" "${image%.png}" --psm 6 >/dev/null 2>&1; done
python3 - "$out" "$mode" "${6:-}" <<'PY_OCR'
import json, re, subprocess, sys
from pathlib import Path
out=Path(sys.argv[1]); mode=sys.argv[2]; deck_path=Path(sys.argv[3]) if len(sys.argv)>3 and sys.argv[3] else None; files=sorted(out.glob('reopened-slide-*.txt'))
expected=[['Three slides, one source model'],['Synthetic quarterly growth','12','18','percent','src-synthetic'],['Preserve meaning across modes']]
deck=None
expected=[['Three slides, one source model'],['Synthetic quarterly growth','12','18','percent','src-synthetic'],['Preserve meaning across modes']]
if deck_path:
 deck=json.loads(deck_path.read_text()); expected=[[slide['action_title']] for slide in deck['slides']]
if len(files)!=len(expected): raise SystemExit(f'OCR image count {len(files)} != {len(expected)}')
records=[]
for index,file in enumerate(files):
 text=file.read_text().lower(); normalized=re.sub(r'[^a-z0-9]+',' ',text)
 missing=[token for token in expected[index] if re.sub(r'[^a-z0-9]+',' ',token.lower()).strip() not in normalized]
 records.append({'slide':index+1,'ocr':text,'ocr_missing_expected':missing})
if deck is not None:
 pdfs=sorted(out.glob('*.pdf'))
 if len(pdfs)!=1: raise SystemExit('reopened PDF evidence missing or ambiguous')
 extracted=subprocess.run(['pdftotext','-layout',str(pdfs[0]),'-'],check=True,text=True,capture_output=True).stdout
 normalized_pdf=re.sub(r'\s+',' ',extracted).lower()
 data_fields=('value','unit','as_of','denominator')
 for slide in deck['slides']:
  tokens=[slide['action_title']]
  for datum in slide.get('data_refs',[]):
   tokens.extend(str(datum[key]) for key in data_fields if datum.get(key))
   tokens.extend(str(source_id) for source_id in datum.get('source_ids',[]))
  for token in tokens:
   if re.sub(r'\s+',' ',token).lower() not in normalized_pdf: raise SystemExit(f"reopened PPTX text missing content on {slide['slide_id']}")
(out/'ocr-receipt.json').write_text(json.dumps({'mode':mode,'engine':'Tesseract 5.3.0-2','slides':records,'text_verification':'pdftotext on LibreOffice-reopened PDF'},indent=2)+'\n')
PY_OCR
printf '{"reopened_by":"LibreOffice Impress","pdf":"%s","images":' "$(basename "$pdf")"
find "$out" -maxdepth 1 -name 'reopened-slide-*.png' -type f | wc -l | tr -d ' '
printf ',"ocr":"ocr-receipt.json"}\n'
