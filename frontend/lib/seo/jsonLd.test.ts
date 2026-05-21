/**
 * Tests for the JSON-LD inline-script serializer. Round-trip every output
 * through JSON.parse to prove the helper preserves JSON validity even on
 * adversarial input, then assert no `</script>` can survive in the output.
 *
 * Run with: npx tsx lib/seo/jsonLd.test.ts
 *
 * Background: review notif-20f6866d / H1. The previous helper escaped all
 * backslashes after JSON.stringify, mangling JSON's own escape sequences.
 */

import { escapeForScriptTag, jsonLdHtml } from './jsonLd'

const GREEN = '\x1b[92m'
const RED = '\x1b[91m'
const RESET = '\x1b[0m'

let failed = 0

function assert(cond: boolean, msg: string): void {
  if (cond) {
    console.log(`${GREEN}OK${RESET}   ${msg}`)
  } else {
    console.log(`${RED}FAIL${RESET} ${msg}`)
    failed++
  }
}

function roundTrip(label: string, input: unknown): void {
  const escaped = jsonLdHtml(input)
  let parsed: unknown
  try {
    parsed = JSON.parse(escaped)
  } catch (err) {
    assert(false, `${label}: output did not parse — ${(err as Error).message}: ${escaped}`)
    return
  }
  assert(
    JSON.stringify(parsed) === JSON.stringify(input),
    `${label}: round-trip equality`,
  )
  assert(
    !/<\/script/i.test(escaped),
    `${label}: no </script literal in output`,
  )
}

// Simple values
roundTrip('plain object', { a: 1, b: 'hello' })
roundTrip('empty string field', { a: '' })

// Backslash hazards — the bug we're fixing
roundTrip('field with single backslash', { x: 'a\\b' })
roundTrip('field with json-significant chars', {
  q: 'quote " slash / backslash \\',
})
roundTrip('newline + tab', { x: 'line1\nline2\tend' })

// HTML injection attempts
roundTrip('embedded </script>', {
  body: 'before </script><img src=x onerror=alert(1)> after',
})
roundTrip('mixed case </SCRIPT/>', {
  body: '</SCRIPT/><script>evil()</script>',
})
roundTrip('html comment <!--', { body: 'a <!-- b --> c' })

// Unicode separator hazards
roundTrip('U+2028', { line: 'before after' })
roundTrip('U+2029', { line: 'before after' })

// Verify the actual escape happens for the dangerous chars
{
  const out = jsonLdHtml({ x: '<script>' })
  assert(out.includes('\\u003c'), '`<` is escaped to \\u003c in output')
  assert(!out.includes('<script>'), 'no literal <script> in output')
}

{
  const out = jsonLdHtml({ x: 'a b' })
  assert(out.includes('\\u2028'), 'U+2028 is escaped in output')
}

// Empty + nested shapes that the real codebase emits
roundTrip('schema.org Article-like', {
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline: 'Headline with </script> attempt and \\ backslash',
  description: 'Multi\nline\tcontent',
  author: { '@type': 'Organization', name: 'webwhen' },
})

if (failed > 0) {
  console.log(`\n${RED}${failed} test(s) failed${RESET}`)
  process.exit(1)
} else {
  console.log(`\n${GREEN}All jsonLd tests passed${RESET}`)
}

// Reference escapeForScriptTag so tsc doesn't drop the symbol from the
// emitted output if we add tests against it directly later.
void escapeForScriptTag
