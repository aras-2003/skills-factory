import { mkdtemp, mkdir, writeFile, readFile, rm, chmod } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';

const root = await mkdtemp(path.join(tmpdir(), 'sf-chrome-cli-print-'));
const input = path.join(root, 'input');
const output = path.resolve(process.argv[2] ?? path.join(root, 'output'));
await mkdir(input);
await mkdir(output, { recursive: true });
await chmod(output, 0o777);
await writeFile(path.join(input, 'blank.html'), '<!doctype html><meta charset="utf-8"><title>Blank Chromium print probe</title><body></body>');

function classify(stderr, timedOut) {
  if (/crashpad|database is required/i.test(stderr)) return 'CHROME_CRASHPAD_FAILURE';
  if (/cannot open shared object|error while loading shared libraries/i.test(stderr)) return 'CHROME_SHARED_LIBRARY_MISSING';
  if (/no usable sandbox|sandbox.*(failed|error|denied)/i.test(stderr)) return 'CHROME_SANDBOX_FAILURE';
  if (/failed to connect to.*dbus|dbus.*(failed|unavailable)/i.test(stderr)) return 'CHROME_DBUS_FAILURE';
  if (/print.*(failed|error)|printing failed/i.test(stderr)) return 'CHROME_PRINT_FAILURE';
  if (/failed to launch|DevToolsActivePort/i.test(stderr)) return 'CHROME_LAUNCH_FAILURE';
  if (timedOut) return 'CHROME_OPERATION_TIMEOUT';
  return 'CHROME_EXIT_NONZERO';
}

const image = process.env.SF_MARP_IMAGE ?? 'ghcr.io/skills-factory/presentation-marp:1.0.0';
const name = 'sf-chrome-cli-print-' + process.pid;
const args = [
  'run', '--name', name, '--rm', '--network', 'none', '--read-only',
  '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
  '--pids-limit', '128', '--memory', '2g', '--shm-size', '256m', '--cpus', '2',
  '--user', '10001:10001', '--env', 'HOME=/tmp',
  '--tmpfs', '/tmp:rw,noexec,nosuid,size=512m',
  '-v', input + ':/work/input:ro', '-v', output + ':/work/output:rw',
  '--entrypoint', '/usr/local/bin/chrome', image,
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--disable-background-networking', '--disable-extensions', '--no-first-run',
  '--no-default-browser-check', '--no-pdf-header-footer',
  '--user-data-dir=/tmp/chrome-cli-profile',
  '--print-to-pdf=/work/output/chrome-cli.pdf', 'file:///work/input/blank.html',
];

try {
  const result = await new Promise(resolve => {
    const child = spawn('docker', args, { shell: false, stdio: ['ignore', 'ignore', 'pipe'] });
    let stderr = '';
    let timedOut = false;
    let settled = false;
    child.stderr.setEncoding('utf8');
    child.stderr.on('data', chunk => { if (stderr.length < 16384) stderr += chunk.slice(0, 16384 - stderr.length); });
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGTERM');
      spawn('docker', ['kill', name], { shell: false, stdio: 'ignore' }).on('error', () => {});
    }, 30000);
    child.on('error', () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ code: 127, classification: 'DOCKER_SPAWN_FAILED' });
    });
    child.on('close', code => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ code, classification: classify(stderr, timedOut) });
    });
  });
  const bytes = await readFile(path.join(output, 'chrome-cli.pdf')).catch(() => null);
  const valid = Boolean(bytes && bytes.subarray(0, 5).toString() === '%PDF-');
  const report = result.code === 0 && valid
    ? { state: 'PASS', pdf_valid: true }
    : { state: 'FAIL', classification: valid ? result.classification : (result.code === 0 ? 'CHROME_PDF_OUTPUT_INVALID' : result.classification), pdf_valid: valid };
  await writeFile(path.join(output, 'chrome-cli-result.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
  if (report.state === 'FAIL') process.exitCode = 1;
} finally {
  await rm(root, { recursive: true, force: true });
}
