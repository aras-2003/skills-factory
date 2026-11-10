import { createHash, randomUUID } from 'node:crypto';
import { mkdtemp, mkdir, readFile, realpath, rm, stat, writeFile, copyFile, lstat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { chmod } from 'node:fs/promises';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const IMAGE = 'ghcr.io/skills-factory/presentation-marp:1.0.0';
export const MODES = new Set(['html', 'pdf', 'pptx_flattened', 'pptx_editable_experimental']);
const MAX_INPUT = 5 * 1024 * 1024;
const MAX_ASSETS = 50;
const MAX_ASSET_TOTAL = 10 * 1024 * 1024;
const MAX_OUTPUT = 100 * 1024 * 1024;
const TIMEOUT_MS = 120_000;

export class AdapterError extends Error {
  constructor(code, message, details = {}) { super(message); this.name = 'AdapterError'; this.code = code; this.details = details; }
}
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const safeText = (value) => String(value ?? '').replace(/[\r\n]+/g, ' ').trim().replace(/([\\`*_{}\[\]()#+.!|~-])/g, '\\$1').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const safeNote = (value) => String(value ?? '').replace(/--/g, '—').replace(/\r?\n/g, ' ');

export function run(command, args, { timeout = 10_000, maxBytes = 16_384, env = process.env } = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { shell: false, env, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '', stderr = '', total = 0, settled = false;
    const collect = (target, chunk) => {
      total += chunk.length;
      if (total > maxBytes) { child.kill('SIGKILL'); if (!settled) { settled = true; reject(new AdapterError('BLOCKED_OUTPUT_LIMIT', 'Runtime output exceeded the configured limit.')); } return; }
      if (target === 'out') stdout += chunk.toString('utf8'); else stderr += chunk.toString('utf8');
    };
    child.stdout.on('data', c => collect('out', c)); child.stderr.on('data', c => collect('err', c));
    const timer = setTimeout(() => { child.kill('SIGKILL'); if (!settled) { settled = true; reject(new AdapterError('BLOCKED_TIMEOUT', 'Renderer exceeded the 120 second time limit.')); } }, timeout);
    child.on('error', err => { clearTimeout(timer); if (!settled) { settled = true; reject(new AdapterError('BLOCKED_MISSING_RUNTIME', `Could not start ${path.basename(command)}.`, { cause: err.code })); } });
    child.on('close', code => { clearTimeout(timer); if (settled) return; settled = true; if (code !== 0) { const pdfStageMatch = stderr.match(/SF_PDF_STAGE:(html_generation|asset_copy|slide_count|pptx_generation|libreoffice_conversion|weasyprint_conversion)/); const editableStageMatch = stderr.match(/SF_EDITABLE_STAGE:(html_generation|pdf_generation|libreoffice_import|output_check|marp_cli)/); const pdfMatch = stderr.match(/SF_PDF_RENDER_FAILED:(launch|navigation|slide_count|fonts|print|chrome_print|output_check):([0-9-]+):([0-9-]+)(?::([^:]+):([^:]+):([^\\r\\n]*))?/); const pdfStage = pdfStageMatch?.[1] ?? pdfMatch?.[1]; const runtimeFailure = pdfStage ? `PDF_${pdfStage.toUpperCase()}` : editableStageMatch ? `PPTX_EDITABLE_${editableStageMatch[1].toUpperCase()}` : /No usable sandbox|Failed to move to new namespace/i.test(stderr) ? 'BROWSER_SANDBOX' : /Failed to launch the browser process/i.test(stderr) ? 'BROWSER_LAUNCH' : /error while loading shared libraries/i.test(stderr) ? 'BROWSER_DEPENDENCY' : undefined; return reject(new AdapterError('RENDER_FAILED', 'A bounded subprocess failed; raw diagnostics were omitted to avoid echoing source content.', { exitCode: code, ...(runtimeFailure ? { runtimeFailure } : {}), ...(pdfMatch ? { pdfSlideCount: { actual: Number(pdfMatch[2]), expected: Number(pdfMatch[3]) }, ...(pdfMatch[4] ? { rendererError: { name: pdfMatch[4].slice(0, 40), code: pdfMatch[5].slice(0, 40), ...(pdfMatch[6] ? { info: pdfMatch[6].slice(0, 100) } : {}) } } : {}) } : {}) })); } resolve({ stdout, stderr }); });
  });
}

export async function preflight(mode, { docker = 'docker', image = IMAGE } = {}) {
  if (!MODES.has(mode)) throw new AdapterError('INVALID_MODE', `Choose one of: ${[...MODES].join(', ')}.`);
  const imageInfo = await run(docker, ['image', 'inspect', image, '--format', '{{.Id}}'], { maxBytes: 2048 }).catch(() => { throw new AdapterError('BLOCKED_MISSING_RUNTIME', `Docker is unavailable or the pinned renderer image is missing: ${image}. Start Docker and build the adapter image first.`); });
  const probeName = `sf-marp-preflight-${randomUUID()}`;
  const checks = await run(docker, ['run', '--name', probeName, '--rm', '--network', 'none', image, 'sf-preflight', mode], { timeout: 20_000, maxBytes: 4096 }).catch(async error => { if (error.code === 'BLOCKED_TIMEOUT') await run(docker, ['kill', probeName], { timeout: 5_000, maxBytes: 1024 }).catch(() => {}); throw error; });
  let runtime;
  try { runtime = JSON.parse(checks.stdout); } catch { throw new AdapterError('RUNTIME_IDENTITY_INVALID', 'Pinned renderer returned an invalid runtime identity.'); }
  if (runtime.marp !== '4.5.1' || runtime.node !== '26.8.1') throw new AdapterError('RUNTIME_IDENTITY_MISMATCH', `Expected Marp 4.5.1 and Node 26.8.1; received Marp ${String(runtime.marp)} and Node ${String(runtime.node)}.`);
  if (['pptx_flattened', 'pptx_editable_experimental'].includes(mode) && (!runtime.browser || !runtime.browser_sha256)) throw new AdapterError('BLOCKED_MISSING_RUNTIME', `The ${mode} mode requires the pinned Chromium browser runtime.`);
  if (['pptx_flattened', 'pptx_editable_experimental'].includes(mode) && runtime.browser_path !== '/usr/local/bin/chrome') throw new AdapterError('RUNTIME_IDENTITY_MISMATCH', 'Pinned Chromium executable path does not match the locked runtime.');
  if (mode === 'pdf' && !runtime.weasyprint) throw new AdapterError('BLOCKED_MISSING_RUNTIME', 'PDF export requires the pinned WeasyPrint runtime; no fallback was produced.');
  if (mode === 'pdf' && (runtime.weasyprint !== '57.2' || runtime.weasyprint_package !== '57.2-1')) throw new AdapterError('RUNTIME_IDENTITY_MISMATCH', 'PDF export requires the locked WeasyPrint 57.2 runtime.');
  if (mode === 'pptx_editable_experimental' && !runtime.libreoffice) throw new AdapterError('BLOCKED_MISSING_RUNTIME', 'Experimental editable PPTX requires LibreOffice Impress to verify the generated file; no fallback was produced.');
  if (mode === 'pptx_editable_experimental' && (!runtime.libreoffice.startsWith('7.4.7') || runtime.libreoffice_package !== '4:7.4.7-1+deb12u14')) throw new AdapterError('RUNTIME_IDENTITY_MISMATCH', 'Experimental editable PPTX requires the locked LibreOffice 7.4.7 runtime.');
  runtime.adapter_image_id = imageInfo.stdout.trim();
  return runtime;
}

export function validateDeck(deck) {
  if (!deck || deck.schema_version !== '1.0' || !Array.isArray(deck.slides) || deck.slides.length === 0) throw new AdapterError('INVALID_DECK', 'Input must be a canonical DeckSpec v1 with at least one slide.');
  if (deck.slides.length > 50) throw new AdapterError('BLOCKED_DECK_SIZE', 'Deck exceeds the 50 slide limit.');
  const ids = new Set();
  for (const slide of deck.slides) {
    if (!slide || typeof slide.slide_id !== 'string' || ids.has(slide.slide_id) || typeof slide.action_title !== 'string') throw new AdapterError('INVALID_DECK', 'Slide IDs must be unique and every slide needs an action title.');
    ids.add(slide.slide_id);
    for (const ex of slide.exhibits ?? []) if (!['bar_chart', 'table', 'image'].includes(ex.visual_type)) throw new AdapterError('UNSUPPORTED_EXHIBIT', `Unsupported exhibit type: ${safeText(ex.visual_type)}.`);
  }
}

export function renderDeck(deck, themePath, assetMap = new Map()) {
  const lines = ['---', 'marp: true', 'size: 16:9', 'paginate: true', `theme: ${path.basename(themePath, '.css')}`, '---', ''];
  for (const slide of deck.slides) {
    lines.push(`# ${safeText(slide.action_title)}`, '');
    if (slide.body) lines.push(safeText(slide.body), '');
    for (const claim of slide.claims ?? []) if (claim.statement) lines.push(`- ${safeText(claim.statement)}`);
    for (const datum of slide.data_refs ?? []) {
      const provenance = [datum.unit, datum.as_of, datum.denominator, datum.source_ids?.join(', ')].filter(Boolean).map(safeText).join(' · ');
      lines.push(`- **${safeText(datum.data_ref_id)}:** ${safeText(datum.value)}${datum.unit ? ` ${safeText(datum.unit)}` : ''}${provenance ? ` <small>(${provenance})</small>` : ''}`);
    }
    for (const exhibit of slide.exhibits ?? []) {
      if (exhibit.visual_type === 'image' || exhibit.visual_type === 'bar_chart') { const asset = assetMap.get(exhibit.asset_id || `${slide.slide_id}:${exhibit.exhibit_id}`); if (!asset) throw new AdapterError('BLOCKED_ASSET_REFERENCE', `No locally staged asset matches ${safeText(exhibit.asset_id || exhibit.exhibit_id)}.`); lines.push(`![${safeText(exhibit.alternative_text || exhibit.visual_job || exhibit.exhibit_id)}](${asset})`); }
      else if (exhibit.visual_type === 'table') lines.push(`- ${safeText(exhibit.alternative_text || exhibit.visual_job || exhibit.exhibit_id)}: ${safeText(exhibit.supported_data.join(', '))}`);
    }
    if (slide.notes) lines.push('', `<!-- ${safeNote(slide.notes)} -->`);
    if (slide !== deck.slides.at(-1)) lines.push('', '---', '');
  }
  return `${lines.join('\n')}\n`;
}

export async function collectAssets(deck, inputRoot, stage) {
  const manifest = deck.extensions?.presentation_marp?.assets ?? [];
  if (!Array.isArray(manifest)) throw new AdapterError('INVALID_ASSET_MANIFEST', 'Local assets must use an array manifest.');
  if (manifest.length > MAX_ASSETS) throw new AdapterError('BLOCKED_ASSET_SIZE', 'Asset manifest exceeds the 50 asset limit.');
  const records = []; let totalBytes = 0;
  for (const item of manifest) {
    if (!item || typeof item.asset_id !== 'string' || typeof item.path !== 'string') throw new AdapterError('INVALID_ASSET_MANIFEST', 'Asset manifest entries require asset_id and path.');
    if (records.some(record => record.id === item.asset_id)) throw new AdapterError('INVALID_ASSET_MANIFEST', `Duplicate local asset id: ${safeText(item.asset_id)}.`);
    const rel = item.path;
    if (path.isAbsolute(rel) || rel.includes('\\') || rel.split('/').some(p => !p || p === '.' || p === '..') || /^([a-z]+:|\/\/)/i.test(rel)) throw new AdapterError('BLOCKED_ASSET_PATH', 'Only normalized relative local asset paths are allowed.');
    const source = path.join(inputRoot, rel); const meta = await lstat(source);
    if (meta.isSymbolicLink() || !meta.isFile()) throw new AdapterError('BLOCKED_ASSET_PATH', 'Assets must be regular files; symlinks are blocked.');
    const resolvedRoot = await realpath(inputRoot); const resolved = await realpath(source);
    if (!resolved.startsWith(`${resolvedRoot}${path.sep}`)) throw new AdapterError('BLOCKED_ASSET_PATH', 'Asset path escapes the input root.');
    const bytes = await readFile(resolved); totalBytes += bytes.length;
    if (totalBytes > MAX_ASSET_TOTAL) throw new AdapterError('BLOCKED_ASSET_SIZE', 'Local assets exceed the 10 MiB total limit.');
    if (bytes.length > 2 * 1024 * 1024) throw new AdapterError('BLOCKED_ASSET_SIZE', 'Asset exceeds the 2 MiB limit.');
    const ext = path.extname(rel).toLowerCase();
    if (!['.png', '.jpg', '.jpeg', '.webp', '.svg'].includes(ext)) throw new AdapterError('BLOCKED_ASSET_TYPE', 'Only PNG, JPEG, WebP and restricted SVG assets are supported.');
    if (ext === '.svg') { const svg = bytes.toString('utf8'); const tags = [...svg.matchAll(/<\/?([A-Za-z][\w:-]*)/g)].map(m => m[1].toLowerCase()); const attrs = [...svg.matchAll(/\s([A-Za-z_:][\w:.-]*)\s*=/g)].map(m => m[1].toLowerCase()); if (/<!DOCTYPE|<!ENTITY|<script\b|<foreignObject\b|\bon\w+\s*=|(?:href|src)\s*=|url\s*\(|<\?/i.test(svg) || tags.some(t => !['svg','g','rect','circle','ellipse','path','line','polyline','polygon','text','tspan','title','desc'].includes(t)) || attrs.some(a => !['xmlns','viewbox','width','height','x','y','x1','x2','y1','y2','cx','cy','r','rx','ry','d','points','fill','stroke','stroke-width','font-size','font-family','text-anchor','transform','opacity','role','aria-label'].includes(a))) throw new AdapterError('BLOCKED_UNSAFE_SVG', 'SVG uses content outside the passive shape and text allowlist.'); }
    const file = `${sha256(bytes)}${ext}`; await writeFile(path.join(stage, file), bytes, { flag: 'wx' }); records.push({ id: item.asset_id, file, sha256: sha256(bytes) });
  }
  return records;
}

export async function render({ input, outputDir, mode, theme = 'sf-editorial', docker = 'docker', image = process.env.SF_MARP_IMAGE ?? IMAGE }) {
  let raw; try { raw = await readFile(input); } catch (error) { throw new AdapterError('INPUT_UNREADABLE', 'Could not read the selected DeckSpec input.', { cause: error.code }); }
  if (raw.length > MAX_INPUT) throw new AdapterError('BLOCKED_INPUT_LIMIT', 'DeckSpec exceeds the 5 MiB input limit.');
  let deck; try { deck = JSON.parse(raw.toString('utf8')); } catch { throw new AdapterError('INVALID_JSON', 'DeckSpec is not valid JSON.'); }
  validateDeck(deck);
  const repoRoot = path.resolve(HERE, '../../..');
  try { await run(process.env.PYTHON ?? 'python3', [path.join(repoRoot, 'scripts/validate/presentation_model.py'), input], { timeout: 15_000, maxBytes: 16_384 }); }
  catch (error) { if (error.code === 'RENDER_FAILED') throw new AdapterError('INVALID_DECK', 'Canonical DeckSpec schema or semantic validation failed; raw diagnostics were omitted to protect source content.', { exitCode: error.details.exitCode }); throw error; }
  const runtime = await preflight(mode, { docker, image });
  const root = await mkdtemp(path.join(tmpdir(), 'sf-marp-')); const inDir = path.join(root, 'input'); const outDir = path.join(root, 'output');
  try {
    await mkdir(inDir); await mkdir(outDir);
    const themeFile = path.join(HERE, '..', 'themes', `${theme}.css`); const themeInfo = await stat(themeFile).catch(() => null);
    if (theme !== 'sf-editorial' || !themeInfo?.isFile()) throw new AdapterError('UNKNOWN_THEME', 'Only the bundled sf-editorial theme is available.');
    const assets = await collectAssets(deck, path.dirname(path.resolve(input)), inDir);
    for (const slide of deck.slides) for (const ex of slide.exhibits ?? []) if (ex.visual_type === 'bar_chart') {
      const dataMap = new Map((slide.data_refs ?? []).map(ref => [ref.data_ref_id, ref]));
      const chartId = `${slide.slide_id}:${ex.exhibit_id}`; const points = ex.supported_data.map(id => { const ref = dataMap.get(id); if (!ref || typeof ref.value !== 'number' || !Number.isFinite(ref.value)) throw new AdapterError('INVALID_CHART_DATA', `Chart ${safeText(ex.exhibit_id)} requires finite numeric data references.`); return { id, value: ref.value, label: String(id), unit: ref.unit ?? ex.units ?? '' }; });
      if (!points.length) throw new AdapterError('INVALID_CHART_DATA', `Chart ${safeText(ex.exhibit_id)} has no data points.`);
      if (points.length > 8) throw new AdapterError('BLOCKED_CHART_SIZE', 'Bar charts are limited to eight points.'); const max = Math.max(1, ...points.map(p => Math.abs(p.value))); const segment = 780 / points.length, barWidth = Math.min(112, segment * 0.55); const xml = v => String(v).replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&apos;'}[c]));
      const shapes = points.map((p,i) => { const h=Math.max(2,Math.round(Math.abs(p.value)/max*125)), x=60+i*segment+(segment-barWidth)/2, y=p.value>=0?200-h:200, labelY=p.value>=0?Math.max(42,y-14):Math.min(370,y+h+28); return `<g><rect x="${x}" y="${y}" width="${barWidth}" height="${h}" rx="8" fill="#176b87"/><text x="${x+barWidth/2}" y="${labelY}" text-anchor="middle" font-size="22" fill="#17243a">${xml(p.value)} ${xml(p.unit)}</text><text x="${x+barWidth/2}" y="354" text-anchor="middle" font-size="21" fill="#52627a">${xml(p.label)}</text></g>`; }).join('');
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="400" viewBox="0 0 900 400"><rect width="900" height="400" fill="#f6f4ee"/><path d="M60 200H840" stroke="#94a3b8" stroke-width="2"/>${shapes}</svg>`;
      const bytes = Buffer.from(svg); const file = `${sha256(bytes)}.svg`; await writeFile(path.join(inDir,file),bytes,{flag:'wx'}); assets.push({id:chartId,file,sha256:sha256(bytes),generated:'deterministic-data-chart'});
    }
    const assetMap = new Map(assets.map(a => [a.id, `./${a.file}`]));
    const md = renderDeck(deck, themeFile, assetMap); await writeFile(path.join(inDir, 'deck.md'), md);
    await writeFile(path.join(inDir, 'deck.json'), raw);
    await chmod(outDir, 0o777);
    await copyFile(themeFile, path.join(inDir, 'sf-editorial.css'));
    const renderName = `sf-marp-render-${randomUUID()}`;
    const command = ['run', '--name', renderName, '--rm', '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pids-limit', '128', '--memory', '2g', '--shm-size', '256m', '--cpus', '2', '--ulimit', 'fsize=104857600:104857600', '--user', '10001:10001', '--env', 'HOME=/tmp', '--env', 'CHROME_NO_SANDBOX=1', '--tmpfs', '/tmp:rw,noexec,nosuid,size=512m', '-v', `${inDir}:/work/input:ro`, '-v', `${outDir}:/work/output:rw`, image, 'sf-render', mode];
    await run(docker, command, { timeout: TIMEOUT_MS, maxBytes: 16_384 }).catch(async error => { if (error.code === 'BLOCKED_TIMEOUT') await run(docker, ['kill', renderName], { timeout: 5_000, maxBytes: 1024 }).catch(() => {}); throw error; });
    const names = { html: 'deck.html', pdf: 'deck.pdf', pptx_flattened: 'deck.pptx', pptx_editable_experimental: 'deck-editable.pptx' };
    const file = path.join(outDir, names[mode]); const info = await stat(file).catch(() => null);
    if (!info?.isFile() || info.size === 0) throw new AdapterError('RENDER_FAILED', 'Renderer did not produce the requested output.');
    if (info.size > MAX_OUTPUT) throw new AdapterError('BLOCKED_OUTPUT_LIMIT', 'Rendered artifact exceeds the 100 MiB limit.');
    await mkdir(outputDir, { recursive: true }); const dest = path.join(outputDir, names[mode]); await copyFile(file, dest);
    if (mode === 'html') for (const asset of assets) await copyFile(path.join(inDir, asset.file), path.join(outputDir, asset.file));
    const result = { schema_version: 1, requested_mode: mode, output: names[mode], output_sha256: sha256(await readFile(dest)), input_sha256: sha256(raw), image, runtime, assets, slide_count: deck.slides.length, slide_ids: deck.slides.map(slide => slide.slide_id), security: { network: 'disabled', input_read_only: true, timeout_ms: TIMEOUT_MS, max_input_bytes: MAX_INPUT, max_output_bytes: MAX_OUTPUT } };
    await writeFile(path.join(outputDir, 'receipt.json'), `${JSON.stringify(result, null, 2)}\n`);
    return result;
  } finally { await rm(root, { recursive: true, force: true }); }
}

function usage() { return 'Usage: node src/adapter.js render --input deck.json --output-dir out --mode html|pdf|pptx_flattened|pptx_editable_experimental [--theme sf-editorial]'; }
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args[0] === '--help') { console.log(usage()); process.exit(0); }
  const opts = Object.fromEntries(args.slice(1).reduce((a, v, i, all) => v.startsWith('--') ? (a.push([v.slice(2), all[i + 1]]), a) : a, []));
  if (args[0] !== 'render' || !opts.input || !opts['output-dir'] || !opts.mode) { console.error(usage()); process.exit(2); }
  render({ input: opts.input, outputDir: opts['output-dir'], mode: opts.mode, theme: opts.theme ?? 'sf-editorial', docker: opts.docker ?? 'docker' }).then(r => console.log(JSON.stringify(r))).catch(e => { const failure = e instanceof AdapterError ? e : new AdapterError('IO_ERROR', 'Adapter could not complete the operation; raw diagnostics were omitted.', { cause: e.code }); console.error(JSON.stringify({ code: failure.code, message: failure.message, details: failure.details })); process.exit(1); });
}
