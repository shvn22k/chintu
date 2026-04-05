export type QueryType =
  | "causal_explosion_viz"
  | "narrative_trace"
  | "event_text_search"
  | "entity_impact"
  | "topic_timeline"
  | "causal_chain";

export interface GraphNode {
  id: string;
  label: string;
  type: "Event" | "Entity" | "Topic";
  event_type?: string;
  entity_type?: string;
  timestamp?: string;
  impact_score?: number;
  severity?: number;
  influence_score?: number;
  location?: string;
  source_url?: string;
  hop_count?: number;
  /** From CHINTU causal_explosion_viz (used for size / layout when impact_score is tiny). */
  cumulative_strength?: number;
  is_seed?: boolean;
  role?: string;
}

export interface GraphLink {
  source: string;
  target: string;
  strength: number;
  lag_days?: number;
  polarity: 1 | -1;
  influence_type?: string;
  edge_type?: string;
}

/** UI bundle after adapting CHINTU API (or legacy mock). */
export interface BackendResponse {
  query: QueryType;
  seed_event_id?: string;
  graph: {
    nodes: GraphNode[];
    links: GraphLink[];
  };
  text?: string;
  /** Set when Flask returned `error` in the envelope (still often HTTP 200). */
  apiError?: string;
  meta?: Record<string, unknown>;
  sources?: {
    articles?: unknown[];
    graph_query: { name: string; params: Record<string, unknown> } | null;
  };
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: BackendResponse;
}
