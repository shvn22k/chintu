"""
CHINTU GDELT Parser
Parses GDELT event data into CHINTU graph format:
- Events, Entities, Topics
- INVOLVES edges (Event -> Entity)
- Prepares data for TigerGraph loading
"""

import _bootstrap  # noqa: F401

import pandas as pd
import glob
import os
from datetime import datetime
from collections import defaultdict
import hashlib

# GDELT Column indices (GDELT 2.0 Event format)
COLS = {
    'global_event_id': 0,
    'date': 1,
    'year': 3,
    'actor1_code': 5,
    'actor1_name': 6,
    'actor1_country': 7,
    'actor1_type1': 8,
    'actor2_code': 15,
    'actor2_name': 16,
    'actor2_country': 17,
    'actor2_type1': 18,
    'is_root_event': 25,
    'event_code': 26,
    'event_base_code': 27,
    'event_root_code': 28,
    'quad_class': 29,        # 1=Verbal Coop, 2=Material Coop, 3=Verbal Conflict, 4=Material Conflict
    'goldstein': 30,         # -10 to +10 scale
    'num_mentions': 31,
    'num_sources': 32,
    'num_articles': 33,
    'avg_tone': 34,
    'actor1_geo_name': 36,
    'actor1_geo_country': 38,
    'actor1_geo_lat': 40,
    'actor1_geo_long': 41,
    'actor2_geo_name': 44,
    'actor2_geo_country': 46,
    'action_geo_name': 52,
    'action_geo_country': 54,
    'action_geo_lat': 56,
    'action_geo_long': 57,
    'source_url': 60,
}

# CAMEO event code to event_type mapping
CAMEO_ROOT_TO_TYPE = {
    '01': 'diplomatic',    # Make public statement
    '02': 'diplomatic',    # Appeal
    '03': 'diplomatic',    # Express intent to cooperate
    '04': 'diplomatic',    # Consult
    '05': 'diplomatic',    # Engage in diplomatic cooperation
    '06': 'economic',      # Engage in material cooperation
    '07': 'humanitarian',  # Provide aid
    '08': 'economic',      # Yield
    '09': 'diplomatic',    # Investigate
    '10': 'political',     # Demand
    '11': 'political',     # Disapprove
    '12': 'political',     # Reject
    '13': 'political',     # Threaten
    '14': 'political',     # Protest
    '15': 'military',      # Exhibit force posture
    '16': 'military',      # Reduce relations
    '17': 'military',      # Coerce
    '18': 'military',      # Assault
    '19': 'military',      # Fight
    '20': 'military',      # Use unconventional mass violence
}

# QuadClass to sentiment mapping
QUAD_TO_SENTIMENT = {
    1: 'positive',   # Verbal Cooperation
    2: 'positive',   # Material Cooperation
    3: 'negative',   # Verbal Conflict
    4: 'negative',   # Material Conflict
}

# Actor type codes to entity_type
ACTOR_TYPE_MAP = {
    'GOV': 'government',
    'MIL': 'military',
    'REB': 'rebel',
    'OPP': 'opposition',
    'PTY': 'political_party',
    'AGR': 'agriculture',
    'BUS': 'business',
    'CRM': 'criminal',
    'CVL': 'civilian',
    'DEV': 'development',
    'EDU': 'education',
    'ELI': 'elite',
    'ENV': 'environmental',
    'HLH': 'health',
    'HRI': 'human_rights',
    'IGO': 'intl_org',
    'JUD': 'judicial',
    'LAB': 'labor',
    'LEG': 'legislature',
    'MED': 'media',
    'REF': 'refugee',
    'REL': 'religious',
    'SPY': 'intelligence',
    'UAF': 'armed_faction',
}

# Topic mapping based on event types
EVENT_TYPE_TO_TOPIC = {
    'diplomatic': 'topic_diplomacy',
    'political': 'topic_politics',
    'military': 'topic_security',
    'economic': 'topic_economy',
    'humanitarian': 'topic_humanitarian',
}


