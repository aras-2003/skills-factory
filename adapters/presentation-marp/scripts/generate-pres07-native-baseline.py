#!/usr/bin/env python3
"""Generate a deterministic synthetic native-editable PRES-07 baseline."""
import json, zipfile, hashlib, re, sys
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace
src=Path(sys.argv[1]); out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
odp=out/'native-baseline.odp'
D={'office':'urn:oasis:names:tc:opendocument:xmlns:office:1.0','style':'urn:oasis:names:tc:opendocument:xmlns:style:1.0','text':'urn:oasis:names:tc:opendocument:xmlns:text:1.0','draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','presentation':'urn:oasis:names:tc:opendocument:xmlns:presentation:1.0','svg':'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0','fo':'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0','xlink':'http://www.w3.org/1999/xlink'}
for p,u in D.items(): register_namespace(p,u)
root=Element('{%s}document-content'%D['office'],{'{%s}version'%D['office']:'1.3'})
auto=SubElement(root,'{%s}automatic-styles'%D['office'])
frame_style=SubElement(auto,'{%s}style'%D['style'],{'{%s}name'%D['style']:'fr1','{%s}family'%D['style']:'graphic'}); SubElement(frame_style,'{%s}graphic-properties'%D['style'],{'{%s}fill'%D['draw']:'none','{%s}stroke'%D['draw']:'none'})
for name,size,color,weight in [('TitleP','24pt','#17243a','bold'),('BodyP','14pt','#52627a','normal'),('SmallP','10pt','#52627a','normal')]:
 st=SubElement(auto,'{%s}style'%D['style'],{'{%s}name'%D['style']:name,'{%s}family'%D['style']:'paragraph'}); SubElement(st,'{%s}text-properties'%D['style'],{'{%s}font-family'%D['style']:'Liberation Sans','{%s}font-size'%D['fo']:size,'{%s}color'%D['fo']:color,'{%s}font-weight'%D['fo']:weight})
page_layout=SubElement(auto,'{%s}page-layout'%D['style'],{'{%s}name'%D['style']:'PL1'}); SubElement(page_layout,'{%s}page-layout-properties'%D['style'],{'{%s}page-width'%D['fo']:'28.222cm','{%s}page-height'%D['fo']:'15.875cm'})
body=SubElement(root,'{%s}body'%D['office']); pres=SubElement(body,'{%s}presentation'%D['office'])
NS='{%s}'
def frame(page,name,x,y,w,h,text,cls='outline'):
 f=SubElement(page,NS%D['draw']+'frame',{NS%D['draw']+'name':name,NS%D['draw']+'style-name':'fr1',NS%D['presentation']+'class':cls,NS%D['svg']+'x':f'{x}cm',NS%D['svg']+'y':f'{y}cm',NS%D['svg']+'width':f'{w}cm',NS%D['svg']+'height':f'{h}cm'})
 tb=SubElement(f,NS%D['draw']+'text-box')
 for line in str(text).split('\n'):
  p=SubElement(tb,NS%D['text']+'p',{NS%D['text']+'style-name':'TitleP' if cls=='title' else 'BodyP'}); p.text=line
 return f
def rect(page,name,x,y,w,h,fill='#176b87'):
 st='shape'+str(len(list(page)))
 sty=SubElement(auto,NS%D['style']+'style',{NS%D['style']+'name':st,NS%D['style']+'family':'graphic'}); SubElement(sty,NS%D['style']+'graphic-properties',{NS%D['draw']+'fill':'solid',NS%D['draw']+'fill-color':fill,NS%D['draw']+'stroke':'none'})
 SubElement(page,NS%D['draw']+'rect',{NS%D['draw']+'name':name,NS%D['draw']+'style-name':st,NS%D['svg']+'x':f'{x}cm',NS%D['svg']+'y':f'{y}cm',NS%D['svg']+'width':f'{w}cm',NS%D['svg']+'height':f'{h}cm'})

