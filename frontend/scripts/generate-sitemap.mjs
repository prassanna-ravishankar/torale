import { writeFileSync, existsSync, unlinkSync } from 'node:fs';
import { join } from 'node:path';
import { build } from 'esbuild';

// publicRoutes.ts lives in TS and imports from other TS files. Bundle it to a
// single in-memory ESM module via esbuild (already a transitive dep of vite),
// then dynamic-import the bundle to get PUBLIC_ROUTES. No separate tsconfig,
// no ts-node/tsx runtime.
const PROJECT_ROOT = join(import.meta.dirname, '..');
const DIST = join(PROJECT_ROOT, 'dist');
const SOURCE = join(PROJECT_ROOT, 'src/data/publicRoutes.ts');
const SITE_ORIGIN = 'https://torale.ai';

const bundle = await build({
  entryPoints: [SOURCE],
  bundle: true,
  format: 'esm',
  platform: 'node',
  target: 'node20',
  write: false,
  external: [],
});
const code = bundle.outputFiles[0].text;
const dataUrl = `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`;
const { PUBLIC_ROUTES } = await import(dataUrl);

const now = new Date().toISOString().slice(0, 10);
const urls = PUBLIC_ROUTES.map((route) => {
  const priority = route.priority ?? 0.8;
  return [
    '  <url>',
    `    <loc>${SITE_ORIGIN}${route.path}</loc>`,
    `    <lastmod>${now}</lastmod>`,
    `    <priority>${priority.toFixed(1)}</priority>`,
    '  </url>',
  ].join('\n');
}).join('\n');

const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`;

const outPath = join(DIST, 'sitemap.xml');
writeFileSync(outPath, xml, 'utf-8');
console.log(`Wrote ${PUBLIC_ROUTES.length} routes to ${outPath}`);

// Remove any stale sitemap-index.xml vite may have copied from public/.
const staleIndex = join(DIST, 'sitemap-index.xml');
if (existsSync(staleIndex)) {
  unlinkSync(staleIndex);
  console.log(`Removed stale ${staleIndex}`);
}
