import { mkdtemp, mkdir, writeFile, readFile, rm, chmod } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';

const root = await mkdtemp(path.join(tmpdir(), 'sf-puppeteer-print-'));
const input = path.join(root, 'input');
const output = path.resolve(process.argv[2] ?? path.join(root, 'output'));
await mkdir(input);
await mkdir(output, { recursive: true });
await chmod(output, 0o777);
await writeFile(path.join(input, 'probe.html'), '<!doctype html><meta charset="utf-8"><title>Synthetic PDF probe</title><style>@page{size:1280px 720px;margin:0}html,body{margin:0;width:1280px;height:720px}body{font:28px sans-serif;background:#f6f4ee;color:#17243a}main{padding:72px 86px}</style><main><h1>Puppeteer print probe</h1><p>synthetic only</p></main>');
const probe = String.raw`const { createRequire } = require('node:module');
const fs = require('node:fs');
const requireMarp = createRequire('/home/marp/.cli/package.json');
const puppeteer = requireMarp('puppeteer-core');
const classify = message => {
  if (message.includes('Protocol error (Page.printToPDF')) return 'PRINT_TO_PDF_PROTOCOL_ERROR';
  if (message.includes('Page.printToPDF')) return 'PRINT_TO_PDF_OPERATION';
  if (message.includes('Page.navigate')) return 'NAVIGATION_OPERATION';
  if (message.includes('waitForNetworkIdle')) return 'NETWORK_IDLE_OPERATION';
  if (message.includes('setContent')) return 'CONTENT_SETUP_OPERATION';
  if (/Navigation timeout of \d+ ms exceeded/i.test(message)) return 'NAVIGATION_TIMEOUT';
  if (/Timed out after waiting \d+ms/i.test(message)) return 'BROWSER_OPERATION_TIMEOUT';
  if (/crashpad|database is required/i.test(message)) return 'CHROME_CRASHPAD_FAILURE';
  if (/Failed to launch the browser process/i.test(message)) return 'BROWSER_LAUNCH_FAILURE';
  if (/Target closed/i.test(message)) return 'BROWSER_TARGET_CLOSED';
  return 'UNKNOWN_PUPPETEER_FAILURE';
};
(async () => {
  let browser;
  let stage = 'launch';
  try {
    const useFirefox = process.env.SF_PUPPETEER_BROWSER === 'firefox';
    browser = await puppeteer.launch({
      browser: useFirefox ? 'firefox' : 'chrome',
      protocol: useFirefox ? 'webDriverBiDi' : 'cdp',
      executablePath: useFirefox ? process.env.SF_FIREFOX_PATH : '/usr/local/bin/chrome',
      headless: useFirefox || process.env.PUPPETEER_HEADLESS_MODE !== 'shell' ? true : 'shell',
      args: useFirefox || process.env.SF_CHROME_SANDBOX === '1' ? [] : ['--no-sandbox'],
      timeout: 30000,
    });
    stage = 'new_page';
    const page = await browser.newPage();
    stage = 'navigation';
    await page.goto('file:///work/input/probe.html', { waitUntil: 'domcontentloaded' });
    stage = 'network_idle';
    await page.waitForNetworkIdle({ timeout: 30000 });
    stage = 'animation_frame';
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => resolve())));
    stage = 'print_to_pdf';
    let pdf;
    if (process.env.SF_PDF_TRANSFER_MODE === 'base64') {
      const client = await page.createCDPSession();
      try {
        const response = await client.send('Page.printToPDF', {
          transferMode: 'ReturnAsBase64',
          printBackground: true,
          preferCSSPageSize: true,
          paperWidth: 1280 / 96,
          paperHeight: 720 / 96,
        });
        pdf = Buffer.from(response.data, 'base64');
      } finally {
        await client.detach();
      }
    } else {
      pdf = await page.pdf({
        printBackground: true,
        ...(process.env.SF_PUPPETEER_BROWSER === 'firefox' ? {} : { preferCSSPageSize: true }),
        width: '1280px',
        height: '720px',
      });
    }
    stage = 'write_pdf';
    fs.writeFileSync('/work/output/puppeteer-probe.pdf', pdf);
    process.stdout.write(JSON.stringify({ state: 'PASS' }));
  } catch (error) {
    process.stdout.write(JSON.stringify({ state: 'FAIL', stage, classification: classify(String(error?.message ?? '')) }));
    process.exitCode = 1;
  } finally {
    await browser?.close().catch(() => {});
  }
})();`;
await writeFile(path.join(input, 'probe.cjs'), probe);
const image = process.env.SF_MARP_IMAGE ?? 'ghcr.io/skills-factory/presentation-marp:1.0.0';
const tempMount = process.env.SF_CHROME_TMPFS_EXEC === '1'
  ? '/tmp:rw,nosuid,size=512m'
  : '/tmp:rw,noexec,nosuid,size=512m';
