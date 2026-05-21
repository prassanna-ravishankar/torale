import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
  // A package-lock.json exists in /Users/prass/ — pin the tracing root to
  // this frontend so the standalone build doesn't try to bundle unrelated
  // workspace files.
  outputFileTracingRoot: __dirname,
  // SEO contract from frontend/nginx.conf:
  // - non-trailing-slash canonical site-wide (Next.js default is false; explicit here as a contract)
  // - Vite tree is still the source of truth until commit 6 lands; this config
  //   is inert against `npm run build` (which still runs vite) — Next.js scripts
  //   under `next-*` opt in explicitly.
  trailingSlash: false,
  // The Vite tree under src/ uses Vite-only APIs (import.meta.env, window
  // globals) that don't typecheck under Next's strict tsconfig. tsconfig.json
  // already excludes src/**; ignoreBuildErrors mirrors that for the bundler's
  // own type-check pass. The Vite tree continues to typecheck via
  // `tsc -p tsconfig.vite.json` until commit 6 deletes it.
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Marketing routes that previously prerendered to <route>.html now live
  // under app/(marketing). Auth tree lives under app/(app) and app/(auth).
  // No experimental flags needed for the App Router on next@15.
}

export default nextConfig
