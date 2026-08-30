# Authenticated owner deep links

- Production diagnosis on 2026-08-30 showed private task and execution requests
  returning 404 immediately before `/auth/me` returned 200 on cold notification
  deep links. Dashboard navigation worked because auth had already settled.
- The cause was a mutable, module-global API client whose Clerk token getter was
  installed by a post-render effect. Route components could fetch before that
  effect ran, turning an owner request into an anonymous public-access check.
- Auth now owns the API client and exposes an explicit `loading`,
  `authenticated`, `unauthenticated`, or `error` state. `AuthReadyBoundary`
  keeps the entire authenticated route subtree unmounted until the backend user
  is resolved; individual pages must not recreate auth-timing guards.
- `AuthUser.databaseId` is the database UUID used for ownership and analytics;
  `AuthUser.clerkId` is the Clerk identity used for Clerk/admin comparisons.
  Do not collapse these back into a generic `id`.
- Authenticated `/api/v1/tasks/{id}` and its execution/notification routes
  require credentials. Anonymous reads use `/api/v1/public/*`, whose response
  is always scrubbed regardless of incidental Authorization headers.
- API failures use `ApiError.status`: only a real 404 should render “watch not
  found.” Auth, authorization, network, and server failures have distinct retry
  or sign-in states.
