'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useState, useCallback, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import ConceptVisuals from '@/components/landing/ConceptVisuals';

const navLink =
  'text-sm font-medium text-black/55 hover:text-black transition-colors duration-150';

export default function LandingPage() {
  const router = useRouter();
  const [transitioning, setTransitioning] = useState(false);
  const [newsletterModalOpen, setNewsletterModalOpen] = useState(false);
  const [newsletterName, setNewsletterName] = useState('');
  const [newsletterEmail, setNewsletterEmail] = useState('');
  const [newsletterSubmitted, setNewsletterSubmitted] = useState(false);
  const [newsletterLoading, setNewsletterLoading] = useState(false);
  const [newsletterError, setNewsletterError] = useState<string | null>(null);

  const handleNavigate = useCallback(() => {
    setTransitioning(true);
    setTimeout(() => {
      router.push('/chat');
    }, 600);
  }, [router]);

  useEffect(() => {
    if (!newsletterModalOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setNewsletterModalOpen(false);
    };
    window.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [newsletterModalOpen]);

  const closeNewsletterModal = useCallback(() => {
    setNewsletterModalOpen(false);
    setNewsletterName('');
    setNewsletterEmail('');
    setNewsletterError(null);
    setNewsletterLoading(false);
  }, []);

  const openNewsletterModal = useCallback(() => {
    setNewsletterError(null);
    setNewsletterModalOpen(true);
  }, []);

  const handleNewsletterSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const name = newsletterName.trim();
    const email = newsletterEmail.trim();
    if (!name || !email) return;

    setNewsletterLoading(true);
    setNewsletterError(null);
    try {
      const res = await fetch('/api/newsletter/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email }),
      });
      const data = (await res.json().catch(() => ({}))) as {
        ok?: boolean;
        error?: string;
        detail?: string;
      };

      if (!res.ok) {
        const msg =
          data.detail ||
          (data.error === 'newsletter_not_configured'
            ? 'Newsletter service is not configured on the server.'
            : data.error === 'newsletter_unreachable'
              ? 'Could not reach the newsletter service. Is it running?'
              : data.error || `Subscribe failed (${res.status})`);
        setNewsletterError(msg);
        return;
      }

      setNewsletterSubmitted(true);
      closeNewsletterModal();
    } catch {
      setNewsletterError('Network error. Try again in a moment.');
    } finally {
      setNewsletterLoading(false);
    }
  };

  return (
    <div className={`landing-page min-h-screen flex flex-col font-sora ${transitioning ? 'page-fade-out' : ''}`}>
      <nav className="w-full border-b border-black/5 bg-white/90 backdrop-blur-md sticky top-0 z-30 h-16 shrink-0">
        <div className="max-w-[1200px] mx-auto px-6 sm:px-10 h-full flex items-center justify-between gap-4">
          <div className="flex items-center gap-6 lg:gap-10 min-w-0">
            <Link href="/" className="flex items-center gap-2.5 shrink-0">
              <Image
                src="/logo.png"
                alt="CHINTU"
                width={36}
                height={36}
                className="h-9 w-9 shrink-0 object-contain bg-transparent"
                priority
                unoptimized
              />
              <span className="font-bold text-[17px] tracking-tight text-[#1b1b1b] hidden sm:inline">
                CHINTU
              </span>
            </Link>
            <div className="hidden md:flex items-center gap-6 lg:gap-7">
              <Link href="#how-it-works" className={navLink}>
                How it works
              </Link>
              <Link href="#modes" className={navLink}>
                Query modes
              </Link>
              <Link href="#stack" className={navLink}>
                Stack
              </Link>
              <Link href="#about" className={navLink}>
                About
              </Link>
              <Link href="#newsletter" className={navLink}>
                Newsletter
              </Link>
            </div>
          </div>
          <button
            type="button"
            onClick={handleNavigate}
            className="shrink-0 px-4 sm:px-5 py-2 rounded-full bg-black text-white text-sm font-semibold hover:bg-black/80 transition-all cursor-pointer"
          >
            Launch app
          </button>
        </div>
      </nav>

      {/* Hero — full first viewport below nav */}
      <section className="bg-white border-b border-black/5 min-h-[calc(100svh-4rem)] flex flex-col items-center justify-center px-6 sm:px-10 py-16">
        <div className="max-w-3xl mx-auto text-center flex flex-col items-center">
          <p className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-semibold text-black tracking-tight font-outfit mb-4 md:mb-5">
            Introducing
          </p>
          <h1 className="text-[clamp(3.5rem,14vw,7.5rem)] leading-[0.95] font-bold font-outfit tracking-tight text-accent mb-6 md:mb-8">
            CHINTU
          </h1>
          <p className="text-base sm:text-lg md:text-xl font-jetbrains text-black/50 leading-relaxed max-w-2xl">
          Causal and Hierarchical Intelligence for Narrative Tracking
          </p>
        </div>
      </section>

      {/* Editorial — cream */}
      <section
        className="py-20 md:py-28 border-t border-black/[0.06]"
        style={{ backgroundColor: 'var(--bg-landing)' }}
      >
        <div className="max-w-[1200px] mx-auto px-6 sm:px-10">
          <div className="flex flex-col items-center text-center mb-14 md:mb-16">
            <span className="text-[12px] font-bold font-outfit text-black/50 uppercase tracking-[0.2em] mb-5">
              Geopolitical intelligence
            </span>
            <h2 className="text-[clamp(1.75rem,5vw,3.25rem)] leading-[1.12] font-bold font-outfit tracking-tight max-w-[900px] text-[#1b1b1b]">
              What&apos;s happening <br />
              <span className="text-accent">in the world?</span>
            </h2>
            <p className="mt-6 text-[17px] md:text-[19px] font-sora text-black/70 tracking-tight max-w-xl leading-snug">
              Causal chains · Entity networks · Event timelines · Knowledge graphs
            </p>
            <button
              type="button"
              onClick={handleNavigate}
              className="mt-10 px-8 py-3.5 rounded-full bg-accent text-[#fbfaf8] text-lg font-semibold shadow-lg shadow-accent/15 hover:scale-[1.02] transition-transform cursor-pointer"
            >
              Start analysis →
            </button>
          </div>

          <ConceptVisuals />
        </div>
      </section>

      {/* How it works + stack */}
      <section id="how-it-works" className="bg-white py-20 md:py-24 border-t border-black/5 scroll-mt-24">
        <div className="max-w-[800px] mx-auto px-6 sm:px-10">
          <h2 className="text-3xl md:text-4xl font-bold font-outfit text-[#1b1b1b] mb-8 text-center">
            How it works
          </h2>
          <ol className="space-y-6 text-[17px] leading-[1.75] text-black/75 font-sora list-decimal list-inside marker:text-accent marker:font-bold">
            <li>
              <strong className="text-[#1b1b1b]">Events enter the graph</strong> as vertices with titles, locations,
              timestamps, and source URLs—linked to entities and topics and to each other via documented influence
              relationships.
            </li>
            <li>
              <strong className="text-[#1b1b1b]">You ask in natural language.</strong> We infer intent (causal vs
              narrative), resolve an <code className="text-[13px] font-jetbrains bg-black/[0.06] px-1.5 py-0.5 rounded">evt_*</code>{' '}
              when needed using substring search on the graph, then run a fixed, audited TigerGraph query—never raw GSQL
              from the client.
            </li>
            <li>
              <strong className="text-[#1b1b1b]">Answers stay grounded.</strong> We fetch text from URLs on the subgraph,
              feed structured graph JSON plus excerpts to the model, and return both <strong>prose</strong> and a{' '}
              <strong>normalized graph payload</strong> for your UI.
            </li>
          </ol>
        </div>
      </section>

      <section id="stack" className="py-20 md:py-24 border-t border-black/5 scroll-mt-24" style={{ backgroundColor: 'var(--bg-landing)' }}>
        <div className="max-w-[900px] mx-auto px-6 sm:px-10 text-center">
          <h2 className="text-3xl md:text-4xl font-bold font-outfit text-[#1b1b1b] mb-4">
            Built on serious infrastructure
          </h2>
          <p className="text-black/65 font-sora text-[17px] leading-relaxed mb-10 max-w-2xl mx-auto">
            CHINTU is designed for analysts and product teams who need repeatable graph analytics, not one-off prompts.
            The backend is a small Flask service; the graph lives on TigerGraph Cloud (or your cluster) with versioned
            GSQL queries checked into the repo.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {['TigerGraph', 'Python · Flask', 'OpenAI-compatible LLMs', 'GDELT-shaped event data', 'Next.js app'].map((label) => (
              <span
                key={label}
                className="px-4 py-2 rounded-full border border-black/10 bg-white/80 text-sm font-jetbrains text-black/70"
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section id="about" className="bg-white py-20 md:py-24 border-t border-black/5 scroll-mt-24">
        <div className="max-w-[720px] mx-auto px-6 sm:px-10 text-center">
          <h2 className="text-3xl md:text-4xl font-bold font-outfit text-[#1b1b1b] mb-6">
            About this project
          </h2>
          <p className="text-[17px] leading-[1.8] text-black/70 font-sora">
            CHINTU is an experimental <strong className="text-[#1b1b1b]">geopolitical knowledge graph</strong> stack:
            ingest and model events, expose them through a constrained API, and pair structured retrieval with careful
            language generation. It is meant for research, demos, and as a foundation for richer analyst workflows—not
            for automated decisions without human review.
          </p>
        </div>
      </section>

      <footer id="newsletter" className="bg-[#141414] text-[#e8e6e1] border-t border-white/10 scroll-mt-24">
        <div className="max-w-[1100px] mx-auto px-6 sm:px-10 py-16 md:py-20">
          <div className="grid gap-12 md:grid-cols-2 lg:grid-cols-4 md:gap-10">
            <div className="lg:col-span-1">
              <div className="flex items-center gap-2 mb-4">
                <Image
                  src="/logo.png"
                  alt=""
                  width={32}
                  height={32}
                  className="h-8 w-8 object-contain opacity-90"
                  unoptimized
                />
                <span className="font-bold text-lg font-outfit tracking-tight">CHINTU</span>
              </div>
              <p className="text-sm text-white/50 leading-relaxed font-sora">
                Graph-native geopolitical intelligence. Events, influence, and evidence in one loop.
              </p>
            </div>
            <div>
              <h3 className="font-jetbrains text-[11px] uppercase tracking-[0.2em] text-white/40 mb-4">Product</h3>
              <ul className="space-y-2.5 text-sm text-white/65 font-sora">
                <li>
                  <Link href="/chat" className="hover:text-white transition-colors">
                    Open app
                  </Link>
                </li>
                <li>
                  <Link href="#modes" className="hover:text-white transition-colors">
                    Query modes
                  </Link>
                </li>
                <li>
                  <Link href="#how-it-works" className="hover:text-white transition-colors">
                    How it works
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-jetbrains text-[11px] uppercase tracking-[0.2em] text-white/40 mb-4">Resources</h3>
              <ul className="space-y-2.5 text-sm text-white/65 font-sora">
                <li>
                  <span className="text-white/40">GitHub — add your repo URL</span>
                </li>
                <li>
                  <span className="text-white/35">API docs (repo README)</span>
                </li>
                <li>
                  <Link href="#stack" className="hover:text-white transition-colors">
                    Technology
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-jetbrains text-[11px] uppercase tracking-[0.2em] text-white/40 mb-4">Newsletter</h3>
              <p className="text-sm text-white/50 mb-4 font-sora leading-relaxed">
                Occasional updates on graph features and releases. No spam.
              </p>
              {newsletterSubmitted ? (
                <p className="text-sm text-[#5ab87a] font-sora">Thanks — you&apos;re on the list.</p>
              ) : (
                <button
                  type="button"
                  onClick={openNewsletterModal}
                  className="rounded-lg bg-accent text-[#1a1a1a] text-sm font-semibold px-5 py-2.5 hover:bg-accent/90 transition-colors w-full sm:w-auto"
                >
                  Subscribe to newsletter
                </button>
              )}
            </div>
          </div>
          <div className="mt-14 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
            <span className="text-[12px] font-jetbrains text-white/35">
              © {new Date().getFullYear()} CHINTU · TigerGraph knowledge graph
            </span>
            <span className="text-[12px] font-jetbrains text-white/35">Privacy · Terms (placeholder)</span>
          </div>
        </div>
      </footer>

      {newsletterModalOpen && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6"
          role="presentation"
        >
          <button
            type="button"
            aria-label="Close newsletter dialog"
            className="absolute inset-0 bg-black/65 backdrop-blur-[2px]"
            onClick={closeNewsletterModal}
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="newsletter-modal-title"
            className="relative w-full max-w-md rounded-2xl border border-white/12 bg-[#1c1c1c] shadow-2xl shadow-black/40 p-6 sm:p-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4 mb-6">
              <h2 id="newsletter-modal-title" className="text-xl font-bold font-outfit text-white pr-2">
                Subscribe to the newsletter
              </h2>
              <button
                type="button"
                onClick={closeNewsletterModal}
                className="shrink-0 rounded-lg p-1.5 text-white/50 hover:text-white hover:bg-white/10 transition-colors"
                aria-label="Close"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
                  <path
                    d="M5 5l10 10M15 5L5 15"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>
            <p className="text-sm text-white/50 font-sora mb-6 leading-relaxed">
              Get occasional updates on CHINTU—new graph features, releases, and research notes.
            </p>
            {newsletterError && (
              <p className="text-sm text-red-400/95 font-sora mb-4 leading-relaxed" role="alert">
                {newsletterError}
              </p>
            )}
            <form onSubmit={handleNewsletterSubmit} className="flex flex-col gap-4">
              <div>
                <label htmlFor="nl-name" className="block text-[11px] font-jetbrains uppercase tracking-wider text-white/40 mb-2">
                  Name
                </label>
                <input
                  id="nl-name"
                  type="text"
                  name="name"
                  required
                  autoComplete="name"
                  placeholder="Your name"
                  value={newsletterName}
                  onChange={(e) => setNewsletterName(e.target.value)}
                  className="w-full rounded-lg bg-white/[0.08] border border-white/15 px-3 py-2.5 text-sm text-white placeholder:text-white/35 focus:outline-none focus:ring-2 focus:ring-accent/55 focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="nl-email" className="block text-[11px] font-jetbrains uppercase tracking-wider text-white/40 mb-2">
                  Email
                </label>
                <input
                  id="nl-email"
                  type="email"
                  name="email"
                  required
                  autoComplete="email"
                  placeholder="you@organization.org"
                  value={newsletterEmail}
                  onChange={(e) => setNewsletterEmail(e.target.value)}
                  className="w-full rounded-lg bg-white/[0.08] border border-white/15 px-3 py-2.5 text-sm text-white placeholder:text-white/35 focus:outline-none focus:ring-2 focus:ring-accent/55 focus:border-transparent"
                />
              </div>
              <div className="flex flex-col-reverse sm:flex-row gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeNewsletterModal}
                  disabled={newsletterLoading}
                  className="sm:flex-1 rounded-lg border border-white/20 text-white/80 text-sm font-semibold py-2.5 hover:bg-white/5 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={newsletterLoading}
                  className="sm:flex-1 rounded-lg bg-accent text-[#1a1a1a] text-sm font-semibold py-2.5 hover:bg-accent/90 transition-colors disabled:opacity-60"
                >
                  {newsletterLoading ? 'Subscribing…' : 'Subscribe'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
