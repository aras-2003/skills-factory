import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, writeFile, chmod } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.resolve(process.argv[2] || path.join(root, '.tmp/theme-regression'));
const image = process.env.SF_MARP_IMAGE || 'ghcr.io/skills-factory/presentation-marp:1.0.0';
const fixture = path.join(root, 'fixtures/theme-layout-gallery-v1.json');
const registryPath = path.join(root, 'themes/registry.json');
const allowedClassifications = new Set(['THEME_REGISTRY_INVALID','THEME_LAYOUT_COVERAGE_FAILED','THEME_RENDER_FAILED','THEME_SCREENSHOT_MISSING','THEME_SCREENSHOT_NONDETERMINISTIC','THEME_RESPONSIVE_LAYOUT_FAILED','THEME_EDITABLE_SAFE_EXPORT_FAILED','THEME_EDITABLE_SAFE_REOPEN_FAILED','VISUAL_DRIFT_OVER_THRESHOLD','FONT_FALLBACK_UNAVAILABLE']);
let activeStage = 'theme_registry';

function sha(bytes) { return createHash('sha256').update(bytes).digest('hex'); }
function run(command, args, stage, capture=false) {
  return new Promise((resolve,reject) => {
    const child=spawn(command,args,{stdio:['ignore',capture?'pipe':'ignore','pipe'],shell:false});
    let stdout='',stderr='';
    child.stdout?.on('data',chunk=>{if(stdout.length<65536)stdout+=chunk.toString('utf8').slice(0,65536-stdout.length);});
    child.stderr.on('data',chunk=>{if(stderr.length<4096)stderr+=chunk.toString('utf8').slice(0,4096-stderr.length);});
    child.on('error',()=>reject(new Error('THEME_RENDER_FAILED')));
    child.on('close',code=>code===0?resolve(stdout):reject(new Error(stage==='editable_safe_visual_compare' && stderr.includes('VISUAL_DRIFT_OVER_THRESHOLD')?'VISUAL_DRIFT_OVER_THRESHOLD':stage==='html_inspection' && stderr.includes('HTML_MOBILE_LAYOUT_INVALID')?'THEME_RESPONSIVE_LAYOUT_FAILED':'THEME_RENDER_FAILED')));
  });
}
async function render(theme, mode, dest) {
  await mkdir(dest,{recursive:true});
  await run('node',[path.join(root,'src/adapter.js'),'render','--input',fixture,'--output-dir',dest,'--mode',mode,'--theme',theme],'theme_render');
}
async function inspectHtml(renderDir, screenshotDir) {
  await mkdir(screenshotDir,{recursive:true}); await chmod(screenshotDir,0o777);
  await run('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=256m','-v',renderDir+':/evidence:ro','-v',path.dirname(fixture)+':/fixture:ro','-v',output+':/output:rw',image,'sf-inspect-html','/evidence/deck.html','/output/'+path.relative(output,screenshotDir),'7','/fixture/theme-layout-gallery-v1.json'],'html_inspection');
}
async function inspectFontFallbacks(styles) {
  const families=[...new Set(styles.flatMap(theme=>['font_display','font_body','font_label'].map(key=>theme.tokens[key].split(',')[0].trim())))];
  const fallbackProbe='SkillsFactoryFontThatDoesNotExist';
  const requested=[...families,fallbackProbe];
  const resolved={};
  for(const family of requested) {
    activeStage='theme_font_fallback';
    const value=await run('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',image,'sf-font-fallback',family],'font_fallback',true);
    const face=value.trim().split(/\r?\n/)[0];
    if(!face || !face.includes(':')) throw new Error('FONT_FALLBACK_UNAVAILABLE');
    resolved[family]=face;
  }
  if(!resolved[fallbackProbe]) throw new Error('FONT_FALLBACK_UNAVAILABLE');
  return {requested_to_resolved:resolved,fallback_probe:fallbackProbe};
}

