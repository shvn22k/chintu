"""
Resolve a natural-language question to a CHINTU ``evt_*`` id when the user does not paste one.

Pipeline: search needles (from intent LLM or heuristics) → ``event_text_search`` on TigerGraph →
optional LLM disambiguation among top candidates.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from typing import Any

from chintu.nlp.intent_extract import IntentResult
from chintu.tigergraph_client import run_installed_query
from chintu.viz_payload import extract_event_id_heuristic, graph_viz_from_event_text_search

_STOP = frozenset(
    """
    what when where which this that from with have were been after before about their there
    would could should might must event effects happen causal trace downstream consequences
    impact results leads led lead causes caused because why how does did doing into onto
    the and for you are was were not but can may its his her they them then than only also
    just like more most some such very will your our out off over under again further once
    here there where every other another into through during before after above below
    between both each few own same so than too very just don now being during
    us per the new old any all
    """.split()
)

# Substring search on these almost never hits GDELT-style titles ("IRAN other event", etc.).
_VAGUE_SUBSTRINGS = frozenset(
    """
    tensions tension conflict situation crisis developments fallout uncertainty escalation
    background context consequences implications geopolitics geopolitical
    """.split()
)


def _openai_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def sanitize_search_needle(s: str) -> str:
    """Strip SQL LIKE wildcards and junk so user/LLM input cannot broaden the pattern."""
    t = re.sub(r"[%_\[\]]+", " ", (s or "").strip())
    t = re.sub(r"\s+", " ", t).strip()
    return t[:100]


def expand_needles_for_gdelt_titles(
    needles: list[str],
    keywords: list[str] | None = None,
    *,
    max_total: int = 16,
) -> list[str]:
    """
    GDELT event titles are usually short tokens (e.g. ``IRAN other event``). A phrase like
    ``Iran nuclear program`` will not match ``LIKE '%needle%'``. Expand to individual
    words (and keyword tokens) so at least one substring hits.
    """
    seen: set[str] = set()
    out: list[str] = []

    def consider(raw: str, *, allow_vague: bool = False) -> None:
        s = sanitize_search_needle(raw)
        if len(s) < 3:
            return
        low = s.lower()
        if low in seen:
            return
        if not allow_vague and low in _VAGUE_SUBSTRINGS:
            return
        if low in _STOP:
            return
        seen.add(low)
        out.append(s)

    for n in needles:
        s = sanitize_search_needle(n)
        if not s:
            continue
        sl = s.lower()
        # Skip lone fuzzy words as a full needle (they rarely match GDELT titles).
        if not (sl in _VAGUE_SUBSTRINGS and " " not in s):
            # Full phrase first (sometimes matches description or longer titles).
            consider(s, allow_vague=True)
        for part in re.split(r"[\s,\-/]+", s):
            part = part.strip("-'\"")
            if len(part) >= 3:
                consider(part, allow_vague=False)

    if keywords:
        for kw in keywords[:12]:
            ks = sanitize_search_needle(str(kw))
            if not ks:
                continue
            consider(ks, allow_vague=True)
            for part in re.split(r"[\s,\-/]+", ks):
                part = part.strip("-'\"")
                if len(part) >= 3:
                    consider(part, allow_vague=False)

    return out[:max_total]


def heuristic_search_needles(question: str) -> list[str]:
    """No-LLM fallback: quoted phrases + longest alphabetic tokens (for TG substring search)."""
    q = (question or "").strip()
    if not q:
        return []
    out: list[str] = []
    for m in re.finditer(r'"([^"]{3,120})"|\'([^\']{3,120})\'', q):
        chunk = (m.group(1) or m.group(2) or "").strip()
        if len(chunk) >= 3:
            out.append(chunk)
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,48}", q)
    for t in tokens:
        low = t.lower()
        if low in _STOP or t in out:
            continue
        out.append(t)
        if len(out) >= 8:
            break
    seen: set[str] = set()
    uniq: list[str] = []
    for x in out:
        sx = sanitize_search_needle(x)
        if len(sx) < 2:
            continue
        key = sx.lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(sx)
        if len(uniq) >= 6:
            break
    return uniq


def _rows_from_event_search_raw(raw: Any) -> list[dict[str, Any]]:
    g = graph_viz_from_event_text_search(raw)
    nodes = g.get("nodes") or []
    rows: list[dict[str, Any]] = []
    for n in nodes:
        eid = str(n.get("id") or "").strip()
        if not eid:
            continue
        attrs = dict(n.get("attributes") or {})
        row = {
            "event_id": eid,
            "title": attrs.get("title") or n.get("label"),
            "description": attrs.get("description"),
            "timestamp": attrs.get("timestamp"),
            "location": attrs.get("location"),
            "source_url": attrs.get("source_url"),
        }
        rows.append(row)
    return rows


def run_event_text_search(needle: str, max_results: int = 25) -> list[dict[str, Any]]:
    sn = sanitize_search_needle(needle)
    if len(sn) < 2:
        return []
    raw = run_installed_query(
        "event_text_search",
        {"needle": sn, "max_results": int(max_results)},
    )
    return _rows_from_event_search_raw(raw)


def aggregate_event_candidates(needles: list[str], *, max_per_needle: int = 22, max_needles: int = 14) -> list[dict[str, Any]]:
    """
    Run one substring search per needle and merge by event_id.
    Rank by (hit count across needles, then timestamp desc).
    """
    scores: dict[str, int] = defaultdict(int)
    by_id: dict[str, dict[str, Any]] = {}
    for n in needles[:max_needles]:
        rows = run_event_text_search(n, max_results=max_per_needle)
        for r in rows:
            eid = r.get("event_id")
            if not eid:
                continue
            scores[str(eid)] += 1
            if eid not in by_id:
                by_id[str(eid)] = r

    def sort_key(eid: str) -> tuple[int, str]:
        ts = str(by_id[eid].get("timestamp") or "")
        return (-scores[eid], ts)

    ordered = sorted(by_id.keys(), key=sort_key)
    return [by_id[i] for i in ordered]


def llm_expand_search_needles(question: str, keywords: list[str]) -> list[str]:
    """Ask the model for short substring needles that should match Event.title in the DB."""
    from chintu.llm.client import chat_completion_json

    system = (
        "You help search a news-event database. Event titles look like short tokens: "
        "\"IRAN other event\", \"UNITED STATES - IRANIAN other event\", city or country names — "
        "NOT full sentences. Return ONLY JSON: {\"needles\": [\"3-6 strings\"], \"note\": \"optional\"}. "
        "Each needle must be something that can appear INSIDE such a title: single country or actor "
        "(IRAN, ISRAEL, Tehran, Trump), or a very short phrase. "
        "Do NOT use abstract multi-word concepts like \"Iran nuclear program\" or \"US sanctions\" as "
        "the only needles — split into tokens: Iran, nuclear, sanctions, Israel, etc. "
        "Avoid useless alone words: tensions, crisis, situation, geopolitics."
    )
    payload = {"question": question.strip(), "keywords": keywords[:10]}
    data = chat_completion_json(system=system, user=json.dumps(payload, ensure_ascii=False), temperature=0.15)
    needles = data.get("needles") if isinstance(data, dict) else None
    if not isinstance(needles, list):
        return []
    out: list[str] = []
    for x in needles:
        s = sanitize_search_needle(str(x))
        if len(s) >= 2:
            out.append(s)
    return out[:6]


def llm_pick_best_event(question: str, candidates: list[dict[str, Any]]) -> tuple[str | None, float]:
    """Return (event_id, confidence)."""
    from chintu.llm.client import chat_completion_json

    if not candidates:
        return None, 0.0
    slim = [
        {
            "event_id": c.get("event_id"),
            "title": c.get("title"),
            "location": c.get("location"),
            "timestamp": c.get("timestamp"),
        }
        for c in candidates[:14]
        if c.get("event_id")
    ]
    if not slim:
        return None, 0.0
    if len(slim) == 1:
        return str(slim[0]["event_id"]), 1.0

    system = (
        "Pick the single event record that best matches the user's question. "
        'Return ONLY JSON: {"event_id": "evt_..."|null, "confidence": number 0-1}. '
        "If none fit, event_id null and confidence low."
    )
    user = json.dumps({"question": question.strip(), "candidates": slim}, ensure_ascii=False)
    data = chat_completion_json(system=system, user=user, temperature=0.1)
    if not isinstance(data, dict):
        return str(slim[0]["event_id"]), 0.4
    eid = data.get("event_id")
    if eid is not None:
        eid = str(eid).strip()
    try:
        conf = float(data.get("confidence", 0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    if not eid or not eid.startswith("evt_"):
        return str(slim[0]["event_id"]), conf
    return eid, conf


def resolve_event_id_for_question(intent: IntentResult, question: str) -> tuple[str | None, dict[str, Any]]:
    """
    Return ``(event_id, resolution_meta)`` for graph queries.

    ``resolution_meta`` is safe to merge into API ``meta`` (needles tried, previews, confidence).
    """
    q = (question or "").strip()
    meta: dict[str, Any] = {"event_resolution": {}}
    er: dict[str, Any] = meta["event_resolution"]

    direct = intent.event_id or extract_event_id_heuristic(q)
    if direct:
        er["source"] = "user_or_heuristic_id"
        return direct, meta

    if intent.intent not in ("causal_explore", "narrative_trace"):
        er["source"] = "skipped_intent"
        return None, meta

    needles: list[str] = []
    if intent.event_search_needles:
        needles = [sanitize_search_needle(x) for x in intent.event_search_needles if sanitize_search_needle(x)]
    if not needles and _openai_configured():
        try:
            needles = llm_expand_search_needles(q, intent.keywords)
            er["needles_from"] = "llm_expand"
        except Exception as e:
            er["llm_expand_error"] = str(e)[:200]
    if not needles:
        needles = heuristic_search_needles(q)
        er["needles_from"] = er.get("needles_from") or "heuristic"

    expanded = expand_needles_for_gdelt_titles(needles, intent.keywords)
    er["needles_tried"] = expanded
    if len(expanded) > len(needles):
        er["needles_pre_expand"] = needles[:12]

    if not expanded:
        er["source"] = "no_needles"
        return None, meta

    try:
        candidates = aggregate_event_candidates(expanded)
    except Exception as e:
        er["search_error"] = str(e)[:500]
        return None, meta

    er["candidate_count"] = len(candidates)
    er["candidates_preview"] = [
        {
            "event_id": c.get("event_id"),
            "title": c.get("title"),
            "timestamp": c.get("timestamp"),
            "location": c.get("location"),
            "source_url": c.get("source_url"),
        }
        for c in candidates[:8]
    ]

    if not candidates:
        er["source"] = "no_matches"
        return None, meta

    if len(candidates) == 1:
        er["source"] = "search_unique"
        er["picked_event_id"] = candidates[0]["event_id"]
        er["confidence"] = 1.0
        return str(candidates[0]["event_id"]), meta

    picked: str | None = None
    conf = 0.55
    if _openai_configured():
        try:
            picked, conf = llm_pick_best_event(q, candidates)
            er["source"] = "search_llm_pick"
        except Exception as e:
            er["llm_pick_error"] = str(e)[:200]
            picked = str(candidates[0]["event_id"])
            conf = 0.45
            er["source"] = "search_fallback_first"
    else:
        picked = str(candidates[0]["event_id"])
        conf = 0.45
        er["source"] = "search_first_ranked_no_llm"

    er["picked_event_id"] = picked
    er["confidence"] = conf
    if conf < 0.55:
        er["low_confidence"] = True

    return picked, meta
