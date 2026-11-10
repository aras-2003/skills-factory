const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const candidates = ['/home/marp/.cli/node_modules', '/usr/local/lib/node_modules', '/usr/lib/node_modules'];
let puppeteer;
for (const base of candidates) { try { puppeteer = require(require.resolve('puppeteer-core', { paths: [base] })); break; } catch {} }
if (!puppeteer) throw new Error('Pinned puppeteer-core was not found in the renderer image');
let stage = 'launch'; let actualSlides = -1; let expectedSlideCount = -1;
(async () => {
  const html = path.resolve(process.argv[2]); const output = path.resolve(process.argv[3]); const expectedSlides = Number(process.argv[4]);
  if (!Number.isInteger(expectedSlides) || expectedSlides < 1) throw new Error('Expected slide count is invalid');
  expectedSlideCount = expectedSlides;
  stage = 'slide_count';
  const htmlSource = fs.readFileSync(html, 'utf8');
  actualSlides = (htmlSource.match(/<section\b/gi) ?? []).length;
  if (actualSlides !== expectedSlides) throw new Error('Generated HTML slide count does not match DeckSpec');
  const browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH, headless: true, protocolTimeout: 120_000, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  try {
    const page = await browser.newPage();
    stage = 'navigation';
    await page.setRequestInterception(true);
    page.on('request', request => { const url = request.url(); if (url.startsWith('file:') || url.startsWith('data:')) request.continue(); else request.abort(); });
    await page.goto(pathToFileURL(html).href, { waitUntil: 'networkidle0', timeout: 60000 });
    stage = 'fonts';
    await page.evaluate(() => document.fonts.ready.then(() => true));
    stage = 'print';
    await page.pdf({ path: output, printBackground: true, preferCSSPageSize: true, waitForFonts: false, timeout: 0 });
    stage = 'output_check';
    const size = fs.statSync(output).size;
    if (!size) throw new Error('Chromium produced an empty PDF');
  } finally { await browser.close(); }
})().catch(error => { const name = error && typeof error.name === 'string' ? error.name.slice(0, 40) : 'Error'; const code = error && typeof error.code === 'string' ? error.code.slice(0, 40) : 'none'; const message = String(error && error.message || '').replace(/(?:file|https?):\/\/\S+/g, '[url]').replace(/\/[^\s]+/g, '[path]').replace(/[\r\n:]+/g, ' ').slice(0, 160); console.error(`SF_PDF_RENDER_FAILED:${stage}:${actualSlides}:${expectedSlideCount}:${name}:${code}:${message}`); process.exit(1); });
