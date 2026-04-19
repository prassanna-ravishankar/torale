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

// Batch git history lookup: one `git log` call produces dates for every
// tracked source file at once. Per-file execFile would scale O(routes).
// Use commit dates, not mtimes — CI fresh clones otherwise mark every
// page as changed on every deploy.
function loadCommitDates(sources) {
  if (sources.length === 0) return new Map();
  try {
    const out = execFileSync(
      'git',
      ['log', '--name-only', '--format=__COMMIT__%cI', '--', ...sources],
      { cwd: PROJECT_ROOT, encoding: 'utf-8' },
    );
    // git emits paths relative to the repo root, which may differ from our
    // PROJECT_ROOT-relative input. Index by path basename+suffix so both
    // "src/data/concepts.ts" and "frontend/src/data/concepts.ts" resolve.
    const dates = new Map();
    let currentDate = null;
    for (const line of out.split('\n')) {
      if (line.startsWith('__COMMIT__')) {
        currentDate = line.slice('__COMMIT__'.length, '__COMMIT__'.length + 10);
      } else if (line && currentDate) {
        // Match on suffix so the input key ("src/data/x.ts") finds entries
        // that git reports with a package prefix ("frontend/src/data/x.ts").
        for (const source of sources) {
          if ((line === source || line.endsWith(`/${source}`)) && !dates.has(source)) {
            dates.set(source, currentDate);
          }
        }
      }
    }
    return dates;
  } catch {
    return new Map();
  }
}

const allSources = [
  ...Object.values(STATIC_SOURCES),
  ...DYNAMIC_SOURCES.map((d) => d.file),
];
const commitDates = loadCommitDates(allSources);

function lastmodFor(path) {
  const rel = sourceFor(path);
  return (rel && commitDates.get(rel)) || buildDate;
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

const outPath = join(DIST, 'sitemap-static.xml');
writeFileSync(outPath, xml, 'utf-8');
console.log(`Wrote ${PUBLIC_ROUTES.length} routes to ${outPath}`);

// Remove stale sitemap files vite may have copied from public/. The backend
// owns /sitemap.xml (sitemap index) and /sitemap-dynamic.xml at the gateway.
for (const stale of ['sitemap.xml', 'sitemap-index.xml', 'sitemap-dynamic.xml']) {
  const path = join(DIST, stale);
  if (existsSync(path)) {
    unlinkSync(path);
    console.log(`Removed stale ${path}`);
  }
}
