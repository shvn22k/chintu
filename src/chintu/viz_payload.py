"""
Turn TigerGraph *installed query* responses into a stable ``graph_viz`` shape.

TigerGraph / pyTigerGraph return shapes vary (list of dicts, nested ``results``, etc.).
These helpers normalize to::

    {"nodes": [...], "edges": [...]}

Each node: ``id``, ``label``, ``type``, ``attributes``.
Each edge: ``source``, ``target``, ``type``, ``attributes``.
"""

from __future__ import annotations

import json
import re
from typing import Any

# CHINTU Event ids in exports look like ``evt_<hash>`` — used as a weak hint when the LLM forgets to label intent.
_EVENT_ID_PATTERN = re.compile(r"\bevt_[a-zA-Z0-9_]+\b")


def extract_event_id_heuristic(text: str) -> str | None:
    """If the user pasted an event id, pull the first ``evt_*`` token from free text."""
    m = _EVENT_ID_PATTERN.search(text or "")
    return m.group(0) if m else None


def _as_dict_list(x: Any) -> list[dict[str, Any]]:
    if x is None:
        return []
    if isinstance(x, list):
        return [i for i in x if isinstance(i, dict)]
    if isinstance(x, dict):
        return [x]
    return []


def _unwrap_first_block(raw: Any) -> dict[str, Any]:
    """
    Installed queries often return a list with one dict per PRINT,
    or a single dict, or REST ``{"results": [...]}``.
    """
    if raw is None:
        return {}
    if isinstance(raw, dict) and "results" in raw:
        inner = raw["results"]
        if isinstance(inner, list) and inner:
            first = inner[0]
            return first if isinstance(first, dict) else {}
        return {}
    if isinstance(raw, list):
        merged: dict[str, Any] = {}
        for item in raw:
            if isinstance(item, dict):
                merged.update(item)
        return merged
    if isinstance(raw, dict):
        return raw
    return {}


