/**
 * Map CHINTU Flask `POST /api/v1/chat/complete` JSON into the UI `BackendResponse` shape.
 */

import type { BackendResponse, GraphLink, GraphNode, QueryType } from '@/types';

export interface ChintuChatCompleteResponse {
  version?: string;
  answer: string;
  graph_viz: {
    nodes: ChintuGraphVizNode[];
    edges: ChintuGraphVizEdge[];
  };
  sources: {
    articles?: unknown[];
    graph_query: { name: string; params: Record<string, unknown> } | null;
  };
  meta?: Record<string, unknown>;
  error?: string;
}

export interface ChintuGraphVizNode {
  id: string;
  label: string;
  type: string;
  attributes?: Record<string, unknown>;
}

export interface ChintuGraphVizEdge {
  source: string;
  target: string;
  type?: string;
  attributes?: Record<string, unknown>;
}

function parseStrength(v: unknown): number {
  const n = parseFloat(String(v ?? ''));
  if (Number.isFinite(n)) return Math.min(1, Math.max(0.15, Math.abs(n)));
  return 0.55;
}

function parsePolarity(v: unknown): 1 | -1 {
  if (v === -1 || v === '-1') return -1;
  const n = Number(v);
  if (Number.isFinite(n) && n < 0) return -1;
  return 1;
}

function flattenEventAttributes(attrs: Record<string, unknown> | undefined): Partial<GraphNode> {
  if (!attrs) return {};
  const out: Partial<GraphNode> = {};
  const pick = (k: string) => (attrs[k] != null ? String(attrs[k]) : undefined);
  const ts = pick('timestamp') || pick('date');
  if (ts) out.timestamp = ts;
  const loc = pick('location') || pick('ActionGeo_FullName');
  if (loc) out.location = loc;
  const url = pick('source_url') || pick('SOURCEURL');
  if (url) out.source_url = url;
  const imp = attrs.impact_score ?? attrs.implicit_impact ?? attrs.GoldsteinScale;
  if (imp != null && !Number.isNaN(Number(imp))) {
    const x = Number(imp);
    out.impact_score = x >= 0 && x <= 1 ? x : Math.min(1, Math.abs(x) / 10);
  }
  const hop = attrs.hop_count;
  if (hop != null && hop !== "" && !Number.isNaN(Number(hop))) {
    out.hop_count = Number(hop);
  }
  const cs = attrs.cumulative_strength;
  if (cs != null && cs !== "" && !Number.isNaN(Number(cs))) {
    out.cumulative_strength = Number(cs);
  }
  const et = pick("event_type");
  if (et) out.event_type = et;
  return out;
}

function coerceNodeType(t: string): GraphNode['type'] {
  if (t === 'Entity') return 'Entity';
  if (t === 'Topic') return 'Topic';
  return 'Event';
}

export function mapQueryNameToQueryType(name: string | undefined | null): QueryType {
  const n = (name || '').trim();
  if (n === 'narrative_trace') return 'narrative_trace';
  if (n === 'event_text_search') return 'event_text_search';
  if (n === 'causal_explosion_viz') return 'causal_explosion_viz';
  return 'causal_explosion_viz';
}

function resolveSeedEventId(
  sources: ChintuChatCompleteResponse['sources'],
  meta: Record<string, unknown> | undefined
): string | undefined {
  const params = sources?.graph_query?.params as Record<string, unknown> | undefined;
  const fromParams = params?.event_id;
  if (typeof fromParams === 'string' && fromParams.startsWith('evt_')) return fromParams;

  const er = meta?.event_resolution as Record<string, unknown> | undefined;
  const picked = er?.picked_event_id;
  if (typeof picked === 'string' && picked.startsWith('evt_')) return picked;
  return undefined;
}

export function mapChintuCompleteToBackendResponse(raw: ChintuChatCompleteResponse): BackendResponse {
  const query = mapQueryNameToQueryType(raw.sources?.graph_query?.name);
  const seedEventId = resolveSeedEventId(raw.sources, raw.meta);

  const rawNodes = raw.graph_viz?.nodes || [];
  const seenIds = new Set<string>();
  const deduped = rawNodes.filter((n) => {
    if (!n.id || seenIds.has(n.id)) return false;
    seenIds.add(n.id);
    return true;
  });

  const nodes: GraphNode[] = deduped.map((n) => {
    const type = coerceNodeType(n.type || 'Event');
    const flat = flattenEventAttributes(n.attributes);
    return {
      id: n.id,
      label: n.label || n.id,
      type,
      ...flat,
      is_seed: seedEventId ? n.id === seedEventId : false,
    };
  });

  const links: GraphLink[] = (raw.graph_viz?.edges || []).map((e) => ({
    source: e.source,
    target: e.target,
    strength: parseStrength(e.attributes?.strength),
    polarity: parsePolarity(e.attributes?.polarity),
    lag_days:
      e.attributes?.lag_days != null && e.attributes.lag_days !== ''
        ? Number(e.attributes.lag_days)
        : undefined,
    influence_type:
      e.attributes?.influence_type != null ? String(e.attributes.influence_type) : undefined,
  }));

  return {
    query,
    seed_event_id: seedEventId,
    graph: { nodes, links },
    text: raw.answer || '',
    apiError: raw.error,
    meta: raw.meta,
    sources: raw.sources,
  };
}
