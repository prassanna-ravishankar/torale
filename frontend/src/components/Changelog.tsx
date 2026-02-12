import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "@/lib/motion-compat";
import { ArrowLeft, ArrowUpRight, Github, Rss } from "lucide-react";
import { ChangelogEntryCard } from "./ChangelogEntryCard";
import { ChangelogEntry } from "@/types/changelog";
import { GITHUB_REPO_URL } from "@/constants/links";
import { Logo } from "./Logo";
import { DynamicMeta } from "./DynamicMeta";
import { generateChangelogStructuredData } from "@/utils/structuredData";
import { Helmet } from "react-helmet-async";
import api from "@/lib/api";

export default function Changelog() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<ChangelogEntry[]>([]);
  const [structuredData, setStructuredData] = useState<string>("");

  useEffect(() => {
    const fetchChangelog = async () => {
      try {
        const response = await fetch(`${api.getBaseUrl()}/static/changelog.json`);
        if (response.ok) {
          const data = await response.json();
          setEntries(data);
          // Generate structured data for SEO
          const schema = generateChangelogStructuredData(data);
          setStructuredData(JSON.stringify(schema));
        }
      } catch (error) {
        console.error("Failed to fetch changelog:", error);
      }
    };

    fetchChangelog();
  }, []);

  return (
    <>
      <DynamicMeta
        title="Changelog - Torale Product Updates & Features"
        description="Track every update to Torale's AI-powered web monitoring platform. New features, improvements, and fixes shipped weekly."
        url="https://torale.ai/changelog"
        image="https://torale.ai/og-image.webp"
      />
      <Helmet>
        <link
          rel="alternate"
          type="application/rss+xml"
          title="Torale Changelog"
          href="https://torale.ai/changelog.xml"
        />
      </Helmet>
      {structuredData && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: structuredData.replace(/</g, '\\u003c')
          }}
        />
      )}
      <div className="min-h-screen bg-zinc-50 text-zinc-900 font-sans selection:bg-[hsl(10,90%,55%)] selection:text-white">
      {/* Background Grid */}
      <div
        className="fixed inset-0 pointer-events-none z-0 opacity-[0.3]"
        style={{
          backgroundImage: `radial-gradient(#a1a1aa 1px, transparent 1px)`,
          backgroundSize: '32px 32px'
        }}
      />

      {/* Navigation Bar */}
      <nav className="sticky top-0 z-50 bg-zinc-50/90 backdrop-blur-md border-b border-zinc-200">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/")}
              className="group flex items-center gap-2 text-zinc-500 hover:text-zinc-900 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              <span className="text-sm font-medium">Back to Home</span>
            </button>
          </div>

          <Logo className="cursor-default" />

          <div className="flex items-center gap-4 w-[120px] justify-end">
            <a
              href="/changelog.xml"
              className="group flex items-center gap-2 text-zinc-500 hover:text-zinc-900 transition-colors"
              title="Subscribe to RSS feed"
            >
              <Rss className="w-4 h-4" />
              <span className="text-sm font-medium">RSS</span>
            </a>
          </div>
        </div>
      </nav>

      <main className="relative z-10 pb-32">
        {/* Header Section */}
        <section className="pt-24 pb-16 px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 bg-zinc-100 border border-zinc-200 rounded-full text-[10px] font-mono font-medium tracking-widest uppercase mb-6"
          >
            <div className="w-2 h-2 bg-[hsl(10,90%,55%)] rounded-full animate-pulse" />
            Live Feed
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold font-grotesk tracking-tight mb-6 text-zinc-900"
          >
            What's New
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg md:text-xl text-zinc-500 max-w-2xl mx-auto leading-relaxed mb-10"
          >
            Torale is built in the open. Every feature, improvement, and bug fix is shaped by real user feedback.
          </motion.p>

          <motion.a
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            href={GITHUB_REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm font-bold text-zinc-900 hover:text-[hsl(10,90%,55%)] transition-colors border-b border-zinc-900 hover:border-[hsl(10,90%,55%)] pb-0.5"
          >
            <Github className="w-4 h-4" />
            View Source on GitHub
            <ArrowUpRight className="w-3 h-3" />
          </motion.a>
        </section>

        {/* Timeline Section */}
        <div className="container mx-auto max-w-5xl px-6 relative">
          {/* Top Gradient Fade for Line */}
          <div className="absolute top-0 left-0 md:left-1/2 w-px h-16 bg-gradient-to-b from-transparent to-zinc-200 -ml-px md:-ml-0.5" />

          <div className="pt-16">
            {entries.map((entry, index) => (
              <ChangelogEntryCard key={entry.id} entry={entry} index={index} />
            ))}
          </div>

          {/* Bottom "End of Line" Marker */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="flex justify-center mt-12 relative z-10"
          >
            <div className="px-4 py-2 bg-zinc-100 border border-zinc-200 rounded-full text-xs font-mono text-zinc-400">
              Initial Release • Oct 2025
            </div>
          </motion.div>
        </div>
      </main>
    </div>
    </>
  );
}
