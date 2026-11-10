#!/usr/bin/env python3
"""Create conservative native/editable PPTX from canonical DeckSpec v1."""
import json, sys
from pathlib import Path
import collections.abc
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

source, target = Path(sys.argv[1]), Path(sys.argv[2])
deck = json.loads(source.read_text())
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333333), Inches(7.5)
blank = prs.slide_layouts[6]
BG = RGBColor(246,244,238); INK = RGBColor(23,36,58); TEAL = RGBColor(23,107,135); MUTED = RGBColor(82,98,122); WHITE = RGBColor(255,255,255)

def textbox(slide, text, x, y, w, h, size, color=INK, bold=False):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame; tf.clear(); tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.text = str(text); p.font.name = 'Liberation Sans'; p.font.size = Pt(size); p.font.bold = bold; p.font.color.rgb = color
    return shape

for index, item in enumerate(deck['slides'], 1):
    slide = prs.slides.add_slide(blank)
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = BG
    textbox(slide, item['action_title'], .7, .45, 11.9, .9, 30, INK, True)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(.7), Inches(1.42), Inches(1.15), Inches(.055))
    bar.fill.solid(); bar.fill.fore_color.rgb = TEAL; bar.line.fill.background()
    body = item.get('body', '')
    claims = [c.get('statement','') for c in item.get('claims',[]) if c.get('statement')]
    left = [body] if body else []
    left += ['• ' + c for c in claims]
    if item.get('data_refs'):
        left += [f"{d['value']} {d.get('unit','')}  ·  {d['data_ref_id']}  ·  {d.get('as_of','')}  ·  {', '.join(d.get('source_ids',[]))}" for d in item['data_refs']]
    if left:
        textbox(slide, '\n\n'.join(left), .85, 1.8, 5.1, 4.55, 18, MUTED)
    for exhibit in item.get('exhibits', []):
        if exhibit.get('visual_type') == 'bar_chart':
            refs = {d['data_ref_id']:d for d in item.get('data_refs',[])}
            points = [refs[k] for k in exhibit.get('supported_data',[]) if k in refs]
            if not points or any(not isinstance(p.get('value'), (int,float)) for p in points):
                raise SystemExit('editable chart requires finite numeric DeckSpec data')
            maximum = max(1, max(abs(p['value']) for p in points)); base_y=5.65
            for pos, datum in enumerate(points):
                x=6.7+pos*2.65; height=max(.05,2.6*abs(datum['value'])/maximum)
                rect=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(base_y-height), Inches(1.3), Inches(height))
                rect.fill.solid(); rect.fill.fore_color.rgb=TEAL; rect.line.fill.background()
                textbox(slide, f"{datum['value']} {datum.get('unit', exhibit.get('units',''))}", x-.35, base_y-height-.42, 2.0, .35, 14, INK, True)
                textbox(slide, datum['data_ref_id'], x-.25, base_y+.1, 1.8, .35, 12, MUTED)
        elif exhibit.get('visual_type') == 'image':
            raise SystemExit('experimental editable mode blocks image exhibits until native image-object mapping is implemented')
        elif exhibit.get('visual_type') == 'table':
            raise SystemExit('experimental editable mode blocks table exhibits until native table mapping is implemented')
        else:
            raise SystemExit('unsupported exhibit in experimental editable mode')
    textbox(slide, f"{index:02d}", 12.0, 6.92, .55, .25, 10, MUTED)
prs.save(str(target))
