import { useRef } from "react";
import { motion, useTransform } from "framer-motion";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { ParticleBackground } from "./ParticleBackground";
import { SystemVisualization } from "./SystemVisualization";
import { CodeTabs } from "./CodeTabs";
import { CapacityBadge } from "./CapacityBadge";
import { useScrollProgress } from "@/hooks/useScrollProgress";

export default function LandingParallax() {
  const { isAuthenticated } = useAuth();
  const containerRef = useRef<HTMLDivElement>(null);

  const {
    heroOpacity,
    heroProgress,
    systemOpacity,
    systemProgress,
    codeOpacity,
    pricingOpacity,
  } = useScrollProgress(containerRef);

  // Particle opacity based on scene
  const particleOpacity = useTransform(
    systemProgress,
    [0, 0.5, 1],
    [1, 0.3, 0.3]
  );

  // Hero transformations
  const heroScale = useTransform(heroProgress, [0, 1], [1, 0.7]);
  const heroY = useTransform(heroProgress, [0, 1], [0, -100]);

  const sceneWrapper =
    "relative h-[170vh] md:h-[190vh] lg:h-[200vh] flex flex-col justify-start";

  return (
    <>
      {/* Particle Background with dynamic opacity */}
      <motion.div
        style={{ opacity: particleOpacity }}
        className="pointer-events-none"
        aria-hidden="true"
      >
        <ParticleBackground />
      </motion.div>

      {/* Main scroll container */}
      <div ref={containerRef} className="relative bg-transparent z-10">
        {/* Scene 1: HERO */}
        <section data-scene="hero" className={sceneWrapper}>
          <motion.div
            style={{ opacity: heroOpacity, scale: heroScale, y: heroY }}
            className="sticky top-0 min-h-screen flex flex-col items-center justify-center px-4"
          >
            <div className="max-w-4xl w-full text-center space-y-8">
              <CapacityBadge />

              <h1 className="text-5xl md:text-7xl font-bold">
                Make the web work for{" "}
                <span className="blinking-underscore">you</span>
              </h1>

              <p className="text-xl text-brand-grey">
                Grounded AI monitoring that watches the web, so you don't have
                to.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                {isAuthenticated ? (
                  <Link
                    to="/dashboard"
                    className="bg-brand-red text-white uppercase font-bold py-3 px-6 text-sm tracking-wide text-center"
                  >
                    [ + Go to Dashboard ]
                  </Link>
                ) : (
                  <Link
                    to="/sign-up"
                    className="bg-brand-red text-white uppercase font-bold py-3 px-6 text-sm tracking-wide text-center"
                  >
                    [ + Get Started ]
                  </Link>
                )}
                <a
                  href="https://github.com/prassanna-ravishankar/torale"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-white text-black border border-black uppercase font-bold py-3 px-6 text-sm tracking-wide text-center"
                >
                  [ + View on Github ]
                </a>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Scene 2: SYSTEM */}
        <section data-scene="system" className={sceneWrapper}>
          <motion.div
            style={{ opacity: systemOpacity }}
            className="sticky top-0 min-h-screen bg-white border-y-2 border-brand-grid flex items-center"
          >
            <SystemVisualization progress={systemProgress} />
          </motion.div>
        </section>

        {/* Scene 3: CODE */}
        <section data-scene="code" className={sceneWrapper}>
          <motion.div
            style={{ opacity: codeOpacity }}
            className="sticky top-0 min-h-screen flex items-center justify-center bg-white border-y-2 border-brand-grid p-8"
          >
            <div className="max-w-4xl w-full space-y-8">
              <div className="text-center">
                <h2 className="text-3xl font-bold mb-4 uppercase tracking-wide font-mono">
                  [ BUILT FOR DEVELOPERS ]
                </h2>
                <p className="text-brand-grey">
                  Create, manage, and monitor from your terminal.
                </p>
              </div>
              <CodeTabs />
            </div>
          </motion.div>
        </section>

        {/* Scene 4: PRICING */}
        <section data-scene="pricing" className={sceneWrapper}>
          <motion.div
            style={{ opacity: pricingOpacity }}
            className="sticky top-0 min-h-screen flex items-center justify-center bg-white p-8"
          >
            <div className="max-w-md w-full border-2 border-black p-8 text-center bg-white">
              <h3 className="font-bold text-2xl mb-2">Free</h3>
              <p className="text-lg text-brand-grey mb-6">
                "Free till I figure things out."
              </p>
              <ul className="space-y-2 mb-6 text-left">
                <li className="flex items-center gap-2 font-mono text-sm">
                  <span className="text-brand-red">[+]</span> Open-Source
                </li>
                <li className="flex items-center gap-2 font-mono text-sm">
                  <span className="text-brand-red">[+]</span> Unlimited Monitors
                </li>
                <li className="flex items-center gap-2 font-mono text-sm">
                  <span className="text-brand-red">[+]</span> Community Support
                </li>
              </ul>
              <Link
                to="/sign-up"
                className="bg-black text-white uppercase font-bold py-3 px-6 text-sm tracking-wide w-full text-center block"
              >
                [ + Get Started for Free ]
              </Link>
            </div>
          </motion.div>
        </section>

        {/* Scene 5: FOOTER */}
        <footer className="p-6 md:p-12 bg-white border-t border-brand-grid">
          <div className="text-center text-sm text-brand-grey space-y-2">
            <p>τorale is an open-source project.</p>
            <div className="flex justify-center gap-6 font-mono">
              <a
                href="https://github.com/prassanna-ravishankar/torale"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-brand-red"
              >
                GitHub
              </a>
              <Link to="/changelog" className="hover:text-brand-red">
                Changelog
              </Link>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
