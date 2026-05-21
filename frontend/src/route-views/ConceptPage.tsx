import { useParams, Navigate, Link } from 'react-router-dom';
import { MarketingLayout } from '@/components/marketing/MarketingLayout';
import { DynamicMeta } from '@/components/DynamicMeta';
import { cn } from '@/lib/utils';
import landingStyles from '@/components/landing/Landing.module.css';
import marketingStyles from '@/components/marketing/marketing.module.css';
import { CONCEPTS } from '@/data/concepts';
import { generateBreadcrumbStructuredData } from '@/utils/structuredData';
import { escapeForScriptTag } from '@/utils/jsonLd';

/**
 * Concept landing page: editorial explainer for webwhen's conceptual surfaces.
 * Routes: /concepts/self-scheduling-agents, /concepts/...
 */
export function ConceptPage() {
  const { concept } = useParams<{ concept: string }>();

  if (!concept || !CONCEPTS[concept]) {
    return <Navigate to="/" replace />;
  }

  const data = CONCEPTS[concept];

  const breadcrumbJson = JSON.stringify(
    generateBreadcrumbStructuredData([
      { name: 'Home', path: '/' },
      { name: 'Concepts', path: '/concepts' },
      { name: data.title, path: `/concepts/${data.slug}` },
    ]),
  );

  return (
    <MarketingLayout activePath="/concepts">
      <DynamicMeta
        path={`/concepts/${data.slug}`}
        title={data.metaTitle}
        description={data.metaDescription}
        type="article"
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: escapeForScriptTag(breadcrumbJson) }}
      />

      <section className={cn(landingStyles.section, marketingStyles.articleHero)}>
        <div className={landingStyles.container}>
          <div className={marketingStyles.reading}>
            <div className={marketingStyles.articleHeroEyebrow}>Concept</div>
            <h1 className={marketingStyles.articleHeading}>{data.title}</h1>
            <p className={marketingStyles.articleLede}>{data.lede}</p>
          </div>
        </div>
      </section>

      <section className={landingStyles.section} style={{ paddingTop: 0 }}>
        <div className={landingStyles.container}>
          <div className={marketingStyles.reading}>
            {data.sections.map((section, i) => (
              <div key={i}>
                <h2>{section.heading}</h2>
                {section.paragraphs.map((para, j) => (
                  <p key={j}>{para}</p>
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>

      {data.related && data.related.length > 0 && (
        <section className={cn(landingStyles.section, landingStyles.sectionAlt)}>
          <div className={landingStyles.container}>
            <div className={landingStyles.eyebrow}>Related</div>
            <h2 className={landingStyles.sectionHeading}>
              Keep <span className={landingStyles.sectionHeadingAccent}>reading.</span>
            </h2>
            <div className={landingStyles.cases}>
              {data.related.map((rel) => (
                <Link to={rel.path} key={rel.path} className={landingStyles.caseCard}>
                  <div className={landingStyles.caseTag}>{rel.kind}</div>
                  <p className={landingStyles.caseQuestion}>{rel.title}</p>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className={cn(landingStyles.section, landingStyles.cta)}>
        <div className={landingStyles.container}>
          <h2 className={landingStyles.ctaHeading}>
            What are you waiting <span className={landingStyles.heroEmber}>for</span>?
          </h2>
          <p className={landingStyles.ctaBody}>
            Free while in beta. One condition takes about 30 seconds to set up.
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
