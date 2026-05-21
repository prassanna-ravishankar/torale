import { PUBLIC_ROUTES } from '../../lib/publicRoutes'

// Route handler for /sitemap-static.xml.
//
// Ownership contract (reconciled per review notif-fb212083 / B3):
//   - Static (this file) owns enumerated marketing articles whose content
//     is NOT DB-derived: /compare/[tool], /use-cases/[usecase],
//     /concepts/[concept], /terms, /privacy. Source: lib/publicRoutes.ts.
//   - Backend `/sitemap-dynamic.xml` owns DB-derived URLs (`/`, `/changelog`,
//     `/explore`, public `/tasks/<uuid>`) with proper lastmod from the
//     DB. See backend/src/webwhen/api/routers/sitemap.py.
//
// Disjoint sets — no URL appears in both children of the sitemap index.
// Previously /, /changelog, /explore, and task URLs appeared in both with
// conflicting lastmod semantics; crawlers had to pick. Fixed here.

const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'

// Routes that backend dynamic owns. Filter these out of the static export.
const DYNAMIC_OWNED = new Set<string>(['/', '/changelog'])

// Revalidate the cached response once per day. Combined with the
// Cache-Control header below, this lets Next.js's ISR + the CDN serve a
// stable sitemap between origin hits instead of regenerating on every
// crawler request.
export const revalidate = 86400

// Compute lastmod ONCE at module load time, not per-request. Using
// `new Date()` inside GET() incorrectly signals to crawlers that every URL
// was modified at the moment of the request — a regression flagged in PR
// review PRRT_kwDON2GAYM6Dr-YA. Trade-off: a long-running container will
// drift from "today" until it's restarted/redeployed, but ISR refreshes
// this module's response every `revalidate` seconds so the worst case is
// roughly one day of staleness. Acceptable for a marketing sitemap.
const LASTMOD = new Date().toISOString().slice(0, 10)

export function GET() {
  const urls = PUBLIC_ROUTES.filter(
    (route) => !DYNAMIC_OWNED.has(route.path),
  ).map((route) => {
    const priority = (route.priority ?? 0.8).toFixed(1)
    return [
      '  <url>',
      `    <loc>${SITE_ORIGIN}${route.path}</loc>`,
      `    <lastmod>${LASTMOD}</lastmod>`,
      `    <priority>${priority}</priority>`,
      '  </url>',
    ].join('\n')
  })

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join('\n')}
</urlset>
`

  return new Response(xml, {
    status: 200,
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      // Match the ISR window so CDN edges can cache between origin hits.
      'Cache-Control': 'public, max-age=86400, s-maxage=86400',
    },
  })
}
