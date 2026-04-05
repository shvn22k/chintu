import { NextRequest, NextResponse } from "next/server";
import { BackendResponse } from "@/types";

const causalExplosionMock: BackendResponse = {
  query: "causal_explosion_viz",
  seed_event_id: "evt_001",
  graph: {
    nodes: [
      { id: "evt_001", label: "US–China Tariff Escalation", type: "Event", event_type: "trade_war", impact_score: 0.95, is_seed: true, timestamp: "2025-12-01", location: "Washington DC" },
      { id: "evt_002", label: "EU Retaliatory Tariffs", type: "Event", event_type: "trade_policy", impact_score: 0.7, hop_count: 1, timestamp: "2025-12-15" },
      { id: "evt_003", label: "Global Supply Chain Disruption", type: "Event", event_type: "economic_shock", impact_score: 0.85, hop_count: 1, timestamp: "2026-01-03" },
      { id: "evt_004", label: "ASEAN Emergency Summit", type: "Event", event_type: "diplomatic", impact_score: 0.6, hop_count: 2, timestamp: "2026-01-20" },
      { id: "ent_001", label: "United States", type: "Entity", entity_type: "country", influence_score: 0.9 },
      { id: "ent_002", label: "China", type: "Entity", entity_type: "country", influence_score: 0.88 },
      { id: "ent_003", label: "European Union", type: "Entity", entity_type: "organization", influence_score: 0.75 },
      { id: "ent_004", label: "WTO", type: "Entity", entity_type: "organization", influence_score: 0.5 },
      { id: "top_001", label: "Trade War", type: "Topic", impact_score: 0.9 },
      { id: "top_002", label: "Supply Chain Risk", type: "Topic", impact_score: 0.78 },
      { id: "top_003", label: "Diplomatic Tensions", type: "Topic", impact_score: 0.65 },
    ],
    links: [
      { source: "evt_001", target: "evt_002", strength: 0.8, lag_days: 14, polarity: 1, influence_type: "causal" },
      { source: "evt_001", target: "evt_003", strength: 0.9, lag_days: 33, polarity: -1, influence_type: "causal" },
      { source: "evt_002", target: "evt_004", strength: 0.5, lag_days: 36, polarity: 1, influence_type: "causal" },
      { source: "evt_001", target: "ent_001", strength: 0.85, polarity: 1, influence_type: "actor" },
      { source: "evt_001", target: "ent_002", strength: 0.85, polarity: -1, influence_type: "actor" },
      { source: "evt_002", target: "ent_003", strength: 0.7, polarity: 1, influence_type: "actor" },
      { source: "evt_003", target: "ent_004", strength: 0.4, polarity: 1, influence_type: "institutional" },
      { source: "evt_001", target: "top_001", strength: 0.95, polarity: 1, influence_type: "topic" },
      { source: "evt_003", target: "top_002", strength: 0.8, polarity: -1, influence_type: "topic" },
      { source: "evt_004", target: "top_003", strength: 0.6, polarity: 1, influence_type: "topic" },
    ],
  },
  text: "The US–China Tariff Escalation in December 2025 triggered a causal chain of 3 downstream events across 2 hops. The EU responded with retaliatory tariffs within 14 days, while global supply chains experienced significant disruption. The ASEAN bloc convened an emergency summit to address the diplomatic fallout. Key entities affected include the United States, China, and the European Union, with the WTO facing institutional pressure to mediate.",
};

const entityImpactMock: BackendResponse = {
  query: "entity_impact",
  graph: {
    nodes: [
      { id: "ent_usa", label: "United States", type: "Entity", entity_type: "country", influence_score: 0.92 },
      { id: "evt_tariff", label: "Tariff Announcement", type: "Event", event_type: "trade_policy", impact_score: 0.9, role: "initiator", timestamp: "2025-11-15" },
      { id: "evt_sanction", label: "Semiconductor Export Ban", type: "Event", event_type: "sanction", impact_score: 0.85, role: "initiator", timestamp: "2025-12-01" },
      { id: "evt_alliance", label: "AUKUS Expansion", type: "Event", event_type: "military_alliance", impact_score: 0.7, role: "initiator", timestamp: "2026-01-10" },
      { id: "evt_climate", label: "COP31 Withdrawal Threat", type: "Event", event_type: "environmental", impact_score: 0.6, role: "target", timestamp: "2026-02-05" },
      { id: "evt_cyber", label: "Cyber Infrastructure Attack", type: "Event", event_type: "cyber_warfare", impact_score: 0.82, role: "target", timestamp: "2026-02-20" },
    ],
    links: [
      { source: "ent_usa", target: "evt_tariff", strength: 0.9, polarity: 1, influence_type: "actor" },
      { source: "ent_usa", target: "evt_sanction", strength: 0.85, polarity: 1, influence_type: "actor" },
      { source: "ent_usa", target: "evt_alliance", strength: 0.7, polarity: 1, influence_type: "actor" },
      { source: "ent_usa", target: "evt_climate", strength: 0.6, polarity: -1, influence_type: "actor" },
      { source: "ent_usa", target: "evt_cyber", strength: 0.82, polarity: -1, influence_type: "actor" },
    ],
  },
  text: "The United States (influence score: 0.92) is connected to 5 significant geopolitical events. As an initiator, the US drove the Tariff Announcement, Semiconductor Export Ban, and AUKUS Expansion. As a target, the US faced the COP31 Withdrawal Threat and a major Cyber Infrastructure Attack.",
};

