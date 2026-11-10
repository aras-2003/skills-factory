import { mkdtemp, mkdir, writeFile, stat, rm, chmod } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';

const root = await mkdtemp(path.join(tmpdir(), 'sf-marp-base-editable-'));
const input = path.join(root, 'input');
const output = path.resolve(process.argv[2] ?? path.join(root, 'output'));
await mkdir(input);
await mkdir(output, { recursive: true });
await chmod(output, 0o777);
await writeFile(path.join(input, 'deck.md'), [
  '---',
  'marp: true',
  'size: 16:9',
  '---',
  '',
  '# Minimal editable smoke test',
  '',
  'Plain text only.',
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
  '--tmpfs', '/tmp:rw,noexec,nosuid,size=512m',
  '-v', input + ':/work/input:ro',
  '-v', output + ':/work/output:rw',
  '--entrypoint', 'node',
  image,
  '/home/marp/.cli/marp-cli.js',
  '/work/input/deck.md',
  '--browser-timeout', '90',
  '--pptx', '--pptx-editable', '--allow-local-files',
  '--output', '/work/output/base-editable.pptx',
];
try {
  await new Promise((resolve, reject) => {
    const child = spawn('docker', args, { shell: false, stdio: 'inherit' });
    child.on('error', reject);
    child.on('close', code => code === 0 ? resolve() : reject(new Error('Marp base smoke test failed')));
  });
  const outputInfo = await stat(path.join(output, 'base-editable.pptx'));
  if (!outputInfo.isFile() || outputInfo.size === 0) throw new Error('Marp produced an empty editable PPTX');
  console.log(JSON.stringify({ state: 'PASS', output: 'base-editable.pptx', size_bytes: outputInfo.size }));
} catch {
  console.error(JSON.stringify({ state: 'FAIL', classification: 'BASE_MARP_EDITABLE_RUNTIME_FAILED' }));
  process.exitCode = 1;
} finally {
  await rm(root, { recursive: true, force: true });
}
