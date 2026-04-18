/**
 * Single source of truth for public (SEO-relevant) routes on torale.ai.
 *
 * Consumed by:
 *   - scripts/prerender.mjs   — knows which routes to prerender
 *   - scripts/generate-sitemap.mjs — emits sitemap.xml
 *   - DynamicMeta component   — rendering per-page meta
 *
 * Adding a new public page means: add a data entry (if dynamic) or push
 * to STATIC_ROUTES here. Nothing else to wire up.
 */

import { COMPETITORS } from './competitors';
import { USE_CASES } from './useCases';
import { CONCEPTS } from './concepts';

export interface PublicRoute {
  path: string;
  title: string;
  description: string;
  /** Relative priority in sitemap; 0.0–1.0. Defaults to 0.8 if omitted. */
  priority?: number;
  ogType?: 'website' | 'article';
}

/** Routes with no dynamic parameter, defined inline. */
const STATIC_ROUTES: PublicRoute[] = [
  {
    path: '/',
    title: 'Torale - Monitor the Web, Get Notified When It Matters',
    description:
      'Automate web monitoring with AI-powered conditional alerts. Track product launches, stock availability, event announcements, and more. Set it and forget it.',
    priority: 1.0,
  },
  {
    path: '/changelog',
    title: 'Changelog - Torale Product Updates & Features',
    description:
      "Track every update to Torale's AI-powered web monitoring platform. New features, improvements, and fixes shipped weekly.",
    priority: 0.7,
  },
  {
    path: '/explore',
    title: 'Explore - Torale Public Monitoring Feed',
    description:
      'See what the Torale community is monitoring — public tasks and recent detections across the web.',
    priority: 0.9,
  },
  {
    path: '/terms',
    title: 'Terms of Service - Torale',
    description: "Terms of service for using Torale's AI-powered web monitoring platform.",
    priority: 0.4,
  },
  {
    path: '/privacy',
    title: 'Privacy Policy - Torale',
    description: 'Privacy policy for Torale. Learn how we protect your data and monitoring queries.',
    priority: 0.4,
  },
];

function getCompareRoutes(): PublicRoute[] {
  return Object.entries(COMPETITORS).map(([slug, data]) => ({
    path: `/compare/${slug}`,
    title: data.metaTitle,
    description: data.metaDescription,
    ogType: 'article',
  }));
}

function getUseCaseRoutes(): PublicRoute[] {
  return Object.entries(USE_CASES).map(([slug, data]) => ({
    path: `/use-cases/${slug}`,
    title: data.metaTitle,
    description: data.metaDescription,
    ogType: 'article',
  }));
}

function getConceptRoutes(): PublicRoute[] {
  return Object.entries(CONCEPTS).map(([slug, data]) => ({
    path: `/concepts/${slug}`,
    title: data.metaTitle,
    description: data.metaDescription,
    ogType: 'article',
  }));
}

/**
 * All public routes — the union of static + dynamic. Order is stable across
 * builds (alphabetical within each group) so sitemap diffs stay minimal.
 */
export const PUBLIC_ROUTES: PublicRoute[] = [
  ...STATIC_ROUTES,
  ...getCompareRoutes(),
  ...getUseCaseRoutes(),
  ...getConceptRoutes(),
];
