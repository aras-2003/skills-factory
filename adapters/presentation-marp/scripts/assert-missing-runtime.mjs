import { preflight, AdapterError } from '../src/adapter.js';
const image = process.env.SF_MARP_NO_BROWSER_IMAGE;
if (!image) throw new Error('SF_MARP_NO_BROWSER_IMAGE is required');
try { await preflight('pdf', { image }); }
catch (error) { if (error instanceof AdapterError && error.code === 'BLOCKED_MISSING_RUNTIME' && /browser/i.test(error.message)) { console.log('PASS: PDF mode blocks without the browser runtime'); process.exit(0); } throw error; }
throw new Error('PDF mode unexpectedly succeeded without the browser runtime');
