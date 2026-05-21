import { useParams, Navigate, Link } from 'react-router-dom';
import { MarketingLayout } from '@/components/marketing/MarketingLayout';
import { DynamicMeta } from '@/components/DynamicMeta';
import { cn } from '@/lib/utils';
import landingStyles from '@/components/landing/Landing.module.css';
import marketingStyles from '@/components/marketing/marketing.module.css';
import { COMPETITORS } from '@/data/competitors';
import { generateBreadcrumbStructuredData } from '@/utils/structuredData';
import { escapeForScriptTag } from '@/utils/jsonLd';

/**
 * Editorial comparison page — webwhen vs a single competitor.
 * Routes: /compare/visualping-alternative, /compare/distill-alternative, /compare/changetower-alternative.
 *
 * No feature grid, no checkmark table. Manifesto-style prose contrast.
 */
export function ComparePage() {
  const { tool } = useParams<{ tool: string }>();

  if (!tool || !COMPETITORS[tool]) {
    return <Navigate to="/" replace />;
  }

  const competitor = COMPETITORS[tool];

  const breadcrumbJson = JSON.stringify(
    generateBreadcrumbStructuredData([
      { name: 'Home', path: '/' },
      { name: 'Compare', path: '/compare' },
      { name: competitor.name, path: `/compare/${competitor.slug}` },
    ]),
  );

  return (
    <MarketingLayout activePath="/compare">
      <DynamicMeta
        path={`/compare/${competitor.slug}`}
        title={competitor.seoTitle}
        description={competitor.seoDescription}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: escapeForScriptTag(breadcrumbJson) }}
      />

      {/* Hero — smaller than Landing's */}
      <section className={cn(landingStyles.section, marketingStyles.articleHero)}>
        <div className={landingStyles.container}>
          <div className={marketingStyles.reading}>
            <div className={marketingStyles.articleHeroEyebrow}>vs {competitor.name}</div>
            <h1 className={marketingStyles.articleHeading}>{competitor.heroHeadline}</h1>
            <p className={marketingStyles.articleLede}>{competitor.heroLede}</p>
          </div>
        </div>
      </section>

      {/* Editorial body */}
      <section className={landingStyles.section}>
        <div className={landingStyles.container}>
          <div className={marketingStyles.reading}>
            <p className={landingStyles.manifestoQuote}>{competitor.openingQuote}</p>
            {competitor.body.map((para, i) => (
              <p
                key={i}
                className={landingStyles.manifestoBody}
                style={i === 0 ? { marginTop: '32px' } : undefined}
              >
                {para}
              </p>
            ))}
          </div>
        </div>
      </section>

      {/* Single subtle differentiator callout */}
      <section className={cn(landingStyles.section, landingStyles.sectionAlt)}>
        <div className={landingStyles.container}>
          <div className={marketingStyles.reading}>
            <div className={landingStyles.eyebrow}>The honest difference</div>
            <p className={landingStyles.manifestoQuote} style={{ marginTop: '24px' }}>
              {competitor.differentiator}
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className={cn(landingStyles.section, landingStyles.cta)}>
        <div className={landingStyles.container}>
          <h2 className={landingStyles.ctaHeading}>
            Try webwhen <span className={landingStyles.heroEmber}>instead</span>.
          </h2>
          <p className={landingStyles.ctaBody}>
            Free while in beta. No setup, no configuration. The agent decides everything.
          </p>
          <Link
            to="/sign-up"
            className={cn(landingStyles.btn, landingStyles.btnPrimary, landingStyles.btnLg)}
          >
            Start watching <span style={{ fontFamily: 'var(--ww-font-mono)' }}>→</span>
          </Link>
        </div>
      </section>
    </MarketingLayout>
  );
}
