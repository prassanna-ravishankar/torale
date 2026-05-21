// Server-side breadcrumb JSON-LD helper. Delegates serialization to the
// shared lib/seo/jsonLd helper so the inline-script escape contract has
// exactly one home.
import { jsonLdHtml } from '../../../lib/seo/jsonLd'

const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'

export interface BreadcrumbItem {
  name: string
  path: string
}

export function breadcrumbJsonLd(items: BreadcrumbItem[]): string {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, idx) => ({
      '@type': 'ListItem',
      position: idx + 1,
      name: item.name,
      item: `${SITE_ORIGIN}${item.path}`,
    })),
  }
  return jsonLdHtml(data)
}
