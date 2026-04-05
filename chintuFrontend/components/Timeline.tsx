'use client';

import { GraphNode } from '@/types';

interface TimelineProps {
  graph: {
    nodes: GraphNode[];
  };
}

function getImpactColor(score: number): string {
  if (score >= 0.8) return 'text-red';
  if (score >= 0.6) return 'text-amber';
  return 'text-green';
}

export default function Timeline({ graph }: TimelineProps) {
  const events = graph.nodes
    .filter((n) => n.type === 'Event' && n.timestamp)
    .sort((a, b) => {
      const ta = a.timestamp || '';
      const tb = b.timestamp || '';
      return ta.localeCompare(tb);
    });

  return (
    <div className="space-y-0">
      {events.map((evt, i) => (
        <div key={evt.id} className="flex items-start gap-0">
          {/* Date column */}
          <div className="w-[80px] shrink-0 text-right pr-3 pt-0.5">
            <span className="text-[11px] font-jetbrains text-muted">
              {evt.timestamp || '—'}
            </span>
          </div>

          {/* Vertical line */}
          <div className="flex flex-col items-center shrink-0">
            <div className="w-2 h-2 rounded-full bg-accent mt-1.5" />
            {i < events.length - 1 && (
              <div className="w-px flex-1 bg-accent/30 min-h-[32px]" />
            )}
          </div>

          {/* Event info */}
          <div className="pl-3 pb-4 min-w-0 flex-1">
            <div className="text-sm font-sora text-text">{evt.label}</div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] font-jetbrains text-muted">
                {evt.event_type || 'event'}
              </span>
              {evt.impact_score != null && (
                <span className={`text-[10px] font-jetbrains ${getImpactColor(evt.impact_score)}`}>
                  impact: {evt.impact_score.toFixed(2)}
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
