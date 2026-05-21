/**
 * Backend origin for server-side data fetching from RSC routes.
 *
 * Resolves to NEXT_PUBLIC_API_BASE_URL (read at request/build time on the
 * server) and falls back to the production API origin so that static
 * generation never crashes in a stripped CI/build environment. Local dev
 * should set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 in .env.
 */
export function getApiOrigin(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL
  if (fromEnv && fromEnv.length > 0) return fromEnv.replace(/\/+$/, '')
  return 'https://api.webwhen.ai'
}

/** Build a fully-qualified API URL by joining `path` onto the origin. */
export function apiUrl(path: string): string {
  const origin = getApiOrigin()
  const suffix = path.startsWith('/') ? path : `/${path}`
  return `${origin}${suffix}`
}
