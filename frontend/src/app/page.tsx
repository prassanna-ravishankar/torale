"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import AuthModal from "@/components/auth/AuthModal";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<'signin' | 'signup'>('signin');

  useEffect(() => {
    if (!loading && user) {
      // If user is logged in, redirect to dashboard
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-indigo-500 border-r-transparent"></div>
          <p className="mt-4 text-gray-700 text-lg">Loading...</p>
        </div>
      </main>
    );
  }

  if (user) {
    return null; // Will redirect to dashboard
  }

  const openAuthModal = (tab: 'signin' | 'signup') => {
    setAuthModalTab(tab);
    setIsAuthModalOpen(true);
  };

  return (
    <main className="relative overflow-hidden">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-4">
        {/* Background Elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full opacity-20 animate-float"></div>
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-br from-blue-400 to-indigo-400 rounded-full opacity-20 animate-float" style={{ animationDelay: '1s' }}></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-gradient-to-br from-emerald-400 to-teal-400 rounded-full opacity-10 animate-float" style={{ animationDelay: '2s' }}></div>
        </div>

        <div className="relative z-10 text-center max-w-5xl mx-auto">
          <div className="mb-8">
            <div className="flex items-center justify-center mb-6">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/torale-logo.svg" alt="Torale" className="w-16 h-16 mr-3" />
              <span className="text-2xl font-bold gradient-text font-space-grotesk">Torale</span>
            </div>
            <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold mb-6 leading-tight">
              <span className="gradient-text font-space-grotesk">Monitor</span>
              <br />
              <span className="text-gray-800">What Matters</span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              AI-powered content monitoring that understands natural language. 
              Get instant alerts when websites, feeds, and sources change in ways that matter to you.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <button
              onClick={() => openAuthModal('signup')}
              className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl text-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 shadow-xl hover:shadow-2xl transform hover:scale-105 animate-pulse-glow"
            >
              Get Started Free
            </button>
            <a
              href="#features"
              className="px-8 py-4 bg-white/80 backdrop-blur-sm text-gray-800 rounded-xl text-lg font-semibold hover:bg-white transition-all duration-300 shadow-lg hover:shadow-xl border border-gray-200"
            >
              Learn More
            </a>
          </div>

          {/* Demo Preview */}
          <div className="startup-card rounded-2xl p-8 max-w-4xl mx-auto">
            <div className="bg-gray-900 rounded-xl p-6 text-left">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              </div>
              <div className="text-green-400 font-mono text-sm">
                <div className="mb-2">$ Tell me when OpenAI updates their research page</div>
                <div className="text-gray-400 mb-2">✓ Monitoring openai.com/research</div>
                <div className="text-gray-400 mb-2">✓ AI-powered change detection active</div>
                <div className="text-blue-400">🔔 Alert: New paper published - &ldquo;GPT-5: Scaling Laws&rdquo;</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 gradient-text font-space-grotesk">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Everything you need to stay on top of the content that matters most to your business or interests.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: "🧠",
                title: "Natural Language Queries",
                description: "Just describe what you want to monitor in plain English. Our AI understands context and intent."
              },
              {
                icon: "⚡",
                title: "Real-time Monitoring",
                description: "Get instant notifications when content changes. No more manual checking or missed updates."
              },
              {
                icon: "🎯",
                title: "Smart Filtering",
                description: "AI-powered relevance detection ensures you only get alerts for meaningful changes."
              },
              {
                icon: "🔗",
                title: "Multiple Sources",
                description: "Monitor websites, RSS feeds, YouTube channels, and more from a single dashboard."
              },
              {
                icon: "📊",
                title: "Analytics Dashboard",
                description: "Track trends, view change history, and understand patterns in your monitored content."
              },
              {
                icon: "🔔",
                title: "Multi-channel Alerts",
                description: "Receive notifications via email, Slack, Discord, or webhooks to your favorite tools."
              }
            ].map((feature, index) => (
              <div key={index} className="startup-card rounded-xl p-6 text-center group hover:scale-105 transition-all duration-300">
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold mb-3 text-gray-800">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 px-4 bg-gradient-to-br from-indigo-50 to-purple-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 gradient-text font-space-grotesk">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Get started in minutes with our simple three-step process.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Describe What to Monitor",
                description: "Tell us in plain English what you want to track. 'Monitor Tesla's latest announcements' or 'Watch for new AI research papers'.",
                icon: "💬"
              },
              {
                step: "02",
                title: "AI Finds the Sources",
                description: "Our AI discovers the best sources to monitor and sets up intelligent tracking for meaningful changes.",
                icon: "🤖"
              },
              {
                step: "03",
                title: "Get Smart Alerts",
                description: "Receive notifications only when there are relevant updates. No noise, just the information you care about.",
                icon: "🎯"
              }
            ].map((step, index) => (
              <div key={index} className="text-center">
                <div className="relative mb-6">
                  <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-float" style={{ animationDelay: `${index * 0.5}s` }}>
                    <span className="text-3xl">{step.icon}</span>
                  </div>
                  <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-br from-orange-400 to-red-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                    {step.step}
                  </div>
                </div>
                <h3 className="text-xl font-semibold mb-3 text-gray-800">{step.title}</h3>
                <p className="text-gray-600 leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-12 gradient-text font-space-grotesk">
            Trusted by Forward-Thinking Teams
          </h2>
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            {[
              {
                metric: "10,000+",
                label: "Sources Monitored",
                description: "Across websites, feeds, and channels"
              },
              {
                metric: "99.9%",
                label: "Uptime",
                description: "Reliable monitoring you can count on"
              },
              {
                metric: "< 5min",
                label: "Average Alert Time",
                description: "Lightning-fast change detection"
              }
            ].map((stat, index) => (
              <div key={index} className="startup-card rounded-xl p-6">
                <div className="text-3xl font-bold gradient-text mb-2">{stat.metric}</div>
                <div className="text-lg font-semibold text-gray-800 mb-1">{stat.label}</div>
                <div className="text-gray-600 text-sm">{stat.description}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="startup-card rounded-2xl p-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 gradient-text font-space-grotesk">
              Ready to Get Started?
            </h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Join thousands of users who trust Torale to keep them informed about what matters most.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button
                onClick={() => openAuthModal('signup')}
                className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl text-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 shadow-xl hover:shadow-2xl transform hover:scale-105"
              >
                Start Monitoring Today
              </button>
              <a
                href="#features"
                className="px-8 py-4 bg-white/80 backdrop-blur-sm text-gray-800 rounded-xl text-lg font-semibold hover:bg-white transition-all duration-300 shadow-lg hover:shadow-xl border border-gray-200"
              >
                Learn More
              </a>
            </div>
            <p className="text-gray-500 text-sm mt-4">
              No credit card required • Free forever plan available
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-gray-200">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-xl font-bold text-white">T</span>
              </div>
              <span className="text-xl font-bold text-gray-800 font-space-grotesk">Torale</span>
            </div>
            <div className="flex items-center space-x-6 text-gray-600">
              <button onClick={() => openAuthModal('signin')} className="hover:text-indigo-600 transition-colors">Sign In</button>
              <a href="#features" className="hover:text-indigo-600 transition-colors">Features</a>
              <a href="#" className="hover:text-indigo-600 transition-colors">Privacy</a>
              <a href="#" className="hover:text-indigo-600 transition-colors">Terms</a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-200 text-center text-gray-500">
            <p>&copy; 2025 Torale. All rights reserved. Built with ❤️ for the future of content monitoring.</p>
          </div>
        </div>
      </footer>

      {/* Auth Modal */}
      <AuthModal 
        isOpen={isAuthModalOpen} 
        onClose={() => setIsAuthModalOpen(false)}
        defaultTab={authModalTab}
      />
    </main>
  );
}