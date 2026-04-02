"""
CHINTU Data Loader
Loads parsed GDELT data into TigerGraph using REST API
"""

import _bootstrap  # noqa: F401

import pandas as pd
import requests
import json
import os
from datetime import datetime

try:
    from dotenv import load_dotenv

    load_dotenv(_bootstrap.REPO_ROOT / ".env")
except ImportError:
    pass

from chintu.config import CHINTU_EXPORT_DIR

# TigerGraph connection config (set in environment or .env — see .env.example)
TG_HOST = os.environ.get("TG_HOST", "")
TG_GRAPHNAME = os.environ.get("TG_GRAPHNAME", "CHINTU")
TG_USERNAME = os.environ.get("TG_USERNAME", "")
TG_PASSWORD = os.environ.get("TG_PASSWORD", "")
TG_SECRET = os.environ.get("TG_SECRET", "")

DATA_DIR = str(CHINTU_EXPORT_DIR)
BATCH_SIZE = 500  # Number of records per batch


class TigerGraphClient:
    def __init__(self, host, graphname, username, password, secret):
        self.host = host.rstrip('/')
        self.graphname = graphname
        self.username = username
        self.password = password
        self.secret = secret
        self.token = None
        
    def get_token(self):
        """Get authentication token using secret"""
        # Try secret-based token request
        url = f"{self.host}/restpp/requesttoken"
        payload = {"secret": self.secret, "graph": self.graphname}
        headers = {"Content-Type": "application/json"}
        
        # Use basic auth
        auth = (self.username, self.password)
        
        response = requests.post(url, json=payload, headers=headers, auth=auth)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token") or data.get("results", {}).get("token")
            if self.token:
                return self.token
        
        # Try with secret in URL params
        url = f"{self.host}/restpp/requesttoken?secret={self.secret}&graph={self.graphname}"
        response = requests.get(url, auth=auth)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token") or data.get("results", {}).get("token")
            if self.token:
                return self.token
                
        raise Exception(f"Failed to get token: {response.text}")
    
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def upsert_vertices(self, vertex_type, vertices):
        """Upsert vertices in batch"""
        url = f"{self.host}/restpp/graph/{self.graphname}"
        
        payload = {
            "vertices": {
                vertex_type: {
                    vid: attrs for vid, attrs in vertices
                }
            }
        }
        
        response = requests.post(url, headers=self._headers(), json=payload)
        if response.status_code != 200:
            raise Exception(f"Upsert failed: {response.text}")
        return response.json()
    
    def upsert_edges(self, source_type, edge_type, target_type, edges):
        """Upsert edges in batch"""
        url = f"{self.host}/restpp/graph/{self.graphname}"
        
        edge_data = {}
        for source_id, target_id, attrs in edges:
            if source_id not in edge_data:
                edge_data[source_id] = {}
            if edge_type not in edge_data[source_id]:
                edge_data[source_id][edge_type] = {}
            if target_type not in edge_data[source_id][edge_type]:
                edge_data[source_id][edge_type][target_type] = {}
            edge_data[source_id][edge_type][target_type][target_id] = attrs
        
        payload = {
            "edges": {
                source_type: edge_data
            }
        }
        
        response = requests.post(url, headers=self._headers(), json=payload)
        if response.status_code != 200:
            raise Exception(f"Upsert failed: {response.text}")
        return response.json()
    
    def get_vertex_count(self, vertex_type="*"):
        """Get vertex count"""
        url = f"{self.host}/restpp/graph/{self.graphname}/vertices"
        response = requests.get(url, headers=self._headers())
        return response.json()
    
    def get_edge_count(self, edge_type="*"):
        """Get edge count"""
        url = f"{self.host}/restpp/graph/{self.graphname}/edges"
        response = requests.get(url, headers=self._headers())
        return response.json()


