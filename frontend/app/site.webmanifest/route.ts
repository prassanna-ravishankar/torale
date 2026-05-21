// /site.webmanifest — intentionally 404. See manifest.webmanifest peer.
export function GET() {
  return new Response(null, { status: 404 })
}
