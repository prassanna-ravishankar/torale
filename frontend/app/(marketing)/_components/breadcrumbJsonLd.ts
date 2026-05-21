import { siteUrl } from '../../../lib/api/origin'
import { jsonLdHtml, SCHEMA_CONTEXT } from '../../../lib/seo/jsonLd'

export interface BreadcrumbItem {
  name: string
  path: string
}

export function breadcrumbJsonLd(items: BreadcrumbItem[]): string {
  const data = {
    '@context': SCHEMA_CONTEXT,
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, idx) => ({
      '@type': 'ListItem',
      position: idx + 1,
      name: item.name,
      item: siteUrl(item.path),
    })),
  }
  return jsonLdHtml(data)
}
