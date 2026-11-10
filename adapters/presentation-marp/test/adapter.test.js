import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, symlink, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { AdapterError, MODES, validateDeck, renderDeck, collectAssets, preflight, run, render } from '../src/adapter.js';

const deck = { schema_version:'1.0', slides:[{slide_id:'s1',action_title:'Quarterly view',claims:[],data_refs:[{data_ref_id:'q1',value:12,unit:'percent',source_ids:['synth']}],exhibits:[{exhibit_id:'e1',visual_type:'bar_chart',supported_data:['q1']}],layout:{layout_id:'data',tokens:{}},notes:'Never close --> comment',provenance:{},desired_editability:'PREFERRED'}] };

test('requires four explicit, non-interchangeable output modes', () => {
  assert.deepEqual([...MODES].sort(), ['html','pdf','pptx_editable_experimental','pptx_flattened'].sort());
});

test('DeckSpec input has unique slide identifiers and supported exhibits', () => {
  validateDeck(deck);
  assert.throws(() => validateDeck({...deck,slides:[deck.slides[0],deck.slides[0]]}), e => e.code === 'INVALID_DECK');
  assert.throws(() => validateDeck({...deck,slides:[{...deck.slides[0],exhibits:[{visual_type:'custom_html'}]}]}), e => e.code === 'UNSUPPORTED_EXHIBIT');
});

test('generated markdown escapes active syntax and uses a staged chart asset', () => {
  const hostile = structuredClone(deck); hostile.slides[0].action_title='![click](https://example.invalid) <script>alert(1)</script>';
  const markdown=renderDeck(hostile,'sf-editorial.css',new Map([['s1:e1','./fixed.svg']]));
  assert.ok(markdown.includes('# \\!\\[click\\]\\(https://example\\.invalid\\)'));
  assert.doesNotMatch(markdown, /<script>/i);
  assert.match(markdown,/\.\/fixed\.svg/);
  assert.doesNotMatch(markdown.match(/<!-- ([\s\S]*?) -->/)?.[1] ?? '', /--/);
});

test('non allowlisted output mode stops before runtime access', async () => {
  await assert.rejects(preflight('pptx'), e => e instanceof AdapterError && e.code === 'INVALID_MODE');
});

test('asset paths reject traversal, remote URLs, and symlinks', async t => {
  const root=await mkdtemp(path.join(tmpdir(),'marp-test-')); const stage=path.join(root,'stage'); await mkdir(stage);
  t.after(async()=>rm(root,{recursive:true,force:true}));
  const hostile={...deck,extensions:{presentation_marp:{assets:[{asset_id:'x',path:'../escape.png'}]}}};
  await assert.rejects(collectAssets(hostile,root,stage),e=>e.code==='BLOCKED_ASSET_PATH');
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
  await writeFile(path.join(root,'safe.svg'),svg); const value={...deck,extensions:{presentation_marp:{assets:[{asset_id:'safe',path:'safe.svg'}]}}};
  assert.equal((await collectAssets(value,root,stage)).length,1);
  await writeFile(path.join(root,'bad.svg'),'<svg><image href="https://example.invalid/x"/></svg>'); value.extensions.presentation_marp.assets[0].path='bad.svg';
  await assert.rejects(collectAssets(value,root,stage),e=>e.code==='BLOCKED_UNSAFE_SVG');
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
