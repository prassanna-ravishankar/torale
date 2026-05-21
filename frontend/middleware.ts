import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

// Only the authenticated app and the Clerk auth flows go through middleware
// — marketing routes (/, /explore, /tasks/[id], /compare/*, /use-cases/*,
// /concepts/*, /changelog, /terms, /privacy) intentionally bypass it.
//
// Rationale:
//   1. clerkMiddleware() requires CLERK_PUBLISHABLE_KEY at module init; if
//      the env var is missing every request 500s. Scoping the matcher to
//      auth-relevant paths means a missing key only breaks auth flows, not
//      the whole site.
//   2. Avoids paying the per-request Clerk overhead on routes that don't
//      need it. Matches the structural PR #337 invariant (marketing
//      surfaces never touch Clerk).
//   3. Sitemap/manifest/static-asset routes bypass naturally because they
//      don't match the matcher prefixes below.
const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/settings(.*)',
  '/admin(.*)',
  '/welcome(.*)',
])

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect()
  }
})

export const config = {
  // Run middleware only for the authenticated app shell and Clerk's own
  // sign-in/sign-up/waitlist surfaces. Everything else (marketing, RSC
  // static pages, _next/*, /sitemap.xml, /manifest.webmanifest,
  // /favicon.ico) is naturally unmatched.
  matcher: [
    '/dashboard/:path*',
    '/dashboard',
    '/settings/:path*',
    '/settings',
    '/admin/:path*',
    '/admin',
    '/welcome',
    '/sign-in/:path*',
    '/sign-up/:path*',
    '/waitlist',
  ],
}
