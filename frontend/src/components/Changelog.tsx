import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { ParticleBackground } from "./ParticleBackground";
import { ChangelogEntryCard } from "./ChangelogEntryCard";
import { ChangelogEntry } from "@/types/changelog";
import { GITHUB_REPO_URL } from "@/constants/links";

export default function Changelog() {
  const [entries, setEntries] = useState<ChangelogEntry[]>([]);
  const [mounted, setMounted] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  // Parallax effect for timeline
  const timelineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  useEffect(() => {
    setMounted(true);

    const fetchChangelog = async () => {
      try {
        const response = await fetch("/changelog.json");
        if (response.ok) {
          const data = await response.json();
          setEntries(data);
        }
      } catch (error) {
        console.error("Failed to fetch changelog:", error);
      }
    };

    fetchChangelog();
  }, []);

  return (
    <>
      {/* Particle Background */}
      <ParticleBackground />

      <div className="min-h-screen bg-white relative">
        {/* Header */}
        <header className="fixed top-0 left-0 right-0 z-50 border-b-2 border-black bg-white">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3">
              <img src="/brand/svg/logo-cropped.svg" alt="Torale" className="h-8 w-8" />
              <span className="text-2xl font-bold tracking-widest">τorale</span>
            </Link>
            <Link
              to="/"
              className="inline-flex items-center gap-2 font-mono text-sm uppercase tracking-wide hover:text-brand-red transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              [ Back to Home ]
            </Link>
          </div>
        </header>

        {/* Content */}
        <main className="pt-32 pb-20 px-4 md:px-6 relative z-10" ref={containerRef}>
          <div className="container mx-auto max-w-4xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={mounted ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5 }}
              className="agno-section-bracket bg-white border-2 border-black p-8 mb-16 text-center"
            >
              <h1 className="text-3xl md:text-5xl font-bold mb-4 uppercase tracking-wide">
                <span className="hidden md:inline">[ </span>CHANGELOG<span className="hidden md:inline"> ]</span>
              </h1>
              <p className="text-lg text-brand-grey mb-3 max-w-2xl mx-auto">
                Torale is built in the open. Every feature, improvement, and bug fix is shaped by real user feedback
                and shared publicly. Follow along as we build a better way to monitor the web.
              </p>
              <p className="font-mono text-sm uppercase tracking-wider">
                <a
                  href={GITHUB_REPO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-black hover:text-brand-red transition-colors inline-flex items-center gap-1"
                >
                  [ + View Source → ]
                </a>
              </p>
            </motion.div>

            {/* Timeline */}
            <div className="relative bg-white p-4 md:p-8 border-2 border-brand-grid">
              {/* Timeline line - gray background (desktop only) */}
              <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-0.5 bg-brand-grid -translate-x-1/2" />

              {/* Timeline progress - red fills as you scroll (desktop only) */}
              <motion.div
                className="hidden md:block absolute left-1/2 top-0 w-0.5 bg-brand-red -translate-x-1/2"
                style={{ height: timelineHeight }}
              />

              {/* Entries */}
              <div className="space-y-12">
                {entries.map((entry, index) => {
                  const isEven = index % 2 === 0;

                  return (
                    <motion.div
                      key={entry.id}
                      initial={{ opacity: 0 }}
                      whileInView={{ opacity: 1 }}
                      viewport={{ once: true, margin: "-100px" }}
                      transition={{ duration: 0.3 }}
                      className="relative"
                    >
                      {/* Timeline dot (desktop only) */}
                      <motion.div
                        className="hidden md:block absolute left-1/2 top-6 w-3 h-3 border-2 border-black -translate-x-1/2 z-10 bg-white"
                        initial={{ backgroundColor: "#FFFFFF" }}
                        whileInView={{ backgroundColor: "#FF0000" }}
                        viewport={{ once: true, margin: "-100px" }}
                        transition={{ duration: 0.2 }}
                      />

                      {/* Content */}
                      <ChangelogEntryCard entry={entry} isEven={isEven} />
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
