#!/usr/bin/env python3
"""Inspect PPTX objects and conversion evidence using only Python's standard library."""
import json, os, re, sys, zipfile, unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET

path = Path(sys.argv[1]); mode = sys.argv[2]
ns = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with zipfile.ZipFile(path) as zf:
    names = zf.namelist()
    slides = sorted((n for n in names if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)), key=lambda n:int(re.search(r'\d+', n).group()))
    notes = sorted((n for n in names if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml', n)), key=lambda n:int(re.search(r'\d+', n).group()))
    presentation = ET.fromstring(zf.read('ppt/presentation.xml'))
    size = presentation.find('p:sldSz', ns)
    shapes = []; image_slides = []; slide_texts = []
    for name in slides:
        root = ET.fromstring(zf.read(name))
        shapes.append(len(root.findall('.//p:sp', ns)))
        image_slides.append(len(root.findall('.//p:pic', ns)) + len(root.findall('.//p:bg//a:blip', ns)))
        slide_texts.append(unicodedata.normalize('NFKC', re.sub(r'\s+', ' ', ''.join(root.itertext()))))
    text = '\n'.join(slide_texts)
    expected = json.loads(Path(os.environ.get('SF_PRES07_FIXTURE', '/work/input/deck.json')).read_text())
    expected_titles = [slide['action_title'] for slide in expected['slides']]
    if len(slides) != len(expected['slides']): raise SystemExit('slide count mismatch')
    if size is None or int(size.attrib['cx']) / int(size.attrib['cy']) < 1.77 or int(size.attrib['cx']) / int(size.attrib['cy']) > 1.78: raise SystemExit('slide size is not 16:9')
    if mode == 'pptx_flattened' and not all(count > 0 for count in image_slides): raise SystemExit('flattened PPTX must contain image-backed slide content')
    if mode == 'pptx_editable_experimental' and not all(count > 0 for count in shapes): raise SystemExit('editable PPTX contains no native shapes')
    external_hyperlinks = []
    if mode == 'pptx_native_baseline':
        if not all(count > 0 for count in shapes): raise SystemExit('native baseline PPTX contains no editable native shapes')
        for index, (slide, slide_text) in enumerate(zip(expected['slides'], slide_texts), start=1):
            if slide['action_title'] not in slide_text: raise SystemExit(f'native baseline title missing: {slide["slide_id"]}')
            for claim in slide.get('claims', []):
                if claim['statement'] not in slide_text: raise SystemExit(f'native baseline claim missing: {claim["claim_id"]}')
            for datum in slide.get('data_refs', []):
                for key in ('data_ref_id', 'value', 'unit'):
                    value = str(datum.get(key, '')).strip()
                    if value and value not in slide_text: raise SystemExit(f'native baseline {key} missing: {datum["data_ref_id"]}')
            relationships = f'ppt/slides/_rels/slide{index}.xml.rels'
            if relationships in names:
                rel_root = ET.fromstring(zf.read(relationships))
                external_hyperlinks.extend(rel.attrib.get('Target', '') for rel in rel_root if rel.attrib.get('TargetMode') == 'External')
        urls = [url for slide in expected['slides'] for url in re.findall(r'https://[A-Za-z0-9./_-]+', slide.get('body', ''))]
        if urls and not any(url in external_hyperlinks for url in urls): raise SystemExit('native baseline external hyperlink missing')
    report = {'mode':mode,'slide_count':len(slides),'width_emu':int(size.attrib['cx']),'height_emu':int(size.attrib['cy']),'native_shapes_by_slide':shapes,'image_shapes_and_backgrounds_by_slide':image_slides,'notes_slide_count':len(notes),'notes_text':[],'external_hyperlink_count':len(external_hyperlinks)}
    report['notes_text'] = [''.join(ET.fromstring(zf.read(name)).itertext()) for name in notes]
    if mode in ('pptx_flattened', 'pptx_native_baseline') and len(notes) != len(slides): raise SystemExit('presenter notes missing')
    notes_joined = '\n'.join(report['notes_text'])
    if mode in ('pptx_flattened', 'pptx_native_baseline'):
        for slide in expected['slides']:
            if slide.get('notes') and slide['notes'] not in notes_joined: raise SystemExit(f"presenter note missing: {slide['slide_id']}")
            if mode == 'pptx_native_baseline':
                for source_id in slide.get('provenance', {}).get('source_ids', []):
                    if source_id not in notes_joined: raise SystemExit(f"presenter note provenance missing: {slide['slide_id']}")
    if mode == 'pptx_editable_experimental' and notes: raise SystemExit('experimental editable PPTX unexpectedly contains notes')
    if mode == 'pptx_editable_experimental':
        normalized_text = re.sub(r'\s+', ' ', text)
        for title in expected_titles:
            title_pattern = r'\s*'.join(re.escape(word) for word in title.split())
            if not re.search(title_pattern, normalized_text): raise SystemExit(f'editable slide title missing from OOXML: {title}')
        for slide in expected['slides']:
            for datum in slide.get('data_refs', []):
                if str(datum.get('value')) not in normalized_text or (datum.get('unit') and datum['unit'] not in normalized_text): raise SystemExit(f"editable slide missing data or units: {datum['data_ref_id']}")
    print(json.dumps(report, indent=2))
