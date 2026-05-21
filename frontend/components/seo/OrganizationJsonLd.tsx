// Server component — renders the site-wide Organization JSON-LD into every
// page via the root layout. Replaces the prerender-time origin probe with
// an env-var read since RSC runs server-side with no window.

const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'

// Inline-script escape contract — mirrors src/utils/jsonLd.ts. Backslashes
// first, then `<` so closing-tag literals can't form, then `/` to neutralize
// any `</script>` an entry could smuggle. U+2028/U+2029 codepoints are
// declared via fromCharCode so this file stays free of literal separators.
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
      dangerouslySetInnerHTML={{ __html: escapeForScriptTag(JSON.stringify(data)) }}
    />
  )
}

export default OrganizationJsonLd
