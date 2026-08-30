# Authenticated owner deep links

- Private owner routes can render before `AuthedApiBootstrap` has installed the
  Clerk token getter on the shared API client.
- A request made during that window is anonymous. Private task endpoints return
  404 by design, so the resulting UI looks like the watch was deleted even
  though it exists.
- This is most visible on cold notification-email deep links. Navigation from
  the dashboard works because auth has already settled.
- Owner pages must wait for the backend `user` from `AuthContext`, not merely
  Clerk's `isLoaded`, before mounting data-fetching components. The dashboard
  follows this pattern already.
- Production diagnosis on 2026-08-30 showed task and executions requests
  returning 404 immediately before `/auth/me` returned 200 for the same page
  load.
