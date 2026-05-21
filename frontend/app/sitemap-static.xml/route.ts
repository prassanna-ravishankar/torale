import { PUBLIC_ROUTES } from '../../lib/publicRoutes'
import { fetchPublicTasksList } from '../../lib/api/public'

// Route handler for /sitemap-static.xml — replaces the previous
// scripts/generate-sitemap.mjs build step. Backend continues to own
// /sitemap.xml (the index) and /sitemap-dynamic.xml (the DB-derived
// lastmod surface). The static sitemap enumerates every URL the
// frontend can serve to crawlers.
//
// Includes the top-N public tasks the same way generateStaticParams
// in app/(marketing)/tasks/[taskId]/page.tsx does, so crawlers and
// the static SSG cache agree on what's discoverable. The list is
// revalidated every 10 minutes to match the cadence of new public
// tasks being published.

export const revalidate = 600

const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'

const PUBLIC_TASK_LIMIT = 100

export async function GET() {
  const lastmod = new Date().toISOString().slice(0, 10)

  const enumeratedUrls = PUBLIC_ROUTES.map((route) => {
    const priority = (route.priority ?? 0.8).toFixed(1)
    return urlBlock(route.path, lastmod, priority)
  })

  // /explore — not in PUBLIC_ROUTES (was deliberately excluded in the
  // Vite era because it couldn't prerender). The SSG route now ships
  // real HTML, so add it here.
  enumeratedUrls.push(urlBlock('/explore', lastmod, '0.8'))

  // Top-N public tasks. Falls back to [] if the backend is unreachable
  // — the static sitemap still serves the enumerated routes, and the
  // backend dynamic sitemap covers the DB-truth case separately.
  const tasks = await fetchPublicTasksList({ limit: PUBLIC_TASK_LIMIT }).catch(
    () => [],
  )
  for (const task of tasks) {
    enumeratedUrls.push(urlBlock(`/tasks/${task.id}`, lastmod, '0.6'))
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${enumeratedUrls.join('\n')}
</urlset>
`

  return new Response(xml, {
    status: 200,
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  })
}

function urlBlock(path: string, lastmod: string, priority: string): string {
  return [
    '  <url>',
    `    <loc>${SITE_ORIGIN}${path}</loc>`,
    `    <lastmod>${lastmod}</lastmod>`,
    `    <priority>${priority}</priority>`,
    '  </url>',
  ].join('\n')
}
