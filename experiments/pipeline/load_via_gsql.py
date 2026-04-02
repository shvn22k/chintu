"""
CHINTU GSQL Data Loader
Creates GSQL INSERT statements for batch loading via interpreted queries
"""

import _bootstrap  # noqa: F401

import pandas as pd
import os

from chintu.config import CHINTU_EXPORT_DIR, GSQL_LOAD_DIR

DATA_DIR = str(CHINTU_EXPORT_DIR)
OUTPUT_DIR = str(GSQL_LOAD_DIR)
BATCH_SIZE = 100  # Smaller batches for GSQL

os.makedirs(OUTPUT_DIR, exist_ok=True)


def escape_string(s):
    """Escape string for GSQL"""
    if pd.isna(s) or s is None:
        return ""
    s = str(s)
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', ' ')
    s = s.replace('\r', '')
    return s[:200]  # Truncate long strings


def generate_vertex_inserts(vertex_type, csv_file, columns_order):
    """Generate INSERT statements for vertices"""
    filepath = os.path.join(DATA_DIR, csv_file)
    df = pd.read_csv(filepath)
    df = df.fillna('')
    
    total = len(df)
    print(f"Generating {total} {vertex_type} inserts...")
    
    batch_num = 0
    for i in range(0, total, BATCH_SIZE):
        batch = df.iloc[i:i+BATCH_SIZE]
        
        statements = []
        for _, row in batch.iterrows():
            values = []
            for col in columns_order:
                val = row[col]
                if col in ['severity', 'impact_score', 'influence_score', 'relevance_score']:
                    values.append(str(float(val) if val != '' else 0.0))
                elif col == 'timestamp':
                    values.append(f'to_datetime("{escape_string(val)}")')
                else:
                    values.append(f'"{escape_string(val)}"')
            
            stmt = f'INSERT INTO {vertex_type} VALUES({", ".join(values)});'
            statements.append(stmt)
        
        output_file = os.path.join(OUTPUT_DIR, f"{vertex_type.lower()}_batch_{batch_num:04d}.gsql")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(statements))
        
        batch_num += 1
    
    print(f"  Generated {batch_num} batch files")
    return batch_num


def generate_edge_inserts(edge_type, csv_file, columns_order):
    """Generate INSERT statements for edges"""
    filepath = os.path.join(DATA_DIR, csv_file)
    df = pd.read_csv(filepath)
    df = df.fillna('')
    
    total = len(df)
    print(f"Generating {total} {edge_type} inserts...")
    
    batch_num = 0
    for i in range(0, total, BATCH_SIZE):
        batch = df.iloc[i:i+BATCH_SIZE]
        
        statements = []
        for _, row in batch.iterrows():
            values = []
            for col in columns_order:
                val = row[col]
                if col in ['from_id', 'to_id']:
                    # These need vertex type annotations
                    if edge_type == 'INVOLVES':
                        if col == 'from_id':
                            values.append(f'"{escape_string(val)}" Event')
                        else:
                            values.append(f'"{escape_string(val)}" Entity')
                    elif edge_type == 'BELONGS_TO':
                        if col == 'from_id':
                            values.append(f'"{escape_string(val)}" Event')
                        else:
                            values.append(f'"{escape_string(val)}" Topic')
                    elif edge_type == 'INFLUENCES':
                        values.append(f'"{escape_string(val)}" Event')
                elif col in ['strength', 'relevance_score']:
                    values.append(str(float(val) if val != '' else 0.0))
                elif col in ['lag_days', 'polarity']:
                    values.append(str(int(float(val)) if val != '' else 0))
                else:
                    values.append(f'"{escape_string(val)}"')
            
            stmt = f'INSERT INTO {edge_type} VALUES({", ".join(values)});'
            statements.append(stmt)
        
        output_file = os.path.join(OUTPUT_DIR, f"{edge_type.lower()}_batch_{batch_num:04d}.gsql")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(statements))
        
        batch_num += 1
    
    print(f"  Generated {batch_num} batch files")
    return batch_num


def generate_loader_query():
    """Generate the master loader query template"""
    
    query_template = '''USE GRAPH CHINTU
BEGIN
CREATE QUERY load_batch(STRING batch_statements) FOR GRAPH CHINTU {
  # This query executes the INSERT statements passed to it
  # Batch statements should be semicolon-separated INSERT commands
  
  PRINT "Batch loading is done via GSQL file loading";
}
END
'''
    
    with open(os.path.join(OUTPUT_DIR, "loader_template.gsql"), 'w') as f:
        f.write(query_template)


def main():
    print("=" * 50)
    print("CHINTU GSQL Batch Generator")
    print("=" * 50)
    
    stats = {}
    
    # Generate vertex inserts
    print("\n--- Generating Vertex Inserts ---")
    stats['topics'] = generate_vertex_inserts(
        "Topic", "topics.csv",
        ['id', 'name', 'description', 'keywords']
    )
    stats['entities'] = generate_vertex_inserts(
        "Entity", "entities.csv", 
        ['id', 'name', 'entity_type', 'description', 'influence_score']
    )
    stats['events'] = generate_vertex_inserts(
        "Event", "events.csv",
        ['id', 'title', 'description', 'event_type', 'timestamp', 'severity', 'impact_score', 'location', 'source_url']
    )
    
    # Generate edge inserts
    print("\n--- Generating Edge Inserts ---")
    stats['involves'] = generate_edge_inserts(
        "INVOLVES", "involves_edges.csv",
        ['from_id', 'to_id', 'role', 'sentiment']
    )
    stats['belongs_to'] = generate_edge_inserts(
        "BELONGS_TO", "belongs_to_edges.csv",
        ['from_id', 'to_id', 'relevance_score']
    )
    stats['influences'] = generate_edge_inserts(
        "INFLUENCES", "influences_edges.csv",
        ['from_id', 'to_id', 'strength', 'lag_days', 'polarity', 'influence_type']
    )
    
    # Summary
    print("\n" + "=" * 50)
    print("Generation Complete!")
    print("=" * 50)
    total_batches = sum(stats.values())
    print(f"Total batch files: {total_batches}")
    for key, count in stats.items():
        print(f"  {key}: {count} batches")
    
    print(f"\nOutput directory: {OUTPUT_DIR}/")
    print("\nTo load into TigerGraph, run each batch file via GSQL.")


if __name__ == "__main__":
    main()
