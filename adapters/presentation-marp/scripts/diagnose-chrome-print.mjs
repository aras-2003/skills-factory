import { mkdtemp, mkdir, writeFile, readFile, rm, chmod } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';

const root = await mkdtemp(path.join(tmpdir(), 'sf-chrome-print-'));
const input = path.join(root, 'input');
const output = path.resolve(process.argv[2] ?? path.join(root, 'output'));
await mkdir(input);
await mkdir(output, { recursive: true });
await chmod(output, 0o777);
await writeFile(path.join(input, 'probe.html'), '<!doctype html><meta charset="utf-8"><title>Synthetic print probe</title><h1>Chromium print probe</h1><p>synthetic only</p>');
const image = process.env.SF_MARP_IMAGE ?? 'ghcr.io/skills-factory/presentation-marp:1.0.0';
const name = 'sf-chrome-print-' + randomUUID();
const args = [
  'run', '--name', name, '--rm', '--network', 'none', '--read-only',
  '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
  '--pids-limit', '128', '--memory', '2g', '--shm-size', '256m',
  '--cpus', '2', '--ulimit', 'fsize=104857600:104857600',
  '--user', '10001:10001', '--env', 'HOME=/tmp',
  '--env', 'CHROME_CONFIG_HOME=/tmp/marp-config',
  '--tmpfs', '/tmp:rw,noexec,nosuid,size=512m',
  '-v', input + ':/work/input:ro', '-v', output + ':/work/output:rw',
  '--entrypoint', '/usr/local/bin/chrome', image,
  '--no-sandbox', '--headless', '--disable-gpu',
  '--user-data-dir=/tmp/marp-config/chrome-user-data',
  '--print-to-pdf=/work/output/chrome-probe.pdf',
  'file:///work/input/probe.html',
];
function classify(stderr, timedOut, pdfValid) {
  if (/crashpad|database is required/i.test(stderr)) return 'CHROME_CRASHPAD_FAILURE';
  if (/printing failed|failed to print/i.test(stderr)) return 'CHROME_PRINT_FAILURE';
  if (/failed to launch|executable not found/i.test(stderr)) return 'CHROME_LAUNCH_FAILURE';
  if (/target closed/i.test(stderr)) return 'CHROME_TARGET_CLOSED';
  if (timedOut && pdfValid) return 'CHROME_HUNG_AFTER_VALID_PDF';
  if (timedOut) return 'CHROME_PRINT_TIMEOUT';
  if (pdfValid) return 'CHROME_EXITED_AFTER_VALID_PDF';
  return 'UNKNOWN_CHROME_FAILURE';
}
async function run() {
  return await new Promise((resolve) => {
    const child = spawn('docker', args, { shell: false, stdio: ['ignore', 'ignore', 'pipe'] });
    let stderr = '';
    let timedOut = false;
    let settled = false;
    child.stderr.setEncoding('utf8');
    child.stderr.on('data', chunk => { if (stderr.length < 32768) stderr += chunk.slice(0, 32768 - stderr.length); });
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGTERM');
      const killer = spawn('docker', ['kill', name], { shell: false, stdio: 'ignore' });
      killer.on('error', () => {});
    }, 60_000);
    child.on('error', () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ code: 127, category: 'DOCKER_SPAWN_FAILED' });
    });
    child.on('close', async code => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      const bytes = await readFile(path.join(output, 'chrome-probe.pdf')).catch(() => null);
      const pdfValid = Boolean(bytes && bytes.subarray(0, 5).toString() === '%PDF-');
      resolve({ code, timedOut, pdfValid, category: classify(stderr, timedOut, pdfValid) });
    });
  });
}
try {
  const result = await run();
  const report = result.code === 0 && result.pdfValid
    ? { state: 'PASS', output: 'chrome-probe.pdf', pdf_valid: true, process_exit: 0 }
    : { state: 'FAIL', classification: result.category, pdf_valid: result.pdfValid };
  await writeFile(path.join(output, 'result.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
  if (report.state === 'FAIL') process.exitCode = 1;
} finally {
  await rm(root, { recursive: true, force: true });
}
