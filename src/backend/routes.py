"""
HTTP routes — keep handlers thin; logic lives in ``chintu.pipeline`` and ``chintu.*``.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from chintu.nlp.query_router import ALLOWED_QUERIES
from chintu.pipeline.ask import run_ask_pipeline, run_nlp_parse_only, run_whitelisted_graph_query
from chintu.llm.client import openai_healthcheck
from chintu.tigergraph_client import ping_graph

api_bp = Blueprint("api", __name__)


@api_bp.get("/health/openai")
def health_openai():
    """Verify ``OPENAI_*`` env + a real ``models.list`` (no secrets in response)."""
    data = openai_healthcheck()
    code = 200 if data.get("ok") else 503
    return jsonify(data), code


@api_bp.get("/health/graph")
def health_graph():
    """TigerGraph connectivity + coarse counts."""
    try:
        data = ping_graph()
        code = 200 if data.get("ok") else 503
        return jsonify(data), code
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)[:500]}), 503


@api_bp.post("/chat/complete")
def chat_complete():
    """
    Full user flow: NLP → graph → articles → LLM.

    Body JSON: ``{"question": "..."}``
    """
    body = request.get_json(silent=True) or {}
    question = body.get("question", "")
    if not isinstance(question, str):
        return jsonify({"error": "invalid_body", "detail": "question must be a string"}), 400
    result = run_ask_pipeline(question)
    return jsonify(result), 200


@api_bp.post("/nlp/parse")
def nlp_parse():
    """Debug: intent + optional ``event_text_search`` resolution + planned query (no main graph/answer LLM)."""
    body = request.get_json(silent=True) or {}
    question = body.get("question", "")
    if not isinstance(question, str):
        return jsonify({"error": "invalid_body", "detail": "question must be a string"}), 400
    return jsonify(run_nlp_parse_only(question)), 200


@api_bp.post("/graph/query")
def graph_query():
    """
    Debug: run one **whitelisted** installed query with explicit parameters.

    Body JSON::

        {"query": "causal_explosion_viz", "params": {"event_id": "evt_...", "max_hops": 3, "top_k": 50}}
    """
    body = request.get_json(silent=True) or {}
    qname = body.get("query")
    params = body.get("params")
    if not isinstance(qname, str) or not isinstance(params, dict):
        return (
            jsonify(
                {
                    "error": "invalid_body",
                    "detail": 'Expected {"query": string, "params": object}',
                }
            ),
            400,
        )
    if qname not in ALLOWED_QUERIES:
        return (
            jsonify(
                {
                    "error": "query_not_allowed",
                    "detail": f"Allowed: {sorted(ALLOWED_QUERIES)}",
                }
            ),
            400,
        )
    try:
        graph_viz, raw = run_whitelisted_graph_query(qname, params)
    except Exception as e:
        return jsonify({"error": "tigergraph_error", "detail": str(e)[:1000]}), 502
    return jsonify({"graph_viz": graph_viz, "raw": raw}), 200
