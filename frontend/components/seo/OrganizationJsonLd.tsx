// Server component — renders the site-wide Organization JSON-LD into every
// page via the root layout.
import { jsonLdHtml } from '../../lib/seo/jsonLd'

const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'

export function OrganizationJsonLd() {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'webwhen',
    url: SITE_ORIGIN,
    logo: `${SITE_ORIGIN}/brand/webwhen-mark.svg`,
    description:
      'The agent that waits for the web. Tell webwhen what to watch for in plain English; it sits with the question and tells you the moment your condition is met.',
    foundingDate: '2025',
  }
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: jsonLdHtml(data) }}
    />
  )
}

export default OrganizationJsonLd
