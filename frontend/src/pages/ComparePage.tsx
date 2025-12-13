import { useParams, Navigate, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from '@/lib/motion-compat';
import { CheckCircle2, XCircle, ArrowRight, Zap } from 'lucide-react';
import { COMPETITORS } from '@/data/competitors';

/**
 * Comparison page for Torale vs competitors
 * Routes: /compare/visualping-alternative, /compare/distill-alternative, etc.
 */

export function ComparePage() {
  const { tool } = useParams<{ tool: string }>();
  const navigate = useNavigate();

  if (!tool || !COMPETITORS[tool]) {
    return <Navigate to="/" replace />;
  }

  const data = COMPETITORS[tool];

  return (
    <>
      <Helmet>
        <title>{data.metaTitle}</title>
        <meta name="description" content={data.metaDescription} />
        <meta property="og:title" content={data.metaTitle} />
        <meta property="og:description" content={data.metaDescription} />
        <meta property="og:type" content="article" />
      </Helmet>

      <div className="min-h-screen bg-[#fafafa]">
        {/* Hero Section */}
        <section className="relative pt-32 pb-24 px-6 border-b border-zinc-200">
          <div className="container mx-auto max-w-4xl text-center">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mb-8"
            >
              <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border-2 border-zinc-900 text-zinc-900 text-xs font-mono font-bold uppercase tracking-wider shadow-brutalist">
                <Zap className="w-3 h-3" />
                {data.tagline}
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="text-5xl md:text-6xl font-bold font-grotesk tracking-tight mb-6 text-zinc-900"
            >
              {data.heroTitle}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="text-xl text-zinc-500 mb-10 max-w-2xl mx-auto font-medium"
            >
              {data.heroSubtitle}
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-4 justify-center"
            >
              <button
                onClick={() => navigate('/dashboard')}
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-brand-orange text-white text-lg font-bold hover:bg-[hsl(10,90%,50%)] transition-all shadow-brutalist-lg hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(24,24,27,1)] border-2 border-zinc-900"
              >
                Try Torale Free
                <ArrowRight className="h-5 w-5" />
              </button>
            </motion.div>
          </div>
        </section>

        {/* Why Torale Section */}
        <section className="py-24 px-6 bg-white">
          <div className="container mx-auto max-w-4xl">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-8 text-zinc-900">
              Why Choose Torale Over {data.competitorName}?
            </h2>

            <div className="space-y-4">
              {data.toraleAdvantages.map((advantage, idx) => (
                <div key={idx} className="flex items-start gap-3 p-4 bg-emerald-50 border-l-4 border-emerald-500">
                  <CheckCircle2 className="h-6 w-6 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <p className="text-zinc-700 font-medium">{advantage}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Comparison Table */}
        <section className="py-24 px-6 bg-zinc-50">
          <div className="container mx-auto max-w-4xl">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-12 text-zinc-900 text-center">
              Feature Comparison
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full border-2 border-zinc-900 bg-white">
                <thead>
                  <tr className="border-b-2 border-zinc-900">
                    <th className="px-6 py-4 text-left font-bold text-zinc-900 border-r-2 border-zinc-900">Feature</th>
                    <th className="px-6 py-4 text-left font-bold text-zinc-900 border-r-2 border-zinc-900">{data.competitorName}</th>
                    <th className="px-6 py-4 text-left font-bold text-zinc-900">Torale</th>
                  </tr>
                </thead>
                <tbody>
                  {data.comparisonTable.map((row, idx) => (
                    <tr key={idx} className="border-b border-zinc-200 last:border-0">
                      <td className="px-6 py-4 font-medium text-zinc-900 border-r-2 border-zinc-200">{row.feature}</td>
                      <td className="px-6 py-4 text-zinc-600 border-r-2 border-zinc-200">
                        {typeof row.competitor === 'boolean' ? (
                          row.competitor ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <XCircle className="h-5 w-5 text-zinc-300" />
                        ) : row.competitor}
                      </td>
                      <td className="px-6 py-4 text-zinc-600">
                        {typeof row.torale === 'boolean' ? (
                          row.torale ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <XCircle className="h-5 w-5 text-zinc-300" />
                        ) : row.torale}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Use Cases */}
        <section className="py-24 px-6 bg-white">
          <div className="container mx-auto max-w-4xl">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-12 text-zinc-900">
              Use Cases Where Torale Excels
            </h2>

            <div className="grid gap-8">
              {data.useCases.map((useCase, idx) => (
                <div key={idx} className="p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-colors">
                  <h3 className="text-xl font-bold font-grotesk text-zinc-900 mb-3">{useCase.title}</h3>
                  <p className="text-zinc-600 mb-4">{useCase.description}</p>
                  <div className="bg-zinc-50 p-4 border-l-4 border-emerald-500 font-mono text-sm text-zinc-700">
                    {useCase.example}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="py-24 px-6 bg-zinc-50">
          <div className="container mx-auto max-w-3xl">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-12 text-zinc-900 text-center">
              Frequently Asked Questions
            </h2>

            <div className="space-y-8">
              {data.faq.map((item, idx) => (
                <div key={idx}>
                  <h3 className="text-xl font-bold text-zinc-900 mb-3">{item.question}</h3>
                  <p className="text-zinc-600 leading-relaxed">{item.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24 px-6 bg-zinc-900 text-white">
          <div className="container mx-auto max-w-3xl text-center">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-6">
              Ready to Try Torale?
            </h2>
            <p className="text-xl text-zinc-300 mb-10">
              Join free beta and experience AI-powered web monitoring
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-brand-orange text-white text-lg font-bold hover:bg-[hsl(10,90%,50%)] transition-all shadow-brutalist-lg hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(255,255,255,0.1)]"
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