def safe_str(val):
    """Safely convert value to string, handling NaN"""
    if pd.isna(val) or str(val).lower() == 'nan':
        return None
    return str(val).strip()


def safe_float(val, default=0.0):
    """Safely convert value to float"""
    try:
        if pd.isna(val):
            return default
        return float(val)
    except:
        return default


def normalize_score(val, min_val=-10, max_val=10):
    """Normalize value to 0-1 range"""
    return (val - min_val) / (max_val - min_val)


def get_event_type(event_root_code):
    """Map CAMEO root code to event type"""
    code = safe_str(event_root_code)
    if code and len(code) >= 2:
        return CAMEO_ROOT_TO_TYPE.get(code[:2], 'other')
    return 'other'


def get_entity_type(actor_code, actor_type):
    """Determine entity type from actor codes"""
    type_code = safe_str(actor_type)
    if type_code and type_code in ACTOR_TYPE_MAP:
        return ACTOR_TYPE_MAP[type_code]
    
    actor = safe_str(actor_code)
    if actor:
        if len(actor) == 3 and actor.isupper():
            return 'country'
        if actor.endswith('GOV'):
            return 'government'
        if actor.endswith('MIL'):
            return 'military'
    return 'organization'


def generate_event_title(row):
    """Generate a descriptive event title"""
    actor1 = safe_str(row[COLS['actor1_name']]) or safe_str(row[COLS['actor1_code']])
    actor2 = safe_str(row[COLS['actor2_name']]) or safe_str(row[COLS['actor2_code']])
    event_type = get_event_type(row[COLS['event_root_code']])
    
    if actor1 and actor2:
        return f"{actor1} - {actor2} {event_type} event"
    elif actor1:
        return f"{actor1} {event_type} event"
    return f"Global {event_type} event"


