"""
Run all CHINTU CSV data into TigerGraph via interpreted GSQL (same path as MCP gsql).

Credentials: set TG_* env vars, or rely on load_to_tigergraph.py constants if present.

Usage (from repository root):
  python experiments/pipeline/load_all_gsql_batches.py              # full load (clears graph data first)
  python experiments/pipeline/load_all_gsql_batches.py --no-clear   # append without clearing
"""

from __future__ import annotations

import _bootstrap  # noqa: F401

import argparse
import os
import sys
import time

from pyTigerGraph import TigerGraphConnection

import batch_loader as bl

# Prefer environment; fall back to existing loader module (local dev).
try:
    from load_to_tigergraph import (
        TG_GRAPHNAME,
        TG_HOST,
        TG_PASSWORD,
        TG_SECRET,
        TG_USERNAME,
    )
except ImportError:
    TG_HOST = os.environ.get("TG_HOST", "")
    TG_GRAPHNAME = os.environ.get("TG_GRAPHNAME", "CHINTU")
    TG_USERNAME = os.environ.get("TG_USERNAME", "")
    TG_PASSWORD = os.environ.get("TG_PASSWORD", "")
    TG_SECRET = os.environ.get("TG_SECRET", "")


def _normalize_host(url: str) -> str:
    """pyTigerGraph requires host URL with http(s) scheme."""
    u = url.rstrip("/")
    if not u.startswith(("http://", "https://")):
        return "https://" + u
    return u


def connect() -> TigerGraphConnection:
    if not all([TG_HOST, TG_SECRET]):
        sys.exit(
            "Missing TigerGraph config. Set TG_HOST, TG_SECRET "
            "(and TG_USERNAME, TG_PASSWORD if not using load_to_tigergraph.py)."
        )
    host = _normalize_host(TG_HOST)
    restpp = os.environ.get("TG_RESTPP_PORT", "443")
    gs = os.environ.get("TG_GS_PORT", "443")
    conn = TigerGraphConnection(
        host=host,
        graphname=TG_GRAPHNAME,
        username=TG_USERNAME,
        password=TG_PASSWORD,
        gsqlSecret=TG_SECRET,
        tgCloud=True,
        restppPort=restpp,
        gsPort=gs,
    )
    conn.getToken(TG_SECRET)
    return conn


def run_batch(conn: TigerGraphConnection, label: str, batch_index: int, query: str) -> None:
    t0 = time.perf_counter()
    try:
        conn.runInterpretedQuery(query)
    except Exception as e:
        raise RuntimeError(f"{label} batch {batch_index} failed: {e}") from e
    dt = time.perf_counter() - t0
    if batch_index % 20 == 0:
        print(f"  {label} batch {batch_index} ok ({dt:.1f}s)")


def clear_graph_data(conn: TigerGraphConnection) -> None:
    q = f"""USE GRAPH {TG_GRAPHNAME}
INTERPRET QUERY () FOR GRAPH {TG_GRAPHNAME} {{
  CLEAR GRAPH DATA -HARD
  PRINT "cleared";
}}"""
    print("Clearing graph data (CLEAR GRAPH DATA -HARD)...")
    conn.runInterpretedQuery(q)
    print("Graph data cleared.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--no-clear",
        action="store_true",
        help="Do not run CLEAR GRAPH DATA (may fail on duplicate primary keys).",
    )
    ap.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help=f"Override batch size (default {bl.BATCH_SIZE} from batch_loader).",
    )
    args = ap.parse_args()
    bs = args.batch_size or bl.BATCH_SIZE

    print("Connecting...")
    conn = connect()
    print(f"Connected to graph {TG_GRAPHNAME}")

    if not args.no_clear:
        clear_graph_data(conn)

    # Topics (small)
    print("Loading topics...")
    run_batch(conn, "topics", 0, bl.load_topics())

    counts = bl.get_counts()

    def loop_entities() -> int:
        n = 0
        idx = 0
        while idx < counts["entities"]:
            query, c = bl.generate_entity_batch(idx, bs)
            if not query or c == 0:
                break
            run_batch(conn, "entity", n, query)
            n += 1
            idx += bs
        return n

    def loop_events() -> int:
        n = 0
        idx = 0
        while idx < counts["events"]:
            query, c = bl.generate_event_batch(idx, bs)
            if not query or c == 0:
                break
            run_batch(conn, "event", n, query)
            n += 1
            idx += bs
        return n

    def loop_edges(name: str, gen, total_key: str) -> int:
        n = 0
        idx = 0
        total = counts[total_key]
        while idx < total:
            query, c = gen(idx, bs)
            if not query or c == 0:
                break
            run_batch(conn, name, n, query)
            n += 1
            idx += bs
        return n

    print(f"Loading entities ({counts['entities']:,} rows, batch_size={bs})...")
    print(f"  {loop_entities()} batches")

    print(f"Loading events ({counts['events']:,} rows)...")
    print(f"  {loop_events()} batches")

    print(f"Loading INVOLVES ({counts['involves']:,} rows)...")
    print(f"  {loop_edges('involves', bl.generate_involves_batch, 'involves')} batches")

    print(f"Loading BELONGS_TO ({counts['belongs_to']:,} rows)...")
    print(f"  {loop_edges('belongs_to', bl.generate_belongs_to_batch, 'belongs_to')} batches")

    print(f"Loading INFLUENCES ({counts['influences']:,} rows)...")
    print(f"  {loop_edges('influences', bl.generate_influences_batch, 'influences')} batches")

    print("Done. Verifying counts...")
    for vt in ("Topic", "Entity", "Event"):
        try:
            cnt = conn.getVertexCount(vt)
            print(f"  {vt}: {cnt}")
        except Exception as e:
            print(f"  {vt}: (could not count) {e}")


if __name__ == "__main__":
    main()
