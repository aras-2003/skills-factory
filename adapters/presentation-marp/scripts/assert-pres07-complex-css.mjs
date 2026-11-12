import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { access, mkdir, mkdtemp, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const adapterRoot = path.resolve(here, '..');
const fixture = path.resolve(process.env.SF_MARP_FIXTURE ?? path.join(adapterRoot, 'fixtures/pres07-cross-format-v1.json'));
const receiptPath = path.resolve(process.argv[2] ?? path.join(adapterRoot, '.tmp/pres07-complex-css/receipt.json'));
const fixtureBytes = await readFile(fixture);
const scratch = await mkdtemp(path.join(tmpdir(), 'sf-pres07-complex-css-'));
const outputDir = path.join(scratch, 'output');

function runAdapter() {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [
      path.join(adapterRoot, 'src/adapter.js'), 'render',
      '--input', fixture, '--output-dir', outputDir,
      '--mode', 'pptx_editable_experimental', '--theme', 'sf-technology',
    ], { stdio: ['ignore', 'pipe', 'pipe'], shell: false });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', chunk => { if (stdout.length < 4096) stdout += chunk.toString('utf8').slice(0, 4096 - stdout.length); });
    child.stderr.on('data', chunk => { if (stderr.length < 4096) stderr += chunk.toString('utf8').slice(0, 4096 - stderr.length); });
    child.on('error', () => reject(new Error('PRES07_COMPLEX_CSS_CASE_FAILED')));
    child.on('close', code => resolve({ code, stdout, stderr }));
  });
}

try {
  const result = await runAdapter();
  assert.equal(result.code, 1, 'PRES07_COMPLEX_CSS_UNEXPECTED_SUCCESS');
  const lines = result.stderr.trim().split(/\r?\n/);
  const failure = JSON.parse(lines.at(-1) ?? '{}');
  assert.equal(failure.code, 'BLOCKED_THEME_UNSUPPORTED', 'PRES07_COMPLEX_CSS_NOT_EXPLICITLY_BLOCKED');
  assert.equal(result.stdout.trim(), '', 'PRES07_COMPLEX_CSS_EMITTED_OUTPUT');
  await assert.rejects(stat(outputDir), error => error?.code === 'ENOENT', 'PRES07_COMPLEX_CSS_OUTPUT_DIR_CREATED');
  await assert.rejects(access(path.join(outputDir, 'deck-editable.pptx')), error => error?.code === 'ENOENT', 'PRES07_COMPLEX_CSS_SILENT_DOWNGRADE');
  const receipt = {
    schema_version: 1,
    fixture_sha256: createHash('sha256').update(fixtureBytes).digest('hex'),
    requested_mode: 'pptx_editable_experimental',
    requested_theme: 'sf-technology',
    css_complexity: 'progressive',
    verdict: 'BLOCKED_AS_DESIGNED',
    observed_code: failure.code,
    silent_downgrade: false,
    output_created: false,
  };
  await mkdir(path.dirname(receiptPath), { recursive: true });
  await writeFile(receiptPath, JSON.stringify(receipt, null, 2) + '\n');
  console.log(JSON.stringify({ state: 'PASS', ...receipt }));
} catch {
  console.error(JSON.stringify({ classification: 'PRES07_COMPLEX_CSS_CASE_FAILED' }));
  process.exitCode = 1;
} finally {
  await rm(scratch, { recursive: true, force: true });
}
