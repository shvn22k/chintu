"""
CHINTU Batch Loader
Loads data into TigerGraph using GSQL interpreted queries via the MCP tool.
Run this in chunks to load the full dataset.
"""

import _bootstrap  # noqa: F401

import pandas as pd
import os
import json
import subprocess
import time

from chintu.config import CHINTU_EXPORT_DIR, GSQL_BATCHES_DIR

DATA_DIR = str(CHINTU_EXPORT_DIR)
BATCH_SIZE = 50  # Small batches for GSQL INSERT


def escape_gsql(s):
    """Escape string for GSQL"""
    if pd.isna(s) or s is None:
        return ""
    s = str(s)
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', ' ')
    s = s.replace('\r', '')
    return s[:200]


def load_topics():
    """Load all topics (only 5 records)"""
    df = pd.read_csv(os.path.join(DATA_DIR, "topics.csv")).fillna('')
    
    statements = []
    for _, row in df.iterrows():
        stmt = f'INSERT INTO Topic VALUES("{escape_gsql(row["id"])}", "{escape_gsql(row["name"])}", "{escape_gsql(row["description"])}", "{escape_gsql(row["keywords"])}");'
        statements.append(stmt)
    
    return "USE GRAPH CHINTU\nINTERPRET QUERY () FOR GRAPH CHINTU {\n" + "\n".join(statements) + '\nPRINT "Topics loaded";\n}'


def generate_entity_batch(start_idx, batch_size=BATCH_SIZE):
    """Generate GSQL for loading a batch of entities"""
    df = pd.read_csv(os.path.join(DATA_DIR, "entities.csv")).fillna('')
    batch = df.iloc[start_idx:start_idx + batch_size]
    
    if len(batch) == 0:
        return None, 0
    
    statements = []
    for _, row in batch.iterrows():
        stmt = f'INSERT INTO Entity VALUES("{escape_gsql(row["id"])}", "{escape_gsql(row["name"])}", "{escape_gsql(row["entity_type"])}", "{escape_gsql(row["description"])}", {float(row["influence_score"])});'
        statements.append(stmt)
    
    query = f'USE GRAPH CHINTU\nINTERPRET QUERY () FOR GRAPH CHINTU {{\n{chr(10).join(statements)}\nPRINT "Batch loaded";\n}}'
    return query, len(batch)


def generate_event_batch(start_idx, batch_size=BATCH_SIZE):
    """Generate GSQL for loading a batch of events"""
    df = pd.read_csv(os.path.join(DATA_DIR, "events.csv")).fillna('')
    batch = df.iloc[start_idx:start_idx + batch_size]
    
    if len(batch) == 0:
        return None, 0
    
    statements = []
    for _, row in batch.iterrows():
        # Format timestamp
        ts = escape_gsql(row["timestamp"])
        stmt = f'INSERT INTO Event VALUES("{escape_gsql(row["id"])}", "{escape_gsql(row["title"])}", "{escape_gsql(row["description"])}", "{escape_gsql(row["event_type"])}", to_datetime("{ts}"), {float(row["severity"])}, {float(row["impact_score"])}, "{escape_gsql(row["location"])}", "{escape_gsql(row["source_url"])}");'
        statements.append(stmt)
    
    query = f'USE GRAPH CHINTU\nINTERPRET QUERY () FOR GRAPH CHINTU {{\n{chr(10).join(statements)}\nPRINT "Batch loaded";\n}}'
    return query, len(batch)


def generate_involves_batch(start_idx, batch_size=BATCH_SIZE):
    """Generate GSQL for loading a batch of INVOLVES edges"""
    df = pd.read_csv(os.path.join(DATA_DIR, "involves_edges.csv")).fillna('')
    batch = df.iloc[start_idx:start_idx + batch_size]
    
    if len(batch) == 0:
        return None, 0
    
    statements = []
    for _, row in batch.iterrows():
        stmt = f'INSERT INTO INVOLVES VALUES("{escape_gsql(row["from_id"])}" Event, "{escape_gsql(row["to_id"])}" Entity, "{escape_gsql(row["role"])}", "{escape_gsql(row["sentiment"])}");'
        statements.append(stmt)
    
    query = f'USE GRAPH CHINTU\nINTERPRET QUERY () FOR GRAPH CHINTU {{\n{chr(10).join(statements)}\nPRINT "Batch loaded";\n}}'
    return query, len(batch)


def generate_belongs_to_batch(start_idx, batch_size=BATCH_SIZE):
    """Generate GSQL for loading a batch of BELONGS_TO edges"""
    df = pd.read_csv(os.path.join(DATA_DIR, "belongs_to_edges.csv")).fillna('')
    batch = df.iloc[start_idx:start_idx + batch_size]
    
    if len(batch) == 0:
        return None, 0
    
    statements = []
    for _, row in batch.iterrows():
        stmt = f'INSERT INTO BELONGS_TO VALUES("{escape_gsql(row["from_id"])}" Event, "{escape_gsql(row["to_id"])}" Topic, {float(row["relevance_score"])});'
        statements.append(stmt)
    
    query = f'USE GRAPH CHINTU\nINTERPRET QUERY () FOR GRAPH CHINTU {{\n{chr(10).join(statements)}\nPRINT "Batch loaded";\n}}'
    return query, len(batch)


