"""Unit tests for graph response normalization (no TigerGraph required)."""

from __future__ import annotations

import unittest

from chintu.viz_payload import (
    build_graph_viz,
    collect_source_urls,
    ensure_narrative_focal_node,
    extract_event_id_heuristic,
    graph_viz_from_causal_explosion_viz,
    graph_viz_from_event_text_search,
    graph_viz_from_narrative_trace,
)


class TestEventIdHeuristic(unittest.TestCase):
    def test_finds_evt_token(self):
        self.assertEqual(
            extract_event_id_heuristic("What about evt_ab12_cd then?"),
            "evt_ab12_cd",
        )

    def test_none_when_missing(self):
        self.assertIsNone(extract_event_id_heuristic("no id here"))


class TestCausalViz(unittest.TestCase):
    def test_parses_nodes_and_edges(self):
        raw = [
            {
                "Nodes": [
                    {
                        "event_id": "evt_1",
                        "title": "A",
                        "source_url": "https://example.com/a",
                    }
                ],
                "edges": ["evt_1|evt_2|0.5|0|1|direct"],
            }
        ]
        g = graph_viz_from_causal_explosion_viz(raw)
        self.assertEqual(len(g["nodes"]), 1)
        self.assertEqual(g["nodes"][0]["id"], "evt_1")
        self.assertEqual(len(g["edges"]), 1)
        self.assertEqual(g["edges"][0]["source"], "evt_1")
        self.assertEqual(g["edges"][0]["target"], "evt_2")

    def test_build_graph_viz_dispatch(self):
        raw = [{"Nodes": [{"event_id": "e1", "title": "T"}], "edges": []}]
        g = build_graph_viz("causal_explosion_viz", raw)
        self.assertEqual(g["nodes"][0]["id"], "e1")

    def test_event_text_search_shape(self):
        raw = [{"matches": [{"event_id": "evt_x", "title": "Flood zone visit", "location": "Brazil"}]}]
        g = graph_viz_from_event_text_search(raw)
        self.assertEqual(len(g["nodes"]), 1)
        self.assertEqual(g["nodes"][0]["id"], "evt_x")
        self.assertEqual(g["edges"], [])
        g2 = build_graph_viz("event_text_search", raw)
        self.assertEqual(g2["nodes"][0]["label"], "Flood zone visit")

    def test_narrative_trace_merges_seed_and_predecessors(self):
        raw = [
            {
                "seed": [{"event_id": "evt_seed", "title": "IRAN other event", "hop_count": 0}],
                "out_rows": [{"event_id": "evt_prev", "title": "Earlier event", "hop_count": 1}],
            }
        ]
        g = graph_viz_from_narrative_trace(raw)
        self.assertEqual(len(g["nodes"]), 2)
        self.assertEqual(g["nodes"][0]["id"], "evt_seed")

    def test_ensure_narrative_focal_node_fills_empty(self):
        gv = {"nodes": [], "edges": []}
        ensure_narrative_focal_node(
            gv,
            "narrative_trace",
            event_id="evt_1",
            event_resolution={
                "candidates_preview": [
                    {"event_id": "evt_1", "title": "Test title", "source_url": "https://example.com/a"}
                ]
            },
        )
        self.assertEqual(len(gv["nodes"]), 1)
        self.assertEqual(gv["nodes"][0]["id"], "evt_1")
        self.assertEqual(gv["nodes"][0]["attributes"].get("source_url"), "https://example.com/a")

    def test_rest_nested_attributes_flatten_and_urls(self):
        """TigerGraph REST often wraps fields under attributes (sometimes double-nested)."""
        raw = [
            {
                "Nodes": [
                    {
                        "v_id": "evt_x",
                        "v_type": "Event",
                        "attributes": {
                            "title": "Headline",
                            "attributes": {
                                "source_url": "https://example.com/news",
                            },
                        },
                    }
                ],
                "edges": [],
            }
        ]
        g = graph_viz_from_causal_explosion_viz(raw)
        self.assertEqual(g["nodes"][0]["id"], "evt_x")
        self.assertEqual(g["nodes"][0]["label"], "Headline")
        self.assertNotIn("attributes", g["nodes"][0]["attributes"])
        urls = collect_source_urls(g)
        self.assertEqual(urls, ["https://example.com/news"])


if __name__ == "__main__":
    unittest.main()