async function main() {
  const registry=JSON.parse(await readFile(registryPath,'utf8'));
  const deck=JSON.parse(await readFile(fixture,'utf8'));
  const styles=registry.themes.filter(theme=>theme.id!=='sf-marp-editable-safe');
  const layoutIds=[...new Set(deck.slides.map(slide=>slide.layout.layout_id))].sort();
  if(styles.length<4 || layoutIds.length<6) throw new Error('THEME_LAYOUT_COVERAGE_FAILED');
  await mkdir(output,{recursive:true}); await chmod(output,0o777);
  const fontResolution=await inspectFontFallbacks(styles);
  const records=[];
  for(const theme of styles) {
    activeStage='theme_html_repeatability';
    const first=path.join(output,'html',theme.id,'first');
    const repeat=path.join(output,'html',theme.id,'repeat');
    await render(theme.id,'html',first);
    await render(theme.id,'html',repeat);
    const firstShots=path.join(output,'screenshots',theme.id,'first');
    const repeatShots=path.join(output,'screenshots',theme.id,'repeat');
    activeStage='theme_html_screenshot';
    await inspectHtml(first,firstShots);
    await inspectHtml(repeat,repeatShots);
    const firstReport=JSON.parse(await readFile(path.join(firstShots,'html-reopen.json'),'utf8'));
    const repeatReport=JSON.parse(await readFile(path.join(repeatShots,'html-reopen.json'),'utf8'));
    if(firstReport.slides.length!==deck.slides.length || repeatReport.slides.length!==deck.slides.length) throw new Error('THEME_SCREENSHOT_MISSING');
    if(firstReport.mobile.width>391 || firstReport.mobile.height>845 || Math.abs(firstReport.mobile.ratio-16/9)>0.02) throw new Error('THEME_RESPONSIVE_LAYOUT_FAILED');
    const names=firstReport.slides.map(slide=>slide.screenshot);
    const hashes={};
    for(const name of names) {
      const a=await readFile(path.join(firstShots,name));
      const b=await readFile(path.join(repeatShots,name));
      if(sha(a)!==sha(b)) throw new Error('THEME_SCREENSHOT_NONDETERMINISTIC');
      hashes[name]=sha(a);
    }
    const mobileA=await readFile(path.join(firstShots,'html-responsive-mobile.png'));
    const mobileB=await readFile(path.join(repeatShots,'html-responsive-mobile.png'));
    if(sha(mobileA)!==sha(mobileB)) throw new Error('THEME_SCREENSHOT_NONDETERMINISTIC');
    records.push({id:theme.id,version:theme.version,layout_ids:layoutIds,screenshot_hashes:hashes,mobile_screenshot_sha256:sha(mobileA),mobile_viewport:firstReport.mobile.viewport});
  }

  activeStage='editable_safe_export';
  const safeTheme='sf-marp-editable-safe';
  const safeHtml=path.join(output,'html',safeTheme,'first');
  const safeHtmlRepeat=path.join(output,'html',safeTheme,'repeat');
  await render(safeTheme,'html',safeHtml);
  await render(safeTheme,'html',safeHtmlRepeat);
  const safeHtmlShots=path.join(output,'screenshots',safeTheme,'first');
  const safeHtmlRepeatShots=path.join(output,'screenshots',safeTheme,'repeat');
  activeStage='theme_html_screenshot';
  await inspectHtml(safeHtml,safeHtmlShots);
  await inspectHtml(safeHtmlRepeat,safeHtmlRepeatShots);
  const safeHtmlReport=JSON.parse(await readFile(path.join(safeHtmlShots,'html-reopen.json'),'utf8'));
  for(const slide of safeHtmlReport.slides) {
    const a=await readFile(path.join(safeHtmlShots,slide.screenshot));
    const b=await readFile(path.join(safeHtmlRepeatShots,slide.screenshot));
    if(sha(a)!==sha(b)) throw new Error('THEME_SCREENSHOT_NONDETERMINISTIC');
  }
  const safePptx=path.join(output,'editable-safe');
  await render(safeTheme,'pptx_editable_experimental',safePptx);
  const inspectionDir=path.join(output,'editable-safe-inspection');
  await mkdir(inspectionDir,{recursive:true}); await chmod(inspectionDir,0o777);
  const editableReport=await run('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=256m','-v',safePptx+':/pptx:ro','-v',fixture+':/work/input/deck.json:ro',image,'sf-inspect-pptx','/pptx/deck-editable.pptx','pptx_editable_experimental'],'editable_safe_reopen',true);
  await writeFile(path.join(inspectionDir,'pptx-inspection.json'),editableReport);

  activeStage='editable_safe_reopen';
  const reopened=path.join(output,'editable-safe-reopened');
  await mkdir(reopened,{recursive:true}); await chmod(reopened,0o777);
  const reopenedSlides=path.join(reopened,'pptx_editable_experimental');
  await mkdir(reopenedSlides,{recursive:true}); await chmod(reopenedSlides,0o777);
  await run('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=512m','-v',safePptx+':/input:ro','-v',fixture+':/work/input/deck.json:ro','-v',reopened+':/output:rw',image,'sf-reopen-pptx','/input/deck-editable.pptx','/output/pptx_editable_experimental','7','pptx_editable_experimental','/work/input/deck.json'],'editable_safe_reopen');
  const reopenedPngs=(await readdir(reopenedSlides)).filter(name=>name.endsWith('.png')).sort();
  if(reopenedPngs.length!==deck.slides.length) throw new Error('THEME_EDITABLE_SAFE_REOPEN_FAILED');

  activeStage='editable_safe_visual_compare';
  const refScreens=path.join(output,'screenshots',safeTheme,'first');
  await run('docker',['run','--rm','--network','none','--read-only','--user','10001:10001','--env','HOME=/tmp','--tmpfs','/tmp:rw,noexec,nosuid,size=256m','-v',refScreens+':/reference:ro','-v',reopenedSlides+':/reopened:ro','-v',output+':/evidence:rw',image,'sf-compare-images','/reference','/reopened','/evidence/editable-safe-visual-comparison.json','0.20'],'editable_safe_visual_compare',true);
  const receipt={schema_version:1,theme_registry_version:registry.theme_registry_version,layout_ids:layoutIds,font_resolution:fontResolution,theme_screenshot_regressions:records,editable_safe:{theme:safeTheme,requested_mode:'pptx_editable_experimental',reopened_slide_count:reopenedPngs.length,inspection:JSON.parse(editableReport),visual_comparison_threshold:'0.20'}};
  await writeFile(path.join(output,'theme-regression-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify({stage:'theme_layout_screenshot_regression',classification:'THEME_REGRESSION_PASS'}));
}
main().catch(error=>{
  const raw=String(error?.message||'');
  const classification=allowedClassifications.has(raw)?raw:'THEME_REGRESSION_FAILED';
  console.error(JSON.stringify({stage:activeStage,classification}));
  process.exitCode=1;
});