def connect():
    """Establish connection to TigerGraph"""
    if not all([TG_HOST, TG_SECRET]):
        raise RuntimeError(
            "Missing TG_HOST or TG_SECRET. Copy .env.example to .env and set credentials."
        )
    print("Connecting to TigerGraph...")
    client = TigerGraphClient(TG_HOST, TG_GRAPHNAME, TG_USERNAME, TG_PASSWORD, TG_SECRET)
    token = client.get_token()
    print(f"Connected to graph: {TG_GRAPHNAME}")
    print(f"Token obtained: {token[:20]}...")
    return client


def load_vertices(client, vertex_type, csv_file, batch_size=BATCH_SIZE):
    """Load vertices from CSV in batches"""
    filepath = os.path.join(DATA_DIR, csv_file)
    df = pd.read_csv(filepath)
    
    # Handle NaN values
    df = df.fillna('')
    
    total = len(df)
    print(f"\nLoading {total} {vertex_type} vertices...")
    
    loaded = 0
    errors = 0
    
    for i in range(0, total, batch_size):
        batch = df.iloc[i:i+batch_size]
        vertices = []
        
        for _, row in batch.iterrows():
            vertex_data = row.to_dict()
            vertex_id = str(vertex_data.pop('id'))
            
            # Format attributes for TigerGraph API
            attrs = {}
            for k, v in vertex_data.items():
                if isinstance(v, float):
                    attrs[k] = {"value": v}
                else:
                    attrs[k] = {"value": str(v)}
            
            vertices.append((vertex_id, attrs))
        
        try:
            client.upsert_vertices(vertex_type, vertices)
            loaded += len(vertices)
            print(f"  {loaded}/{total} loaded...", end='\r')
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"\n  Error at batch {i}: {str(e)[:100]}")
    
    print(f"\n  {loaded}/{total} {vertex_type} vertices loaded. ({errors} batch errors)")
    return loaded


def load_edges(client, edge_type, csv_file, source_type, target_type, batch_size=BATCH_SIZE):
    """Load edges from CSV in batches"""
    filepath = os.path.join(DATA_DIR, csv_file)
    df = pd.read_csv(filepath)
    
    # Handle NaN values  
    df = df.fillna('')
    
    total = len(df)
    print(f"\nLoading {total} {edge_type} edges...")
    
    loaded = 0
    errors = 0
    
    for i in range(0, total, batch_size):
        batch = df.iloc[i:i+batch_size]
        edges = []
        
        for _, row in batch.iterrows():
            source_id = str(row['from_id'])
            target_id = str(row['to_id'])
            
            # Format attributes
            attrs = {}
            for k, v in row.to_dict().items():
                if k not in ['from_id', 'to_id']:
                    if isinstance(v, (int, float)):
                        attrs[k] = {"value": v}
                    else:
                        attrs[k] = {"value": str(v)}
            
            edges.append((source_id, target_id, attrs))
        
        try:
            client.upsert_edges(source_type, edge_type, target_type, edges)
            loaded += len(edges)
            print(f"  {loaded}/{total} loaded...", end='\r')
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"\n  Error at batch {i}: {str(e)[:100]}")
    
    print(f"\n  {loaded}/{total} {edge_type} edges loaded. ({errors} batch errors)")
    return loaded


def main():
    print("=" * 50)
    print("CHINTU Data Loader")
    print("=" * 50)
    
    client = connect()
    
    stats = {}
    
    # Load vertices (order matters - load referenced vertices first)
    print("\n--- Loading Vertices ---")
    stats['topics'] = load_vertices(client, "Topic", "topics.csv")
    stats['entities'] = load_vertices(client, "Entity", "entities.csv")
    stats['events'] = load_vertices(client, "Event", "events.csv")
    
    # Load edges
    print("\n--- Loading Edges ---")
    stats['involves'] = load_edges(client, "INVOLVES", "involves_edges.csv", "Event", "Entity")
    stats['belongs_to'] = load_edges(client, "BELONGS_TO", "belongs_to_edges.csv", "Event", "Topic")
    stats['influences'] = load_edges(client, "INFLUENCES", "influences_edges.csv", "Event", "Event")
    
    # Summary
    print("\n" + "=" * 50)
    print("Loading Complete!")
    print("=" * 50)
    for key, count in stats.items():
        print(f"  {key}: {count:,}")


if __name__ == "__main__":
    main()
