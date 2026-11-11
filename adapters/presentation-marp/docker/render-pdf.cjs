#!/usr/bin/env node
const { createRequire } = require('node:module');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const requireMarp = createRequire('/home/marp/.cli/package.json');
const puppeteer = requireMarp('puppeteer-core');

const source = path.resolve(process.argv[2] ?? '');
const destination = path.resolve(process.argv[3] ?? '');
const assetRoot = path.resolve(process.argv[4] ?? '');
const fail = (stage, classification) => {
  process.stdout.write(JSON.stringify({ state: 'FAIL', stage, classification }) + '\n');
  process.exit(1);
};

(async () => {
  if (!fs.existsSync(source) || !fs.statSync(source).isFile() ||
      !fs.existsSync(assetRoot) || !fs.statSync(assetRoot).isDirectory() ||
      !destination) fail('input_check', 'PDF_INPUT_INVALID');

  let browser;
  const copiedAssets = [];
  let stage = 'launch';
  try {
    browser = await puppeteer.launch({
      browser: 'chrome',
      protocol: 'cdp',
      executablePath: process.env.CHROME_PATH ?? '/usr/local/bin/chrome-headless-shell',
      headless: process.env.PUPPETEER_HEADLESS_MODE === 'old' ? 'shell' : true,
      args: ['--no-sandbox'],
      timeout: 30000,
    });
    stage = 'page_setup';
    const page = await browser.newPage();
    const html = fs.readFileSync(source, 'utf8');
    const outputRoot = path.dirname(source);
    const assetNames = new Set([...html.matchAll(/(?:src|href)=["'](?:\.\/)?([a-f0-9]{64}\.(?:svg|png|jpe?g|webp))["']/gi)].map(match => match[1]));
    for (const name of assetNames) {
      const from = path.join(assetRoot, name);
      const to = path.join(outputRoot, name);
      if (!fs.existsSync(from) || !fs.statSync(from).isFile()) fail('asset_check', 'PDF_ASSET_MISSING');
      if (!fs.existsSync(to)) { fs.copyFileSync(from, to); copiedAssets.push(to); }
    }
    const base = '<base href="' + pathToFileURL(outputRoot + path.sep).href + '">';
    const document = html.replace(/<head\b([^>]*)>/i, '<head$1>' + base);
    const renderSource = path.join(outputRoot, 'deck-browser-pdf.html');
    fs.writeFileSync(renderSource, document);
    stage = 'navigation';
    await page.goto(pathToFileURL(renderSource).href, { waitUntil: 'domcontentloaded', timeout: 30000 });
    stage = 'render';
    await page.waitForNetworkIdle({ timeout: 30000 });
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => resolve())));
    const pdf = await page.pdf({
      path: destination,
      printBackground: true,
      preferCSSPageSize: true,
      width: '1280px',
      height: '720px',
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
    });
    if (!pdf || pdf.subarray(0, 5).toString() !== '%PDF-') fail('output_check', 'PDF_OUTPUT_INVALID');
    process.stdout.write(JSON.stringify({ state: 'PASS', output: path.basename(destination), size_bytes: pdf.length }) + '\n');
  } catch {
    fail(stage, stage === 'launch' ? 'BROWSER_LAUNCH_FAILURE'
      : stage === 'navigation' ? 'BROWSER_NAVIGATION_FAILURE'
      : 'BROWSER_PDF_RENDER_FAILURE');
  } finally {
    await browser?.close().catch(() => {});
    try { fs.rmSync(path.join(path.dirname(source), 'deck-browser-pdf.html'), { force: true }); } catch {}
    for (const asset of copiedAssets) { try { fs.rmSync(asset, { force: true }); } catch {} }
  }
})();
