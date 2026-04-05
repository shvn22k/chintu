/**
 * Three CHINTU query modes: causal exploration, narrative trace, integrated (blended) Q&A.
 * Matches backend intents / installed queries where applicable.
 */

export default function ConceptVisuals() {
  return (
    <div className="space-y-14 md:space-y-20">
      <div className="max-w-[720px] mx-auto text-center px-2">
        <p className="text-[17px] md:text-[19px] leading-[1.7] text-black/80 font-sora">
          CHINTU ingests world events into a <strong className="text-black font-semibold">TigerGraph</strong> knowledge
          graph—events, actors, and topics linked by influence and membership. You ask in plain language; we resolve an
          event, run a <strong className="text-black font-semibold">whitelisted graph query</strong>, pull linked
          articles, and return a <strong className="text-black font-semibold">grounded answer</strong> plus an
          interactive subgraph you can explore in the app.
        </p>
      </div>

      <div id="modes" className="grid gap-10 lg:gap-8 lg:grid-cols-3 max-w-[1100px] mx-auto scroll-mt-28">
        {/* 1 — Causal exploration → causal_explosion_viz */}
        <figure className="flex flex-col rounded-2xl border border-black/[0.08] bg-white/80 p-8 shadow-[0_1px_0_rgba(0,0,0,0.04)]">
          <figcaption className="font-outfit text-xl font-bold text-[#1b1b1b] mb-1">Causal exploration</figcaption>
          <p className="text-[12px] font-jetbrains text-black/45 uppercase tracking-wider mb-6">
            Downstream · <span className="text-accent">causal_explosion_viz</span>
          </p>
          <div className="flex-1 flex items-center">
            <svg viewBox="0 0 320 200" className="w-full h-auto" role="img" aria-label="Seed event with forward influence edges">
              <text x="160" y="22" textAnchor="middle" fill="rgba(0,0,0,0.45)" fontSize="10" fontFamily="ui-monospace">
                “What followed from this event?”
              </text>
              <circle cx="160" cy="100" r="22" fill="#c87c5a" fillOpacity="0.35" stroke="#c87c5a" strokeWidth="2" />
              <text x="160" y="104" textAnchor="middle" fill="#1b1b1b" fontSize="11" fontWeight="600" fontFamily="system-ui">
                seed
              </text>
              <line x1="182" y1="92" x2="248" y2="62" stroke="#c87c5a" strokeWidth="2" />
              <polygon points="252,60 246,68 244,58" fill="#c87c5a" />
              <circle cx="268" cy="56" r="16" fill="none" stroke="rgba(0,0,0,0.35)" strokeWidth="1.5" />
              <line x1="182" y1="108" x2="248" y2="138" stroke="#c87c5a" strokeWidth="2" />
              <polygon points="252,140 244,142 246,132" fill="#c87c5a" />
              <circle cx="268" cy="144" r="16" fill="none" stroke="rgba(0,0,0,0.35)" strokeWidth="1.5" />
              <text x="160" y="178" textAnchor="middle" fill="rgba(0,0,0,0.4)" fontSize="10" fontFamily="ui-monospace">
                INFLUENCES → forward hops
              </text>
            </svg>
          </div>
          <p className="mt-4 text-sm text-black/60 leading-relaxed font-sora">
            Expand <strong className="text-black/80">downstream</strong> consequences from a seed event—how effects
            propagate through the graph within bounded hops.
          </p>
        </figure>

        {/* 2 — Narrative trace → narrative_trace */}
        <figure className="flex flex-col rounded-2xl border border-black/[0.08] bg-white/80 p-8 shadow-[0_1px_0_rgba(0,0,0,0.04)]">
          <figcaption className="font-outfit text-xl font-bold text-[#1b1b1b] mb-1">Narrative trace</figcaption>
          <p className="text-[12px] font-jetbrains text-black/45 uppercase tracking-wider mb-6">
            Upstream · <span className="text-blue">narrative_trace</span>
          </p>
          <div className="flex-1 flex items-center">
            <svg viewBox="0 0 320 200" className="w-full h-auto" role="img" aria-label="Predecessor events flowing into seed">
              <text x="160" y="22" textAnchor="middle" fill="rgba(0,0,0,0.45)" fontSize="10" fontFamily="ui-monospace">
                “What led to this?”
              </text>
              <circle cx="52" cy="70" r="14" fill="none" stroke="rgba(0,0,0,0.35)" strokeWidth="1.5" />
              <circle cx="52" cy="130" r="14" fill="none" stroke="rgba(0,0,0,0.35)" strokeWidth="1.5" />
              <line x1="66" y1="72" x2="132" y2="96" stroke="#5a8fc8" strokeWidth="2" />
              <polygon points="136,98 128,100 132,92" fill="#5a8fc8" />
              <line x1="66" y1="128" x2="132" y2="104" stroke="#5a8fc8" strokeWidth="2" />
              <polygon points="136,102 128,100 132,108" fill="#5a8fc8" />
              <circle cx="160" cy="100" r="22" fill="#c87c5a" fillOpacity="0.35" stroke="#c87c5a" strokeWidth="2" />
              <text x="160" y="104" textAnchor="middle" fill="#1b1b1b" fontSize="11" fontWeight="600" fontFamily="system-ui">
                seed
              </text>
              <text x="160" y="178" textAnchor="middle" fill="rgba(0,0,0,0.4)" fontSize="10" fontFamily="ui-monospace">
                Predecessors → backstory
              </text>
            </svg>
          </div>
          <p className="mt-4 text-sm text-black/60 leading-relaxed font-sora">
            Walk <strong className="text-black/80">backward</strong> along influence edges to surface precursors and
            context behind a focal event.
          </p>
        </figure>

        {/* 3 — Blended / integrated pipeline */}
        <figure className="flex flex-col rounded-2xl border border-black/[0.08] bg-white/80 p-8 shadow-[0_1px_0_rgba(0,0,0,0.04)]">
          <figcaption className="font-outfit text-xl font-bold text-[#1b1b1b] mb-1">Blended analysis</figcaption>
          <p className="text-[12px] font-jetbrains text-black/45 uppercase tracking-wider mb-6">
            End-to-end · graph + sources + prose
          </p>
          <div className="flex-1 flex items-center">
            <svg viewBox="0 0 320 200" className="w-full h-auto" role="img" aria-label="Question through resolution subgraph articles and answer">
              <text x="160" y="20" textAnchor="middle" fill="rgba(0,0,0,0.45)" fontSize="10" fontFamily="ui-monospace">
                One question, full picture
              </text>
              <rect x="24" y="48" width="56" height="36" rx="6" fill="rgba(0,0,0,0.05)" stroke="rgba(0,0,0,0.12)" />
              <text x="52" y="70" textAnchor="middle" fill="rgba(0,0,0,0.65)" fontSize="9" fontFamily="system-ui">
                Ask
              </text>
              <line x1="80" y1="66" x2="108" y2="66" stroke="rgba(0,0,0,0.2)" strokeWidth="1.5" />
              <polygon points="112,66 104,62 104,70" fill="rgba(0,0,0,0.25)" />
              <rect x="116" y="48" width="72" height="36" rx="6" fill="#c87c5a" fillOpacity="0.15" stroke="#c87c5a" />
              <text x="152" y="70" textAnchor="middle" fill="#1b1b1b" fontSize="9" fontWeight="600" fontFamily="system-ui">
                Resolve + graph
              </text>
              <line x1="188" y1="66" x2="216" y2="66" stroke="rgba(0,0,0,0.2)" strokeWidth="1.5" />
              <polygon points="220,66 212,62 212,70" fill="rgba(0,0,0,0.25)" />
              <rect x="224" y="48" width="72" height="36" rx="6" fill="#5a8fc8" fillOpacity="0.12" stroke="#5a8fc8" />
              <text x="260" y="70" textAnchor="middle" fill="#1b1b1b" fontSize="9" fontWeight="600" fontFamily="system-ui">
                Sources
              </text>
              <rect x="100" y="108" width="120" height="44" rx="8" fill="rgba(0,0,0,0.04)" stroke="rgba(0,0,0,0.1)" strokeDasharray="4 3" />
              <text x="160" y="128" textAnchor="middle" fill="rgba(0,0,0,0.5)" fontSize="10" fontFamily="system-ui">
                subgraph + excerpts
              </text>
              <text x="160" y="144" textAnchor="middle" fill="rgba(0,0,0,0.45)" fontSize="9" fontFamily="ui-monospace">
                → grounded answer
              </text>
              <text x="160" y="188" textAnchor="middle" fill="rgba(0,0,0,0.4)" fontSize="10" fontFamily="ui-monospace">
                event_text_search · articles · LLM
              </text>
            </svg>
          </div>
          <p className="mt-4 text-sm text-black/60 leading-relaxed font-sora">
            <strong className="text-black/80">Mix retrieval, structure, and language</strong>: resolve the right event,
            run the appropriate trace, attach article evidence, and synthesize—without you picking SQL or query names.
          </p>
        </figure>
      </div>
    </div>
  );
}
