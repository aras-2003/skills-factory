import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, symlink, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { AdapterError, MODES, LAYOUTS, validateDeck, renderDeck, renderDiagramSvg, renderBarChartSvg, resolveLayout, validateThemeRegistry, contrastRatio, buildThemeCss, collectAssets, preflight, run, render } from '../src/adapter.js';

const deck = { schema_version:'1.0', slides:[{slide_id:'s1',action_title:'Quarterly view',claims:[],data_refs:[{data_ref_id:'q1',value:12,unit:'percent',source_ids:['synth']}],exhibits:[{exhibit_id:'e1',visual_type:'bar_chart',supported_data:['q1'],alternative_text:'Synthetic quarterly chart'}],layout:{layout_id:'data',tokens:{}},notes:'Never close --> comment',provenance:{},desired_editability:'PREFERRED'}] };

test('requires four explicit, non-interchangeable output modes', () => {
  assert.deepEqual([...MODES].sort(), ['html','pdf','pptx_editable_experimental','pptx_flattened'].sort());
});

test('DeckSpec input has unique slide identifiers and supported exhibits', () => {
  validateDeck(deck);
  assert.throws(() => validateDeck({...deck,slides:[deck.slides[0],deck.slides[0]]}), e => e.code === 'INVALID_DECK');
  assert.throws(() => validateDeck({...deck,slides:[{...deck.slides[0],exhibits:[{exhibit_id:'bad',visual_type:'custom_html',supported_data:[]}]}]}), e => e.code === 'UNSUPPORTED_EXHIBIT');
});

test('architecture diagrams validate bounded graph structure and render deterministic passive SVG', () => {
  const model={title:'Synthetic flow',nodes:[{id:'source',label:'Source'},{id:'model',label:'Canonical model'},{id:'output',label:'Output'}],edges:[{from:'source',to:'model',label:'validated'},{from:'model',to:'output'}]};
  const tokens={canvas:'#ffffff',ink:'#17243a',muted:'#52627a',accent:'#176b87',rule:'#94a3b8'};
  assert.equal(renderDiagramSvg(model,tokens),renderDiagramSvg(structuredClone(model),tokens));
  assert.match(renderDiagramSvg(model,tokens),/<svg[^>]+viewBox="0 0 1000 360"/);
  assert.match(renderDiagramSvg(model,tokens),/Canonical model/);
  assert.throws(()=>renderDiagramSvg({...model,edges:[{from:'missing',to:'model'}]},tokens),e=>e.code==='INVALID_DIAGRAM');
  assert.throws(()=>renderDiagramSvg({...model,nodes:[...model.nodes,...Array.from({length:10},(_,i)=>({id:`n${i}`,label:'node'}))]},tokens),e=>e.code==='INVALID_DIAGRAM');
  const hostile={...model,nodes:[{id:'n',label:'<script>alert(1)</script>'}],edges:[]};
  assert.doesNotMatch(renderDiagramSvg(hostile,tokens),/<script>/i);
  assert.match(renderDiagramSvg(hostile,tokens),/&lt;script&gt;/);
});

test('generated data charts reject invalid values and escape labels while retaining exact values', () => {
  const tokens={canvas:'#ffffff',ink:'#17243a',muted:'#52627a',accent:'#176b87',rule:'#94a3b8'};
  const points=[{label:'Q1',value:12,unit:'percent'},{label:'Q2',value:18,unit:'percent'}];
  assert.equal(renderBarChartSvg(points,tokens),renderBarChartSvg(structuredClone(points),tokens));
  assert.match(renderBarChartSvg(points,tokens),/>18 percent</);
  assert.throws(()=>renderBarChartSvg([{label:'bad',value:Infinity}],tokens),e=>e.code==='INVALID_CHART_DATA');
});

