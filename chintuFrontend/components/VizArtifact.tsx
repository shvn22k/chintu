'use client';

import { BackendResponse } from '@/types';
import ForceGraph from './ForceGraph';
import EntityCards from './EntityCards';
import Timeline from './Timeline';

interface VizArtifactProps {
  response: BackendResponse;
}

const BADGE_STYLES: Record<string, { label: string; bg: string; text: string }> = {
  causal_explosion_viz: {
    label: 'Causal graph',
    bg: 'bg-blue/10',
    text: 'text-blue',
  },
  narrative_trace: {
    label: 'Narrative trace',
    bg: 'bg-green/10',
    text: 'text-green',
  },
  event_text_search: {
    label: 'Event search',
    bg: 'bg-amber/10',
    text: 'text-amber',
  },
  entity_impact: {
    label: 'Entity cards',
    bg: 'bg-amber/10',
    text: 'text-amber',
  },
  topic_timeline: {
    label: 'Timeline',
    bg: 'bg-accent/10',
    text: 'text-accent',
  },
  causal_chain: {
    label: 'Causal flow',
    bg: 'bg-green/10',
    text: 'text-green',
  },
};

export default function VizArtifact({ response }: VizArtifactProps) {
  const badge = BADGE_STYLES[response.query] || BADGE_STYLES.causal_explosion_viz;
  const nodeCount = response.graph.nodes.length;
  const linkCount = response.graph.links.length;

  const useForceGraph =
    response.query === 'causal_explosion_viz' ||
    response.query === 'narrative_trace' ||
    response.query === 'event_text_search' ||
    response.query === 'causal_chain';

  return (
    <div className="mt-3 border border-border rounded-lg overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 bg-bg3 border-b border-border">
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-jetbrains font-medium ${badge.bg} ${badge.text}`}
        >
          {badge.label}
        </span>
        <span className="text-[10px] font-jetbrains text-muted">
          {nodeCount} nodes · {linkCount} edges
        </span>
        {response.sources?.graph_query?.name && (
          <span className="text-[10px] font-jetbrains text-muted/70 truncate ml-auto max-w-[140px]">
            {response.sources.graph_query.name}
          </span>
        )}
      </div>

      <div className="p-3">
        {useForceGraph &&
          (nodeCount > 0 ? (
            <ForceGraph graph={response.graph} />
          ) : (
            <p className="text-muted text-xs py-6 text-center font-jetbrains leading-relaxed">
              No graph nodes in this response (empty subgraph or resolution-only). The answer above still reflects
              available context.
            </p>
          ))}
        {response.query === 'entity_impact' && (
          <EntityCards graph={response.graph} />
        )}
        {response.query === 'topic_timeline' && (
          <Timeline graph={response.graph} />
        )}
      </div>
    </div>
  );
}
