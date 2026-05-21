// Shared safe-serializer for inline <script type="application/ld+json"> tags.
// Centralizes the escape contract previously duplicated across
// components/seo/OrganizationJsonLd.tsx and app/(marketing)/_components/
// breadcrumbJsonLd.ts.
//
// Why the escape: our CSP allows 'unsafe-inline' on script-src, so any
// user-controlled field that lands inside a JSON-LD payload can smuggle a
// `</script>` literal and end the script context. Defense pattern (in this
// order):
//   1. `\\` first so subsequent escapes don't double-escape.
//   2. `<` so `</script>` and `<!--` can never form.
//   3. `/` so the engine can't reconstruct a closing tag via concat tricks.
//   4. U+2028 / U+2029 (LS / PS) which terminate JS string literals on some
//      legacy parsers. Declared via fromCharCode so this file stays free of
//      literal separators.

const LS = String.fromCharCode(0x2028)
const PS = String.fromCharCode(0x2029)

export function escapeForScriptTag(json: string): string {
  return json
    .replace(/\\/g, '\\\\')
    .replace(/</g, '\\u003c')
    .replace(/\//g, '\\/')
    .split(LS)
    .join('\\u2028')
    .split(PS)
    .join('\\u2029')
}

// Convenience: takes the object to be serialized, returns the safe inline
// HTML payload ready for dangerouslySetInnerHTML.
export function jsonLdHtml(data: unknown): string {
  return escapeForScriptTag(JSON.stringify(data))
}
