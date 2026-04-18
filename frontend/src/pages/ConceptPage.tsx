import { useParams, Navigate, useNavigate } from 'react-router-dom';
import { motion } from '@/lib/motion-compat';
import { ArrowRight, ArrowUpRight } from 'lucide-react';
import { CONCEPTS } from '@/data/concepts';
import { DynamicMeta } from '@/components/DynamicMeta';
import { generateFAQStructuredData } from '@/utils/structuredData';

/**
 * Concept landing page: explainer content for Torale's conceptual surfaces.
 * Routes: /concepts/self-scheduling-agents, /concepts/...
 */
export function ConceptPage() {
  const { concept } = useParams<{ concept: string }>();
  const navigate = useNavigate();

  if (!concept || !CONCEPTS[concept]) {
    return <Navigate to="/" replace />;
  }

  const data = CONCEPTS[concept];
  const faqStructuredData = generateFAQStructuredData(data.faq);

  return (
    <>
      <DynamicMeta
        path={`/concepts/${concept}`}
        title={data.metaTitle}
        description={data.metaDescription}
        type="article"
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(faqStructuredData).replace(/</g, '\\u003c'),
        }}
      />

      <div className="min-h-screen bg-[#fafafa]">
        <section className="relative pt-32 pb-16 px-6 border-b border-zinc-200">
          <div className="container mx-auto max-w-3xl">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mb-8"
            >
              <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border-2 border-zinc-900 text-zinc-900 text-xs font-mono font-bold uppercase tracking-wider shadow-brutalist">
                {data.tagline}
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="text-4xl md:text-5xl font-bold font-grotesk tracking-tight mb-6 text-zinc-900"
            >
              {data.heroTitle}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="text-xl text-zinc-600 mb-8 font-medium leading-relaxed"
            >
              {data.heroSubtitle}
            </motion.p>

            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="text-base text-zinc-700 leading-relaxed"
            >
              {data.intro}
            </motion.p>
          </div>
        </section>

        {data.sections.map((section, idx) => (
          <section
            key={idx}
            className={`py-16 px-6 ${idx % 2 === 0 ? 'bg-white' : 'bg-zinc-50'}`}
          >
            <div className="container mx-auto max-w-3xl">
              <h2 className="text-2xl md:text-3xl font-bold font-grotesk mb-6 text-zinc-900">
                {section.heading}
              </h2>
              <div className="space-y-4 text-zinc-700 leading-relaxed">
                {section.paragraphs.map((p, pIdx) => (
                  <p key={pIdx}>{p}</p>
                ))}
              </div>
            </div>
          </section>
        ))}

        {data.engineeringDoc && (
          <section className="py-12 px-6 bg-zinc-900 text-white">
            <div className="container mx-auto max-w-3xl">
              <p className="text-sm uppercase tracking-wider text-zinc-400 mb-2 font-mono">
                Going deeper
              </p>
              <a
                href={data.engineeringDoc.href}
                className="group inline-flex items-center gap-3 text-xl font-grotesk font-bold hover:text-brand-orange transition-colors"
              >
                {data.engineeringDoc.label}
                <ArrowUpRight className="h-5 w-5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </a>
            </div>
          </section>
        )}

        <section className="py-16 px-6 bg-white">
          <div className="container mx-auto max-w-3xl">
            <h2 className="text-2xl md:text-3xl font-bold font-grotesk mb-8 text-zinc-900">
              Frequently Asked Questions
            </h2>
            <div className="space-y-6">
              {data.faq.map((item, idx) => (
                <div key={idx} className="border-b-2 border-zinc-200 pb-6 last:border-b-0">
                  <h3 className="text-lg font-bold text-zinc-900 mb-2">{item.question}</h3>
                  <p className="text-zinc-700 leading-relaxed">{item.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {data.relatedLinks && data.relatedLinks.length > 0 && (
          <section className="py-12 px-6 bg-zinc-50 border-t border-zinc-200">
            <div className="container mx-auto max-w-3xl">
              <p className="text-sm uppercase tracking-wider text-zinc-500 mb-4 font-mono">
                Related
              </p>
              <ul className="space-y-2">
                {data.relatedLinks.map((link) => (
                  <li key={link.href}>
                    <a
                      href={link.href}
                      className="inline-flex items-center gap-2 text-zinc-900 font-medium hover:text-brand-orange transition-colors"
                    >
                      {link.label}
                      <ArrowRight className="h-4 w-4" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}

        <section className="py-16 px-6 bg-yellow-400 border-t-4 border-zinc-900">
          <div className="container mx-auto max-w-3xl text-center">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-6 text-zinc-900">
              Ready to try it?
            </h2>
            <button
              onClick={() => navigate('/dashboard')}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-zinc-900 text-white text-lg font-bold hover:bg-zinc-800 transition-all shadow-brutalist-lg hover:translate-x-[2px] hover:translate-y-[2px] border-2 border-zinc-900"
            >
              Start Monitoring Free
              <ArrowRight className="h-5 w-5" />
            </button>
          </div>
        </section>
      </div>
    </>
  );
}
