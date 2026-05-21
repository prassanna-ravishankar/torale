import { PUBLIC_ROUTES } from '../../lib/publicRoutes'

// Route handler for /sitemap-static.xml — replaces the previous
// scripts/generate-sitemap.mjs build step. Backend continues to own
// /sitemap.xml (the index), /sitemap-dynamic.xml, and /changelog.xml.
//
// Lastmod is the build/request time. The plan retires the
// `git log`-based lookup; backend's dynamic sitemap covers the
// content-change cadence for /changelog and /.

const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'

export function GET() {
  const lastmod = new Date().toISOString().slice(0, 10)
  const urls = PUBLIC_ROUTES.map((route) => {
    const priority = (route.priority ?? 0.8).toFixed(1)
    return [
      '  <url>',
      `    <loc>${SITE_ORIGIN}${route.path}</loc>`,
      `    <lastmod>${lastmod}</lastmod>`,
      `    <priority>${priority}</priority>`,
      '  </url>',
    ].join('\n')
  }).join('\n')

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`

  return new Response(xml, {
    status: 200,
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  })
}
