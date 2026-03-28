import { chromium } from 'playwright';
import handler from 'serve-handler';
import http from 'node:http';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';

const DIST = join(import.meta.dirname, '..', 'dist');
const PORT = 4567;

const ROUTES = [
  '/',
  '/explore',
  '/changelog',
  '/terms',
  '/privacy',
  '/use-cases/steam-game-price-alerts',
  '/use-cases/competitor-price-change-monitor',
  '/use-cases/crypto-exchange-listing-alert',
  '/compare/visualping-alternative',
  '/compare/distill-alternative',
  '/compare/changetower-alternative',
];

// Serve dist/ on a local port
const server = http.createServer((req, res) =>
  handler(req, res, {
    public: DIST,
    rewrites: [{ source: '**', destination: '/index.html' }],
  })
);

await new Promise((resolve) => server.listen(PORT, resolve));
console.log(`Serving dist/ on http://localhost:${PORT}`);

const browser = await chromium.launch();

for (const route of ROUTES) {
  const page = await browser.newPage();
  await page.goto(`http://localhost:${PORT}${route}`, {
    waitUntil: 'networkidle',
  });
  // Wait for React to render visible content
  await page.waitForSelector('nav, main, h1', { timeout: 15000 });

  const html = await page.content();

  const outPath =
    route === '/'
      ? join(DIST, 'index.html')
      : join(DIST, route.slice(1), 'index.html');

  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, html, 'utf-8');
  console.log(`Prerendered: ${route} → ${outPath}`);

  await page.close();
}

await browser.close();
server.close();
console.log('Prerendering complete.');
