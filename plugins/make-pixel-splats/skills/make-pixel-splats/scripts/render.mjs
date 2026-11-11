// Renders frames of the pixel splat scenes in headless Chrome on the GPU.
// Usage: node render.mjs <plan.mjs> <output folder>   (run from the folder that holds this file and node_modules)
// The plan module exports `frames`: an array of { file, scene, spacing, options } (options go to window.renderFrame).
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { extname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright-core';

const projectRoot = import.meta.dirname;
const [planPath, outputFolder] = process.argv.slice(2);
const { frames } = await import(pathToFileURL(resolve(planPath)).href);
await mkdir(outputFolder, { recursive: true });

const contentTypes = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.wasm': 'application/wasm', '.json': 'application/json' };
const server = createServer(async (request, response) => {
  const requested = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
  const path = requested === '/' ? '/index.html' : requested;
  try {
    const file = await readFile(join(projectRoot, path));
    response.writeHead(200, { 'Content-Type': contentTypes[extname(path)] ?? 'application/octet-stream' }).end(file);
  } catch {
    response.writeHead(404).end();
  }
});
await new Promise(done => server.listen(0, '127.0.0.1', done));

const browser = await chromium.launch({
  channel: 'chrome',
  // Draw on the real GPU. Software rendering works but is several times slower.
  args: [...(process.platform === 'win32' ? ['--use-angle=d3d11'] : []), '--enable-gpu', '--ignore-gpu-blocklist', '--disable-gpu-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 1200, height: 1200 } });
page.on('pageerror', error => console.error('page error:', error.message));
page.on('console', message => { if (message.type() === 'error') console.error('console:', message.text()); });
await page.goto(`http://127.0.0.1:${server.address().port}/`);
await page.waitForFunction(() => window.pageReady === true);

const started = Date.now();
for (const [frameIndex, frame] of frames.entries()) {
  const count = await page.evaluate(({ scene, spacing }) => window.setupScene(scene, spacing), frame);
  const result = await page.evaluate(options => window.renderFrame(options), frame.options);
  await writeFile(join(outputFolder, frame.file), Buffer.from(result.url.split(',')[1], 'base64'));
  if (frameIndex % 30 === 0 || frames.length < 20) {
    console.log(`${frame.file} scene=${frame.scene} static=${count} drawn=${result.splatCount} elapsed=${((Date.now() - started) / 1000).toFixed(1)}s`);
  }
}
await browser.close();
server.close();
