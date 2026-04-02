"""
Use an LLM to turn a user question into **structured JSON**:

- ``intent`` — which kind of graph question this is
- ``keywords`` — short phrases for logging / UI
- ``event_id`` — CHINTU Event primary key when the user names one (``evt_...``)
- ``max_hops``, ``top_k`` — graph search bounds

If ``OPENAI_API_KEY`` is missing, we fall back to a tiny heuristic (regex ``evt_*`` only).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

from chintu.viz_payload import extract_event_id_heuristic

# Intents must match keys in ``query_router.INTENT_TO_QUERY`` (plus ``unknown``).
_INTENT_JSON_SCHEMA_HINT = """
Return ONLY valid JSON with keys:
- intent: one of "causal_explore", "narrative_trace", "unknown"
- keywords: array of 3-8 short strings
- event_id: string or null (CHINTU Event id like evt_abc123 only if the user pasted it or it appears verbatim)
- event_search_needles: array of 3-8 tokens when event_id is null. Titles in the DB look like "IRAN other event" or "UNITED STATES - IRANIAN other event" — use **single words or very short proper-name chunks** that literally appear inside those titles (IRAN, ISRAEL, Tehran, Trump, sanctions, nuclear). Avoid abstract multi-word phrases only ("Iran nuclear program") and avoid useless alone words (tensions, crisis, situation).
- max_hops: integer 1-5, default 3
- top_k: integer 5-200, default 50
- reasoning: one short sentence (for developers)

causal_explore: downstream effects, consequences, "what happened next", geopolitical ripples.
narrative_trace: predecessors, roots, "what led to this", backstory.
unknown: chit-chat, coding help, or nothing to do with news events / causality.
Do NOT set unknown solely because event_id is missing — use event_search_needles so the backend can search the graph.
"""


@dataclass
class IntentResult:
    intent: str
    keywords: list[str]
    event_id: str | None
    event_search_needles: list[str] = field(default_factory=list)
    max_hops: int = 3
    top_k: int = 50
    reasoning: str = ""
    raw_model_json: dict | None = None


def _clamp_int(n: Any, default: int, lo: int, hi: int) -> int:
    try:
        v = int(n)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def _heuristic_intent(question: str) -> IntentResult:
    """No API key: detect ``evt_*`` ids, else causal/narrative + substring needles when possible."""
    from chintu.nlp.event_resolve import heuristic_search_needles

    q = (question or "").strip()
    eid = extract_event_id_heuristic(q)
    if eid:
        # Default to causal_explore when we only know the id (user can switch via explicit words later).
        lower = q.lower()
        if any(w in lower for w in ("why", "led to", "predecessor", "before", "cause", "root")):
            intent = "narrative_trace"
        else:
            intent = "causal_explore"
        return IntentResult(
            intent=intent,
            keywords=re.findall(r"\w{4,}", lower)[:8],
            event_id=eid,
            max_hops=3,
            top_k=50,
            reasoning="Heuristic: found evt_* id in text (no LLM).",
        )
    lower = q.lower()
    needles = heuristic_search_needles(q)
    narrative_hints = ("why", "led to", "predecessor", "before", "cause", "root", "brought")
    causal_hints = (
        "after",
        "next",
        "downstream",
        "effect",
        "consequence",
        "happened",
        "impact",
        "result",
        "then",
    )
    if needles and (any(w in lower for w in causal_hints) or any(w in lower for w in narrative_hints)):
        intent = "narrative_trace" if any(w in lower for w in narrative_hints) else "causal_explore"
        return IntentResult(
            intent=intent,
            keywords=re.findall(r"\w{4,}", lower)[:8],
            event_id=None,
            event_search_needles=needles,
            max_hops=3,
            top_k=50,
            reasoning="Heuristic: no evt_* id; using substring needles + cue words (no LLM).",
        )
    return IntentResult(
        intent="unknown",
        keywords=[],
        event_id=None,
        reasoning="No OPENAI_API_KEY, no evt_* id, and no usable search needles in the question.",
    )


def parse_question_intent(question: str) -> IntentResult:
    """
    Parse the user's natural-language question.

    Uses OpenAI if ``OPENAI_API_KEY`` is set; otherwise :func:`_heuristic_intent`.
    """
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        return _heuristic_intent(question)

    from chintu.llm.client import chat_completion_json

    system = (
        "You map user questions about news events and causality to a fixed JSON schema. "
        + _INTENT_JSON_SCHEMA_HINT
    )
    user = f"Question:\n{question.strip()}"
    try:
        data = chat_completion_json(
            system=system,
            user=user,
            temperature=0.2,
        )
    except Exception:
        return _heuristic_intent(question)

    if not isinstance(data, dict):
        return _heuristic_intent(question)

    intent = str(data.get("intent") or "unknown").strip()
    if intent not in ("causal_explore", "narrative_trace", "unknown"):
        intent = "unknown"
    keywords = data.get("keywords")
    if not isinstance(keywords, list):
        keywords = []
    keywords = [str(k).strip() for k in keywords if str(k).strip()][:12]
    eid = data.get("event_id")
    if eid is not None:
        eid = str(eid).strip() or None
    if eid and not eid.startswith("evt_"):
        # Allow model mistakes; try substring
        m = re.search(r"evt_[a-zA-Z0-9_]+", eid)
        eid = m.group(0) if m else extract_event_id_heuristic(eid)

    esn = data.get("event_search_needles")
    needles: list[str] = []
    if isinstance(esn, list):
        needles = [str(x).strip() for x in esn if str(x).strip()][:8]

    return IntentResult(
        intent=intent,
        keywords=keywords,
        event_id=eid,
        event_search_needles=needles,
        max_hops=_clamp_int(data.get("max_hops"), 3, 1, 5),
        top_k=_clamp_int(data.get("top_k"), 50, 5, 200),
        reasoning=str(data.get("reasoning") or "")[:500],
        raw_model_json=data,
    )


def intent_result_to_json(ir: IntentResult) -> dict:
    """Serialize for API responses (optional debug)."""
    return {
        "intent": ir.intent,
        "keywords": ir.keywords,
        "event_id": ir.event_id,
        "event_search_needles": ir.event_search_needles,
        "max_hops": ir.max_hops,
        "top_k": ir.top_k,
        "reasoning": ir.reasoning,
    }
