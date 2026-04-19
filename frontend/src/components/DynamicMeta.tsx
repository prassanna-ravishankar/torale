import { Helmet } from 'react-helmet-async';

/**
 * Canonical origin for all SEO URLs. Change here only.
 */
export const SITE_ORIGIN = 'https://torale.ai';

const DEFAULT_IMAGE = `${SITE_ORIGIN}/og-image.webp`;

interface DynamicMetaProps {
  /**
   * Path from site root (e.g. "/compare/visualping-alternative"). Used to
   * build canonical, og:url and twitter:url. Provide this for every public
   * page — `url` is only an escape hatch for non-Torale canonicals.
   */
  path?: string;
  url?: string;
  title?: string;
  description?: string;
  image?: string;
  type?: 'website' | 'article';
}

export function DynamicMeta({
  path,
  url,
  title = 'Torale - AI-Powered Web Monitoring',
  description = 'Monitor the web with AI. Get notified when conditions are met.',
  image = DEFAULT_IMAGE,
  type = 'website',
}: DynamicMetaProps) {
  const resolvedUrl = url ?? `${SITE_ORIGIN}${path ?? '/'}`;

  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />

      <meta property="og:type" content={type} />
      <meta property="og:url" content={resolvedUrl} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image} />

      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:url" content={resolvedUrl} />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={image} />

      <link rel="canonical" href={resolvedUrl} />
    </Helmet>
  );
}
