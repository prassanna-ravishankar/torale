import { chromium } from 'playwright';
import handler from 'serve-handler';
import http from 'node:http';
import { writeFileSync, mkdirSync, existsSync } from 'node:fs';
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

// Ensure config.js exists (normally injected at runtime by nginx)
const configPath = join(DIST, 'config.js');
if (!existsSync(configPath)) {
  writeFileSync(configPath, 'window.CONFIG = {};', 'utf-8');
}

// Serve dist/ on a local port
const server = http.createServer((req, res) =>
  handler(req, res, {
    public: DIST,
    rewrites: [{ source: '**', destination: '/index.html' }],
  })
);

await new Promise((resolve) => server.listen(PORT, resolve));
console.log(`Prerendering ${ROUTES.length} routes...`);

const browser = await chromium.launch();
const context = await browser.newContext();

// Bypass auth during prerendering — app checks this flag to use NoAuthProvider
await context.addInitScript(() => {
  window.__PRERENDER__ = true;
});

let failed = 0;

for (const route of ROUTES) {
  const page = await context.newPage();

  page.on('pageerror', (err) => console.error(`  [error] ${route}: ${err.message}`));

  await page.goto(`http://localhost:${PORT}${route}`, {
    waitUntil: 'networkidle',
  });

  try {
    await page.waitForSelector('nav, main, h1', { timeout: 15000 });
  } catch {
    const bodyHTML = await page.evaluate(() => document.body.innerHTML.slice(0, 300));
    console.error(`  SKIP ${route} (render failed). Body: ${bodyHTML}`);
    failed++;
    await page.close();
    continue;
  }

  // Remove prerender flag from output HTML so it doesn't affect real users
  await page.evaluate(() => { delete window.__PRERENDER__; });

  const html = await page.content();
  // Non-trailing-slash is the canonical URL form. Write /route to /route.html
  // so nginx `try_files $uri $uri.html` serves it without a 301 hop.
  const outPath =
    route === '/'
      ? join(DIST, 'index.html')
      : join(DIST, `${route.slice(1)}.html`);

  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, html, 'utf-8');
  console.log(`  OK ${route}`);

  await page.close();
}

await browser.close();
server.close();

if (failed > 0) {
  console.error(`Prerendering done with ${failed} failures.`);
  process.exit(1);
}
console.log('Prerendering complete.');