const name = 'sf-puppeteer-print-' + randomUUID();
const args = [
  'run', '--name', name, '--rm', '--network', 'none', '--read-only',
  '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
  '--pids-limit', '128', '--memory', '2g', '--shm-size', '256m',
  '--cpus', '2', '--ulimit', 'fsize=104857600:104857600',
  '--workdir', '/work/input', '--user', '10001:10001',
  '--env', 'HOME=/tmp', '--env', 'CHROME_CONFIG_HOME=/tmp/marp-config', '--env', 'XDG_CONFIG_HOME=/tmp/.chromium-config', '--env', 'XDG_CACHE_HOME=/tmp/.chromium-cache', '--env', 'PUPPETEER_HEADLESS_MODE=' + (process.env.SF_PUPPETEER_HEADLESS_MODE === 'chrome' ? 'chrome' : 'shell'), '--env', 'SF_PUPPETEER_BROWSER=' + (process.env.SF_PUPPETEER_BROWSER === 'firefox' ? 'firefox' : 'chrome'), '--env', 'SF_FIREFOX_PATH=/opt/puppeteer-browsers/firefox/linux-150.0.2/firefox/firefox', '--env', 'SF_PDF_TRANSFER_MODE=' + (process.env.SF_PDF_TRANSFER_MODE === 'base64' ? 'base64' : 'stream'), '--env', 'SF_CHROME_SANDBOX=' + (process.env.SF_CHROME_SANDBOX === '1' ? '1' : '0'),
  '--tmpfs', tempMount,
  '-v', input + ':/work/input:ro', '-v', output + ':/work/output:rw',
  '--entrypoint', 'node', image, '/work/input/probe.cjs',
];
function classifyOuter(stderr, timedOut) {
  if (/crashpad|database is required/i.test(stderr)) return 'CHROME_CRASHPAD_FAILURE';
  if (/Protocol error \(Page\.printToPDF/i.test(stderr)) return 'PRINT_TO_PDF_PROTOCOL_ERROR';
  if (/Target closed/i.test(stderr)) return 'BROWSER_TARGET_CLOSED';
  if (timedOut) return 'PUPPETEER_PROBE_TIMEOUT';
  return 'PUPPETEER_CONTAINER_FAILURE';
}
async function run() {
  return await new Promise(resolve => {
    const child = spawn('docker', args, { shell: false, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    let settled = false;
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', chunk => { if (stdout.length < 4096) stdout += chunk.slice(0, 4096 - stdout.length); });
    child.stderr.on('data', chunk => { if (stderr.length < 32768) stderr += chunk.slice(0, 32768 - stderr.length); });
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGTERM');
      spawn('docker', ['kill', name], { shell: false, stdio: 'ignore' }).on('error', () => {});
    }, 60_000);
    child.on('error', () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ code: 127, category: 'DOCKER_SPAWN_FAILED' });
    });
    child.on('close', code => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      let report = null;
      for (const line of stdout.split(/\r?\n/).reverse()) {
        try { report = JSON.parse(line); break; } catch {}
      }
      resolve({ code, timedOut, stage: report?.stage ?? null, category: report?.classification ?? classifyOuter(stderr, timedOut) });
    });
  });
}
try {
  const result = await run();
  const bytes = await readFile(path.join(output, 'puppeteer-probe.pdf')).catch(() => null);
  const pdfValid = Boolean(bytes && bytes.subarray(0, 5).toString() === '%PDF-');
  const report = result.code === 0 && pdfValid
    ? { state: 'PASS', output: 'puppeteer-probe.pdf', pdf_valid: true }
    : { state: 'FAIL', stage: result.stage, classification: result.category, pdf_valid: pdfValid };
  await writeFile(path.join(output, 'result.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
  if (report.state === 'FAIL') process.exitCode = 1;
} finally {
  await rm(root, { recursive: true, force: true });
}
