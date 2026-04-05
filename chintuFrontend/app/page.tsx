'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';

export default function LandingPage() {
  const router = useRouter();
  const [transitioning, setTransitioning] = useState(false);

  const handleNavigate = useCallback(() => {
    setTransitioning(true);
    // Smooth transition delay to let animation finish
    setTimeout(() => {
      router.push('/chat');
    }, 600);
  }, [router]);

  return (
    <div className={`landing-page min-h-screen flex flex-col font-sora ${transitioning ? 'page-fade-out' : ''}`}>
      {/* Navbar - Light Editorial */}
      <nav className="w-full border-b bg-[#faf9f6]/80 backdrop-blur-md border-black/5 sticky top-0 z-30">
        <div className="max-w-[1200px] mx-auto px-10 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="border-[1.5px] border-black/80 rounded-[4px] px-1.5 py-0.5 font-jetbrains text-[12px] text-black font-bold tracking-tight">
                CHN
              </div>
              <span className="font-bold text-[18px] tracking-tight">CHINTU</span>
            </div>
            <div className="hidden md:flex items-center gap-7">
              <span className="text-sm text-black/60 font-medium">Research</span>
              <span className="text-sm text-black/60 font-medium">Graph</span>
              <span className="text-sm text-black/60 font-medium">Docs</span>
            </div>
          </div>
          <button
            onClick={handleNavigate}
            className="px-5 py-2 rounded-full bg-black text-white text-sm font-semibold hover:bg-black/80 transition-all cursor-pointer"
          >
            Launch App
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-[1200px] mx-auto px-10 pt-28 pb-20">
        <div className="flex flex-col items-center text-center">
          <span className="text-[14px] font-bold font-outfit text-black uppercase tracking-[0.25em] mb-8">
            Geopolitical intelligence
          </span>
          <h1 className="text-[72px] leading-[1.1] font-bold font-outfit tracking-tight max-w-[900px]">
            What&apos;s happening <br />
            <span className="text-accent">in the world?</span>
          </h1>
          <p className="mt-8 text-[20px] font-bold font-outfit text-black/80 tracking-tight">
            Causal chains · Entity networks · Event timelines · Knowledge graphs
          </p>
          <button
            onClick={handleNavigate}
            className="mt-12 px-8 py-3.5 rounded-full bg-accent text-[#fbfaf8] text-lg font-semibold shadow-lg shadow-accent/10 hover:scale-[1.02] transition-transform cursor-pointer"
          >
            Start analysis →
          </button>
        </div>
      </main>


      {/* Editorial Section - Replicating Anthropic Style */}
      <section className="bg-white py-32 border-t border-black/5">
        <div className="max-w-[760px] mx-auto px-10">
          <div className="text-center mb-16">
            <span className="text-sm font-bold text-black/90 tracking-wide uppercase font-jetbrains mb-6 block">
              Announcements
            </span>
            <h2 className="text-[72px] font-bold text-black tracking-tight leading-none mb-6">
              Introducing CHINTU
            </h2>
            <p className="text-[15px] font-jetbrains text-black/50 mb-10 italic">
              Causal Heterogeneous Intelligence Network for Threat Understanding
            </p>
            <span className="text-[15px] font-jetbrains text-black/40">5 April 2026</span>
          </div>

          <div className="space-y-10">
            {/* Image Placeholder stylized like the logo sketch in the provided img */}
            <div className="w-full aspect-[16/9] bg-[#f2f0eb] rounded-2xl border border-black/5 flex items-center justify-center p-10 overflow-hidden">
               <svg width="240" height="240" viewBox="0 0 240 240" fill="none">
                 <path d="M120 40C120 40 80 120 60 160C40 200 80 200 80 200" stroke="black" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                 <path d="M120 40C120 40 160 120 180 160C200 200 160 200 160 200" stroke="black" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                 <circle cx="120" cy="40" r="12" fill="#c87c5a" />
                 <circle cx="60" cy="160" r="10" fill="#5a8fc8" />
                 <circle cx="180" cy="160" r="10" fill="#5ab87a" />
                 <circle cx="120" cy="180" r="8" fill="#c8a85a" />
               </svg>
            </div>

            <div className="text-[19px] leading-[1.75] font-serif text-black/85 space-y-8">
              <p>
                After working for several months on foundational geopolitical graph modeling, we&apos;re 
                excited to introduce <span className="font-bold underline decoration-accent/30 underline-offset-4">CHINTU</span> — a next-generation 
                intelligence assistant based on TigerGraph&apos;s robust causal infrastructure. 
                Accessible through an intuitive chat interface and advanced visualization console, 
                CHINTU is capable of mapping complex world events with high degree of reliability.
              </p>

              <p>
                CHINTU models the world as a heterogeneous graph where <strong>events, entities, and topics</strong> form the core nodes. 
                Unlike traditional news feeds, CHINTU surfaces the <em>causal chains</em> that link these nodes, enabling 
                analysts to see not just what happened, but the subsequent shockwaves across diplomatic, 
                economic, and security domains.
              </p>

              <p>
                The system helps with several critical intelligence use cases:
              </p>
              
              <ul className="list-none space-y-4 pt-2">
                <li className="flex gap-4">
                  <span className="text-accent font-bold">·</span>
                  <span><strong>Causal Explosion:</strong> Trace the blast radius of a seed event across multiple causal hops.</span>
                </li>
                <li className="flex gap-4">
                  <span className="text-accent font-bold">·</span>
                  <span><strong>Entity Impact:</strong> Understand how a country or organization influences and is influenced by the network.</span>
                </li>
                <li className="flex gap-4">
                  <span className="text-accent font-bold">·</span>
                  <span><strong>Topic Timeline:</strong> Reconstruct the historical arc of emerging threats and diplomatic shifts.</span>
                </li>
              </ul>

              <p className="pt-4">
                By encoding geopolitical knowledge as a persistent graph, CHINTU enables patterns to emerge 
                from the noise of the global news cycle. It represents our commitment to building transparent, 
                accurate intelligence tools that empower decision-makers with graph intelligence.
              </p>
              
              <div className="pt-8 flex justify-center">
                 <button 
                  onClick={handleNavigate}
                  className="px-10 py-4 rounded-full bg-black text-white text-lg font-bold hover:bg-black/90 transition-all cursor-pointer"
                 >
                   Try CHINTU
                 </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-20 bg-white border-t border-black/5 text-center">
        <span className="text-[12px] font-jetbrains text-black/40 font-medium">
          CHINTU · TIGERGRAPH KNOWLEDGE GRAPH · 2026
        </span>
      </footer>
    </div>
  );
}
