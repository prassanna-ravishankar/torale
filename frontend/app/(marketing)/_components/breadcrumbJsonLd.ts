// Server-side breadcrumb JSON-LD helper. Mirrors
// src/utils/structuredData.ts#generateBreadcrumbStructuredData but reads the
// origin from NEXT_PUBLIC_SITE_ORIGIN since we have no window context.

const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'

const LS = String.fromCharCode(0x2028)
const PS = String.fromCharCode(0x2029)

function escapeForScriptTag(json: string): string {
  return json
    .replace(/\\/g, '\\\\')
    .replace(/</g, '\\u003c')
    .replace(/\//g, '\\/')
    .split(LS)
    .join('\\u2028')
    .split(PS)
    .join('\\u2029')
}

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
  return escapeForScriptTag(JSON.stringify(data))
}
