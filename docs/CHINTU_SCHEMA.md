# CHINTU - TigerGraph Schema

**Causal and Hierarchical Intelligence for Narrative Tracking and Understanding**

## Graph Overview

| Metric | Count |
|--------|-------|
| Events | 5 |
| Entities | 3 |
| Topics | 2 |

---

## Vertex Types

### 1. Event
Real-world events with temporal and contextual attributes.

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | STRING | Primary key (unique event identifier) |
| `title` | STRING | Event title/headline |
| `description` | STRING | Detailed event description |
| `event_type` | STRING | Category: political, economic, military, social |
| `timestamp` | DATETIME | When the event occurred |
| `severity` | FLOAT | Severity level (0.0 - 1.0) |
| `impact_score` | FLOAT | **Event importance/impact** (0.0 - 1.0) |
| `location` | STRING | Geographic location |
| `source_url` | STRING | Reference URL |

### 2. Entity
Countries, organizations, people, and other actors.

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | STRING | Primary key |
| `name` | STRING | Display name |
| `entity_type` | STRING | Type: country, organization, person |
| `description` | STRING | Entity description |
| `influence_score` | FLOAT | Global influence (0.0 - 1.0) |

### 3. Topic
Thematic categories for event classification.

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | STRING | Primary key |
| `name` | STRING | Topic name |
| `description` | STRING | Topic description |
| `keywords` | STRING | Comma-separated keywords |

---

## Edge Types

### 1. INFLUENCES (Event → Event)
**Causal relationship** - One event causes or contributes to another.

| Attribute | Type | Description |
|-----------|------|-------------|
| `strength` | FLOAT | Influence strength (0.0 - 1.0) |
| `lag_days` | INT | Time delay between events (days) |
| `polarity` | INT | **Direction of influence: +1 (same direction) or -1 (opposite)** |
| `influence_type` | STRING | direct, indirect, enabling, constraining |

**Polarity Examples:**
- Oil price ↑ → Inflation ↑ → `polarity: +1` (positive correlation)
- Interest rate ↑ → Demand ↓ → `polarity: -1` (negative correlation)

**Use for:** Multi-hop causal reasoning, narrative chains, propagation simulation

### 2. INVOLVES (Event → Entity)
**Participation relationship** - An entity is involved in an event.

| Attribute | Type | Description |
|-----------|------|-------------|
| `role` | STRING | initiator, target, mediator, observer, victim |
| `sentiment` | STRING | positive, negative, neutral |

**Use for:** Entity impact analysis

### 3. RELATED_TO (Event ↔ Event)
**Non-causal similarity** - Events are thematically or contextually related.

| Attribute | Type | Description |
|-----------|------|-------------|
| `relation_type` | STRING | same_topic, same_region, temporal_proximity |
| `similarity_score` | FLOAT | Similarity measure (0.0 - 1.0) |

**Use for:** Finding related narratives, clustering events

### 4. BELONGS_TO (Event → Topic)
**Categorization** - Event belongs to a topic.

| Attribute | Type | Description |
|-----------|------|-------------|
| `relevance_score` | FLOAT | Topic relevance (0.0 - 1.0) |

**Use for:** Topic-based filtering and analysis

### 5. AFFILIATED_WITH (Entity → Entity)
**Inter-entity relationship** - Relationship between entities.

| Attribute | Type | Description |
|-----------|------|-------------|
| `affiliation_type` | STRING | ally, rival, member, subsidiary, partner |
| `start_date` | STRING | Relationship start date |
| `end_date` | STRING | Relationship end date (empty if ongoing) |

**Use for:** Understanding entity networks

---

## Sample Data Structure

```
                         ┌─────────────────┐
                         │  Topic:Economy  │
                         └────────▲────────┘
                                  │ BELONGS_TO
                                  │
┌──────────────┐    ┌─────────────┴─────────────┐    ┌──────────────────┐
│ Entity:USA   │◄───│ Event:Tariffs             │───►│ Entity:China     │
│ (initiator)  │    │ impact: 0.85              │    │ (target)         │
└──────────────┘    └─────────────┬─────────────┘    └──────────────────┘
       │                          │ INFLUENCES (strength:0.9, lag:5, polarity:+1)
       │                          ▼
       │            ┌─────────────────────────────┐
       │            │ Event:Retaliation           │───► Entity:China
       │            │ impact: 0.80                │
       │            └─────────────┬───────────────┘
       │                          │ INFLUENCES (strength:0.7, lag:12, polarity:+1)
       │                          ▼
       │            ┌─────────────────────────────┐    ┌──────────────────┐
       │            │ Event:G20 Summit            │───►│ Entity:EU        │
       │            │ impact: 0.75                │    │ (mediator)       │
       │            └─────────────┬───────────────┘    └──────────────────┘
       │                          │                           ▲
       │ AFFILIATED_WITH          │ BELONGS_TO                │
       │ (ally)                   ▼                           │
       └──────────────────┐ ┌─────────────────┐               │
                          └─│Topic:Geopolitics│───────────────┘
                            └─────────────────┘

  Additional causal chain:
  
  ┌─────────────────┐     INFLUENCES (0.5, lag:10, +1)      ┌─────────────────┐
  │ Event:Tariffs   │ ─────────────────────────────────────►│ Event:Oil Spike │
  └─────────────────┘                                       └────────┬────────┘
                                                                     │
                                        INFLUENCES (0.8, lag:10, +1) │
                                                                     ▼
                                                          ┌──────────────────────┐
                                                          │ Event:Inflation Rise │
                                                          │ impact: 0.72         │
                                                          └──────────────────────┘
```

---

## Example Queries

### 1. Trace Causal Chain (Multi-hop)
Find all events influenced by a starting event:

```gsql
CREATE QUERY trace_causal_chain(VERTEX<Event> start_event, INT max_hops) FOR GRAPH CHINTU {
  SetAccum<EDGE> @@edges;
  events = {start_event};
  
  FOREACH i IN RANGE[1, max_hops] DO
    events = SELECT t FROM events:s -(INFLUENCES:e)-> Event:t
             ACCUM @@edges += e;
  END;
  
  PRINT events;
  PRINT @@edges;
}
```

### 2. Entity Impact Analysis
Find all events involving a specific entity:

```gsql
CREATE QUERY entity_impact(VERTEX<Entity> target_entity) FOR GRAPH CHINTU {
  events = SELECT e FROM Entity:ent -(INVOLVES:inv)- Event:e
           WHERE ent == target_entity;
  PRINT events;
}
```

### 3. Topic Narrative Timeline
Get chronological events for a topic:

```gsql
CREATE QUERY topic_timeline(VERTEX<Topic> topic) FOR GRAPH CHINTU {
  events = SELECT e FROM Topic:t -(BELONGS_TO:b)- Event:e
           WHERE t == topic
           ORDER BY e.timestamp ASC;
  PRINT events;
}
```

---

## Connection Details

- **Graph Name:** CHINTU
- **API Version:** v2

---

## Next Steps

1. **Add more data** - Use the `insert_sample_data` query as a template
2. **Create analysis queries** - Build multi-hop traversal queries
3. **Set up loading jobs** - For bulk data ingestion from CSV/JSON
4. **Add vector attributes** - For semantic similarity search (TigerGraph 4.2+)