test('table exhibit renders visible rows directly from canonical data refs with provenance', () => {
  const value=structuredClone(deck); value.slides[0].exhibits=[{exhibit_id:'t1',visual_type:'table',supported_data:['q1'],alternative_text:'Synthetic data table'}];
  const markdown=renderDeck(value,'sf-editorial.css');
  assert.match(markdown, /\| Data reference \| Value \| Unit \| As of \| Denominator \| Source IDs \|/);
  assert.match(markdown, /\| q1 \| 12 \| percent \|\s*\|\s*\| synth \|/);
});

test('generated markdown escapes active syntax and uses a staged chart asset', () => {
  const hostile = structuredClone(deck); hostile.slides[0].action_title='![click](https://example.invalid) <script>alert(1)</script>';
  const markdown=renderDeck(hostile,'sf-editorial.css',new Map([['s1:e1','./fixed.svg']]));
  assert.ok(markdown.includes('# \\!\\[click\\]\\(https://example\\.invalid\\)'));
  assert.doesNotMatch(markdown, /<script>/i);
  assert.match(markdown,/\.\/fixed\.svg/);
  assert.ok(markdown.endsWith('\n'), 'Markdown ends with a newline so the final slide is complete');
  assert.equal((markdown.match(/^---$/gm) ?? []).length, 2, 'single-slide Markdown has only its frontmatter delimiter');
  assert.doesNotMatch(markdown.match(/<!-- ([\s\S]*?) -->/)?.[1] ?? '', /--/);
});

test('non allowlisted output mode stops before runtime access', async () => {
  await assert.rejects(preflight('pptx'), e => e instanceof AdapterError && e.code === 'INVALID_MODE');
});

test('asset paths reject traversal, remote URLs, and symlinks', async t => {
  const root=await mkdtemp(path.join(tmpdir(),'marp-test-')); const stage=path.join(root,'stage'); await mkdir(stage);
  t.after(async()=>rm(root,{recursive:true,force:true}));
  const asset={asset_id:'x',path:'../escape.png',source_id:'synth',license_rights:'Synthetic fixture rights',as_of:'2026-11-10',alternative_text:'Synthetic asset',owner:'Skills Factory',confidentiality:'PUBLIC'};
  const hostile={...deck,sources:[{source_id:'synth'}],extensions:{presentation_marp:{assets:[asset]}}};
  await assert.rejects(collectAssets(hostile,root,stage),e=>e.code==='BLOCKED_ASSET_PATH');
  await writeFile(path.join(root,'same.svg'),'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="#fff"/></svg>');
  const duplicate={...hostile,extensions:{presentation_marp:{assets:[{...asset,path:'same.svg'},{...asset,path:'same.svg'}]}}};
  await assert.rejects(collectAssets(duplicate,root,stage),e=>e.code==='INVALID_ASSET_MANIFEST');
  hostile.extensions.presentation_marp.assets[0].path='https://example.invalid/x.png';
  await assert.rejects(collectAssets(hostile,root,stage),e=>e.code==='BLOCKED_ASSET_PATH');
  await writeFile(path.join(root,'real.png'),Buffer.from([1,2,3])); await symlink('real.png',path.join(root,'alias.png'));
  hostile.extensions.presentation_marp.assets[0].path='alias.png';
  await assert.rejects(collectAssets(hostile,root,stage),e=>e.code==='BLOCKED_ASSET_PATH');
  const outside=await mkdtemp(path.join(tmpdir(),'marp-outside-')); t.after(async()=>rm(outside,{recursive:true,force:true})); await writeFile(path.join(outside,'escape.png'),Buffer.from([4,5,6])); await symlink(outside,path.join(root,'linked-dir'));
  hostile.extensions.presentation_marp.assets[0].path='linked-dir/escape.png';
  await assert.rejects(collectAssets(hostile,root,stage),e=>e.code==='BLOCKED_ASSET_PATH');
});

