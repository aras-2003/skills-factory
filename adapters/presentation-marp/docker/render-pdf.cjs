const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { spawn } = require('node:child_process');

const html = path.resolve(process.argv[2]);
const output = path.resolve(process.argv[3]);
const expectedSlides = Number(process.argv[4]);
if (!Number.isInteger(expectedSlides) || expectedSlides < 1) throw new Error('Expected slide count is invalid');

const htmlSource = fs.readFileSync(html, 'utf8');
const actualSlides = (htmlSource.match(/<section\b/gi) ?? []).length;
if (actualSlides !== expectedSlides) throw new Error('Generated HTML slide count does not match DeckSpec');

const child = spawn(process.env.CHROME_PATH, [
  '--headless',
  '--no-sandbox',
  '--disable-dev-shm-usage',
  '--disable-gpu',
  '--disable-background-networking',
  '--no-pdf-header-footer',
  `--print-to-pdf=${output}`,
  pathToFileURL(html).href,
], { stdio: ['ignore', 'ignore', 'pipe'], env: { ...process.env, HOME: '/tmp' } });

let timedOut = false;
const timer = setTimeout(() => { timedOut = true; child.kill('SIGKILL'); }, 90_000);
child.on('error', error => {
  clearTimeout(timer);
  console.error(`SF_PDF_RENDER_FAILED:chrome_print:${actualSlides}:${expectedSlides}:${error.name || 'Error'}:${error.code || 'none'}`);
  process.exit(1);
});
child.on('close', code => {
  clearTimeout(timer);
  const size = fs.existsSync(output) ? fs.statSync(output).size : 0;
  let completePdf = false;
  if (size >= 8) {
    const fd = fs.openSync(output, 'r');
    try {
      const start = Buffer.alloc(5); fs.readSync(fd, start, 0, 5, 0);
      const tail = Buffer.alloc(Math.min(64, size)); fs.readSync(fd, tail, 0, tail.length, size - tail.length);
      completePdf = start.toString('ascii') === '%PDF-' && tail.toString('ascii').trimEnd().endsWith('%%EOF');
    } finally { fs.closeSync(fd); }
  }
  if (code !== 0 && !(timedOut && completePdf)) {
    console.error(`SF_PDF_RENDER_FAILED:chrome_print:${actualSlides}:${expectedSlides}:ExitError:${code}:bytes=${size}`);
    process.exit(1);
  }
  if (!completePdf) {
    console.error(`SF_PDF_RENDER_FAILED:chrome_print:${actualSlides}:${expectedSlides}:IncompleteOutput:bytes=${size}`);
    process.exit(1);
  }
});
