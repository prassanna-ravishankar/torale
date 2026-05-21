// Source of truth for public marketing routes consumed by app/sitemap.ts
// and per-page metadata.

import { COMPETITORS } from '@/data/competitors';
import { USE_CASES } from '@/data/useCases';
import { CONCEPTS } from '@/data/concepts';

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
    title: 'webwhen — the agent that waits for the web',
    description:
      'Tell webwhen what to watch for in plain English. It will sit with the question, search the web on a schedule, and tell you the moment your condition is met.',
    priority: 1.0,
  },
  {
    path: '/changelog',
    title: 'Changelog — webwhen',
    description: 'What webwhen has been up to. Built in the open.',
    priority: 0.7,
  },
  {
    path: '/terms',
    title: 'Terms — webwhen',
    description: 'Terms of service for webwhen, the agent that waits for the web.',
    priority: 0.4,
  },
  {
    path: '/privacy',
    title: 'Privacy — webwhen',
    description:
      "How webwhen handles your data, why we collect what we do, and what we don't do with it.",
    priority: 0.4,
  },
];

interface ArticleMetaSource {
  seoTitle?: string;
  seoDescription?: string;
  metaTitle?: string;
  metaDescription?: string;
  heroHeadline?: string;
  heroLede?: string;
  title?: string;
  lede?: string;
  name?: string;
}

function articleRoutes(
  pathPrefix: string,
  record: Record<string, ArticleMetaSource>,
): PublicRoute[] {
  return Object.entries(record).map(([slug, data]) => {
    const title =
      data.seoTitle ??
      data.metaTitle ??
      data.heroHeadline ??
      data.title ??
      data.name ??
      slug;
    const description =
      data.seoDescription ?? data.metaDescription ?? data.heroLede ?? data.lede ?? '';
    return {
      path: `${pathPrefix}/${slug}`,
      title,
      description,
      ogType: 'article' as const,
    };
  });
}

export const PUBLIC_ROUTES: PublicRoute[] = [
  ...STATIC_ROUTES,
  ...articleRoutes('/compare', COMPETITORS),
  ...articleRoutes('/use-cases', USE_CASES),
  ...articleRoutes('/concepts', CONCEPTS),
];
