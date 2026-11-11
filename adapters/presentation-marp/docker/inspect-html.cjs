const fs = require('node:fs');
const path = require('node:path');
const candidates = ['/home/marp/.cli/node_modules', '/usr/local/lib/node_modules', '/usr/lib/node_modules'];
let puppeteer;
for (const base of candidates) { try { puppeteer = require(require.resolve('puppeteer-core', { paths: [base] })); break; } catch {} }
if (!puppeteer) throw new Error('Pinned puppeteer-core was not found in the renderer image');
(async () => {
  const html = path.resolve(process.argv[2]); const output = path.resolve(process.argv[3]); const count = Number(process.argv[4]);
  fs.mkdirSync(output, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH, headless: true, args: ['--no-sandbox','--disable-dev-shm-usage'] });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
    await page.setRequestInterception(true);
    page.on('request', request => { const url = request.url(); if (url.startsWith('file:') || url.startsWith('data:')) request.continue(); else request.abort(); });
    await page.goto(`file://${html}`, { waitUntil: 'networkidle0', timeout: 30000 });
    const countFound = await page.$$eval('section', nodes => nodes.length);
    if (countFound !== count) throw new Error(`Expected ${count} rendered slides, got ${countFound}`);
    const records = [];
    const allText = await page.$$eval('section', nodes => nodes.map(node => node.textContent).join('\n').replace(/\s+/g, ' ').trim());
    const requiredText = ['Three slides, one source model','Synthetic quarterly growth','Preserve meaning across modes','12 percent','18 percent','src-synthetic','2026-Q1','2026-Q2'];
    const missingText = requiredText.filter(required => !allText.toLowerCase().includes(required.toLowerCase()));
    console.log(`HTML_CONTENT_CHECK:${JSON.stringify({ textLength: allText.length, missing: missingText })}`);
    if (missingText.length) throw new Error(`Rendered HTML is missing expected content: ${missingText.join(', ')}`);
    const controlsHidden = await page.$$eval('.bespoke-marp-osc', nodes => {
      nodes.forEach(node => { node.style.display = 'none'; });
      return nodes.length;
    });
    if (controlsHidden < 1) throw new Error('HTML_PRESENTATION_CONTROLS_NOT_FOUND');
    const slides = await page.$$('section');
    for (let i=0; i<countFound; i++) {
      await page.evaluate(index => {
        document.querySelectorAll('section').forEach((section, n) => {
          const active = n === index;
          const slide = section.closest('svg[data-marpit-svg]');
          if (!slide) throw new Error('HTML_SLIDE_CONTAINER_MISSING');
          slide.style.contentVisibility = active ? 'visible' : 'hidden';
          slide.style.visibility = active ? 'visible' : 'hidden';
          slide.style.opacity = active ? '1' : '0';
          slide.style.pointerEvents = active ? 'auto' : 'none';
          slide.style.zIndex = active ? '1' : '0';
          section.style.visibility = active ? 'visible' : 'hidden';
        });
      }, i);
      const slide = slides[i];
      const box = await slide.boundingBox();
      if (!box || Math.abs(box.width - 1280) > 1 || Math.abs(box.height - 720) > 1) {
        throw new Error('HTML_SLIDE_BOUNDS_INVALID');
      }
      const png = path.join(output, `html-slide-${String(i+1).padStart(2,'0')}.png`);
      await slide.screenshot({ path: png });
      records.push({ slide: i+1, screenshot: path.basename(png), width: Math.round(box.width), height: Math.round(box.height) });
    }
    fs.writeFileSync(path.join(output, 'html-reopen.json'), JSON.stringify({slides:records,text:allText,controls_hidden:controlsHidden}, null, 2)+'\n');
  } finally { await browser.close(); }
})();