test('restricted SVG allowlist blocks scripts and external references', async t => {
  const root=await mkdtemp(path.join(tmpdir(),'marp-test-')); const stage=path.join(root,'stage'); await mkdir(stage); t.after(async()=>rm(root,{recursive:true,force:true}));
  const svg='<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="#fff"/></svg>';
  const asset={asset_id:'safe',path:'safe.svg',source_id:'synth',license_rights:'Synthetic fixture rights',as_of:'2026-11-10',alternative_text:'Synthetic safe vector',owner:'Skills Factory',confidentiality:'PUBLIC'};
  await writeFile(path.join(root,'safe.svg'),svg); const value={...deck,sources:[{source_id:'synth'}],extensions:{presentation_marp:{assets:[asset]}}};
  const safe=await collectAssets(value,root,stage); assert.equal(safe.length,1); assert.equal(safe[0].license_rights,'Synthetic fixture rights');
  await writeFile(path.join(root,'bad.svg'),'<svg><image href="https://example.invalid/x"/></svg>'); value.extensions.presentation_marp.assets[0].path='bad.svg';
  await assert.rejects(collectAssets(value,root,stage),e=>e.code==='BLOCKED_UNSAFE_SVG');
});

test('asset manifests require provenance, rights, ownership, confidentiality and a declared editable raster fallback', async t => {
  const root=await mkdtemp(path.join(tmpdir(),'marp-asset-fallback-')); const stage=path.join(root,'stage'); await mkdir(stage); t.after(async()=>rm(root,{recursive:true,force:true}));
  const svg='<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="#fff"/></svg>';
  await writeFile(path.join(root,'safe.svg'),svg); await writeFile(path.join(root,'fallback.png'),Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/pZ8AAAAASUVORK5CYII=','base64'));
  const asset={asset_id:'safe',path:'safe.svg',source_id:'synth',license_rights:'CC0-1.0 synthetic fixture',as_of:'2026-11-10',alternative_text:'Synthetic vector card',owner:'Skills Factory',confidentiality:'PUBLIC',raster_fallback_path:'fallback.png'};
  const value={...deck,sources:[{source_id:'synth'}],extensions:{presentation_marp:{assets:[asset]}}};
  const editable=await collectAssets(value,root,stage,'pptx_editable_experimental'); assert.equal(editable[0].fallback_used,true); assert.match(editable[0].file,/\.png$/); assert.match(editable[0].source_file,/\.svg$/);
  const missing={...value,extensions:{presentation_marp:{assets:[{...asset,license_rights:'unknown'}]}}};
  await assert.rejects(collectAssets(missing,root,stage),e=>e.code==='INVALID_ASSET_MANIFEST');
  const noOwner={...value,extensions:{presentation_marp:{assets:[Object.fromEntries(Object.entries(asset).filter(([key])=>key!=='owner'))]}}};
  await assert.rejects(collectAssets(noOwner,root,stage),e=>e.code==='INVALID_ASSET_MANIFEST');
  const noFallback={...value,extensions:{presentation_marp:{assets:[Object.fromEntries(Object.entries(asset).filter(([key])=>key!=='raster_fallback_path'))]}}};
  await assert.rejects(collectAssets(noFallback,root,stage,'pptx_editable_experimental'),e=>e.code==='BLOCKED_SVG_FALLBACK');
  const remoteFallback={...value,extensions:{presentation_marp:{assets:[{...asset,raster_fallback_path:'https://example.invalid/fallback.png'}]}}};
  await assert.rejects(collectAssets(remoteFallback,root,stage,'pptx_editable_experimental'),e=>e.code==='BLOCKED_ASSET_PATH');
  const unsafe={...value,extensions:{presentation_marp:{assets:[{...asset,path:'unsafe.svg'}]}}};
  await writeFile(path.join(root,'unsafe.svg'),'<svg><script>alert(1)</script></svg>');
  await assert.rejects(collectAssets(unsafe,root,stage,'pptx_editable_experimental'),e=>e.code==='BLOCKED_UNSAFE_SVG');
});

test('renderer subprocess limits timeout and captured output', async t => {
  const root=await mkdtemp(path.join(tmpdir(),'marp-run-test-')); t.after(async()=>rm(root,{recursive:true,force:true}));
  await assert.rejects(run(process.execPath,['-e','setTimeout(()=>{},500)'],{timeout:30}),e=>e.code==='BLOCKED_TIMEOUT');
  await assert.rejects(run(process.execPath,['-e','process.stdout.write(\"x\".repeat(1000))'],{maxBytes:16}),e=>e.code==='BLOCKED_OUTPUT_LIMIT');
});

test('oversized DeckSpec is rejected before runtime discovery', async t => {
  const root=await mkdtemp(path.join(tmpdir(),'marp-input-test-')); t.after(async()=>rm(root,{recursive:true,force:true}));
  const input=path.join(root,'too-large.json'); await writeFile(input,JSON.stringify({schema_version:'1.0',slides:[],padding:'x'.repeat(5*1024*1024)}));
  await assert.rejects(render({input,outputDir:path.join(root,'out'),mode:'html'}),e=>e.code==='BLOCKED_INPUT_LIMIT');
});

test('adapter errors expose a stable actionable code', () => {
  const error = new AdapterError('BLOCKED_MISSING_RUNTIME', 'No LibreOffice; no flattened fallback.');
  assert.equal(error.code, 'BLOCKED_MISSING_RUNTIME');
  assert.match(error.message, /fallback/i);
});

test('versioned theme registry defines four accessible styles and six semantic layouts', () => {
  assert.equal(validateThemeRegistry(), true);
  assert.ok(LAYOUTS.size >= 6);
  assert.equal(resolveLayout('data'), 'insight-chart');
  assert.equal(resolveLayout('conclusion'), 'summary');
  assert.throws(() => resolveLayout('arbitrary-css'), e => e.code === 'UNSUPPORTED_LAYOUT');
  assert.ok(contrastRatio('#17243a', '#f6f4ee') >= 4.5);
  const invalid = { schema_version: 1, themes: [{ id: 'sf-low-contrast', version: '1.0.0', css_complexity: 'safe', editable_safe: true, tokens: { canvas:'#ffffff', ink:'#eeeeee', muted:'#eeeeee', accent:'#eeeeee', rule:'#777777', font_display:'sans-serif', font_body:'sans-serif', font_label:'serif' } }] };
  assert.throws(() => validateThemeRegistry(invalid), e => e.code === 'INVALID_THEME_REGISTRY' || e.code === 'THEME_CONTRAST_FAILED');
});

test('theme and layout class are explicit in generated Markdown', () => {
  const markdown = renderDeck(deck, 'sf-education.css', new Map([['s1:e1','./fixed.svg']]));
  assert.match(markdown, /theme: sf-education/);
  assert.match(markdown, /_class: sf-theme-sf-education sf-layout-insight-chart/);
});

test('editable-safe CSS avoids advanced grid and media features while progressive theme opts in', () => {
  const tokens = { canvas:'#f6f4ee', ink:'#17243a', muted:'#52627a', accent:'#176b87', rule:'#94a3b8', font_display:'Liberation Sans, sans-serif', font_body:'Liberation Sans, sans-serif', font_label:'Liberation Serif, serif', grid_width:'1108px', space_unit:'8px' };
  const safe = buildThemeCss({ id:'sf-marp-editable-safe', tokens, css_complexity:'minimal' });
  assert.doesNotMatch(safe, /grid-template|@media|linear-gradient/);
  const progressive = buildThemeCss({ id:'sf-technology', tokens, css_complexity:'progressive' });
  assert.match(progressive, /linear-gradient/);
});

test('progressive CSS is blocked for editable export without silently changing theme', async t => {
  const root = await mkdtemp(path.join(tmpdir(),'marp-theme-test-'));
  t.after(async()=>rm(root,{recursive:true,force:true}));
  const input=path.join(root,'deck.json');
  await writeFile(input,JSON.stringify(deck));
  await assert.rejects(render({input,outputDir:path.join(root,'out'),mode:'pptx_editable_experimental',theme:'sf-technology'}),e=>e.code==='BLOCKED_THEME_UNSUPPORTED');
});
