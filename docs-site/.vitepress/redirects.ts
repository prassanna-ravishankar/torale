/**
 * Redirect map for docs.torale.ai. Source of truth for the generated
 * nginx-redirects.conf consumed by the docs nginx server.
 *
 * Add a 301 for deprecated pages that have a sensible live replacement.
 * Use 410 for pages that have been intentionally and permanently removed
 * with no equivalent (signals "gone" to Google, not "moved").
 */

export interface ExactRedirect {
  kind: 'exact';
  /** Path including leading slash, e.g. "/architecture/overview". */
  from: string;
  /** Path of the redirect target (301 only). */
  to: string;
  code: 301;
}

export interface GoneRedirect {
  kind: 'exact';
  from: string;
  code: 410;
}

export interface PrefixRedirect {
  kind: 'prefix';
  /** Prefix with leading slash, matches anything under it. */
  prefix: string;
  /** Path of the redirect target (301 only). */
  to?: string;
  code: 301 | 410;
}

export type RedirectRule = ExactRedirect | GoneRedirect | PrefixRedirect;

export const REDIRECTS: RedirectRule[] = [
  // Architecture docs trimmed during Temporal -> APScheduler migration.
  // Some pages have been reinstated (grounded-search, task-state-machine);
  // the rest point at the closest current equivalent.
  { kind: 'exact', from: '/architecture/temporal-workflows', to: '/architecture/task-state-machine', code: 301 },
  { kind: 'exact', from: '/architecture/state-tracking', to: '/architecture/task-state-machine', code: 301 },
  { kind: 'exact', from: '/architecture/overview', to: '/api/overview', code: 301 },
  { kind: 'exact', from: '/architecture/executors', to: '/sdk/examples', code: 301 },
  { kind: 'exact', from: '/architecture/database-schema', code: 410 },

  // Getting-started sub-pages merged into /getting-started/ index.
  { kind: 'exact', from: '/getting-started/web-dashboard', to: '/getting-started/', code: 301 },
  { kind: 'exact', from: '/getting-started/self-hosted', code: 410 },

  // Entire sections removed when docs were trimmed to developer docs.
  { kind: 'prefix', prefix: '/deployment/', code: 410 },
  { kind: 'prefix', prefix: '/self-hosted/', code: 410 },
  { kind: 'prefix', prefix: '/contributing/', code: 410 },
  { kind: 'prefix', prefix: '/cli/', to: '/sdk/quickstart', code: 301 },
];
