import { readFile, mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { render } from '../src/adapter.js';

const source = path.join(path.dirname(new URL(import.meta.url).pathname), '../fixtures/canonical-deck-v1.json');
const deck = JSON.parse(await readFile(source, 'utf8'));
deck.slides = deck.slides.slice(0, 1);
deck.slides[0].notes = '';
const root = await mkdtemp(path.join(tmpdir(), 'sf-marp-minimal-editable-'));
try {
  const input = path.join(root, 'deck.json');
  const outputDir = path.resolve(process.argv[2] ?? path.join(root, 'output'));
  await writeFile(input, JSON.stringify(deck));
  const result = await render({
    input,
    outputDir,
    mode: 'pptx_editable_experimental',
    docker: 'docker',
    image: process.env.SF_MARP_IMAGE,
  });
  console.log(JSON.stringify({
    state: 'PASS',
    mode: result.requested_mode,
    slide_count: result.slide_count,
    output_sha256: result.output_sha256,
    runtime: {
      marp: result.runtime.marp,
      browser: result.runtime.browser,
      libreoffice: result.runtime.libreoffice,
    },
  }));
} catch (error) {
  console.error(JSON.stringify({
    state: 'FAIL',
    code: error.code ?? 'UNKNOWN',
    runtimeFailure: error.details?.runtimeFailure,
    rendererFailure: error.details?.rendererFailure,
  }));
  process.exitCode = 1;
} finally {
  await rm(root, { recursive: true, force: true });
}
