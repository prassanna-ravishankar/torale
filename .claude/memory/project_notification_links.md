---
name: notification-owner-links
description: Notification CTAs must use the authenticated owner route, not the public watch route
type: project
---

Notification emails are sent to a watch owner and must link to
`/dashboard/tasks/:id`. The `/tasks/:id` route is an anonymous, statically
rendered public page and intentionally returns 404 when `tasks.is_public` is
false.

Legacy notification links used `/watches/:id`. Keep that redirect pointed at
`/dashboard/tasks/:id` so old emails remain usable. The backend-generated
`task_url` and any explicit links in the live Novu templates must also resolve
to that authenticated owner route.