def _flatten_tg_vertex_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    Unwrap TigerGraph REST vertex rows: ``{v_id, v_type, attributes: {…}}`` and any
    chained ``attributes.attributes`` so fields like ``source_url`` sit at the top level.
    """
    merged: dict[str, Any] = {}
    cur: Any = row
    depth = 0
    while isinstance(cur, dict) and depth < 8:
        for k, v in cur.items():
            if k == "attributes":
                continue
            if isinstance(v, dict):
                continue
            merged[k] = v
        inner = cur.get("attributes")
        if isinstance(inner, dict):
            cur = inner
            depth += 1
        else:
            break
    if "event_id" not in merged:
        vid = merged.get("v_id") or row.get("v_id")
        if vid:
            merged["event_id"] = vid
    return merged


def _node_from_event_row(row: dict[str, Any]) -> dict[str, Any]:
    """Map a PRINT row (event fields) to our node schema."""
    row = _flatten_tg_vertex_row(row) if row else row
    eid = str(row.get("event_id") or row.get("id") or row.get("v_id") or "").strip()
    title = str(row.get("title") or row.get("name") or eid).strip()
    attrs = {k: v for k, v in row.items() if k not in ("event_id", "id", "v_id")}
    return {
        "id": eid or title,
        "label": title[:200] if title else (eid or "Event"),
        "type": "Event",
        "attributes": attrs,
    }


def _parse_edge_line(line: str) -> dict[str, Any] | None:
    """
    Parse ``causal_explosion_viz`` edge string:
    ``from|to|strength|lag_days|polarity|influence_type``
    """
    parts = line.split("|")
    if len(parts) < 2:
        return None
    src, tgt = parts[0].strip(), parts[1].strip()
    if not src or not tgt:
        return None
    attrs: dict[str, Any] = {}
    if len(parts) > 2:
        attrs["strength"] = parts[2]
    if len(parts) > 3:
        attrs["lag_days"] = parts[3]
    if len(parts) > 4:
        attrs["polarity"] = parts[4]
    if len(parts) > 5:
        attrs["influence_type"] = parts[5]
    return {
        "source": src,
        "target": tgt,
        "type": "INFLUENCES",
        "attributes": attrs,
    }


def graph_viz_from_causal_explosion_viz(raw: Any) -> dict[str, Any]:
    """Normalize output of installed query ``causal_explosion_viz``."""
    block = _unwrap_first_block(raw)
    nodes_raw = block.get("Nodes") or block.get("nodes")
    edges_raw = block.get("edges") or block.get("@@edge_lines")

    nodes_in = _as_dict_list(nodes_raw)
    if not nodes_in and isinstance(nodes_raw, list):
        nodes_in = [x for x in nodes_raw if isinstance(x, dict)]

    nodes = [_node_from_event_row(r) for r in nodes_in if r]

    edges: list[dict[str, Any]] = []
    if isinstance(edges_raw, list):
        for line in edges_raw:
            if isinstance(line, str):
                e = _parse_edge_line(line)
                if e:
                    edges.append(e)

    return {"nodes": nodes, "edges": edges}


def graph_viz_from_narrative_trace(raw: Any) -> dict[str, Any]:
    """
    Normalize output of ``narrative_trace``.

    Installed query returns **seed** (focal event) plus **out_rows** (predecessors only).
    Older installs used a single ``Out`` block without the seed — we still accept ``Out``/``out``.
    """
    block = _unwrap_first_block(raw)
    if block.get("error"):
        return {"nodes": [], "edges": []}

    seed_rows = _as_dict_list(block.get("seed") or block.get("Seed") or [])
    out_raw = block.get("out_rows") or block.get("Out") or block.get("out") or []
    out_list = _as_dict_list(out_raw)
    if not out_list and isinstance(out_raw, list):
        out_list = [x for x in out_raw if isinstance(x, dict)]

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for r in seed_rows + out_list:
        flat = _flatten_tg_vertex_row(r) if r else {}
        nid = str(flat.get("event_id") or flat.get("v_id") or r.get("event_id") or "").strip()
        if not nid or nid in seen:
            continue
        seen.add(nid)
        merged.append(r)

    nodes = [_node_from_event_row(r) for r in merged if r]
    return {"nodes": nodes, "edges": []}


def ensure_narrative_focal_node(
    graph_viz: dict[str, Any],
    query_name: str,
    *,
    event_id: str | None,
    event_resolution: dict[str, Any] | None = None,
) -> None:
    """
    If ``narrative_trace`` returned no nodes (unknown id error shape, or old GSQL without seed PRINT),
    inject a minimal focal node from resolution metadata so the LLM and UI are not empty.
    """
    if query_name != "narrative_trace" or not event_id:
        return
    nodes = graph_viz.get("nodes") or []
    if nodes:
        return
    er = event_resolution or {}
    preview = er.get("candidates_preview") or []
    title: str | None = None
    ts = None
    loc = None
    url = None
    for p in preview:
        if p.get("event_id") == event_id:
            title = p.get("title")
            ts = p.get("timestamp")
            loc = p.get("location")
            url = p.get("source_url")
            break
    label = (str(title).strip() if title else event_id)[:200]
    attrs: dict[str, Any] = {
        "focal_seed": True,
        "narrative_note": (
            "No INFLUENCES predecessors were returned for this seed within hop/top_k limits "
            "(or reinstall narrative_trace GSQL to include the seed vertex in the response)."
        ),
    }
    if title:
        attrs["title"] = title
    if ts is not None:
        attrs["timestamp"] = ts
    if loc:
        attrs["location"] = loc
    if url:
        attrs["source_url"] = url
    graph_viz["nodes"] = [
        {
            "id": event_id,
            "label": label,
            "type": "Event",
            "attributes": attrs,
        }
    ]


def graph_viz_from_event_text_search(raw: Any) -> dict[str, Any]:
    """Normalize output of installed query ``event_text_search`` (candidate events, no edges)."""
    block = _unwrap_first_block(raw)
    rows = block.get("matches") or block.get("Matches") or []
    nodes_in = _as_dict_list(rows)
    if not nodes_in and isinstance(rows, list):
        nodes_in = [x for x in rows if isinstance(x, dict)]
    nodes = [_node_from_event_row(r) for r in nodes_in if r]
    return {"nodes": nodes, "edges": []}


def build_graph_viz(query_name: str, raw: Any) -> dict[str, Any]:
    """Dispatch to the correct normalizer for a whitelisted query name."""
    if query_name == "causal_explosion_viz":
        return graph_viz_from_causal_explosion_viz(raw)
    if query_name == "narrative_trace":
        return graph_viz_from_narrative_trace(raw)
    if query_name == "event_text_search":
        return graph_viz_from_event_text_search(raw)
    # Safe fallback: try causal shape, then narrative
    g1 = graph_viz_from_causal_explosion_viz(raw)
    if g1["nodes"] or g1["edges"]:
        return g1
    return graph_viz_from_narrative_trace(raw)


def compact_graph_json_for_llm(graph_viz: dict[str, Any], max_nodes: int = 40) -> str:
    """Short JSON string for LLM context (truncated)."""
    slim = {
        "nodes": graph_viz.get("nodes", [])[:max_nodes],
        "edges": graph_viz.get("edges", [])[: max_nodes * 2],
    }
    return json.dumps(slim, ensure_ascii=False, default=str)[:12000]


def _find_source_url_in_value(obj: Any, depth: int = 0) -> str | None:
    """Depth-first search for a string ``source_url`` or any http(s) field named like a URL."""
    if depth > 12:
        return None
    if isinstance(obj, dict):
        u = obj.get("source_url")
        if isinstance(u, str) and u.startswith("http"):
            return u
        for v in obj.values():
            found = _find_source_url_in_value(v, depth + 1)
            if found:
                return found
    return None


def collect_source_urls(graph_viz: dict[str, Any], limit: int = 8) -> list[str]:
    """Gather ``source_url`` values from event nodes for article fetching."""
    urls: list[str] = []
    seen: set[str] = set()
    for n in graph_viz.get("nodes", []):
        attrs = n.get("attributes") or {}
        u = str(attrs.get("source_url") or "").strip()
        if not u.startswith("http"):
            u = _find_source_url_in_value(attrs) or ""
        if u.startswith("http") and u not in seen:
            seen.add(u)
            urls.append(u)
        if len(urls) >= limit:
            break
    return urls
