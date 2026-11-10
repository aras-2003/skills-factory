import { preflight, AdapterError } from '../src/adapter.js';
const image = process.env.SF_MARP_BASE_IMAGE;
if (!image) throw new Error('SF_MARP_BASE_IMAGE is required');
try { await preflight('pptx_editable_experimental', { image }); }
catch (error) { if (error instanceof AdapterError && error.code === 'BLOCKED_MISSING_RUNTIME' && /no flattened fallback/i.test(error.message)) { console.log('PASS: editable mode blocks without LibreOffice and does not fall back'); process.exit(0); } throw error; }
throw new Error('Editable mode unexpectedly succeeded without LibreOffice');
