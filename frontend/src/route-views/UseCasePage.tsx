import { useParams, Navigate, Link } from 'react-router-dom';
import { MarketingLayout } from '@/components/marketing/MarketingLayout';
import { DynamicMeta } from '@/components/DynamicMeta';
import { cn } from '@/lib/utils';
import landingStyles from '@/components/landing/Landing.module.css';
import marketingStyles from '@/components/marketing/marketing.module.css';
import { USE_CASES } from '@/data/useCases';
import { generateBreadcrumbStructuredData } from '@/utils/structuredData';
import { escapeForScriptTag } from '@/utils/jsonLd';

/**
 * Editorial use-case landing page.
 * Routes: /use-cases/:usecase
 */
export function UseCasePage() {
  const { usecase } = useParams<{ usecase: string }>();

  if (!usecase || !USE_CASES[usecase]) {
    return <Navigate to="/" replace />;
  }

  const useCase = USE_CASES[usecase];
  const others = Object.values(USE_CASES).filter((u) => u.slug !== useCase.slug);

  const breadcrumbJson = JSON.stringify(
    generateBreadcrumbStructuredData([
      { name: 'Home', path: '/' },
      { name: 'Use cases', path: '/use-cases' },
      { name: useCase.name, path: `/use-cases/${useCase.slug}` },
    ]),
  );

  return (
    <MarketingLayout activePath="/use-cases">
      <DynamicMeta
        path={`/use-cases/${useCase.slug}`}
        title={useCase.seoTitle ?? `${useCase.heroHeadline} — webwhen`}
        description={useCase.seoDescription ?? useCase.heroLede}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: escapeForScriptTag(breadcrumbJson) }}
      />

      {/* Hero */}
      <section className={cn(landingStyles.section, marketingStyles.articleHero)}>
        <div className={landingStyles.container}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1.1fr 0.9fr',
              gap: '80px',
              alignItems: 'center',
            }}
          >
            <div>
              <div className={marketingStyles.articleHeroEyebrow}>Use case</div>
              <h1 className={marketingStyles.articleHeading}>{useCase.heroHeadline}</h1>
              <p className={marketingStyles.articleLede}>{useCase.heroLede}</p>
            </div>
            <div className={landingStyles.composer}>
              <div className={landingStyles.composerHead}>
                <span>new watch</span>
                <span>plain english · no rules</span>
              </div>
              <div className={landingStyles.composerBody}>
                <p className={landingStyles.composerPrompt}>
                  {useCase.composerPrompt}
                  <span className={landingStyles.composerCursor}></span>
                </p>
                <p className={landingStyles.composerSub}>
                  webwhen will sit with this and decide when to check.
                </p>
              </div>
              <div className={landingStyles.composerFoot}>
                <div>
                  <span className={landingStyles.chip}>nothing to tune</span>
                </div>
                <Link
                  to="/sign-up"
                  className={cn(landingStyles.btn, landingStyles.btnPrimary)}
                  style={{ padding: '8px 14px' }}
                >
                  Watch <span style={{ fontFamily: 'var(--ww-font-mono)' }}>→</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Manifesto-style body */}
      <section className={landingStyles.section}>
        <div className={landingStyles.container}>
          <div className={marketingStyles.reading}>
            <p className={landingStyles.manifestoQuote}>{useCase.openingQuote}</p>
            {useCase.body.map((para, i) => (
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

      {/* Related */}
      <section className={cn(landingStyles.section, landingStyles.sectionAlt)}>
        <div className={landingStyles.container}>
          <div className={landingStyles.eyebrow}>Other watches</div>
          <h2 className={landingStyles.sectionHeading}>
            Things webwhen also{' '}
            <span className={landingStyles.sectionHeadingAccent}>waits for.</span>
          </h2>
          <div className={landingStyles.cases}>
            {others.map((u) => (
              <Link key={u.slug} to={`/use-cases/${u.slug}`} className={landingStyles.caseCard}>
                <div className={landingStyles.caseTag}>{u.shortTag}</div>
                <p className={landingStyles.caseQuestion}>{u.composerPrompt}</p>
                <div className={landingStyles.caseResult}>watching</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
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
