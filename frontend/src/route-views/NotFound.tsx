import { Link } from 'react-router-dom'
import { MarketingLayout } from '@/components/marketing/MarketingLayout'
import { DynamicMeta } from '@/components/DynamicMeta'
import { cn } from '@/lib/utils'
import landingStyles from '@/components/landing/Landing.module.css'
import marketingStyles from '@/components/marketing/marketing.module.css'

// SPA catch-all route. Emits robots noindex so unknown paths aren't indexed
// as soft-404s when the SPA fallback serves index.html with HTTP 200. See
// #305 — Option A interim. The end-state Option B (real 404 status code at
// the edge for non-prerendered paths) is tracked separately.
export default function NotFound() {
  return (
    <>
      <DynamicMeta
        title="Not found — webwhen"
        description="That page isn't here."
        noindex
      />
      <MarketingLayout>
        <section className={cn(landingStyles.section, marketingStyles.articleHero)}>
          <div className={landingStyles.container}>
            <div className={marketingStyles.reading}>
              <div className={marketingStyles.articleHeroEyebrow}>404</div>
              <h1 className={marketingStyles.articleHeading}>
                That page <span className={marketingStyles.articleHeroEmber}>isn't here</span>.
              </h1>
              <p className={marketingStyles.articleLede}>
                The URL you followed may be wrong, or the page may have moved.
              </p>
              <p className={marketingStyles.stamp}>
                <Link to="/">Back to webwhen</Link>
              </p>
            </div>
          </div>
        </section>
      </MarketingLayout>
    </>
  )
}
