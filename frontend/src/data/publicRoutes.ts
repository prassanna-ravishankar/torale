// Source of truth for public routes — consumed by prerender, sitemap, and
// DynamicMeta. Add a new public page here and it flows to all three.

import { COMPETITORS } from './competitors';
import { USE_CASES } from './useCases';
import { CONCEPTS } from './concepts';

export interface PublicRoute {
  path: string;
  title: string;
  description: string;
  /** Sitemap priority, 0.0–1.0. Defaults to 0.8. */
  priority?: number;
  ogType?: 'website' | 'article';
}

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

interface SEOPageMeta {
  metaTitle: string;
  metaDescription: string;
}

function articleRoutes(
  pathPrefix: string,
  record: Record<string, SEOPageMeta>,
): PublicRoute[] {
  return Object.entries(record).map(([slug, data]) => ({
    path: `${pathPrefix}/${slug}`,
    title: data.metaTitle,
    description: data.metaDescription,
    ogType: 'article',
  }));
}

export const PUBLIC_ROUTES: PublicRoute[] = [
  ...STATIC_ROUTES,
  ...articleRoutes('/compare', COMPETITORS),
  ...articleRoutes('/use-cases', USE_CASES),
  ...articleRoutes('/concepts', CONCEPTS),
];
