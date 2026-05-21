import { getSiteOrigin } from '../../lib/api/origin'
import { JsonLd } from '../../lib/seo/jsonLdComponent'
import { SCHEMA_CONTEXT } from '../../lib/seo/jsonLd'

// Site-wide Organization JSON-LD mounted by the root layout. Data is fully
// static; the JSON-LD payload is materialized once at module load rather
// than on every page render.
const ORG_DATA = (() => {
  const origin = getSiteOrigin()
  return {
    '@context': SCHEMA_CONTEXT,
    '@type': 'Organization',
    name: 'webwhen',
    url: origin,
    logo: `${origin}/brand/webwhen-mark.svg`,
    description:
      'The agent that waits for the web. Tell webwhen what to watch for in plain English; it sits with the question and tells you the moment your condition is met.',
    foundingDate: '2025',
  }
})()

export function OrganizationJsonLd() {
  return <JsonLd data={ORG_DATA} />
}

export default OrganizationJsonLd
