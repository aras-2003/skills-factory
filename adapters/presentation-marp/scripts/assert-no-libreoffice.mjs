import { preflight, AdapterError } from '../src/adapter.js';
const image = process.env.SF_MARP_BASE_IMAGE;
if (!image) throw new Error('SF_MARP_BASE_IMAGE is required');
for (const mode of ['pdf', 'pptx_editable_experimental']) {
  try { await preflight(mode, { image }); }
  catch (error) {
    if (error instanceof AdapterError && error.code === 'BLOCKED_MISSING_RUNTIME' && /no fallback/i.test(error.message)) continue;
    throw error;
  }
  throw new Error(`${mode} unexpectedly succeeded without LibreOffice`);
}
console.log('PASS: searchable PDF and editable mode block without LibreOffice; no fallback');
