import { mkdtemp, mkdir, writeFile, stat, rm, chmod } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';

const root = await mkdtemp(path.join(tmpdir(), 'sf-marp-pdf-diagnostic-'));
const input = path.join(root, 'input');
const output = path.resolve(process.argv[2] ?? path.join(root, 'output'));
await mkdir(input);
await mkdir(output, { recursive: true });
await chmod(output, 0o777);
const css = [
  '/* @theme sf-editorial */',
  'section { box-sizing: border-box; width: 1280px; height: 720px; padding: 72px 86px 62px; background: #f6f4ee; color: #17243a; font-family: "Liberation Sans", sans-serif; font-size: 28px; line-height: 1.35; }',
  'h1 { max-width: 1040px; margin: 0 0 34px; color: #17243a; font-size: 52px; line-height: 1.08; }',
  'p, small { color: #52627a; }',
  'li { margin: 12px 0; }',
  'strong { color: #176b87; }',
  'small { font-size: .7em; }',
  '.marpit img { max-width: 100%; max-height: 300px; }',
];
await writeFile(path.join(input, 'sf-editorial.css'), css.join('\n'));
await writeFile(path.join(input, 'deck.md'), [
  '---',
  'marp: true',
  'theme: sf-editorial',
  'size: 16:9',
  '---',
  '',
  '# Minimal PDF diagnostic',
  '',
  'Synthetic text only.',
  '',
].join('\n'));
const image = process.env.SF_MARP_IMAGE ?? 'ghcr.io/skills-factory/presentation-marp:1.0.0';
const args = [
  'run', '--rm', '--network', 'none', '--read-only',
  '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
  '--pids-limit', '128', '--memory', '2g', '--shm-size', '256m',
  '--cpus', '2', '--ulimit', 'fsize=104857600:104857600',
  '--workdir', '/work/input',
  '--user', '10001:10001', '--env', 'HOME=/tmp',
  '--env', 'CHROME_NO_SANDBOX=1',
  '--env', 'DEBUG=marp-cli:browser,puppeteer:protocol',
  '--tmpfs', '/tmp:rw,noexec,nosuid,size=512m',
  '-v', input + ':/work/input:ro',
  '-v', output + ':/work/output:rw',
  '--entrypoint', 'node',
  image,
  '/home/marp/.cli/marp-cli.js',
  '/work/input/deck.md', '--theme-set', './sf-editorial.css',
  '--browser-timeout', '90', '--pdf', '--allow-local-files', '--browser-protocol', 'cdp',
  '--output', '/work/output/base-marp.pdf',
];
function classify(stderr) {
  if (/Page\.printToPDF/i.test(stderr)) return 'PRINT_TO_PDF_OPERATION';
  if (/Page\.navigate/i.test(stderr)) return 'NAVIGATION_OPERATION';
  if (/waitForNetworkIdle/i.test(stderr)) return 'NETWORK_IDLE_OPERATION';
  if (/setContent/i.test(stderr)) return 'CONTENT_SETUP_OPERATION';
  if (/Navigation timeout of \d+ ms exceeded/i.test(stderr)) return 'NAVIGATION_TIMEOUT';
  if (/Timed out after waiting \d+ms/i.test(stderr)) return 'BROWSER_OPERATION_TIMEOUT';
  if (/Protocol error \(Page\.printToPDF/i.test(stderr)) return 'PRINT_TO_PDF_PROTOCOL_ERROR';
  if (/Failed to launch the browser process/i.test(stderr)) return 'BROWSER_LAUNCH_FAILED';
  if (/Target closed/i.test(stderr)) return 'BROWSER_TARGET_CLOSED';
  return 'UNKNOWN_RENDER_FAILURE';
}
async function run() {
  return await new Promise((resolve, reject) => {
    const child = spawn('docker', args, { shell: false, stdio: ['ignore', 'ignore', 'pipe'] });
    let stderr = '';
    child.stderr.setEncoding('utf8');
    child.stderr.on('data', chunk => {
      if (stderr.length < 65536) stderr += chunk.slice(0, 65536 - stderr.length);
    });
    child.on('error', () => reject(new Error('DOCKER_SPAWN_FAILED')));
    child.on('close', code => code === 0 ? resolve() : reject(new Error(classify(stderr))));
  });
}
try {
  await run();
  const file = await stat(path.join(output, 'base-marp.pdf'));
  if (!file.isFile() || file.size === 0) throw new Error('EMPTY_OUTPUT');
  console.log(JSON.stringify({ state: 'PASS', output: 'base-marp.pdf', size_bytes: file.size }));
} catch (error) {
  console.error(JSON.stringify({ state: 'FAIL', classification: String(error.message) }));
  process.exitCode = 1;
} finally {
  await rm(root, { recursive: true, force: true });
}
