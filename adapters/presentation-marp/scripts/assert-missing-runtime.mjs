import { preflight, AdapterError } from '../src/adapter.js';
const image = process.env.SF_MARP_NO_BROWSER_IMAGE;
if (!image) throw new Error('SF_MARP_NO_BROWSER_IMAGE is required');
const mode = 'pptx_flattened';
try { await preflight(mode, { image }); }
catch (error) {
  if (error instanceof AdapterError && error.code === 'BLOCKED_MISSING_RUNTIME' && /browser/i.test(error.message)) {
    console.log('PASS: flattened PPTX mode blocks without the browser runtime');
    process.exit(0);
  }
  throw error;
}
throw new Error(`${mode} unexpectedly succeeded without the browser runtime`);
