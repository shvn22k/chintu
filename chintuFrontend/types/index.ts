export type QueryType =
  | "causal_explosion_viz"
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

export interface BackendResponse {
  query: QueryType;
  seed_event_id?: string;
  graph: {
    nodes: GraphNode[];
    links: GraphLink[];
  };
  text?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: BackendResponse;
}
