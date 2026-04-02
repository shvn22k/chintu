"""Tests for REST response parsing (no live TigerGraph)."""

from __future__ import annotations

import unittest

from chintu.tigergraph_rest import _parse_builtin_vertex_count


class TestBuiltinVertexCount(unittest.TestCase):
    def test_wrapped_results_v2(self):
        data = {
            "version": {"edition": "enterprise", "api": "v2", "schema": 2},
            "error": False,
            "message": "",
            "results": [{"v_type": "Topic", "count": 5}],
        }
        self.assertEqual(_parse_builtin_vertex_count(data, "Topic"), 5)

    def test_bare_list(self):
        data = [{"v_type": "Event", "count": 103}]
        self.assertEqual(_parse_builtin_vertex_count(data, "Event"), 103)


if __name__ == "__main__":
    unittest.main()