def generate_influences_batch(start_idx, batch_size=BATCH_SIZE):
    """Generate GSQL for loading a batch of INFLUENCES edges"""
    df = pd.read_csv(os.path.join(DATA_DIR, "influences_edges.csv")).fillna('')
    batch = df.iloc[start_idx:start_idx + batch_size]
    
    if len(batch) == 0:
        return None, 0
    
    statements = []
    for _, row in batch.iterrows():
        stmt = f'INSERT INTO INFLUENCES VALUES("{escape_gsql(row["from_id"])}" Event, "{escape_gsql(row["to_id"])}" Event, {float(row["strength"])}, {int(row["lag_days"])}, {int(row["polarity"])}, "{escape_gsql(row["influence_type"])}");'
        statements.append(stmt)
    
    query = f'USE GRAPH CHINTU\nINTERPRET QUERY () FOR GRAPH CHINTU {{\n{chr(10).join(statements)}\nPRINT "Batch loaded";\n}}'
    return query, len(batch)


def get_counts():
    """Get current record counts"""
    return {
        'entities': len(pd.read_csv(os.path.join(DATA_DIR, "entities.csv"))),
        'events': len(pd.read_csv(os.path.join(DATA_DIR, "events.csv"))),
        'involves': len(pd.read_csv(os.path.join(DATA_DIR, "involves_edges.csv"))),
        'belongs_to': len(pd.read_csv(os.path.join(DATA_DIR, "belongs_to_edges.csv"))),
        'influences': len(pd.read_csv(os.path.join(DATA_DIR, "influences_edges.csv"))),
    }


def save_batch_queries(output_dir=None, max_batches=None):
    """Save batch queries to files for manual execution"""
    if output_dir is None:
        output_dir = str(GSQL_BATCHES_DIR)
    os.makedirs(output_dir, exist_ok=True)
    counts = get_counts()
    
    print("Generating batch query files...")
    
    # Generate entity batches
    idx = 0
    batch_num = 0
    while idx < counts['entities']:
        query, count = generate_entity_batch(idx)
        if query:
            with open(os.path.join(output_dir, f"entity_{batch_num:04d}.gsql"), 'w') as f:
                f.write(query)
            batch_num += 1
        idx += BATCH_SIZE
        if max_batches and batch_num >= max_batches:
            break
    print(f"  Entity batches: {batch_num}")
    
    # Generate event batches
    idx = 0
    batch_num = 0
    while idx < counts['events']:
        query, count = generate_event_batch(idx)
        if query:
            with open(os.path.join(output_dir, f"event_{batch_num:04d}.gsql"), 'w') as f:
                f.write(query)
            batch_num += 1
        idx += BATCH_SIZE
        if max_batches and batch_num >= max_batches:
            break
    print(f"  Event batches: {batch_num}")
    
    # Generate edge batches (just first few for demo)
    for edge_type, gen_func, prefix in [
        ('involves', generate_involves_batch, 'involves'),
        ('belongs_to', generate_belongs_to_batch, 'belongs_to'),
        ('influences', generate_influences_batch, 'influences'),
    ]:
        idx = 0
        batch_num = 0
        while idx < min(counts.get(edge_type, 0), 500 if max_batches else float('inf')):
            query, count = gen_func(idx)
            if query:
                with open(os.path.join(output_dir, f"{prefix}_{batch_num:04d}.gsql"), 'w') as f:
                    f.write(query)
                batch_num += 1
            idx += BATCH_SIZE
            if max_batches and batch_num >= max_batches:
                break
        print(f"  {edge_type} batches: {batch_num}")
    
    print(f"\nBatch files saved to {output_dir}/")
    print("Run these via: python -c \"from batch_loader import *; print(generate_entity_batch(0)[0])\" | clipboard")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        save_batch_queries(max_batches=10)  # Generate first 10 batches of each type
    else:
        print("CHINTU Batch Loader")
        print("=" * 50)
        counts = get_counts()
        print("\nDataset sizes:")
        for k, v in counts.items():
            print(f"  {k}: {v:,}")
        
        print("\nUsage:")
        print("  python experiments/pipeline/batch_loader.py generate   - Generate batch files")
        print("\nTo load interactively, import functions and use MCP tool:")
        print('  from batch_loader import generate_entity_batch')
        print('  query, count = generate_entity_batch(0)')
        print('  # Then use query with tigergraph__gsql MCP tool')
