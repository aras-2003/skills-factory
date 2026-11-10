#!/usr/bin/env python3
"""Inspect OOXML and conversion evidence using only Python's standard library."""
import json, re, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

path = Path(sys.argv[1]); mode = sys.argv[2]
ns = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with zipfile.ZipFile(path) as zf:
    names = zf.namelist()
    slides = sorted((n for n in names if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)), key=lambda n:int(re.search(r'\d+', n).group()))
    notes = [n for n in names if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml', n)]
    p = ET.fromstring(zf.read('ppt/presentation.xml'))
    size = p.find('p:sldSz', ns)
    shapes = []
    image_slides = []
    for n in slides:
        root = ET.fromstring(zf.read(n)); shapes.append(len(root.findall('.//p:sp', ns))); image_slides.append(len(root.findall('.//p:pic', ns)) + len(root.findall('.//p:bg//a:blip', ns)))
    text = '\n'.join(''.join(ET.fromstring(zf.read(n)).itertext()) for n in slides)
    expected = json.loads(Path('/work/input/deck.json').read_text())
    slide_texts = [s['action_title'] for s in expected['slides']]
    if len(slides) != len(expected['slides']): raise SystemExit('slide count mismatch')
    if mode == 'pptx_editable_experimental':
        for title in slide_texts:
            if title not in text: raise SystemExit('editable slide title missing from OOXML')
    if size is None or int(size.attrib['cx']) / int(size.attrib['cy']) < 1.77 or int(size.attrib['cx']) / int(size.attrib['cy']) > 1.78: raise SystemExit('slide size is not 16:9')
    if mode == 'pptx_flattened' and not all(count > 0 for count in image_slides): raise SystemExit('flattened PPTX must contain image-backed slide content')
    if mode == 'pptx_editable_experimental' and not all(count > 0 for count in shapes): raise SystemExit('editable PPTX contains no native shapes')
    report = {'mode':mode,'slide_count':len(slides),'width_emu':int(size.attrib['cx']),'height_emu':int(size.attrib['cy']),'native_shapes_by_slide':shapes,'image_shapes_and_backgrounds_by_slide':image_slides,'notes_slide_count':len(notes),'notes_text':[]}
    for n in notes:
        report['notes_text'].append(''.join(ET.fromstring(zf.read(n)).itertext()))
    if mode == 'pptx_flattened' and len(notes) != len(slides): raise SystemExit('flattened PPTX presenter notes missing')
    notes_joined = '\n'.join(report_note for report_note in [''.join(ET.fromstring(zf.read(n)).itertext()) for n in notes])
    if mode == 'pptx_flattened':
        for slide in expected['slides']:
            if slide.get('notes') and slide['notes'] not in notes_joined: raise SystemExit(f"presenter note missing: {slide['slide_id']}")
    if mode == 'pptx_editable_experimental' and notes: raise SystemExit('experimental editable PPTX unexpectedly contains notes')
    if mode == 'pptx_editable_experimental':
        for slide in expected['slides']:
            for datum in slide.get('data_refs', []):
                if str(datum.get('value')) not in text or (datum.get('unit') and datum['unit'] not in text): raise SystemExit(f"editable slide missing data or units: {datum['data_ref_id']}")
    print(json.dumps(report, indent=2))