def generate_influences_edges(events, involves_edges, belongs_to_edges, 
                              max_lag_days=3, min_strength=0.4, max_edges_per_event=3,
                              max_events_per_entity=100):
    """
    Generate INFLUENCES edges between events based on:
    1. Shared entities (events involving the same actor)
    2. Same topic
    3. Temporal ordering (earlier event influences later)
    4. Temporal proximity (closer events have stronger influence)
    
    Optimized for large datasets with sampling and limits.
    """
    from datetime import datetime
    from collections import defaultdict
    import random
    
    print("  Building event indices...")
    
    # Parse event timestamps and create lookup
    event_data = {}
    for evt in events:
        try:
            ts = datetime.strptime(evt['timestamp'], "%Y-%m-%d %H:%M:%S")
            event_data[evt['id']] = {
                'timestamp': ts,
                'date_str': evt['timestamp'][:10],
                'severity': evt['severity'],
                'impact_score': evt['impact_score'],
                'event_type': evt['event_type'],
            }
        except:
            continue
    
    print(f"    Indexed {len(event_data)} events")
    
    # Build entity -> events mapping
    entity_to_events = defaultdict(list)
    event_to_entities = defaultdict(set)
    event_entity_sentiment = {}
    
    for edge in involves_edges:
        event_id = edge['from_id']
        entity_id = edge['to_id']
        if event_id in event_data:
            entity_to_events[entity_id].append(event_id)
            event_to_entities[event_id].add(entity_id)
            event_entity_sentiment[(event_id, entity_id)] = edge['sentiment']
    
    # Build topic -> events mapping
    event_to_topic = {}
    for edge in belongs_to_edges:
        event_id = edge['from_id']
        if event_id in event_data:
            event_to_topic[event_id] = edge['to_id']
    
    print(f"    Indexed {len(entity_to_events)} entities")
    
    # Focus on high-impact entities (those with many events)
    significant_entities = [
        (eid, evts) for eid, evts in entity_to_events.items() 
        if 5 <= len(evts) <= 5000  # Filter noise and outliers
    ]
    significant_entities.sort(key=lambda x: len(x[1]), reverse=True)
    
    print(f"  Processing {len(significant_entities)} significant entities...")
    
    influence_candidates = defaultdict(list)
    processed_pairs = set()
    entity_count = 0
    
    for entity_id, event_list in significant_entities:
        entity_count += 1
        if entity_count % 100 == 0:
            print(f"    Processed {entity_count}/{len(significant_entities)} entities...")
        
        # Sample if too many events
        if len(event_list) > max_events_per_entity:
            # Prioritize high-impact events
            event_list_with_impact = [
                (e, event_data[e]['impact_score']) for e in event_list
            ]
            event_list_with_impact.sort(key=lambda x: x[1], reverse=True)
            event_list = [e for e, _ in event_list_with_impact[:max_events_per_entity]]
        
        # Sort events by timestamp
        sorted_events = sorted(event_list, key=lambda e: event_data[e]['timestamp'])
        
        # Create pairs within time window (limited lookahead)
        for i, source_event in enumerate(sorted_events):
            source_ts = event_data[source_event]['timestamp']
            source_impact = event_data[source_event]['impact_score']
            
            # Only look at next 20 events max
            for target_event in sorted_events[i+1:i+21]:
                target_ts = event_data[target_event]['timestamp']
                
                lag = (target_ts - source_ts).days
                if lag > max_lag_days or lag < 0:
                    continue
                
                pair_key = (source_event, target_event)
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                # Calculate influence strength
                shared_entities = event_to_entities[source_event] & event_to_entities[target_event]
                same_topic = event_to_topic.get(source_event) == event_to_topic.get(target_event)
                
                # Temporal decay
                temporal_factor = 1.0 / (1 + lag * 0.3)
                
                # Entity overlap (capped)
                entity_factor = min(0.4, len(shared_entities) * 0.15)
                
                # Topic factor
                topic_factor = 0.15 if same_topic else 0.0
                
                # Impact factor
                impact_factor = source_impact * 0.15
                
                strength = min(1.0, temporal_factor * 0.3 + entity_factor + topic_factor + impact_factor)
                
                if strength >= min_strength:
                    # Determine polarity
                    source_sent = event_entity_sentiment.get((source_event, entity_id), 'neutral')
                    target_sent = event_entity_sentiment.get((target_event, entity_id), 'neutral')
                    polarity = 1 if source_sent == target_sent else -1
                    
                    # Influence type
                    if len(shared_entities) >= 2:
                        influence_type = 'direct'
                    elif same_topic:
                        influence_type = 'thematic'
                    else:
                        influence_type = 'indirect'
                    
                    influence_candidates[target_event].append({
                        'source': source_event,
                        'strength': round(strength, 3),
                        'lag_days': max(1, lag),  # Minimum 1 day
                        'polarity': polarity,
                        'influence_type': influence_type,
                    })
    
    print("  Selecting top influences per event...")
    
    # Select top N influences per event
    influences_edges = []
    
    for target_event, candidates in influence_candidates.items():
        candidates.sort(key=lambda x: x['strength'], reverse=True)
        
        for candidate in candidates[:max_edges_per_event]:
            influences_edges.append({
                'from_id': candidate['source'],
                'to_id': target_event,
                'strength': candidate['strength'],
                'lag_days': candidate['lag_days'],
                'polarity': candidate['polarity'],
                'influence_type': candidate['influence_type'],
            })
    
    return influences_edges


