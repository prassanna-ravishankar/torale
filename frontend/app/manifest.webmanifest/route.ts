// /manifest.webmanifest — intentionally 404. Some browsers/extensions probe
// this path; serving a real manifest is out of scope for this product.
export function GET() {
  return new Response(null, { status: 404 })
}
