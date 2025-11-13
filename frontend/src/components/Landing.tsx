import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { ParticleBackground } from "./ParticleBackground";
import { CodeTabs } from "./CodeTabs";
import { CapacityBadge } from "./CapacityBadge";

export default function Landing() {
  const { isAuthenticated } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Scroll animation observer
  useEffect(() => {
    const sections = document.querySelectorAll('.fade-in-section');
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
          }
        });
      },
      { threshold: 0.1 }
    );

    sections.forEach((section) => {
      observer.observe(section);
    });

    return () => {
      sections.forEach((section) => {
        observer.unobserve(section);
      });
    };
  }, []);

  return (
    <>
      {/* Particle Background */}
      <ParticleBackground />

      {/* Wrapper */}
      <div className="max-w-7xl mx-auto bg-transparent relative z-10">
        {/* Header */}
        <header className="p-6 flex justify-between items-center sticky top-0 z-50 bg-white/90 backdrop-blur-sm border-b border-brand-grid">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <img
              src="https://torale.ai/brand/svg/logo-cropped.svg"
              alt="Torale Logo"
              className="h-8 w-auto"
            />
            <span className="text-2xl font-bold tracking-widest text-black">
              τorale
            </span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6 font-mono text-sm">
            <a href="#how-it-works" className="hover:text-brand-red">
              How it Works
            </a>
            <a href="#code" className="hover:text-brand-red">
              API & CLI
            </a>
            <a href="#pricing" className="hover:text-brand-red">
              Pricing
            </a>
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
          </nav>

          {/* Primary CTA */}
          <div className="hidden sm:flex items-center gap-3">
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="bg-brand-red text-white uppercase font-bold py-3 px-5 text-sm tracking-wide"
              >
                [ + Go to Dashboard ]
              </Link>
            ) : (
              <Link
                to="/sign-up"
                className="bg-brand-red text-white uppercase font-bold py-3 px-5 text-sm tracking-wide"
              >
                [ + Get Started ]
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-black"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {mobileMenuOpen ? (
                <path
                  strokeLinecap="square"
                  strokeLinejoin="miter"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="square"
                  strokeLinejoin="miter"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </header>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-b border-brand-grid p-6 space-y-4 font-mono text-sm">
            <a
              href="#how-it-works"
              className="block hover:text-brand-red"
              onClick={() => setMobileMenuOpen(false)}
            >
              How it Works
            </a>
            <a
              href="#code"
              className="block hover:text-brand-red"
              onClick={() => setMobileMenuOpen(false)}
            >
              API & CLI
            </a>
            <a
              href="#pricing"
              className="block hover:text-brand-red"
              onClick={() => setMobileMenuOpen(false)}
            >
              Pricing
            </a>
            <a
              href="https://github.com/prassanna-ravishankar/torale"
              target="_blank"
              rel="noopener noreferrer"
              className="block hover:text-brand-red"
            >
              GitHub
            </a>
            <Link
              to="/changelog"
              className="block hover:text-brand-red"
              onClick={() => setMobileMenuOpen(false)}
            >
              Changelog
            </Link>
            <div className="pt-4">
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="block bg-brand-red text-white uppercase font-bold py-3 px-5 text-sm tracking-wide text-center"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  [ + Go to Dashboard ]
                </Link>
              ) : (
                <Link
                  to="/sign-up"
                  className="block bg-brand-red text-white uppercase font-bold py-3 px-5 text-sm tracking-wide text-center"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  [ + Get Started ]
                </Link>
              )}
            </div>
          </div>
        )}

        {/* Hero Section */}
        <section className="agno-section grid grid-cols-1 md:grid-cols-2 items-center gap-8 min-h-[70vh]">
          <div className="md:pl-10">
            <CapacityBadge />
            <h1 className="text-5xl md:text-7xl font-bold mb-6">
              Make the web work for <span className="blinking-underscore">you</span>
            </h1>
            <p className="text-xl text-brand-grey mb-8">
              Grounded AI monitoring that watches the web, so you don't have to.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
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

          {/* Empty column for particle background visibility */}
          <div></div>
        </section>

        {/* How It Works Section */}
        <section
          id="how-it-works"
          className="agno-section fade-in-section bg-white border-y border-brand-grid"
        >
          <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Step 1 */}
            <div className="text-center">
              <h3 className="font-mono text-brand-red text-lg mb-2">
                [ 1. Define What to Watch ]
              </h3>
              <p className="text-brand-grey">
                Create monitoring tasks with natural language queries and
                specific conditions you want to track.
              </p>
            </div>

            {/* Step 2 */}
            <div className="text-center">
              <h3 className="font-mono text-brand-red text-lg mb-2">
                [ 2. We Search & Analyze ]
              </h3>
              <p className="text-brand-grey">
                Scheduled grounded Google searches combined with LLM evaluation
                of your conditions - powered by Gemini.
              </p>
            </div>

            {/* Step 3 */}
            <div className="text-center">
              <h3 className="font-mono text-brand-red text-lg mb-2">
                [ 3. Get Smart Notifications ]
              </h3>
              <p className="text-brand-grey">
                Receive alerts only when conditions are met. State tracking
                ensures you're notified of meaningful changes.
              </p>
            </div>
          </div>
        </section>

        {/* Code Section */}
        <section
          id="code"
          className="agno-section agno-section-bracket fade-in-section bg-white p-6 md:p-12"
        >
          <h2 className="text-3xl font-bold text-center mb-4">
            Built for Developers
          </h2>
          <p className="text-center text-brand-grey mb-12">
            Create, manage, and monitor from your terminal.
          </p>

          <CodeTabs />
        </section>

        {/* Pricing Section */}
        <section
          id="pricing"
          className="agno-section fade-in-section bg-white border-y border-brand-grid"
        >
          <h2 className="text-3xl font-bold text-center mb-12">Pricing</h2>
          <div className="max-w-md mx-auto border-2 border-black p-8 text-center">
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
        </section>

        {/* Footer */}
        <footer className="p-6 md:p-12 bg-white">
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
