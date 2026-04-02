"""Heuristics for event resolution (no TigerGraph)."""

from __future__ import annotations

import unittest

from chintu.nlp.event_resolve import (
    expand_needles_for_gdelt_titles,
    heuristic_search_needles,
    sanitize_search_needle,
)


class TestSearchNeedles(unittest.TestCase):
    def test_sanitize_strips_like_wildcards(self):
        self.assertEqual(sanitize_search_needle("foo%bar_baz"), "foo bar baz")

    def test_heuristic_from_quoted_and_tokens(self):
        q = 'What happened after "Rio Grande" floods in Brazil?'
        n = heuristic_search_needles(q)
        self.assertIn("Rio Grande", n)
        self.assertTrue(any("Brazil" in x or x == "Brazil" for x in n))

    def test_expand_splits_phrases_for_substring_match(self):
        base = ["Iran nuclear program", "US sanctions", "tensions"]
        kw = ["Iran", "nuclear program"]
        exp = expand_needles_for_gdelt_titles(base, kw)
        lows = {x.lower() for x in exp}
        self.assertIn("iran", lows)
        self.assertIn("nuclear", lows)
        self.assertIn("program", lows)
        self.assertIn("sanctions", lows)
        self.assertNotIn("tensions", lows)


if __name__ == "__main__":
    unittest.main()
