import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import path from 'node:path';

const [fixturePath, evidenceRoot] = process.argv.slice(2);
assert.ok(fixturePath && evidenceRoot, 'usage: assert-pres07-evidence.mjs FIXTURE EVIDENCE_DIR');
const deck = JSON.parse(await readFile(fixturePath, 'utf8'));
assert.ok(deck.slides.length >= 10 && deck.slides.length <= 15, 'PRES07_FIXTURE_SLIDE_COUNT_INVALID');
const normalizeText = value => String(value).normalize('NFKC').replace(/\s+/g, ' ').trim();
const expectedIds = deck.slides.map(slide => slide.slide_id);
assert.equal(normalizeText('North Seg-\\nment remains distinct from Central Segment.'), normalizeText('North Segment remains distinct from Central Segment.'), 'PRES07_PDF_LINE_WRAP_NORMALIZATION');
const evidence = JSON.parse(await readFile(path.join(evidenceRoot, 'integration-receipt.json'), 'utf8'));
assert.equal(evidence.slide_count, deck.slides.length, 'PRES07_RECEIPT_SLIDE_COUNT_MISMATCH');
assert.deepEqual(evidence.slide_ids, expectedIds, 'PRES07_RECEIPT_SLIDE_ORDER_MISMATCH');

for (const mode of ['html', 'pdf', 'pptx_flattened', 'pptx_editable_experimental']) {
  const receipt = JSON.parse(await readFile(path.join(evidenceRoot, mode, 'receipt.json'), 'utf8'));
  assert.equal(receipt.input_sha256, evidence.fixture_sha256, `PRES07_INPUT_HASH_MISMATCH_${mode}`);
  assert.ok(/^[a-f0-9]{64}$/.test(receipt.output_sha256), `PRES07_OUTPUT_HASH_INVALID_${mode}`);
}
const html = await readFile(path.join(evidenceRoot, 'html', 'deck.html'), 'utf8');
for (const slide of deck.slides) {
  assert.ok(html.includes(slide.action_title), `PRES07_HTML_TITLE_MISSING_${slide.slide_id}`);
  for (const claim of slide.claims ?? []) assert.ok(html.includes(claim.statement), `PRES07_HTML_CLAIM_MISSING_${claim.claim_id}`);
  for (const ref of slide.data_refs ?? []) {
    assert.ok(html.includes(String(ref.data_ref_id)), `PRES07_HTML_LABEL_MISSING_${slide.slide_id}`);
    assert.ok(html.includes(String(ref.value)), `PRES07_HTML_VALUE_MISSING_${slide.slide_id}`);
    assert.ok(html.includes(ref.unit), `PRES07_HTML_UNIT_MISSING_${slide.slide_id}`);
  }
}
const pdf = JSON.parse(await readFile(path.join(evidenceRoot, 'pdf-inspection.json'), 'utf8'));
assert.equal(pdf.pages, deck.slides.length, 'PRES07_PDF_PAGE_COUNT_MISMATCH');
assert.equal(pdf.ratio, 16 / 9, 'PRES07_PDF_ASPECT_RATIO_MISMATCH');
const pdfText = normalizeText(pdf.extracted_text);
for (const slide of deck.slides) {
  assert.ok(pdfText.includes(normalizeText(slide.action_title)), `PRES07_PDF_TITLE_MISSING_${slide.slide_id}`);
  for (const claim of slide.claims ?? []) assert.ok(pdfText.includes(normalizeText(claim.statement)), `PRES07_PDF_CLAIM_MISSING_${claim.claim_id}`);
  for (const ref of slide.data_refs ?? []) {
    assert.ok(pdfText.includes(normalizeText(ref.data_ref_id)), `PRES07_PDF_LABEL_MISSING_${slide.slide_id}`);
    assert.ok(pdfText.includes(normalizeText(ref.value)), `PRES07_PDF_VALUE_MISSING_${slide.slide_id}`);
    assert.ok(pdfText.includes(normalizeText(ref.unit)), `PRES07_PDF_UNIT_MISSING_${slide.slide_id}`);
  }
}
const flat = JSON.parse(await readFile(path.join(evidenceRoot, 'pptx_flattened-inspection.json'), 'utf8'));
assert.equal(flat.slide_count, deck.slides.length, 'PRES07_FLAT_PPTX_SLIDE_COUNT_MISMATCH');
assert.ok(flat.native_shapes_by_slide.every(count => count === 0), 'PRES07_FLATTENED_PPTX_HAS_NATIVE_OBJECTS');
assert.ok(flat.image_shapes_and_backgrounds_by_slide.every(count => count > 0), 'PRES07_FLATTENED_PPTX_IMAGE_MISSING');
assert.equal(flat.notes_slide_count, deck.slides.length, 'PRES07_FLAT_PPTX_NOTES_MISSING');
const native = JSON.parse(await readFile(path.join(evidenceRoot, 'native-baseline', 'native-baseline-receipt.json'), 'utf8'));
assert.equal(native.fixture_sha256, evidence.fixture_sha256, 'PRES07_NATIVE_BASELINE_INPUT_HASH_MISMATCH');
assert.ok(/^[a-f0-9]{64}$/.test(native.pptx_sha256), 'PRES07_NATIVE_BASELINE_HASH_INVALID');
assert.equal(native.manual_edit_status, 'NOT_RUN', 'PRES07_MANUAL_EDIT_STATUS_MUST_REMAIN_EXPLICIT');
const editable = JSON.parse(await readFile(path.join(evidenceRoot, 'pptx_editable_experimental-inspection.json'), 'utf8'));
assert.equal(editable.slide_count, deck.slides.length, 'PRES07_EDITABLE_PPTX_SLIDE_COUNT_MISMATCH');
assert.ok(editable.native_shapes_by_slide.every(count => count > 0), 'PRES07_EDITABLE_PPTX_NATIVE_OBJECTS_MISSING');
assert.equal(editable.notes_slide_count, 0, 'PRES07_EDITABLE_PPTX_NOTES_LIMITATION_CHANGED');
const shots = (await readdir(path.join(evidenceRoot, 'screenshots'))).filter(name => /^html-slide-\d+\.png$/.test(name));
assert.equal(shots.length, deck.slides.length, 'PRES07_HTML_SCREENSHOT_COUNT_MISMATCH');
for (const name of shots) {
  const file = await stat(path.join(evidenceRoot, 'screenshots', name));
  assert.ok(file.size > 10_000, `PRES07_SCREENSHOT_SUSPICIOUSLY_SMALL_${name}`);
}
console.log(JSON.stringify({ state: 'PASS', fixture_slides: deck.slides.length, html_pdf_content: 'PASS', flattened_objects: 'NON_EDITABLE', experimental_editable_objects: 'PRESENT; manual PowerPoint edit NOT asserted', native_editable_baseline: 'PASS; manual edit NOT_RUN', screenshots: shots.length }));
