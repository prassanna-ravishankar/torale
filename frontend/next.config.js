import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// CSP ported from frontend/nginx.conf:42. The Next.js-specific additions
// over the nginx version:
//   - script-src 'unsafe-inline' for Next's inline framework chunks
//     (App Router emits inline RSC payload + flight encoder bootstraps).
//     Nonces would be cleaner but require an edge middleware nonce mint
//     pass per request — defer; current bundle is the same trust surface
//     as the prior nginx-served HTML.
//   - script-src 'unsafe-eval' is NOT added. Next.js production builds
//     don't need it; if a future client lib needs eval, fix the lib.
const CSP = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' https://*.clerk.accounts.dev https://*.clerk.com https://clerk.webwhen.ai https://challenges.cloudflare.com https://static.cloudflareinsights.com https://eu.posthog.com https://eu.i.posthog.com https://eu-assets.i.posthog.com",
  "worker-src 'self' blob:",
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self'",
  "img-src 'self' data: blob: https://*.clerk.com https://*.webwhen.ai",
  "connect-src 'self' https://*.webwhen.ai https://*.clerk.accounts.dev https://*.clerk.com https://api.clerk.com https://eu.posthog.com https://eu.i.posthog.com https://eu-assets.i.posthog.com",
  "frame-src 'self' https://*.clerk.accounts.dev https://*.clerk.com https://clerk.webwhen.ai https://challenges.cloudflare.com",
  "frame-ancestors 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join('; ')

// Security headers — ported one-for-one from nginx more_set_headers block.
// nginx's headers-more was needed because `add_header` was silently dropped
// in child location blocks; Next.js header inheritance is flat so the
// gotcha doesn't apply.
const SECURITY_HEADERS = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains; preload' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'geolocation=(), microphone=(), camera=()' },
  { key: 'Content-Security-Policy', value: CSP },
]

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
  // A package-lock.json exists in /Users/prass/ — pin the tracing root to
  // this frontend so the standalone build doesn't try to bundle unrelated
  // workspace files.
  outputFileTracingRoot: __dirname,
  // Non-trailing-slash canonical site-wide. Match nginx's
  // `rewrite ^/(.+)/$ /$1 permanent;` (which Next.js handles natively when
  // this flag is false — the default — but explicit here as a contract).
  trailingSlash: false,
  async headers() {
    return [
      {
        // Every response gets the security headers. nginx applied these at
        // server scope; here we apply via wildcard so the inheritance gap
        // that bit production in #259 simply can't exist.
        source: '/:path*',
        headers: SECURITY_HEADERS,
      },
      {
        // Hashed static assets are content-addressed; immutable cache.
        // Matches nginx `location ~* \.(js|css|png|...)$ { expires 1y; }`.
        source: '/_next/static/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
    ]
  },
  async redirects() {
    // Ported one-for-one from nginx.conf rewrite directives:
    //   ^/(.+)/$ /$1            — handled natively by trailingSlash: false.
    //   ^/index\.html$ /        — duplicate-homepage trap (B2).
    //   ^/index$ /              — canonical-stripped form of /index.html.
    //   ^/(?!index\.html$|404\.html$)(.+)\.html$ /$1 — general .html strip.
    //
    // Plus app-level redirects from src/App.tsx:
    //   /watches/:taskId → /tasks/:taskId (legacy URL shape).
    //   /settings → /settings/notifications (bare /settings has no UI).
    return [
      { source: '/index.html', destination: '/', permanent: true },
      { source: '/index', destination: '/', permanent: true },
      { source: '/:path*.html', destination: '/:path*', permanent: true },
      { source: '/watches/:taskId', destination: '/tasks/:taskId', permanent: true },
      { source: '/settings', destination: '/settings/notifications', permanent: true },
      // Retired sitemap children (collapsed into the unified /sitemap.xml).
      // Googlebot and other crawlers may have the old sitemap-index entries
      // cached pointing at /sitemap-static.xml + /sitemap-dynamic.xml; 308
      // them to the canonical so the next crawl re-anchors cleanly.
      { source: '/sitemap-static.xml', destination: '/sitemap.xml', permanent: true },
      { source: '/sitemap-dynamic.xml', destination: '/sitemap.xml', permanent: true },
    ]
  },
}

export default nextConfig
