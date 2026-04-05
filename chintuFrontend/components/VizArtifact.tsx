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
    label: 'Force Graph',
    bg: 'bg-blue/10',
    text: 'text-blue',
  },
  entity_impact: {
    label: 'Entity Cards',
    bg: 'bg-amber/10',
    text: 'text-amber',
  },
  topic_timeline: {
    label: 'Timeline',
    bg: 'bg-accent/10',
    text: 'text-accent',
  },
  causal_chain: {
    label: 'Causal Flow',
    bg: 'bg-green/10',
    text: 'text-green',
  },
};

export default function VizArtifact({ response }: VizArtifactProps) {
  const badge = BADGE_STYLES[response.query] || BADGE_STYLES.causal_explosion_viz;
  const nodeCount = response.graph.nodes.length;
  const linkCount = response.graph.links.length;

  return (
    <div className="mt-3 border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 bg-bg3 border-b border-border">
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-jetbrains font-medium ${badge.bg} ${badge.text}`}
        >
          {badge.label}
        </span>
        <span className="text-[10px] font-jetbrains text-muted">
          {nodeCount} nodes · {linkCount} edges
        </span>
      </div>

      {/* Body */}
      <div className="p-3">
        {(response.query === 'causal_explosion_viz' || response.query === 'causal_chain') && (
          <ForceGraph graph={response.graph} />
        )}
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
