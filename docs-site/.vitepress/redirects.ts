/**
 * Source of truth for docs.torale.ai redirects. The generated
 * nginx-redirects.conf is derived from this — edit here, never the conf.
 * Use 301 for deprecated pages with a sensible replacement, 410 for
 * intentionally-removed pages with no equivalent.
 */

export type ExactRedirect =
  | { kind: 'exact'; from: string; to: string; code: 301 }
  | { kind: 'exact'; from: string; code: 410 };

export type PrefixRedirect =
  | { kind: 'prefix'; prefix: string; to: string; code: 301 }
  | { kind: 'prefix'; prefix: string; code: 410 };

export type RedirectRule = ExactRedirect | PrefixRedirect;

export const REDIRECTS: RedirectRule[] = [
  { kind: 'exact', from: '/architecture/temporal-workflows', to: '/architecture/task-state-machine', code: 301 },
  { kind: 'exact', from: '/architecture/state-tracking', to: '/architecture/task-state-machine', code: 301 },
  { kind: 'exact', from: '/architecture/overview', to: '/api/overview', code: 301 },
  { kind: 'exact', from: '/architecture/executors', to: '/sdk/examples', code: 301 },
  { kind: 'exact', from: '/architecture/database-schema', code: 410 },

  { kind: 'exact', from: '/getting-started/web-dashboard', to: '/getting-started', code: 301 },
  { kind: 'exact', from: '/getting-started/self-hosted', code: 410 },

  { kind: 'prefix', prefix: '/deployment/', code: 410 },
  { kind: 'prefix', prefix: '/self-hosted/', code: 410 },
  { kind: 'prefix', prefix: '/contributing/', code: 410 },
  { kind: 'prefix', prefix: '/cli/', to: '/sdk/quickstart', code: 301 },
];
