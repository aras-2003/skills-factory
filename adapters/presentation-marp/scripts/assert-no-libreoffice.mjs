import { preflight, AdapterError } from '../src/adapter.js';
const image = process.env.SF_MARP_BASE_IMAGE;
if (!image) throw new Error('SF_MARP_BASE_IMAGE is required');
const mode = 'pptx_editable_experimental';
try { await preflight(mode, { image }); }
catch (error) {
  if (error instanceof AdapterError && error.code === 'BLOCKED_MISSING_RUNTIME' && /no fallback/i.test(error.message)) {
    console.log('PASS: experimental editable PPTX blocks without LibreOffice; no fallback');
    process.exit(0);
  }
  throw error;
}
throw new Error(`${mode} unexpectedly succeeded without LibreOffice`);