deck=json.loads(src.read_text())
for i,slide in enumerate(deck['slides'],1):
 p=SubElement(pres,NS%D['draw']+'page',{NS%D['draw']+'name':f'Slide {i:02}',NS%D['draw']+'style-name':'dp1',NS%D['draw']+'master-page-name':'Default'})
 frame(p,'Action title',0.9,0.65,26.0,1.6,slide['action_title'],'title')
 frame(p,'Body',1.0,2.25,25.0,1.4,slide.get('body',''))
 exhibits=slide.get('exhibits',[]); chart=next((e for e in exhibits if e.get('visual_type')=='bar_chart'),None); table=next((e for e in exhibits if e.get('visual_type')=='table'),None); diagram=next((e for e in exhibits if e.get('visual_type')=='architecture_diagram'),None)
 claims='\n'.join(c['statement'] for c in slide.get('claims',[]))
 if chart:
  refs=slide.get('data_refs',[]); maxv=max([float(d.get('value',0)) for d in refs] or [1])
  for j,d in enumerate(refs):
   y=4.2+j*1.22; frame(p,f"Chart label {d['data_ref_id']}",1.1,y,8.5,0.8,f"{d['data_ref_id']}   {d.get('value')} {d.get('unit','')}")
   rect(p,f"Chart bar {d['data_ref_id']}",10.0,y+0.08,11.0*float(d.get('value',0))/maxv,0.55)
  periods=sorted({str(d.get('as_of')) for d in refs if d.get('as_of')}); denominators=sorted({str(d.get('denominator')) for d in refs if d.get('denominator')}); source_ids=sorted({sid for d in refs for sid in d.get('source_ids',[])})
  frame(p,'Chart period and denominator',1.1,9.35,25.0,1.1,'Period: '+', '.join(periods)+' | Denominator: '+', '.join(denominators)+' | Source: '+', '.join(source_ids))
  if claims: frame(p,'Claims',1.1,10.6,25.0,1.1,claims)
 elif table:
  rows=['Category | Value | Unit | Period | Denominator | Source']
  for d in slide.get('data_refs',[]): rows.append(f"{d['data_ref_id']} | {d.get('value')} | {d.get('unit','')} | {d.get('as_of','')} | {d.get('denominator','')} | {','.join(d.get('source_ids',[]))}")
  frame(p,'Native data table',1.1,4.1,25.0,4.5,'\n'.join(rows))
  if claims: frame(p,'Claims',1.1,9.2,25.0,1.5,claims)
 elif diagram:
  model=diagram.get('extensions',{}).get('presentation_marp',{}).get('diagram',{}); labels=[node['label'] for node in model.get('nodes',[])]
  for j,label in enumerate(labels):
   x=1.2+j*6.4; rect(p,f'Diagram node {j+1}',x,5.0,4.7,1.25,'#d8e5ed'); frame(p,f'Diagram label {j+1}',x+0.1,5.15,4.5,0.95,label)
  edge_lines=[f"{edge['from']} → {edge['to']}: {edge.get('label','')}" for edge in model.get('edges',[])]
  frame(p,'Diagram relationships',1.1,7.0,25.0,1.4,'\n'.join(edge_lines))
  frame(p,'Diagram alternative text',1.1,8.6,25.0,1.2,diagram.get('alternative_text',''))
 else:
  facts=[c['statement'] for c in slide.get('claims',[])]
  for d in slide.get('data_refs',[]): facts.append(f"{d['data_ref_id']}: {d.get('value','')} {d.get('unit','')} — {d.get('as_of','')} — {d.get('denominator','')} — source {','.join(d.get('source_ids',[]))}")
  for ex in exhibits: facts.append(ex.get('alternative_text',ex.get('visual_job','')))
  if facts: frame(p,'Claims data and provenance',1.1,4.1,25.0,4.8,'\n'.join(facts))
 urls=re.findall(r'https://[A-Za-z0-9./_-]+',slide.get('body',''))
 if urls:
  lf=SubElement(p,NS%D['draw']+'frame',{NS%D['draw']+'name':'Synthetic source hyperlink',NS%D['draw']+'style-name':'fr1',NS%D['svg']+'x':'1cm',NS%D['svg']+'y':'9.3cm',NS%D['svg']+'width':'25cm',NS%D['svg']+'height':'0.8cm'})
  ltb=SubElement(lf,NS%D['draw']+'text-box'); lp=SubElement(ltb,NS%D['text']+'p',{'{%s}style-name'%D['text']:'BodyP'})
  anchor=SubElement(lp,NS%D['text']+'a',{'{%s}type'%D['xlink']:'simple','{%s}href'%D['xlink']:urls[0]})
  anchor.text='Open synthetic source reference'
 if slide.get('notes'):
  frame(p,'Notes and provenance',1.0,12.0,25.0,1.2,slide['notes']+'\nSources: '+', '.join(slide.get('provenance',{}).get('source_ids',[])))
  notes=SubElement(p,NS%D['presentation']+'notes')
  SubElement(notes,NS%D['draw']+'page-thumbnail',{NS%D['draw']+'page-number':str(i),NS%D['draw']+'style-name':'fr1'})
  frame(notes,'Speaker notes',2.0,2.0,24.0,5.0,slide['notes']+'\nSources: '+', '.join(slide.get('provenance',{}).get('source_ids',[])))
styles=Element(NS%D['office']+'document-styles',{NS%D['office']+'version':'1.3'}); autos=SubElement(styles,NS%D['office']+'automatic-styles'); pl=SubElement(autos,NS%D['style']+'page-layout',{NS%D['style']+'name':'PL1'}); SubElement(pl,NS%D['style']+'page-layout-properties',{NS%D['fo']+'page-width':'28.222cm',NS%D['fo']+'page-height':'15.875cm'}); masters=SubElement(styles,NS%D['office']+'master-styles'); SubElement(masters,NS%D['style']+'master-page',{NS%D['style']+'name':'Default',NS%D['style']+'page-layout-name':'PL1'})
with zipfile.ZipFile(odp,'w') as z:
 z.writestr('mimetype','application/vnd.oasis.opendocument.presentation',compress_type=zipfile.ZIP_STORED)
 z.writestr('content.xml',tostring(root,encoding='utf-8',xml_declaration=True))
 z.writestr('styles.xml',tostring(styles,encoding='utf-8',xml_declaration=True))
 z.writestr('META-INF/manifest.xml',b'<?xml version="1.0" encoding="UTF-8"?><manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3"><manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.presentation"/><manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/><manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/></manifest:manifest>')
print(json.dumps({'slides':len(deck['slides']),'output':odp.name,'fixture_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'odp_sha256':hashlib.sha256(odp.read_bytes()).hexdigest()}))