const topicTimelineMock: BackendResponse = {
  query: "topic_timeline",
  graph: {
    nodes: [
      { id: "evt_t1", label: "South China Sea Patrol Clash", type: "Event", event_type: "military_incident", impact_score: 0.75, timestamp: "2025-09-12" },
      { id: "evt_t2", label: "Taiwan Strait Surveillance Spike", type: "Event", event_type: "intelligence", impact_score: 0.68, timestamp: "2025-10-04" },
      { id: "evt_t3", label: "Philippines Base Agreement", type: "Event", event_type: "military_alliance", impact_score: 0.72, timestamp: "2025-11-18" },
      { id: "evt_t4", label: "ASEAN Maritime Code Adopted", type: "Event", event_type: "diplomatic", impact_score: 0.55, timestamp: "2026-01-07" },
      { id: "evt_t5", label: "US Navy Freedom of Navigation Op", type: "Event", event_type: "military_operation", impact_score: 0.88, timestamp: "2026-02-14" },
      { id: "evt_t6", label: "Bilateral De-escalation Talks", type: "Event", event_type: "diplomatic", impact_score: 0.5, timestamp: "2026-03-22" },
    ],
    links: [
      { source: "evt_t1", target: "evt_t2", strength: 0.6, lag_days: 22, polarity: 1, influence_type: "causal" },
      { source: "evt_t2", target: "evt_t3", strength: 0.55, lag_days: 45, polarity: 1, influence_type: "causal" },
      { source: "evt_t3", target: "evt_t4", strength: 0.45, lag_days: 50, polarity: 1, influence_type: "causal" },
      { source: "evt_t4", target: "evt_t5", strength: 0.7, lag_days: 38, polarity: -1, influence_type: "causal" },
      { source: "evt_t5", target: "evt_t6", strength: 0.5, lag_days: 36, polarity: 1, influence_type: "causal" },
    ],
  },
  text: "The Indo-Pacific Security topic shows 6 events spanning from September 2025 to March 2026. Escalation peaked with the US Navy Freedom of Navigation Operation (impact: 0.88), followed by de-escalation talks. The causal chain progresses from military incidents through diplomatic responses.",
};

const causalChainMock: BackendResponse = {
  query: "causal_chain",
  seed_event_id: "evt_c1",
  graph: {
    nodes: [
      { id: "evt_c1", label: "Russian Gas Pipeline Shutdown", type: "Event", event_type: "energy_crisis", impact_score: 0.92, is_seed: true, timestamp: "2025-10-01" },
      { id: "evt_c2", label: "EU Energy Emergency Declared", type: "Event", event_type: "policy_response", impact_score: 0.8, hop_count: 1, timestamp: "2025-10-15" },
      { id: "evt_c3", label: "Industrial Output Decline", type: "Event", event_type: "economic_shock", impact_score: 0.75, hop_count: 1, timestamp: "2025-11-02" },
      { id: "evt_c4", label: "LNG Import Surge from Qatar", type: "Event", event_type: "trade_shift", impact_score: 0.6, hop_count: 2, timestamp: "2025-11-20" },
      { id: "ent_russia", label: "Russia", type: "Entity", entity_type: "country", influence_score: 0.85 },
      { id: "ent_eu", label: "European Union", type: "Entity", entity_type: "organization", influence_score: 0.78 },
      { id: "top_energy", label: "Energy Security", type: "Topic", impact_score: 0.88 },
    ],
    links: [
      { source: "evt_c1", target: "evt_c2", strength: 0.9, lag_days: 14, polarity: -1, influence_type: "causal" },
      { source: "evt_c1", target: "evt_c3", strength: 0.75, lag_days: 32, polarity: -1, influence_type: "causal" },
      { source: "evt_c2", target: "evt_c4", strength: 0.6, lag_days: 36, polarity: 1, influence_type: "causal" },
      { source: "evt_c1", target: "ent_russia", strength: 0.85, polarity: -1, influence_type: "actor" },
      { source: "evt_c2", target: "ent_eu", strength: 0.78, polarity: 1, influence_type: "actor" },
      { source: "evt_c1", target: "top_energy", strength: 0.88, polarity: -1, influence_type: "topic" },
    ],
  },
  text: "Tracing the causal chain from the Russian Gas Pipeline Shutdown: within 14 days, the EU declared an energy emergency. Industrial output declined by the second hop, while the EU pivoted to LNG imports from Qatar. The energy security topic remains critically affected with an impact score of 0.88.",
};

export async function POST(request: NextRequest) {
  const { message } = await request.json();
  const lower = message.toLowerCase();

  await new Promise((r) => setTimeout(r, 800 + Math.random() * 700));

  let response: BackendResponse;

  if (lower.includes("entity") || lower.includes("usa") || lower.includes("impact")) {
    response = entityImpactMock;
  } else if (lower.includes("timeline") || lower.includes("topic")) {
    response = topicTimelineMock;
  } else if (lower.includes("chain")) {
    response = causalChainMock;
  } else {
    response = causalExplosionMock;
  }

  return NextResponse.json(response);
}
