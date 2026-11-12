import { createHash, randomUUID } from 'node:crypto';
import { mkdtemp, mkdir, readFile, realpath, rm, stat, writeFile, copyFile, lstat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { chmod } from 'node:fs/promises';
import { readFileSync } from 'node:fs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const IMAGE = 'ghcr.io/skills-factory/presentation-marp:1.0.0';
export const MODES = new Set(['html', 'pdf', 'pptx_flattened', 'pptx_editable_experimental']);
const MAX_INPUT = 5 * 1024 * 1024;
const MAX_ASSETS = 50;
const MAX_ASSET_TOTAL = 10 * 1024 * 1024;
const MAX_OUTPUT = 100 * 1024 * 1024;
const TIMEOUT_MS = 120_000;
const MAX_DIAGRAM_NODES = 12;
const MAX_DIAGRAM_EDGES = 20;
const ASSET_CONFIDENTIALITY = new Set(['PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED']);
const THEME_REGISTRY = JSON.parse(readFileSync(path.join(HERE, '../themes/registry.json'), 'utf8'));
const LAYOUT_ALIASES = Object.freeze({ title:'title', 'insight-chart':'insight-chart', data:'insight-chart', comparison:'comparison', process:'process', roadmap:'roadmap', architecture:'architecture', summary:'summary', conclusion:'summary' });
export const LAYOUTS = new Set(['title','insight-chart','comparison','process','roadmap','architecture','summary']);

export class AdapterError extends Error {
  constructor(code, message, details = {}) { super(message); this.name = 'AdapterError'; this.code = code; this.details = details; }
}
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const safeText = (value) => String(value ?? '').replace(/[\u0000-\u001f\u007f]+/g, ' ').trim().replace(/([\\`*_{}\[\]()#+.!|~-])/g, '\\$1').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
function safeMarkdownText(value) {
  const text = String(value ?? '').replace(/[\u0000-\u001f\u007f]+/g, ' ');
  const urlPattern = /https:\/\/[^\s<>"']+/g;
  const escapeChunk = chunk => {
    if (!chunk.trim()) return chunk;
    const leading = chunk.match(/^\s*/)?.[0] ?? '';
    const trailing = chunk.match(/\s*$/)?.[0] ?? '';
    return leading + safeText(chunk.slice(leading.length, chunk.length - trailing.length)) + trailing;
  };
  let output = '', cursor = 0;
  for (const match of text.matchAll(urlPattern)) {
    output += escapeChunk(text.slice(cursor, match.index));
    const candidate = match[0];
    try {
      const parsed = new URL(candidate);
      if (parsed.protocol === 'https:' && !parsed.username && !parsed.password) {
        output += `[${safeText(candidate)}](<${parsed.href}>)`;
      } else output += escapeChunk(candidate);
    } catch {
      output += escapeChunk(candidate);
    }
    cursor = match.index + candidate.length;
  }
  return output + escapeChunk(text.slice(cursor));
}
const safeNote = (value) => String(value ?? '').replace(/--/g, '—').replace(/\r?\n/g, ' ');
const xmlText = value => String(value ?? '').replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '').replace(/[&<>\"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&apos;'}[ch]));
const canonicalJson = value => {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  return JSON.stringify(value);
};

function linearChannel(value) { const c=parseInt(value,16)/255; return c<=0.04045?c/12.92:((c+0.055)/1.055)**2.4; }
function luminance(hex) { const rgb=hex.slice(1).match(/../g).map(linearChannel); return 0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2]; }
export function contrastRatio(foreground, background) { const values=[luminance(foreground),luminance(background)].sort((a,b)=>b-a); return (values[0]+0.05)/(values[1]+0.05); }
export function validateThemeRegistry(registry=THEME_REGISTRY) {
  if (registry?.schema_version!==1 || !Array.isArray(registry.themes) || registry.themes.length<4) throw new AdapterError('INVALID_THEME_REGISTRY','Theme registry must contain at least four versioned themes.');
  const ids=new Set();
  for (const theme of registry.themes) {
    if (!theme || !/^sf-[a-z0-9-]+$/.test(theme.id) || ids.has(theme.id) || !/^\d+\.\d+\.\d+$/.test(theme.version)) throw new AdapterError('INVALID_THEME_REGISTRY','Theme IDs must be unique and theme versions must use semantic versioning.');
    ids.add(theme.id);
    const t=theme.tokens;
    if (!t || ['canvas','ink','muted','accent','rule'].some(key=>!/^#[0-9a-f]{6}$/i.test(t[key]??''))) throw new AdapterError('INVALID_THEME_REGISTRY','Every theme requires valid semantic color tokens.');
    if (contrastRatio(t.ink,t.canvas)<4.5 || contrastRatio(t.muted,t.canvas)<4.5 || contrastRatio(t.accent,t.canvas)<4.5) throw new AdapterError('THEME_CONTRAST_FAILED','Theme text and emphasis colors must meet 4.5:1 contrast.');
    for (const key of ['font_display','font_body','font_label']) if (typeof t[key]!=='string' || /[;{}<>]/.test(t[key])) throw new AdapterError('INVALID_THEME_REGISTRY','Font token contains unsupported CSS syntax.');
    if (!['safe','minimal','progressive'].includes(theme.css_complexity) || typeof theme.editable_safe!=='boolean') throw new AdapterError('INVALID_THEME_REGISTRY','Theme CSS capability metadata is incomplete.');
    if (theme.css_complexity==='progressive' && theme.editable_safe) throw new AdapterError('INVALID_THEME_REGISTRY','Progressive CSS themes cannot claim editable-safe support.');
  }
  return true;
}
validateThemeRegistry();
export function resolveLayout(layoutId) {
  const layout=LAYOUT_ALIASES[layoutId];
  if (!layout || !LAYOUTS.has(layout)) throw new AdapterError('UNSUPPORTED_LAYOUT','Unsupported semantic slide layout: '+safeText(layoutId)+'.');
  return layout;
}
function themeById(id) {
  const theme=THEME_REGISTRY.themes.find(item=>item.id===id);
  if (!theme) throw new AdapterError('UNKNOWN_THEME','Select a theme ID from the bundled registry.');
  return theme;
}
export function buildThemeCss(theme, { mode } = {}) {
  const t=theme.tokens;
  const layoutFile=theme.id==='sf-marp-editable-safe'?'layouts-editable-safe.css':'layouts.css';
  const css=readFileSync(path.join(HERE,'../themes',layoutFile),'utf8');
  const values={canvas:t.canvas,ink:t.ink,muted:t.muted,accent:t.accent,rule:t.rule,'font-display':t.font_display,'font-body':t.font_body,'font-label':t.font_label,'grid-width':t.grid_width,'space-unit':t.space_unit};
  const vars=Object.entries(values).map(([key,value])=>'  --sf-'+key+': '+value+';').join('\n');
  const enhancement=theme.css_complexity==='progressive'
    ? '\nsection.sf-theme-'+theme.id+'.sf-layout-title { background-image: linear-gradient(135deg, var(--sf-canvas) 0%, #172554 100%); }\n'
    : '';
  const editableTitleFit=mode==='pptx_editable_experimental'
    ? '\n/* Keep editable title text inside Marp’s fixed-height PPTX text shape. */\nsection.sf-layout-title h1 { max-width: var(--sf-grid-width); font-size: 52px; }\n'
    : '';
  return '/* @theme '+theme.id+' */\n:root {\n'+vars+'\n}\n'+css+enhancement+editableTitleFit;
}


function safeRendererDiagnostic(output) {
  const normalized = output.replace(/\u001b\[[0-9;]*m/g, '').replace(/\[\s*ERROR\s*\]/g, '[ERROR]').replace(/\[\s*WARN\s*\]/g, '[WARN]');
  const lines = normalized.split(/\r?\n/).filter(line =>
    line.includes('[soffice] Error:') || line.includes('[ERROR] Failed converting Markdown')
  );
  return lines.slice(-3).map(line => line.replace(/\/work\/(?:input|output)\/[^\s]*/g, '[fixture-path]').slice(0, 256)).join(' | ').slice(0, 512);
}

export function run(command, args, { timeout = 10_000, maxBytes = 16_384, env = process.env, diagnostic = false } = {}) {
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
    child.on('close', code => { clearTimeout(timer); if (settled) return; settled = true; if (code !== 0) { const safeDiagnostic = diagnostic ? safeRendererDiagnostic(`${stderr}\n${stdout}`) : ''; const pdfStageMatch = stderr.match(/SF_PDF_STAGE:(html_generation|asset_copy|slide_count|pptx_generation|libreoffice_conversion|weasyprint_conversion)/); const editableStageMatch = stderr.match(/SF_EDITABLE_STAGE:(html_generation|pdf_generation|libreoffice_import|output_check|marp_cli)/); const pdfMatch = stderr.match(/SF_PDF_RENDER_FAILED:(launch|navigation|slide_count|fonts|print|chrome_print|output_check):([0-9-]+):([0-9-]+)(?::([^:]+):([^:]+):([^\\r\\n]*))?/); const pdfStage = pdfStageMatch?.[1] ?? pdfMatch?.[1]; const runtimeFailure = pdfStage ? `PDF_${pdfStage.toUpperCase()}` : editableStageMatch ? `PPTX_EDITABLE_${editableStageMatch[1].toUpperCase()}` : /No usable sandbox|Failed to move to new namespace/i.test(stderr) ? 'BROWSER_SANDBOX' : /Failed to launch the browser process/i.test(stderr) ? 'BROWSER_LAUNCH' : /error while loading shared libraries/i.test(stderr) ? 'BROWSER_DEPENDENCY' : undefined; return reject(new AdapterError('RENDER_FAILED', 'A bounded subprocess failed; raw diagnostics were omitted to avoid echoing source content.', { exitCode: code, ...(runtimeFailure ? { runtimeFailure } : {}), ...(diagnostic ? { rendererChannels: { stdoutBytes: stdout.length, stderrBytes: stderr.length }, ...(safeDiagnostic ? { rendererDiagnostic: safeDiagnostic } : {}) } : {}), ...(/source file could not be loaded/i.test(stderr) ? { rendererFailure: 'LIBREOFFICE_SOURCE_NOT_LOADED' } : /LibreOffice could not convert PPTX internally/i.test(stderr) ? { rendererFailure: 'LIBREOFFICE_PPTX_CONVERSION_FAILED' } : {}), ...(pdfMatch ? { pdfSlideCount: { actual: Number(pdfMatch[2]), expected: Number(pdfMatch[3]) }, ...(pdfMatch[4] ? { rendererError: { name: pdfMatch[4].slice(0, 40), code: pdfMatch[5].slice(0, 40), ...(pdfMatch[6] ? { info: pdfMatch[6].slice(0, 100) } : {}) } } : {}) } : {}) })); } resolve({ stdout, stderr }); });
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
  if (runtime.font_package !== '1:1.07.4-11') throw new AdapterError('RUNTIME_IDENTITY_MISMATCH', 'The pinned Debian fonts-liberation package is required for licensed theme rendering.');
  if (['pdf', 'pptx_flattened', 'pptx_editable_experimental'].includes(mode) && (!runtime.browser || !runtime.browser_sha256)) throw new AdapterError('BLOCKED_MISSING_RUNTIME', `The ${mode} mode requires the pinned Chromium browser runtime.`);
  if (mode === 'pptx_editable_experimental' && !runtime.libreoffice) throw new AdapterError('BLOCKED_MISSING_RUNTIME', 'Experimental editable PPTX requires LibreOffice Impress to verify the generated file; no fallback was produced.');
  if (mode === 'pptx_editable_experimental' && (!runtime.libreoffice.startsWith('7.4.7') || runtime.libreoffice_package !== '4:7.4.7-1+deb12u14')) throw new AdapterError('RUNTIME_IDENTITY_MISMATCH', 'Experimental editable PPTX requires the locked LibreOffice 7.4.7 runtime.');
  if (['pdf', 'pptx_flattened', 'pptx_editable_experimental'].includes(mode) && runtime.browser_path !== '/usr/local/bin/chrome-headless-shell') throw new AdapterError('RUNTIME_IDENTITY_MISMATCH', 'Pinned Chromium headless-shell path does not match the locked runtime.');
  runtime.adapter_image_id = imageInfo.stdout.trim();
  return runtime;
}

export function validateDiagram(diagram) {
  if (!diagram || !Array.isArray(diagram.nodes) || !Array.isArray(diagram.edges) || diagram.nodes.length === 0 || diagram.nodes.length > MAX_DIAGRAM_NODES || diagram.edges.length > MAX_DIAGRAM_EDGES) {
    throw new AdapterError('INVALID_DIAGRAM', `Architecture diagrams require 1-${MAX_DIAGRAM_NODES} nodes and at most ${MAX_DIAGRAM_EDGES} edges.`);
  }
  if (Object.keys(diagram).some(key=>!['title','nodes','edges'].includes(key)) || (diagram.title !== undefined && (typeof diagram.title !== 'string' || diagram.title.length > 120 || /[\u0000-\u001f\u007f]/.test(diagram.title)))) throw new AdapterError('INVALID_DIAGRAM', 'Diagram accepts only a bounded title, nodes and edges.');
  const ids = new Set();
  for (const node of diagram.nodes) {
    if (!node || Object.keys(node).some(key=>!['id','label'].includes(key)) || typeof node.id !== 'string' || !/^[A-Za-z0-9._-]{1,32}$/.test(node.id) || ids.has(node.id) || typeof node.label !== 'string' || !node.label.trim() || node.label.length > 80 || /[\u0000-\u001f\u007f]/.test(node.label)) {
      throw new AdapterError('INVALID_DIAGRAM', 'Diagram nodes require unique safe IDs and labels of 1-80 characters.');
    }
    ids.add(node.id);
  }
  const edgeKeys = new Set();
  for (const edge of diagram.edges) {
    if (!edge || Object.keys(edge).some(key=>!['from','to','label'].includes(key)) || !ids.has(edge.from) || !ids.has(edge.to) || edge.from === edge.to || (edge.label !== undefined && (typeof edge.label !== 'string' || edge.label.length > 60 || /[\u0000-\u001f\u007f]/.test(edge.label)))) {
      throw new AdapterError('INVALID_DIAGRAM', 'Diagram edges must connect distinct declared nodes and have optional labels up to 60 characters.');
    }
    const key = `${edge.from}\u0000${edge.to}`;
    if (edgeKeys.has(key)) throw new AdapterError('INVALID_DIAGRAM', 'Duplicate directed diagram edges are not allowed.');
    edgeKeys.add(key);
  }
  return true;
}

export function renderBarChartSvg(points, tokens, title = 'Data chart') {
  if (!Array.isArray(points) || points.length === 0 || points.length > 8 || points.some(point => !point || typeof point.value !== 'number' || !Number.isFinite(point.value) || typeof point.label !== 'string')) {
    throw new AdapterError('INVALID_CHART_DATA', 'Charts require 1-8 labeled finite numeric values.');
  }
  const max = Math.max(1, ...points.map(point => Math.abs(point.value))); const segment = 780 / points.length; const barWidth = Math.min(112, segment * 0.55);
  const shapes = points.map((point,index) => {
    const baseline=128, h=Math.max(2,Math.round(Math.abs(point.value)/max*78)); const x=60+index*segment+(segment-barWidth)/2; const y=point.value>=0?baseline-h:baseline; const labelY=point.value>=0?Math.max(30,y-12):Math.min(246,y+h+26);
    return `<g><rect x="${x}" y="${y}" width="${barWidth}" height="${h}" rx="8" fill="${tokens.accent}"/><text x="${x+barWidth/2}" y="${labelY}" text-anchor="middle" font-size="22" fill="${tokens.ink}">${xmlText(point.value)} ${xmlText(point.unit ?? '')}</text><text x="${x+barWidth/2}" y="278" text-anchor="middle" font-size="20" fill="${tokens.muted}">${xmlText(point.label)}</text></g>`;
  }).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="310" viewBox="0 0 900 310"><title>${xmlText(title)}</title><rect width="900" height="310" fill="${tokens.canvas}"/><path d="M60 128H840" stroke="${tokens.rule}" stroke-width="2"/>${shapes}</svg>`;
}

export function renderDiagramSvg(diagram, tokens) {
  validateDiagram(diagram);
  const columns = Math.min(3, diagram.nodes.length); const rows = Math.ceil(diagram.nodes.length / columns);
  const width = 1000, height = Math.max(360, rows * 180 + 80), nodeWidth = 240, nodeHeight = 92;
  const positions = new Map();
  diagram.nodes.forEach((node, index) => {
    const row = Math.floor(index / columns), col = index % columns;
    const gapX = columns === 1 ? 0 : (width - columns * nodeWidth) / (columns + 1);
    const x = columns === 1 ? (width - nodeWidth) / 2 : gapX + col * (nodeWidth + gapX);
    const y = 40 + row * 180;
    positions.set(node.id, { x, y, cx: x + nodeWidth / 2, cy: y + nodeHeight / 2 });
  });
  const edges = diagram.edges.map(edge => {
    const from = positions.get(edge.from), to = positions.get(edge.to);
    const dx=to.cx-from.cx, dy=to.cy-from.cy, distance=Math.hypot(dx,dy), ux=dx/distance, uy=dy/distance;
    const fromOffset=Math.min((nodeWidth/2)/Math.max(Math.abs(ux),0.0001),(nodeHeight/2)/Math.max(Math.abs(uy),0.0001));
    const toOffset=Math.min((nodeWidth/2)/Math.max(Math.abs(ux),0.0001),(nodeHeight/2)/Math.max(Math.abs(uy),0.0001));
    const x1=from.cx+ux*fromOffset, y1=from.cy+uy*fromOffset, x2=to.cx-ux*toOffset, y2=to.cy-uy*toOffset;
    const px=-uy, py=ux, bx=x2-ux*12, by=y2-uy*12; const arrow=`${x2},${y2} ${bx+px*6},${by+py*6} ${bx-px*6},${by-py*6}`;
    const mx=(x1+x2)/2;
    // Horizontal edge labels sit above the node boxes. Centering them on the
    // connector made labels overlap the boxes when the gap was narrower than
    // the label text (for example, on three-column diagrams).
    const horizontal = Math.abs(y2 - y1) < 0.001;
    const my = horizontal ? Math.min(y1, y2) - nodeHeight / 2 - 8 : (y1 + y2) / 2 - 8;
    return `<g><line x1="${x1}" y1="${y1}" x2="${bx}" y2="${by}" stroke="${tokens.rule}" stroke-width="3"/><polygon points="${arrow}" fill="${tokens.rule}"/>${edge.label ? `<text x="${mx}" y="${my}" text-anchor="middle" font-size="16" fill="${tokens.muted}">${xmlText(edge.label)}</text>` : ''}</g>`;
  }).join('');
  const nodes = diagram.nodes.map(node => {
    const p = positions.get(node.id);
    return `<g><rect x="${p.x}" y="${p.y}" width="${nodeWidth}" height="${nodeHeight}" rx="12" fill="${tokens.canvas}" stroke="${tokens.accent}" stroke-width="3"/><text x="${p.cx}" y="${p.cy + 7}" text-anchor="middle" font-size="20" fill="${tokens.ink}">${xmlText(node.label)}</text></g>`;
  }).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img"><title>${xmlText(diagram.title ?? 'Architecture diagram')}</title>${edges}${nodes}</svg>`;
}

export function validateDeck(deck) {
  if (!deck || deck.schema_version !== '1.0' || !Array.isArray(deck.slides) || deck.slides.length === 0) throw new AdapterError('INVALID_DECK', 'Input must be a canonical DeckSpec v1 with at least one slide.');
  if (deck.slides.length > 50) throw new AdapterError('BLOCKED_DECK_SIZE', 'Deck exceeds the 50 slide limit.');
  const ids = new Set();
  for (const slide of deck.slides) {
    if (!slide || typeof slide.slide_id !== 'string' || ids.has(slide.slide_id) || typeof slide.action_title !== 'string') throw new AdapterError('INVALID_DECK', 'Slide IDs must be unique and every slide needs an action title.');
    ids.add(slide.slide_id);
    if (!slide.layout || typeof slide.layout.layout_id !== 'string') throw new AdapterError('INVALID_DECK','Every slide requires a semantic layout ID.');
    resolveLayout(slide.layout.layout_id);
    const exhibitIds = new Set(); const dataIds = new Set((slide.data_refs ?? []).map(ref => ref?.data_ref_id).filter(Boolean));
    if (dataIds.size !== (slide.data_refs ?? []).length) throw new AdapterError('INVALID_DECK', `Slide ${safeText(slide.slide_id)} contains duplicate or missing data reference IDs.`);
    for (const ex of slide.exhibits ?? []) {
      if (!ex || typeof ex.exhibit_id !== 'string' || exhibitIds.has(ex.exhibit_id)) throw new AdapterError('INVALID_DECK', 'Exhibit IDs must be present and unique within each slide.');
      exhibitIds.add(ex.exhibit_id);
      if (!['bar_chart', 'table', 'image', 'architecture_diagram'].includes(ex.visual_type)) throw new AdapterError('UNSUPPORTED_EXHIBIT', `Unsupported exhibit type: ${safeText(ex.visual_type)}.`);
      if (!Array.isArray(ex.supported_data) || new Set(ex.supported_data).size !== ex.supported_data.length || ex.supported_data.some(id => !dataIds.has(id))) throw new AdapterError('INVALID_EXHIBIT_DATA', `Exhibit ${safeText(ex.exhibit_id)} must reference unique data IDs declared on its slide.`);
      if (['bar_chart', 'table'].includes(ex.visual_type) && ex.supported_data.length === 0) throw new AdapterError('INVALID_EXHIBIT_DATA', `${safeText(ex.visual_type)} exhibits require at least one data reference.`);
      if (!(ex.alternative_text ?? '').trim()) throw new AdapterError('INVALID_EXHIBIT_ALT', `Exhibit ${safeText(ex.exhibit_id)} requires alternative text.`);
      if (ex.visual_type === 'image' && (typeof ex.asset_id !== 'string' || !ex.asset_id.trim())) throw new AdapterError('INVALID_ASSET_REFERENCE', `Image exhibit ${safeText(ex.exhibit_id)} requires asset_id.`);
      if (ex.visual_type === 'bar_chart') for (const refId of ex.supported_data) { const datum=(slide.data_refs ?? []).find(ref=>ref.data_ref_id===refId); if (!datum || typeof datum.value !== 'number' || !Number.isFinite(datum.value)) throw new AdapterError('INVALID_CHART_DATA', `Chart ${safeText(ex.exhibit_id)} requires finite numeric data references.`); }
      if (ex.visual_type === 'architecture_diagram') validateDiagram(ex.extensions?.presentation_marp?.diagram);
    }
  }
}

export function renderDeck(deck, themePath, assetMap = new Map()) {
  const lines = ['---', 'marp: true', 'size: 16:9', 'paginate: true', `theme: ${path.basename(themePath, '.css')}`, '---', ''];
  const themeId=path.basename(themePath,'.css');
  const selectedTheme=themeById(themeId);
  for (const slide of deck.slides) {
    const layout=resolveLayout(slide.layout.layout_id);
    lines.push('<!-- _class: sf-theme-'+selectedTheme.id+' sf-layout-'+layout+' -->', '', `# ${safeText(slide.action_title)}`, '');
    if (slide.body) lines.push(safeMarkdownText(slide.body), '');
    for (const claim of slide.claims ?? []) if (claim.statement) lines.push(`- ${safeText(claim.statement)}`);
    const tableDataRefs = new Set((slide.exhibits ?? []).filter(exhibit => exhibit.visual_type === 'table').flatMap(exhibit => exhibit.supported_data ?? []));
    const chartDataRefs = new Set((slide.exhibits ?? []).filter(exhibit => exhibit.visual_type === 'bar_chart').flatMap(exhibit => exhibit.supported_data ?? []));
    for (const datum of slide.data_refs ?? []) {
      if (tableDataRefs.has(datum.data_ref_id) || chartDataRefs.has(datum.data_ref_id)) continue;
      const provenance = [datum.unit, datum.as_of, datum.denominator, datum.source_ids?.join(', ')].filter(Boolean).map(safeText).join(' · ');
      lines.push(`- **${safeText(datum.data_ref_id)}:** ${safeText(datum.value)}${datum.unit ? ` ${safeText(datum.unit)}` : ''}${provenance ? ` <small>(${provenance})</small>` : ''}`);
    }
    for (const exhibit of slide.exhibits ?? []) {
      if (['image', 'bar_chart', 'architecture_diagram'].includes(exhibit.visual_type)) {
        const asset = assetMap.get(exhibit.asset_id || `${slide.slide_id}:${exhibit.exhibit_id}`);
        if (!asset) throw new AdapterError('BLOCKED_ASSET_REFERENCE', `No locally staged asset matches ${safeText(exhibit.asset_id || exhibit.exhibit_id)}.`);
        lines.push(`![${safeText(exhibit.alternative_text || exhibit.visual_job || exhibit.exhibit_id)}](${asset})`);
        if (exhibit.visual_type === 'bar_chart') {
          const refs = exhibit.supported_data.map(id => (slide.data_refs ?? []).find(datum => datum.data_ref_id === id)).filter(Boolean);
          const groups = new Map();
          for (const ref of refs) {
            const metadata = [ref.as_of, ref.denominator, ref.source_ids?.join(', ')].filter(Boolean);
            if (!metadata.length) continue;
            const key = metadata.join(' · ');
            groups.set(key, [...(groups.get(key) ?? []), ref.data_ref_id]);
          }
          for (const [metadata, labels] of groups) {
            lines.push(`<small>Source for ${labels.map(safeText).join(', ')}: ${safeText(metadata)}</small>`);
          }
        }
      } else if (exhibit.visual_type === 'table') {
        const data = new Map((slide.data_refs ?? []).map(ref => [ref.data_ref_id, ref]));
        const rows = exhibit.supported_data.map(id => data.get(id));
        lines.push(`**${safeText(exhibit.alternative_text || exhibit.visual_job || exhibit.exhibit_id)}**`, '', '| Data reference | Value | Unit | Provenance |', '| --- | ---: | --- | --- |');
        for (const row of rows) {
          const provenance = [row.as_of, row.denominator, (row.source_ids ?? []).join(', ')].filter(Boolean).map(safeText).join(' · ');
          lines.push(`| ${safeText(row.data_ref_id)} | ${safeText(row.value)} | ${safeText(row.unit ?? '')} | ${provenance} |`);
        }
        lines.push('');
      }
    }
    if (slide.notes) lines.push('', `<!-- ${safeNote(slide.notes)} -->`);
    if (slide !== deck.slides.at(-1)) lines.push('', '---', '');
  }
  return `${lines.join('\n')}\n`;
}

export async function collectAssets(deck, inputRoot, stage, mode = 'html') {
  const manifest = deck.extensions?.presentation_marp?.assets ?? [];
  if (!Array.isArray(manifest)) throw new AdapterError('INVALID_ASSET_MANIFEST', 'Local assets must use an array manifest.');
  if (manifest.length > MAX_ASSETS) throw new AdapterError('BLOCKED_ASSET_SIZE', 'Asset manifest exceeds the 50 asset limit.');
  const records = []; const declaredIds=new Set(); let totalBytes = 0;
  const knownSources = new Set((deck.sources ?? []).map(source => source?.source_id).filter(Boolean));
  const root = await realpath(inputRoot);
  const readLocal = async (rel, description) => {
    if (typeof rel !== 'string' || path.isAbsolute(rel) || rel.includes('\\') || rel.split('/').some(p => !p || p === '.' || p === '..') || /^([a-z]+:|\/\/)/i.test(rel)) throw new AdapterError('BLOCKED_ASSET_PATH', 'Only normalized relative local asset paths are allowed.');
    const candidate = path.join(inputRoot, rel); const meta = await lstat(candidate);
    if (meta.isSymbolicLink() || !meta.isFile()) throw new AdapterError('BLOCKED_ASSET_PATH', 'Assets must be regular files; symlinks are blocked.');
    const resolved = await realpath(candidate);
    if (!resolved.startsWith(`${root}${path.sep}`)) throw new AdapterError('BLOCKED_ASSET_PATH', 'Asset path escapes the input root.');
    const bytes = await readFile(resolved);
    if (bytes.length > 2 * 1024 * 1024) throw new AdapterError('BLOCKED_ASSET_SIZE', `${description} exceeds the 2 MiB limit.`);
    return { bytes, ext: path.extname(rel).toLowerCase() };
  };
  const validateSvg = bytes => {
    const svg = bytes.toString('utf8');
    const tags = [...svg.matchAll(/<\/?([A-Za-z][\w:-]*)/g)].map(m => m[1].toLowerCase());
    const attrs = [...svg.matchAll(/\s([A-Za-z_:][\w:.-]*)\s*=/g)].map(m => m[1].toLowerCase());
    if (!/^\s*<svg\b/i.test(svg) || !/<\/svg\s*>\s*$/i.test(svg) || /<!DOCTYPE|<!ENTITY|<script\b|<foreignObject\b|\bon\w+\s*=|(?:href|src)\s*=|url\s*\(|<\?/i.test(svg) || tags.some(t => !['svg','g','rect','circle','ellipse','path','line','polyline','polygon','text','tspan','title','desc'].includes(t)) || attrs.some(a => !['xmlns','viewbox','width','height','x','y','x1','x2','y1','y2','cx','cy','r','rx','ry','d','points','fill','stroke','stroke-width','font-size','font-family','text-anchor','transform','opacity','role','aria-label'].includes(a))) {
      throw new AdapterError('BLOCKED_UNSAFE_SVG', 'SVG uses content outside the passive shape and text allowlist.');
    }
  };
  const validateRaster = (bytes, ext) => {
    const valid = ext === '.png' ? bytes.length >= 24 && bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])) && bytes.toString('ascii',12,16) === 'IHDR' && bytes.readUInt32BE(16) > 0 && bytes.readUInt32BE(20) > 0
      : ['.jpg','.jpeg'].includes(ext) ? bytes.length >= 3 && bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff
      : ext === '.webp' ? bytes.length >= 12 && bytes.toString('ascii',0,4) === 'RIFF' && bytes.toString('ascii',8,12) === 'WEBP'
      : false;
    if (!valid) throw new AdapterError('INVALID_RASTER_ASSET', `Raster asset bytes do not match the declared ${ext} format.`);
  };
  const stageBytes = async (fileName, bytes) => writeFile(path.join(stage, fileName), bytes, { flag: 'wx' }).catch(error => { if (error.code !== 'EEXIST') throw error; });
  for (const item of manifest) {
    if (!item || typeof item.asset_id !== 'string' || !item.asset_id.trim() || typeof item.path !== 'string') throw new AdapterError('INVALID_ASSET_MANIFEST', 'Asset manifest entries require asset_id and path.');
    if (declaredIds.has(item.asset_id)) throw new AdapterError('INVALID_ASSET_MANIFEST', `Duplicate local asset id: ${safeText(item.asset_id)}.`);
    declaredIds.add(item.asset_id);
    for (const key of ['source_id','license_rights','as_of','alternative_text','owner','confidentiality']) {
      if (typeof item[key] !== 'string' || !item[key].trim() || ['unknown','unspecified','unlicensed','n/a'].includes(item[key].trim().toLowerCase())) throw new AdapterError('INVALID_ASSET_MANIFEST', `Asset ${safeText(item.asset_id)} requires explicit ${key} metadata.`);
    }
    if (!knownSources.has(item.source_id)) throw new AdapterError('INVALID_ASSET_MANIFEST', `Asset ${safeText(item.asset_id)} references a source_id absent from deck.sources.`);
    if (!ASSET_CONFIDENTIALITY.has(item.confidentiality)) throw new AdapterError('INVALID_ASSET_MANIFEST', `Asset ${safeText(item.asset_id)} has an unsupported confidentiality classification.`);
    const source = await readLocal(item.path, 'Asset');
    if (!['.png','.jpg','.jpeg','.webp','.svg'].includes(source.ext)) throw new AdapterError('BLOCKED_ASSET_TYPE', 'Only PNG, JPEG, WebP and restricted SVG assets are supported.');
    if (source.ext === '.svg') validateSvg(source.bytes);
    else validateRaster(source.bytes,source.ext);
    totalBytes += source.bytes.length;
    const sourceFile = `${sha256(source.bytes)}${source.ext}`;
    await stageBytes(sourceFile,source.bytes);
    let selected = { bytes: source.bytes, ext: source.ext, file: sourceFile, fallback_used: false };
    let fallback = null;
    if (item.raster_fallback_path !== undefined) {
      const candidate = await readLocal(item.raster_fallback_path, 'Raster fallback');
      if (!['.png','.jpg','.jpeg','.webp'].includes(candidate.ext)) throw new AdapterError('BLOCKED_ASSET_TYPE', 'Raster fallback must be PNG, JPEG or WebP.');
      validateRaster(candidate.bytes,candidate.ext);
      totalBytes += candidate.bytes.length;
      fallback = { file: `${sha256(candidate.bytes)}${candidate.ext}`, sha256: sha256(candidate.bytes), path: item.raster_fallback_path };
      await stageBytes(fallback.file,candidate.bytes);
    }
    if (source.ext === '.svg' && mode === 'pptx_editable_experimental') {
      if (!fallback) throw new AdapterError('BLOCKED_SVG_FALLBACK', `SVG asset ${safeText(item.asset_id)} requires a declared local raster_fallback_path for experimental editable export.`);
      selected = { bytes: await readFile(path.join(stage, fallback.file)), ext: path.extname(fallback.file), file: fallback.file, fallback_used: true };
    }
    if (totalBytes > MAX_ASSET_TOTAL) throw new AdapterError('BLOCKED_ASSET_SIZE', 'Local assets and declared fallbacks exceed the 10 MiB total limit.');
    records.push({ id: item.asset_id, file: selected.file, sha256: sha256(selected.bytes), source_file: sourceFile, source_sha256: sha256(source.bytes), fallback, fallback_used: selected.fallback_used, source_id: item.source_id, license_rights: item.license_rights, as_of: item.as_of, alternative_text: item.alternative_text, owner: item.owner, confidentiality: item.confidentiality });
  }
  return records;
}

export async function render({ input, outputDir, mode, theme = 'sf-editorial', docker = 'docker', image = process.env.SF_MARP_IMAGE ?? IMAGE }) {
  let raw; try { raw = await readFile(input); } catch (error) { throw new AdapterError('INPUT_UNREADABLE', 'Could not read the selected DeckSpec input.', { cause: error.code }); }
  if (raw.length > MAX_INPUT) throw new AdapterError('BLOCKED_INPUT_LIMIT', 'DeckSpec exceeds the 5 MiB input limit.');
  let deck; try { deck = JSON.parse(raw.toString('utf8')); } catch { throw new AdapterError('INVALID_JSON', 'DeckSpec is not valid JSON.'); }
  validateDeck(deck);
  const themeDefinition=themeById(theme);
  if (mode==='pptx_editable_experimental' && !themeDefinition.editable_safe) throw new AdapterError('BLOCKED_THEME_UNSUPPORTED','Selected theme CSS is not verified for editable PPTX; choose a bundled editable-safe theme explicitly. No theme fallback was applied.');
  const repoRoot = path.resolve(HERE, '../../..');
  try { await run(process.env.PYTHON ?? 'python3', [path.join(repoRoot, 'scripts/validate/presentation_model.py'), input], { timeout: 15_000, maxBytes: 16_384 }); }
  catch (error) { if (error.code === 'RENDER_FAILED') throw new AdapterError('INVALID_DECK', 'Canonical DeckSpec schema or semantic validation failed; raw diagnostics were omitted to protect source content.', { exitCode: error.details.exitCode }); throw error; }
  let runtime;
  const root = await mkdtemp(path.join(tmpdir(), 'sf-marp-')); const inDir = path.join(root, 'input'); const outDir = path.join(root, 'output');
  try {
    await mkdir(inDir); await mkdir(outDir);
    const themeFile = path.join(inDir, `${theme}.css`);
    const assets = await collectAssets(deck, path.dirname(path.resolve(input)), inDir, mode);
    const derivedExhibits = []; const diagramSources = [];
    const sourceIndex = new Map((deck.sources ?? []).map(source=>[source.source_id,source]));
    const confidentialityFor = ids => [...new Set(ids.map(sourceId=>sourceIndex.get(sourceId)?.confidentiality).filter(Boolean))].sort();
    const sourceProvenanceFor = ids => [...new Set(ids)].map(sourceId=>{const source=sourceIndex.get(sourceId)??{};return {source_id:sourceId,license_rights:source.license_rights??null,as_of:source.source_as_of??null,confidentiality:source.confidentiality??null};});
    const generatedOwner='Skills Factory presentation-marp adapter';
    for (const slide of deck.slides) for (const ex of slide.exhibits ?? []) {
      const dataMap = new Map((slide.data_refs ?? []).map(ref => [ref.data_ref_id, ref]));
      const id = `${slide.slide_id}:${ex.exhibit_id}`;
      if (ex.visual_type === 'bar_chart') {
        const points = ex.supported_data.map(refId => { const ref = dataMap.get(refId); if (!ref || typeof ref.value !== 'number' || !Number.isFinite(ref.value)) throw new AdapterError('INVALID_CHART_DATA', `Chart ${safeText(ex.exhibit_id)} requires finite numeric data references.`); return { data_ref_id: refId, value: ref.value, label: String(ref.label ?? refId), unit: ref.unit ?? ex.units ?? '', as_of: ref.as_of ?? ex.as_of ?? null, denominator: ref.denominator ?? null, source_ids: ref.source_ids ?? [] }; });
        if (!points.length) throw new AdapterError('INVALID_CHART_DATA', `Chart ${safeText(ex.exhibit_id)} has no data points.`);
        if (points.length > 8) throw new AdapterError('BLOCKED_CHART_SIZE', 'Bar charts are limited to eight points.');
        const svg = renderBarChartSvg(points,themeDefinition.tokens,ex.visual_job ?? ex.exhibit_id);
        const bytes = Buffer.from(svg); const file = `${sha256(bytes)}.svg`; await writeFile(path.join(inDir,file),bytes,{flag:'wx'});
        const sourceIds=[...new Set(points.flatMap(p=>p.source_ids))];
        const sourceProvenance=sourceProvenanceFor(sourceIds); const asOf=[...new Set(points.map(point=>point.as_of).filter(Boolean))];
        const rights=sourceProvenance.map(source=>({source_id:source.source_id,license_rights:source.license_rights})); const confidentiality=confidentialityFor(sourceIds);
        assets.push({id,file,sha256:sha256(bytes),generated:'deterministic-data-chart',data:points,source_ids:sourceIds,source_provenance:sourceProvenance,license_rights:rights,as_of:asOf,alternative_text:ex.alternative_text,owner:generatedOwner,confidentiality}); derivedExhibits.push({slide_id:slide.slide_id,exhibit_id:ex.exhibit_id,visual_type:ex.visual_type,data:points,source_ids:sourceIds,source_provenance:sourceProvenance,license_rights:rights,as_of:asOf,alternative_text:ex.alternative_text,owner:generatedOwner,confidentiality});
      } else if (ex.visual_type === 'architecture_diagram') {
        const model = ex.extensions.presentation_marp.diagram; const sourceBytes = Buffer.from(`${canonicalJson(model)}\n`); const suffix = sha256(Buffer.from(id)).slice(0,16); const sourceFile = `diagram-${suffix}.source.json`;
        await writeFile(path.join(inDir,sourceFile),sourceBytes,{flag:'wx'});
        const bytes=Buffer.from(renderDiagramSvg(model,themeDefinition.tokens)); const file=`${sha256(bytes)}.svg`; await writeFile(path.join(inDir,file),bytes,{flag:'wx'});
        const sourceIds=ex.provenance?.source_ids ?? []; const sourceProvenance=sourceProvenanceFor(sourceIds); const asOf=[...new Set(sourceProvenance.map(source=>source.as_of).filter(Boolean))];
        const rights=sourceProvenance.map(source=>({source_id:source.source_id,license_rights:source.license_rights})); const confidentiality=confidentialityFor(sourceIds); const sourceRecord={slide_id:slide.slide_id,exhibit_id:ex.exhibit_id,file:sourceFile,sha256:sha256(sourceBytes),source_ids:sourceIds,source_provenance:sourceProvenance,license_rights:rights,as_of:asOf,owner:generatedOwner,confidentiality}; diagramSources.push(sourceRecord);
        assets.push({id,file,sha256:sha256(bytes),generated:'deterministic-architecture-diagram',source_ids:sourceIds,source_provenance:sourceProvenance,license_rights:rights,as_of:asOf,alternative_text:ex.alternative_text,owner:generatedOwner,confidentiality,source_json:sourceFile,source_json_sha256:sha256(sourceBytes)});
        derivedExhibits.push({slide_id:slide.slide_id,exhibit_id:ex.exhibit_id,visual_type:ex.visual_type,source_ids:sourceIds,source_provenance:sourceProvenance,license_rights:rights,as_of:asOf,alternative_text:ex.alternative_text,owner:generatedOwner,confidentiality,diagram_source:sourceFile,diagram_source_sha256:sha256(sourceBytes)});
      } else if (ex.visual_type === 'table') {
        const rows=ex.supported_data.map(refId=>{const ref=dataMap.get(refId);return {data_ref_id:refId,value:ref.value,unit:ref.unit??null,as_of:ref.as_of??null,denominator:ref.denominator??null,source_ids:ref.source_ids??[]};});
        const sourceIds=[...new Set(rows.flatMap(row=>row.source_ids))]; derivedExhibits.push({slide_id:slide.slide_id,exhibit_id:ex.exhibit_id,visual_type:ex.visual_type,data:rows,source_ids:sourceIds,source_provenance:sourceProvenanceFor(sourceIds),license_rights:sourceProvenanceFor(sourceIds).map(source=>({source_id:source.source_id,license_rights:source.license_rights})),as_of:[...new Set(rows.map(row=>row.as_of).filter(Boolean))],alternative_text:ex.alternative_text,owner:generatedOwner,confidentiality:confidentialityFor(sourceIds)});
      }
    }
    const assetMap = new Map(assets.map(a => [a.id, `./${a.file}`]));
    const declaredAssets = new Set(assets.filter(asset => !asset.generated).map(asset => asset.id));
    for (const slide of deck.slides) for (const exhibit of slide.exhibits ?? []) if (exhibit.visual_type === 'image' && !declaredAssets.has(exhibit.asset_id)) throw new AdapterError('BLOCKED_ASSET_REFERENCE', `Image exhibit ${safeText(exhibit.exhibit_id)} references an undeclared local asset.`);
    const md = renderDeck(deck, themeFile, assetMap); await writeFile(path.join(inDir, 'deck.md'), md);
    await writeFile(path.join(inDir, 'deck.json'), raw);
    await chmod(outDir, 0o777);
    await writeFile(themeFile, buildThemeCss(themeDefinition, { mode }));
    runtime = await preflight(mode, { docker, image });
    const renderName = `sf-marp-render-${randomUUID()}`;
    const command = ['run', '--name', renderName, '--rm', '--network', 'none', '--read-only', '--env', `SF_MARP_THEME=${theme}`, '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pids-limit', '128', '--memory', '2g', '--shm-size', '256m', '--cpus', '2', '--ulimit', 'fsize=104857600:104857600', '--user', '10001:10001', '--env', 'HOME=/tmp', '--env', 'CHROME_CONFIG_HOME=/tmp/marp-config', '--env', 'CHROME_NO_SANDBOX=1', '--tmpfs', '/tmp:rw,noexec,nosuid,size=512m', '-v', `${inDir}:/work/input:ro`, '-v', `${outDir}:/work/output:rw`, image, 'sf-render', mode];
    await run(docker, command, { timeout: TIMEOUT_MS, maxBytes: 16_384, diagnostic: mode === 'pptx_editable_experimental' && process.env.CI === 'true' && sha256(raw) === '84d20f2411e8e8f7a2d2949f5429c142a61fc7a6ba6d96dc20c388a21054ec69' }).catch(async error => { if (error.code === 'BLOCKED_TIMEOUT') await run(docker, ['kill', renderName], { timeout: 5_000, maxBytes: 1024 }).catch(() => {}); throw error; });
    const names = { html: 'deck.html', pdf: 'deck.pdf', pptx_flattened: 'deck.pptx', pptx_editable_experimental: 'deck-editable.pptx' };
    const file = path.join(outDir, names[mode]); const info = await stat(file).catch(() => null);
    if (!info?.isFile() || info.size === 0) throw new AdapterError('RENDER_FAILED', 'Renderer did not produce the requested output.');
    if (info.size > MAX_OUTPUT) throw new AdapterError('BLOCKED_OUTPUT_LIMIT', 'Rendered artifact exceeds the 100 MiB limit.');
    await mkdir(outputDir, { recursive: true }); const dest = path.join(outputDir, names[mode]); await copyFile(file, dest);
    const evidenceFiles = new Set();
    for (const asset of assets) for (const fileName of [asset.file, asset.source_file, asset.fallback?.file].filter(Boolean)) evidenceFiles.add(fileName);
    for (const fileName of evidenceFiles) await copyFile(path.join(inDir, fileName), path.join(outputDir, fileName));
    for (const diagram of diagramSources) await copyFile(path.join(inDir, diagram.file), path.join(outputDir, diagram.file));
    const result = { schema_version: 1, requested_mode: mode, theme: { id: themeDefinition.id, version: themeDefinition.version, registry_version: THEME_REGISTRY.theme_registry_version }, layouts: deck.slides.map(slide=>({ slide_id: slide.slide_id, layout_id: resolveLayout(slide.layout.layout_id) })), output: names[mode], output_sha256: sha256(await readFile(dest)), input_sha256: sha256(raw), image, runtime, assets, derived_exhibits: derivedExhibits, diagram_sources: diagramSources, slide_count: deck.slides.length, slide_ids: deck.slides.map(slide => slide.slide_id), security: { network: 'disabled', input_read_only: true, timeout_ms: TIMEOUT_MS, max_input_bytes: MAX_INPUT, max_output_bytes: MAX_OUTPUT, external_asset_fetch: false } };
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
