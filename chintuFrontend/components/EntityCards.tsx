'use client';

import { GraphNode, GraphLink } from '@/types';

interface EntityCardsProps {
  graph: {
    nodes: GraphNode[];
    links: GraphLink[];
  };
}

function getImpactColor(score: number): string {
  if (score >= 0.8) return 'text-red';
  if (score >= 0.6) return 'text-amber';
  return 'text-green';
}

function getImpactBg(score: number): string {
  if (score >= 0.8) return 'bg-red/10';
  if (score >= 0.6) return 'bg-amber/10';
  return 'bg-green/10';
}

export default function EntityCards({ graph }: EntityCardsProps) {
  const entities = graph.nodes.filter((n) => n.type === 'Entity');
  const events = graph.nodes.filter((n) => n.type === 'Event');

  return (
    <div className="space-y-3">
      {entities.map((entity) => {
        const connectedEventIds = graph.links
          .filter((l) => l.source === entity.id || l.target === entity.id)
          .map((l) => (l.source === entity.id ? l.target : l.source));

        const connectedEvents = events.filter((e) =>
          connectedEventIds.includes(e.id)
        );

        return (
          <div key={entity.id} className="border border-border rounded-lg overflow-hidden">
            {/* Entity header */}
            <div className="flex items-center gap-3 px-3 py-2.5 bg-bg3">
              <div className="w-8 h-8 rounded-full bg-green/15 border border-green/20 flex items-center justify-center text-xs font-jetbrains text-green font-medium">
                {entity.label.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-sora text-text truncate">{entity.label}</div>
                <div className="text-[10px] font-jetbrains text-muted">
                  {entity.entity_type || 'entity'}
                </div>
              </div>
              <div className="text-xs font-jetbrains text-green">
                {entity.influence_score?.toFixed(2)}
              </div>
            </div>

            {/* Event rows */}
            {connectedEvents.length > 0 && (
              <div className="divide-y divide-border">
                {connectedEvents.map((evt) => (
                  <div key={evt.id} className="flex items-center justify-between px-3 py-2">
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-sora text-text truncate">{evt.label}</div>
                      <div className="text-[10px] font-jetbrains text-muted mt-0.5">
                        {evt.event_type || 'event'}
                        {evt.role ? ` · role: ${evt.role}` : ''}
                      </div>
                    </div>
                    <div
                      className={`ml-3 px-2 py-0.5 rounded text-xs font-jetbrains ${getImpactColor(
                        evt.impact_score || 0
                      )} ${getImpactBg(evt.impact_score || 0)}`}
                    >
                      {(evt.impact_score || 0).toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
