// Shared safe-serializer for inline <script type="application/ld+json"> tags.
//
// Contract: produce a string that is BOTH valid JSON when extracted from the
// script element AND safe to embed inside an HTML <script> body.
//
// Background on the bug we used to ship (review notif-20f6866d / H1):
//   The first iteration of this helper ran `.replace(/\\/g, '\\\\')` and
//   `.replace(/\//g, '\\/')` AFTER `JSON.stringify`. That breaks JSON's own
//   escape sequences — `JSON.stringify({x: '"'})` produces `{"x":"\""}`, and
//   blindly doubling the backslash turns it into `{"x":"\\""}` which is no
//   longer parseable. Same for `\n`, `\t`, `\/`, etc. The output rendered
//   nonsense to Googlebot.
//
// What's actually dangerous when embedding JSON in <script>:
//   - `</script>` (or `</SCRIPT...`) closes the script element. Killing `<`
//     prevents the close tag from ever forming. This is the load-bearing
//     fix — everything else is incidental.
//   - `<!--` opens an HTML comment which has special parser handling
//     inside <script> on legacy browsers. Killing `<` covers this too.
//   - U+2028 (LINE SEPARATOR) and U+2029 (PARAGRAPH SEPARATOR) terminate
//     JavaScript string literals on a few historical parsers. Escape to
//     their `\uXXXX` form. These code points are valid Unicode in JSON
//     strings, so re-encoding them to JSON `\u` escapes keeps validity.
//
// What is NOT dangerous and MUST NOT be touched:
//   - `\` — JSON owns this character. Don't double-escape.
//   - `/` — has no HTML semantics outside `</script>`. Without a preceding
//     `<` it cannot start a close tag.
//   - `"`, `&`, `>` — fine inside <script> bodies. Browsers don't HTML-decode
//     script content.

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
