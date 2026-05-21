import { jsonLdHtml } from './jsonLd'

/**
 * Inline JSON-LD <script> tag with the safe-serializer applied. Replaces
 * the dangerouslySetInnerHTML+jsonLdHtml pattern at every emit site so the
 * escape contract has one observation point.
 */
export function JsonLd({ data }: { data: unknown }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: jsonLdHtml(data) }}
    />
  )
}
