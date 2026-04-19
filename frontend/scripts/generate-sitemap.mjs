import { writeFileSync, existsSync, unlinkSync } from 'node:fs';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { loadTsModule } from './_lib/load-ts.mjs';

const PROJECT_ROOT = join(import.meta.dirname, '..');
const DIST = join(PROJECT_ROOT, 'dist');
const SITE_ORIGIN = 'https://torale.ai';

const { PUBLIC_ROUTES } = await loadTsModule(join(PROJECT_ROOT, 'src/data/publicRoutes.ts'));

// Map each route to the source file whose mtime best represents "when this
// route's content last changed". Used for <lastmod> so Google doesn't treat
// every deploy as a content change on every page.
const STATIC_SOURCES = {
  '/': 'src/components/Landing.tsx',
  '/changelog': 'src/components/Changelog.tsx',
  '/explore': 'src/pages/Explore.tsx',
  '/terms': 'src/pages/TermsOfService.tsx',
  '/privacy': 'src/pages/PrivacyPolicy.tsx',
};
const DYNAMIC_SOURCES = [
  { prefix: '/compare/', file: 'src/data/competitors.ts' },
  { prefix: '/use-cases/', file: 'src/data/useCases.ts' },
  { prefix: '/concepts/', file: 'src/data/concepts.ts' },
];

const buildDate = new Date().toISOString().slice(0, 10);

function sourceFor(path) {
  if (STATIC_SOURCES[path]) return STATIC_SOURCES[path];
  const dyn = DYNAMIC_SOURCES.find((d) => path.startsWith(d.prefix));
  return dyn?.file;
}

function lastmodFor(path) {
  const rel = sourceFor(path);
  if (!rel) return buildDate;
  // Git commit date, not mtime: CI fresh clones set mtimes to checkout time,
  // which would otherwise mark every page as changed on every deploy.
  try {
    const iso = execFileSync('git', ['log', '-1', '--format=%cI', '--', rel], {
      cwd: PROJECT_ROOT,
      encoding: 'utf-8',
    }).trim();
    return iso ? iso.slice(0, 10) : buildDate;
  } catch {
    return buildDate;
  }
}

const urls = PUBLIC_ROUTES.map((route) => {
  const priority = route.priority ?? 0.8;
  return [
    '  <url>',
    `    <loc>${SITE_ORIGIN}${route.path}</loc>`,
    `    <lastmod>${lastmodFor(route.path)}</lastmod>`,
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
