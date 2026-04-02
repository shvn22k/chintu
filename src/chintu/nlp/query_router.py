"""
Map a structured :class:`IntentResult` to a **whitelisted** installed query name and parameters.

We never pass client-supplied raw GSQL — only fixed query names and bounded integers.
"""

from __future__ import annotations

from dataclasses import dataclass

from chintu.nlp.intent_extract import IntentResult
from chintu.viz_payload import extract_event_id_heuristic

# intent string -> TigerGraph installed query name (must exist on your graph).
INTENT_TO_QUERY: dict[str, str] = {
    "causal_explore": "causal_explosion_viz",
    "narrative_trace": "narrative_trace",
}

# Optional lookups (debug / resolution); not chosen from intent alone.
_EXTRA_ALLOWED = frozenset({"event_text_search"})

ALLOWED_QUERIES = frozenset(INTENT_TO_QUERY.values()) | _EXTRA_ALLOWED


@dataclass
class QueryPlan:
    """Resolved server-side graph call."""

    query_name: str
    params: dict
    intent: str


def build_query_plan(intent_result: IntentResult, question_fallback: str = "") -> QueryPlan | None:
    """
    Build a plan or return ``None`` if we cannot run a safe graph query.

    Callers should set ``intent_result.event_id`` after :func:`~chintu.nlp.event_resolve.resolve_event_id_for_question`
    when the user did not paste ``evt_*`` (see ``ask`` pipeline).
    """
    if intent_result.intent == "unknown":
        return None
    qname = INTENT_TO_QUERY.get(intent_result.intent)
    if not qname:
        return None

    eid = intent_result.event_id or extract_event_id_heuristic(question_fallback)
    if not eid:
        return None

    return QueryPlan(
        query_name=qname,
        params={
            "event_id": eid,
            "max_hops": int(intent_result.max_hops),
            "top_k": int(intent_result.top_k),
        },
        intent=intent_result.intent,
    )
