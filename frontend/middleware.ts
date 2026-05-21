import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

// Protected paths require an authenticated Clerk session. Marketing routes,
// /tasks/[id], /explore, /sign-in, /sign-up, /waitlist, and /  stay public so
// SSG/ISR can render anonymous HTML for crawlers.
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
  matcher: [
    // Skip Next.js internals and common static assets.
    '/((?!_next/static|_next/image|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|css|js|map|txt|xml|webmanifest|woff2?)$).*)',
    // Always run for API routes.
    '/(api|trpc)(.*)',
  ],
}
