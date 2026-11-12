import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, writeFile, chmod } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.resolve(process.argv[2] ?? path.join(root, '.tmp/evidence'));
const image = process.env.SF_MARP_IMAGE ?? 'ghcr.io/skills-factory/presentation-marp:1.0.0';
const safeFailureClasses = new Set(['VISUAL_REFERENCE_MISSING','VISUAL_REOPENED_SLIDE_MISSING','VISUAL_METRIC_UNAVAILABLE','VISUAL_DRIFT_OVER_THRESHOLD','PDF_TEXT_ASSERTION_FAILED','PDF_TITLE_MISSING','PDF_VALUE_MISSING','PDF_UNIT_MISSING','PDF_AS_OF_MISSING','PDF_DENOMINATOR_MISSING','PDF_SOURCE_ID_MISSING','PDF_PROVENANCE_MISSING','PDF_CONTENT_INCOMPLETE','HTML_SLIDE_COUNT_MISMATCH','HTML_CONTENT_MISSING','HTML_SLIDE_CONTAINER_MISSING','HTML_SLIDE_BOUNDS_INVALID','HTML_PRESENTATION_CONTROLS_NOT_FOUND','HTML_MOBILE_LAYOUT_INVALID','HTML_INSPECTION_FAILED','PPTX_REOPEN_DATA_MISSING','PPTX_REOPEN_OCR_CONTENT_MISSING','PPTX_REOPEN_COUNT_MISMATCH','PPTX_REOPEN_GEOMETRY_INVALID','PPTX_REOPEN_CONVERSION_FAILED']);
let activeStage = 'initialization';
process.on('unhandledRejection', error => {
  const classification = safeFailureClasses.has(String(error?.message ?? '')) ? error.message : 'VALIDATION_FAILED';
  console.error(JSON.stringify({ state: 'FAIL', stage: activeStage, classification }));
  process.exit(1);
});
process.on('uncaughtException', error => {
  const classification = safeFailureClasses.has(String(error?.message ?? '')) ? error.message : 'VALIDATION_FAILED';
  console.error(JSON.stringify({ state: 'FAIL', stage: activeStage, classification }));
  process.exit(1);
});
const modes = ['html','pdf','pptx_flattened','pptx_editable_experimental'];
const renderTimings = {};
const fixture = path.resolve(process.env.SF_MARP_FIXTURE ?? path.join(root, 'fixtures/canonical-deck-v1.json'));
const deck = JSON.parse(await readFile(fixture, 'utf8')); const count = deck.slides.length;
await mkdir(out, { recursive: true }); await chmod(out,0o777);
function sha(b) { return createHash('sha256').update(b).digest('hex'); }
function run(command,args) {
  return new Promise((resolve,reject)=>{
    const p=spawn(command,args,{stdio:['ignore','ignore','pipe'],shell:false});
    let stderr='';
    p.stderr.on('data',chunk=>{if(stderr.length<4096)stderr+=chunk.toString('utf8').slice(0,4096-stderr.length);});
    p.on('error',()=>reject(new Error('INTEGRATION_SUBPROCESS_FAILED')));
    p.on('close',code=>{
      if(code===0)return resolve();
      const classification=stderr.includes('HTML_MOBILE_LAYOUT_INVALID')?'HTML_MOBILE_LAYOUT_INVALID'
        :stderr.includes('HTML_SLIDE_BOUNDS_INVALID')?'HTML_SLIDE_BOUNDS_INVALID'
        :stderr.includes('HTML_SLIDE_CONTAINER_MISSING')?'HTML_SLIDE_CONTAINER_MISSING'
        :stderr.includes('HTML_PRESENTATION_CONTROLS_NOT_FOUND')?'HTML_PRESENTATION_CONTROLS_NOT_FOUND'
        :stderr.includes('Rendered HTML is missing expected content')?'HTML_CONTENT_MISSING'
        :stderr.includes('Expected ')&&stderr.includes(' rendered slides, got ')?'HTML_SLIDE_COUNT_MISMATCH'
        :stderr.includes('OCR content check failed')?'PPTX_REOPEN_OCR_CONTENT_MISSING'
        :stderr.includes('reopened PPTX text missing data evidence')?'PPTX_REOPEN_DATA_MISSING'
        :stderr.includes('reopened page count')?'PPTX_REOPEN_COUNT_MISMATCH'
        :stderr.includes('reopened page size not 16:9')?'PPTX_REOPEN_GEOMETRY_INVALID'
        :stderr.includes('LibreOffice did not reopen the PPTX')?'PPTX_REOPEN_CONVERSION_FAILED'
        :stderr.includes('HTML_')?'HTML_INSPECTION_FAILED':'INTEGRATION_SUBPROCESS_FAILED';
      reject(new Error(classification));
    });
  });
}
function runCapture(command,args) { return new Promise((resolve,reject)=>{const p=spawn(command,args,{stdio:['ignore','pipe','pipe'],shell:false});let s='',e='';p.stdout.on('data',b=>s+=b);p.stderr.on('data',b=>{if(e.length<4096)e+=b.toString('utf8').slice(0,4096-e.length)});p.on('error',()=>reject(new Error('INTEGRATION_SUBPROCESS_FAILED')));p.on('close',c=>{if(c===0)return resolve(s);const match=e.match(/\b(VISUAL_REFERENCE_MISSING|VISUAL_REOPENED_SLIDE_MISSING|VISUAL_METRIC_UNAVAILABLE|VISUAL_DRIFT_OVER_THRESHOLD|PDF_TEXT_ASSERTION_FAILED|PDF_TITLE_MISSING|PDF_VALUE_MISSING|PDF_UNIT_MISSING|PDF_AS_OF_MISSING|PDF_DENOMINATOR_MISSING|PDF_SOURCE_ID_MISSING|PDF_PROVENANCE_MISSING|PDF_CONTENT_INCOMPLETE)\b/);reject(new Error(match?.[1]??'INTEGRATION_SUBPROCESS_FAILED'));});});}
for (const mode of modes) {
  activeStage = `${mode}_render`; console.log(`Rendering ${mode}`);
  const started = performance.now();
  await run('node',[path.join(root,'src/adapter.js'),'render','--input',fixture,'--output-dir',path.join(out,mode),'--mode',mode]);
  renderTimings[mode] = { build_1_elapsed_ms: Math.round(performance.now() - started) };
}
for (const mode of modes) {
  if (mode !== 'html' && path.basename(fixture) !== 'pres07-cross-format-v1.json') continue;
  const repeatDir = mode === 'html' ? path.join(out,'html-repeat') : path.join(out,`${mode}-repeat`);
  activeStage = `${mode}_repeat_render`;
  const started = performance.now();
  await run('node',[path.join(root,'src/adapter.js'),'render','--input',fixture,'--output-dir',repeatDir,'--mode',mode]);
  renderTimings[mode].build_2_elapsed_ms = Math.round(performance.now() - started);
  const firstReceipt = JSON.parse(await readFile(path.join(out,mode,'receipt.json'),'utf8'));
  const repeatReceipt = JSON.parse(await readFile(path.join(repeatDir,'receipt.json'),'utf8'));
  if (firstReceipt.input_sha256 !== repeatReceipt.input_sha256) throw new Error(`Repeated ${mode} render used a different input`);
  const firstOutput = await readFile(path.join(out,mode,firstReceipt.output));
  const repeatOutput = await readFile(path.join(repeatDir,repeatReceipt.output));
  renderTimings[mode].build_1_output_sha256 = sha(firstOutput);
  renderTimings[mode].build_2_output_sha256 = sha(repeatOutput);
  renderTimings[mode].output_hashes_match = sha(firstOutput) === sha(repeatOutput);
}
activeStage='html_repeat_inspection';
activeStage='html_repeat_inspection'; await run('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=256m','-v',`${path.join(out,'html-repeat')}:/evidence:ro`,'-v',`${fixture}:/fixture/deck.json:ro`,'-v',`${out}:/output:rw`,image,'sf-inspect-html','/evidence/deck.html','/output/repeat-screenshots',String(count),'/fixture/deck.json']);
const htmlReceipt = JSON.parse(await readFile(path.join(out,'html','receipt.json'),'utf8'));
const runtime = htmlReceipt.runtime;
activeStage='html_inspection'; await run('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=256m','-v',`${path.join(out,'html')}:/evidence:ro`,'-v',`${fixture}:/fixture/deck.json:ro`,'-v',`${out}:/output:rw`,image,'sf-inspect-html','/evidence/deck.html','/output/screenshots',String(count),'/fixture/deck.json']);
activeStage='pptx_flattened_inspection'; const flatInspect=await runCapture('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=256m','-v',`${path.join(out,'pptx_flattened')}:/pptx:ro`,'-v',`${fixture}:/work/input/deck.json:ro`,image,'sf-inspect-pptx','/pptx/deck.pptx','pptx_flattened']); await writeFile(path.join(out,'pptx_flattened-inspection.json'),flatInspect);
activeStage='pptx_editable_inspection'; const editInspect=await runCapture('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=256m','-v',`${path.join(out,'pptx_editable_experimental')}:/pptx:ro`,'-v',`${fixture}:/work/input/deck.json:ro`,image,'sf-inspect-pptx','/pptx/deck-editable.pptx','pptx_editable_experimental']); await writeFile(path.join(out,'pptx_editable_experimental-inspection.json'),editInspect);
activeStage='pdf_text_inspection'; const pdfOriginal=await runCapture('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=256m','-v',`${path.join(out,'pdf')}:/pdf:ro`,'-v',`${out}:/output:rw`,'-v',`${fixture}:/work/input/deck.json:ro`,image,'sf-inspect-pdf','/pdf/deck.pdf',String(count),'/output/pdf-screenshots','text','/work/input/deck.json']); await writeFile(path.join(out,'pdf-inspection.json'),pdfOriginal);
for (const mode of ['pptx_flattened','pptx_editable_experimental']) {
  activeStage = `${mode}_reopen`;
  const name = mode === 'pptx_flattened' ? 'deck.pptx' : 'deck-editable.pptx';
  const reopenDir=path.join(out,'reopened',mode); await mkdir(reopenDir,{recursive:true}); await chmod(reopenDir,0o777); await mkdir(path.join(reopenDir,mode),{recursive:true}); await chmod(path.join(reopenDir,mode),0o777);
  await run('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=512m','-v',`${path.join(out,mode)}:/input:ro`,'-v',`${reopenDir}:/output:rw`,'-v',`${fixture}:/work/input/deck.json:ro`,image,'sf-reopen-pptx',`/input/${name}`,`/output/${mode}`,String(count),mode,'/work/input/deck.json']);
  const pdfCheck=path.join(out,`${mode}-reopen-check`); await mkdir(pdfCheck,{recursive:true}); await chmod(pdfCheck,0o777);
  activeStage = `${mode}_reopened_pdf_inspection`; const inspect=await runCapture('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=512m','-v',`${path.join(reopenDir,mode)}:/reopened:ro`,'-v',`${pdfCheck}:/verify:rw`,image,'sf-inspect-pdf','/reopened/'+name.replace(/\.pptx$/i,'.pdf'),String(count),'/verify/screenshots','visual-only']);
  const pngs=(await readdir(path.join(reopenDir,mode))).filter(n=>n.endsWith('.png')).sort(); if(pngs.length!==count) throw new Error(`LibreOffice reopen count ${pngs.length} != ${count}`);
  activeStage = `${mode}_visual_compare`; const cmp=await runCapture('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=256m','-v',`${path.join(out,'screenshots')}:/reference:ro`,'-v',`${path.join(reopenDir,mode)}:/reopened:ro`,'-v',`${out}:/evidence:rw`,image,'sf-compare-images','/reference',`/reopened`,`/evidence/${mode}-visual-comparison.json`,'0.20']);
  await writeFile(path.join(reopenDir,mode,'reopen-inspection.json'),inspect); await writeFile(path.join(out,`${mode}-visual-comparison.stdout.json`),cmp);
}
const pdfDir=path.join(out,'pdf-reopen'); await mkdir(pdfDir,{recursive:true}); await chmod(pdfDir,0o777);
activeStage='pdf_reopen_inspection'; const pdfCheck=await runCapture('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=512m','-v',`${path.join(out,'pdf')}:/pdf:ro`,'-v',`${pdfDir}:/verify:rw`,'-v',`${fixture}:/work/input/deck.json:ro`,image,'sf-inspect-pdf','/pdf/deck.pdf',String(count),'/verify','text','/work/input/deck.json']);
activeStage='pdf_visual_compare'; const pdfCompare=await runCapture('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=256m','-v',`${path.join(out,'screenshots')}:/reference:ro`,'-v',`${pdfDir}:/reopened:ro`,'-v',`${out}:/evidence:rw`,image,'sf-compare-images','/reference','/reopened',`/evidence/pdf-visual-comparison.json`,'0.20']);
await writeFile(path.join(out,'pdf-reopen-inspection.json'),pdfCheck); await writeFile(path.join(out,'pdf-visual-comparison.stdout.json'),pdfCompare);
const repeatReceipt=JSON.parse(await readFile(path.join(out,'html-repeat','receipt.json'),'utf8'));
const first=JSON.parse(await readFile(path.join(out,'html','receipt.json'),'utf8'));
if (first.input_sha256 !== repeatReceipt.input_sha256) throw new Error('Repeat render used a different input');
if (first.output_sha256 !== repeatReceipt.output_sha256) throw new Error('Repeated HTML render output bytes differ');
if (JSON.stringify(htmlReceipt.slide_ids) !== JSON.stringify(deck.slides.map(s=>s.slide_id))) throw new Error('HTML render slide IDs/order differ from the canonical source');
if (JSON.stringify(repeatReceipt.slide_ids) !== JSON.stringify(deck.slides.map(s=>s.slide_id))) throw new Error('Repeated HTML render slide IDs/order differ from the canonical source');
const firstHtml = await readFile(path.join(out,'html','deck.html'));
const repeatHtml = await readFile(path.join(out,'html-repeat','deck.html'));
if (sha(firstHtml) !== first.output_sha256 || sha(repeatHtml) !== repeatReceipt.output_sha256 || sha(firstHtml) !== sha(repeatHtml)) throw new Error('Repeated HTML render output hash mismatch');
const shotDir=path.join(out,'screenshots'); const shotNames=(await readdir(shotDir)).filter(n=>/^html-slide-\d+\.png$/.test(n)).sort();
if (shotNames.length !== count) throw new Error(`Expected ${count} HTML screenshots, found ${shotNames.length}`);
for (const n of shotNames) {
  const a=await readFile(path.join(shotDir,n)); const b=await readFile(path.join(out,'repeat-screenshots',n));
  if(sha(a)!==sha(b)) throw new Error(`Rendered slide is not deterministic: ${n}`);
}
// Record the fallback font resolution without treating the requested missing font as a failure.
activeStage='font_fallback_check'; const font=await new Promise((resolve,reject)=>{const p=spawn('docker',['run','--rm','--network','none',image,'sf-font-fallback','SkillsFactoryFontThatDoesNotExist'],{stdio:['ignore','pipe','inherit']});let s='';p.stdout.on('data',b=>s+=b);p.on('error',reject);p.on('close',c=>c===0?resolve(s.trim()):reject(new Error('font fallback check failed')));});
const repeatShotHashes=Object.fromEntries(await Promise.all((await readdir(path.join(out,'repeat-screenshots'))).filter(n=>/^html-slide-\d+\.png$/.test(n)).sort().map(async n=>[n,sha(await readFile(path.join(out,'repeat-screenshots',n)))])));
const evidence={schema_version:1,candidate_source_sha:process.env.SOURCE_REVISION??'local-unpinned',executed_at_utc:new Date().toISOString(),runner_os:process.env.RUNNER_OS??process.platform,slide_ids:htmlReceipt.slide_ids,commands:['node --test','python scripts/validate/presentation_model.py adapters/presentation-marp/fixtures/canonical-deck-v1.json','node scripts/assert-no-libreoffice.mjs','node scripts/assert-missing-runtime.mjs','node adapters/presentation-marp/scripts/integration.mjs'],fixture_sha256:sha(await readFile(fixture)),image, runtime,slide_count:count,outputs:Object.fromEntries(await Promise.all(modes.map(async m=>{const receipt=JSON.parse(await readFile(path.join(out,m,'receipt.json'),'utf8')); return [m,{file:receipt.output,sha256:receipt.output_sha256}]}))),render_repeatability:renderTimings,html_screenshot_hashes:{build_1:Object.fromEntries(await Promise.all(shotNames.map(async n=>[n,sha(await readFile(path.join(shotDir,n)))]))),build_2:repeatShotHashes},font_fallback:font,visual_comparison:{basis:'Each slide screenshot repeated through same pinned Chromium render and compared to LibreOffice-reopened PDF slides.',threshold:'0 pixel difference for same-mode repeat; normalized mean absolute error <= 0.20 cross-format',cross_format_reports:['pdf-visual-comparison.json','pptx_flattened-visual-comparison.json','pptx_editable_experimental-visual-comparison.json']},limitations:['Experimental editable export is a Marp CLI feature with lower fidelity for complex CSS and no presenter notes.','Synthetic fixture only.']};
await writeFile(path.join(out,'integration-receipt.json'),JSON.stringify(evidence,null,2)+'\n');
console.log(`Integration evidence written to ${path.join(out,'integration-receipt.json')}`);
