/**
 * Sanitize pathname to prevent PII leaks (e.g., usernames in URLs).
 * Replaces dynamic segments with placeholders for analytics tracking.
 */
export function sanitizePath(path: string): string {
  return path
    .replace(/\/t\/[^/]+\/[^/]+/, '/t/[username]/[slug]')
    .replace(/\/tasks\/[a-f0-9-]{36}/, '/tasks/[id]')
}
