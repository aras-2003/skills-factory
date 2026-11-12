import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, readdir, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';

const [fixturePath, evidenceRoot] = process.argv.slice(2);
assert.ok(fixturePath && evidenceRoot, 'usage: assert-pres07-native-baseline.mjs FIXTURE EVIDENCE_DIR');
const fixtureBytes = await readFile(fixturePath);
const deck = JSON.parse(fixtureBytes.toString('utf8'));
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const generation = JSON.parse(await readFile(path.join(evidenceRoot, 'generation.json'), 'utf8'));
const inspection = JSON.parse(await readFile(path.join(evidenceRoot, 'inspection.json'), 'utf8'));
const reopen = JSON.parse(await readFile(path.join(evidenceRoot, 'reopen.json'), 'utf8'));
const ocr = JSON.parse(await readFile(path.join(evidenceRoot, 'reopened', 'ocr-receipt.json'), 'utf8'));
const pptx = await readFile(path.join(evidenceRoot, 'native-baseline.pptx'));
const odp = await readFile(path.join(evidenceRoot, 'native-baseline.odp'));
assert.equal(generation.slides, deck.slides.length, 'PRES07_NATIVE_GENERATION_SLIDE_COUNT');
assert.equal(generation.fixture_sha256, sha256(fixtureBytes), 'PRES07_NATIVE_GENERATION_FIXTURE_HASH');
assert.equal(generation.odp_sha256, sha256(odp), 'PRES07_NATIVE_GENERATION_ODP_HASH');
assert.equal(inspection.mode, 'pptx_native_baseline', 'PRES07_NATIVE_INSPECTION_MODE');
assert.equal(inspection.slide_count, deck.slides.length, 'PRES07_NATIVE_INSPECTION_SLIDE_COUNT');
assert.equal(inspection.notes_slide_count, deck.slides.length, 'PRES07_NATIVE_NOTES_MISSING');
assert.ok(inspection.native_shapes_by_slide.every(count => count > 0), 'PRES07_NATIVE_OBJECTS_MISSING');
assert.ok(inspection.external_hyperlink_count > 0, 'PRES07_NATIVE_HYPERLINK_MISSING');
assert.ok(String(reopen.reopened_by).includes('LibreOffice Impress'), 'PRES07_NATIVE_REOPEN_RUNTIME');
assert.equal(ocr.slides.length, deck.slides.length, 'PRES07_NATIVE_REOPEN_SLIDE_COUNT');
const normalizeText = value => String(value).replace(/\s+/g, ' ').trim().toLowerCase();
const visibleSlideText = normalizeText(ocr.slides.map(slide => slide.ocr).join(' '));
assert.equal(inspection.notes_text.length, deck.slides.length, 'PRES07_NATIVE_NOTES_TEXT_COUNT');
for (const [index, slide] of deck.slides.entries()) {
  if (!slide.notes) continue;
  const noteText = normalizeText(slide.notes);
  assert.ok(normalizeText(inspection.notes_text[index]).includes(noteText), `PRES07_NATIVE_NOTE_CONTENT_MISSING_${index + 1}`);
  assert.ok(!visibleSlideText.includes(noteText), `PRES07_NATIVE_NOTE_LEAKED_ON_SLIDE_${index + 1}`);
}
const screenshots = (await readdir(path.join(evidenceRoot, 'reopened'))).filter(name => /^reopened-slide-\d+\.png$/.test(name));
assert.equal(screenshots.length, deck.slides.length, 'PRES07_NATIVE_REOPEN_SCREENSHOTS');
for (const name of screenshots) assert.ok((await stat(path.join(evidenceRoot, 'reopened', name))).size > 10_000, 'PRES07_NATIVE_SCREENSHOT_SMALL_' + name);
const receipt = {
  schema_version: 1,
  fixture_sha256: sha256(fixtureBytes),
  odp_sha256: generation.odp_sha256,
  pptx_sha256: sha256(pptx),
  slide_count: deck.slides.length,
  native_shapes_by_slide: inspection.native_shapes_by_slide,
  notes_slide_count: inspection.notes_slide_count,
  notes_visible_on_slides: false,
  external_hyperlink_count: inspection.external_hyperlink_count,
  reopened_by: reopen.reopened_by,
  reopen_screenshots: screenshots.length,
  manual_edit_status: 'NOT_RUN',
};
await writeFile(path.join(evidenceRoot, 'native-baseline-receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
console.log(JSON.stringify({ state: 'PASS', ...receipt }));