def parse_gdelt_files(input_dir, output_dir):
    """Parse all GDELT CSV files and output CHINTU-formatted data"""
    
    os.makedirs(output_dir, exist_ok=True)
    files = glob.glob(os.path.join(input_dir, "*.export.CSV"))
    
    print(f"Found {len(files)} GDELT files to process")
    
    events = []
    entities = {}  # id -> entity data
    involves_edges = []
    belongs_to_edges = []
    entity_mention_count = defaultdict(int)  # For calculating influence
    
    # Predefined topics
    topics = [
        {'id': 'topic_diplomacy', 'name': 'Diplomacy', 'description': 'Diplomatic relations and negotiations', 'keywords': 'diplomacy,negotiation,treaty,agreement'},
        {'id': 'topic_politics', 'name': 'Politics', 'description': 'Political events and governance', 'keywords': 'politics,government,election,policy'},
        {'id': 'topic_security', 'name': 'Security', 'description': 'Military and security affairs', 'keywords': 'military,defense,conflict,war,security'},
        {'id': 'topic_economy', 'name': 'Economy', 'description': 'Economic events and trade', 'keywords': 'economy,trade,finance,market,tariff'},
        {'id': 'topic_humanitarian', 'name': 'Humanitarian', 'description': 'Humanitarian aid and crises', 'keywords': 'humanitarian,aid,refugee,crisis,relief'},
    ]
    
    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"Processing: {filename}")
        
        try:
            df = pd.read_csv(file_path, sep="\t", header=None, low_memory=False,
                           encoding='utf-8', on_bad_lines='skip')
        except Exception as e:
            print(f"  Error reading {filename}: {e}")
            continue
        
        for idx, row in df.iterrows():
            try:
                event_id = safe_str(row[COLS['global_event_id']])
                if not event_id:
                    continue
                
                # Parse date
                date_str = safe_str(row[COLS['date']])
                if date_str and len(date_str) == 8:
                    timestamp = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} 00:00:00"
                else:
                    timestamp = "2026-01-01 00:00:00"
                
                # Event attributes
                goldstein = safe_float(row[COLS['goldstein']], 0)
                avg_tone = safe_float(row[COLS['avg_tone']], 0)
                num_mentions = safe_float(row[COLS['num_mentions']], 1)
                num_sources = safe_float(row[COLS['num_sources']], 1)
                quad_class = int(safe_float(row[COLS['quad_class']], 1))
                
                event_type = get_event_type(row[COLS['event_root_code']])
                
                # Calculate severity (0-1) from Goldstein scale
                severity = normalize_score(goldstein, -10, 10)
                
                # Calculate impact_score based on mentions, sources, and tone magnitude
                impact_score = min(1.0, (num_mentions * num_sources * abs(avg_tone)) / 1000)
                impact_score = max(0.1, impact_score)  # Minimum 0.1
                
                # Location
                location = safe_str(row[COLS['action_geo_name']]) or \
                          safe_str(row[COLS['actor1_geo_name']]) or "Unknown"
                
                # Source URL
                source_url = safe_str(row[COLS['source_url']]) or ""
                
                # Create event
                event = {
                    'id': f"evt_{event_id}",
                    'title': generate_event_title(row),
                    'description': f"GDELT Event {event_id}",
                    'event_type': event_type,
                    'timestamp': timestamp,
                    'severity': round(severity, 3),
                    'impact_score': round(impact_score, 3),
                    'location': location[:100],  # Truncate long locations
                    'source_url': source_url[:500],
                }
                events.append(event)
                
                # Process Actor 1
                actor1_code = safe_str(row[COLS['actor1_code']])
                actor1_name = safe_str(row[COLS['actor1_name']]) or actor1_code
                actor1_country = safe_str(row[COLS['actor1_country']])
                
                if actor1_code:
                    entity_id = f"ent_{actor1_code}"
                    entity_mention_count[entity_id] += 1
                    
                    if entity_id not in entities:
                        entities[entity_id] = {
                            'id': entity_id,
                            'name': actor1_name,
                            'entity_type': get_entity_type(actor1_code, row[COLS['actor1_type1']]),
                            'description': f"{actor1_name} ({actor1_country or 'Unknown'})",
                            'influence_score': 0.5,  # Will be updated later
                        }
                    
                    # INVOLVES edge
                    sentiment = QUAD_TO_SENTIMENT.get(quad_class, 'neutral')
                    role = 'initiator' if goldstein >= 0 else 'aggressor'
                    
                    involves_edges.append({
                        'from_id': event['id'],
                        'to_id': entity_id,
                        'role': role,
                        'sentiment': sentiment,
                    })
                
                # Process Actor 2
                actor2_code = safe_str(row[COLS['actor2_code']])
                actor2_name = safe_str(row[COLS['actor2_name']]) or actor2_code
                actor2_country = safe_str(row[COLS['actor2_country']])
                
                if actor2_code:
                    entity_id = f"ent_{actor2_code}"
                    entity_mention_count[entity_id] += 1
                    
                    if entity_id not in entities:
                        entities[entity_id] = {
                            'id': entity_id,
                            'name': actor2_name,
                            'entity_type': get_entity_type(actor2_code, row[COLS['actor2_type1']]),
                            'description': f"{actor2_name} ({actor2_country or 'Unknown'})",
                            'influence_score': 0.5,
                        }
                    
                    sentiment = QUAD_TO_SENTIMENT.get(quad_class, 'neutral')
                    role = 'target' if goldstein < 0 else 'participant'
                    
                    involves_edges.append({
                        'from_id': event['id'],
                        'to_id': entity_id,
                        'role': role,
                        'sentiment': sentiment,
                    })
                
                # BELONGS_TO topic edge
                topic_id = EVENT_TYPE_TO_TOPIC.get(event_type, 'topic_politics')
                relevance = 0.8 + (abs(goldstein) / 50)  # Higher relevance for stronger events
                
                belongs_to_edges.append({
                    'from_id': event['id'],
                    'to_id': topic_id,
                    'relevance_score': round(min(1.0, relevance), 3),
                })
                
            except Exception as e:
                continue
    
    # Update entity influence scores based on mention frequency
    if entity_mention_count:
        max_mentions = max(entity_mention_count.values())
        for entity_id, count in entity_mention_count.items():
            if entity_id in entities:
                entities[entity_id]['influence_score'] = round(0.3 + 0.7 * (count / max_mentions), 3)
    
    # Generate INFLUENCES edges
    print("\nGenerating INFLUENCES edges (causal relationships)...")
    influences_edges = generate_influences_edges(events, involves_edges, belongs_to_edges)
    print(f"  Generated {len(influences_edges)} INFLUENCES edges")
    
    # Save outputs
    print(f"\nSaving outputs to {output_dir}/")
    
    pd.DataFrame(events).to_csv(os.path.join(output_dir, "events.csv"), index=False)
    print(f"  Events: {len(events)}")
    
    pd.DataFrame(list(entities.values())).to_csv(os.path.join(output_dir, "entities.csv"), index=False)
    print(f"  Entities: {len(entities)}")
    
    pd.DataFrame(topics).to_csv(os.path.join(output_dir, "topics.csv"), index=False)
    print(f"  Topics: {len(topics)}")
    
    pd.DataFrame(involves_edges).to_csv(os.path.join(output_dir, "involves_edges.csv"), index=False)
    print(f"  INVOLVES edges: {len(involves_edges)}")
    
    pd.DataFrame(belongs_to_edges).to_csv(os.path.join(output_dir, "belongs_to_edges.csv"), index=False)
    print(f"  BELONGS_TO edges: {len(belongs_to_edges)}")
    
    pd.DataFrame(influences_edges).to_csv(os.path.join(output_dir, "influences_edges.csv"), index=False)
    print(f"  INFLUENCES edges: {len(influences_edges)}")
    
    print("\nDone! Ready for TigerGraph loading.")
    
    return {
        'events': len(events),
        'entities': len(entities),
        'topics': len(topics),
        'involves': len(involves_edges),
        'belongs_to': len(belongs_to_edges),
        'influences': len(influences_edges),
    }


if __name__ == "__main__":
    from chintu.config import CHINTU_EXPORT_DIR, GDELT_RAW_DIR

    stats = parse_gdelt_files(
        input_dir=str(GDELT_RAW_DIR),
        output_dir=str(CHINTU_EXPORT_DIR),
    )
    print(f"\nSummary: {stats}")
