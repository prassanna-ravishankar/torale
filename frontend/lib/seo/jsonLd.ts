// Shared safe-serializer for inline <script type="application/ld+json"> tags.
//
// Contract: produce a string that is BOTH valid JSON when extracted from the
// script element AND safe to embed inside an HTML <script> body.
//
// Dangerous in script bodies (must escape):
//   - close-tag-like sequences: escape every `<` to its JSON < form so
//     `</script>` and `<!--` cannot form.
//   - LINE SEPARATOR / PARAGRAPH SEPARATOR (U+2028 / U+2029) terminate
//     JavaScript string literals on a few historical parsers. Re-encode to
//     their JSON \u escapes (still valid JSON).
//
// MUST NOT be touched (regression hazard — see lib/seo/jsonLd.test.ts):
//   - backslash: JSON owns it; doubling mangles \", \n, etc.
//   - forward slash, ", &, > — no special meaning inside <script> bodies.

const LS = String.fromCharCode(0x2028)
const PS = String.fromCharCode(0x2029)

export function escapeForScriptTag(json: string): string {
  return json
    .replace(/</g, '\\u003c')
    .split(LS)
    .join('\\u2028')
    .split(PS)
    .join('\\u2029')
}

export function jsonLdHtml(data: unknown): string {
  return escapeForScriptTag(JSON.stringify(data))
}

export const SCHEMA_CONTEXT = 'https://schema.org'
