import { useParams, Navigate, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from '@/lib/motion-compat';
import { CheckCircle2, ArrowRight, Zap, Shield, Clock } from 'lucide-react';
import { USE_CASES } from '@/data/useCases';

/**
 * Use case landing page for Torale
 * Routes: /use-cases/steam-game-price-alerts, /use-cases/competitor-price-change-monitor, etc.
 */

const iconMap = {
  zap: Zap,
  shield: Shield,
  clock: Clock,
};

export function UseCasePage() {
  const { usecase } = useParams<{ usecase: string }>();
  const navigate = useNavigate();

  if (!usecase || !USE_CASES[usecase]) {
    return <Navigate to="/" replace />;
  }

  const data = USE_CASES[usecase];

  return (
    <>
      <Helmet>
        <title>{data.metaTitle}</title>
        <meta name="description" content={data.metaDescription} />
        <meta name="keywords" content={data.targetKeyword} />
        <link rel="canonical" href={`https://torale.ai/use-cases/${usecase}`} />
      </Helmet>

      <div className="min-h-screen bg-[#fafafa]">
        {/* Hero Section */}
        <section className="pt-32 pb-24 px-6 border-b border-zinc-200">
          <div className="container mx-auto max-w-6xl text-center">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mb-8"
            >
              <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border-2 border-zinc-900 text-zinc-900 text-xs font-mono font-bold uppercase tracking-wider shadow-brutalist">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
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
                className="group inline-flex items-center justify-center gap-3 px-8 py-4 bg-brand-orange text-white text-lg font-bold hover:bg-[hsl(10,90%,50%)] transition-all shadow-brutalist-lg hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(24,24,27,1)] border-2 border-zinc-900"
              >
                Start Monitoring Free
                <ArrowRight className="h-5 w-5" />
              </button>
            </motion.div>
          </div>
        </section>

        {/* Problem/Solution Section */}
        <section className="py-16 px-4 bg-white">
          <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
            <div className="p-8 border-2 border-zinc-900 shadow-[4px_4px_0px_0px_rgba(239,68,68,0.3)]">
              <h3 className="text-2xl font-bold mb-4 text-red-600 font-grotesk">The Problem</h3>
              <p className="text-zinc-700 leading-relaxed">{data.problemStatement}</p>
            </div>
            <div className="p-8 border-2 border-zinc-900 shadow-[4px_4px_0px_0px_rgba(34,197,94,0.3)]">
              <h3 className="text-2xl font-bold mb-4 text-green-600 font-grotesk">The Solution</h3>
              <p className="text-zinc-700 leading-relaxed">{data.solutionStatement}</p>
            </div>
          </div>
        </section>

        {/* Benefits Section */}
        <section className="py-16 px-4 bg-zinc-50">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12 font-grotesk">Why Use Torale?</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {data.benefits.map((benefit, idx) => {
                const Icon = iconMap[benefit.icon];
                return (
                  <div
                    key={idx}
                    className="p-6 bg-white border-2 border-zinc-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]"
                  >
                    <Icon className="w-10 h-10 mb-4 text-yellow-400" strokeWidth={2} />
                    <h3 className="text-xl font-bold mb-2">{benefit.title}</h3>
                    <p className="text-zinc-600">{benefit.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="py-16 px-4 bg-white">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12 font-grotesk">How It Works</h2>
            <div className="space-y-6">
              {data.howItWorks.map((step, idx) => (
                <div
                  key={idx}
                  className="flex gap-6 p-6 border-2 border-zinc-900 bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]"
                >
                  <div className="flex-shrink-0 w-12 h-12 bg-yellow-400 border-2 border-zinc-900 flex items-center justify-center text-2xl font-bold">
                    {step.step}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-2">{step.title}</h3>
                    <p className="text-zinc-600 mb-2">{step.description}</p>
                    <code className="inline-block px-3 py-1 bg-zinc-100 border border-zinc-300 text-sm font-mono">
                      {step.example}
                    </code>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Example Conditions Section */}
        <section className="py-16 px-4 bg-zinc-50">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12 font-grotesk">Real-World Examples</h2>
            <div className="space-y-4">
              {data.exampleConditions.map((example, idx) => (
                <div
                  key={idx}
                  className="p-6 border-2 border-zinc-900 bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]"
                >
                  <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                    {example.title}
                  </h3>
                  <div className="pl-7 space-y-2">
                    <p className="text-zinc-700">
                      <span className="font-semibold">Condition:</span> {example.condition}
                    </p>
                    <p className="text-green-700">
                      <span className="font-semibold">Result:</span> {example.result}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-16 px-4 bg-white">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12 font-grotesk">Frequently Asked Questions</h2>
            <div className="space-y-6">
              {data.faq.map((item, idx) => (
                <div key={idx} className="border-b-2 border-zinc-200 pb-6 last:border-b-0">
                  <h3 className="text-xl font-bold mb-3">{item.question}</h3>
                  <p className="text-zinc-600 leading-relaxed">{item.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 px-4 bg-yellow-400 border-t-4 border-zinc-900">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-4xl font-bold mb-6 font-grotesk">
              Ready to Start Monitoring?
            </h2>
            <p className="text-xl mb-8 text-zinc-800">
              Join thousands using AI-powered monitoring to never miss important changes
            </p>
            <button
              onClick={() => navigate('/sign-up')}
              className="px-12 py-5 bg-zinc-900 text-white font-bold text-lg border-2 border-zinc-900 shadow-[6px_6px_0px_0px_rgba(0,0,0,0.3)] hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,0.3)] hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all duration-150"
            >
              Start Free Trial →
            </button>
            <p className="mt-4 text-sm text-zinc-700">No credit card required • Free while in beta</p>
          </div>
        </section>
      </div>
    </>
  );
}
