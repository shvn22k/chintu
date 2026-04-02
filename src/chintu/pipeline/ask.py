"""
Full **ask** pipeline: question → intent → TigerGraph → articles → LLM answer.

This module is UI-agnostic; Flask routes should only call these functions and return JSON.
"""

from __future__ import annotations

import os
from dataclasses import replace
from typing import Any

from chintu.articles.link_fetch import fetch_many_excerpts
from chintu.llm import prompts
from chintu.nlp.event_resolve import resolve_event_id_for_question
from chintu.nlp.intent_extract import intent_result_to_json, parse_question_intent
from chintu.nlp.query_router import ALLOWED_QUERIES, QueryPlan, build_query_plan
from chintu.tigergraph_client import run_installed_query
from chintu.viz_payload import (
    build_graph_viz,
    collect_source_urls,
    compact_graph_json_for_llm,
    ensure_narrative_focal_node,
)

RESPONSE_VERSION = "1"


def _envelope(
    *,
    answer: str,
    graph_viz: dict[str, Any],
    sources: dict[str, Any],
    meta: dict[str, Any],
    error: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "version": RESPONSE_VERSION,
        "answer": answer,
        "graph_viz": graph_viz,
        "sources": sources,
        "meta": meta,
    }
    if error:
        body["error"] = error
    return body


def _openai_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def run_nlp_parse_only(question: str) -> dict[str, Any]:
    """
    Run intent extraction, **event id resolution** (may call ``event_text_search`` on TigerGraph),
    and query planning. Does **not** run ``causal_explosion_viz`` / ``narrative_trace`` or the answer LLM.
    """
    q = (question or "").strip()
    intent = parse_question_intent(q)
    resolved_id, res_meta = resolve_event_id_for_question(intent, q)
    intent_r = replace(intent, event_id=intent.event_id or resolved_id)
    plan = build_query_plan(intent_r, q)
    out: dict[str, Any] = {
        "question": q,
        "intent": intent_result_to_json(intent),
        "query_plan": (
            None
            if plan is None
            else {"query_name": plan.query_name, "params": plan.params, "intent": plan.intent}
        ),
    }
    er = res_meta.get("event_resolution") if isinstance(res_meta, dict) else None
    if isinstance(er, dict) and er:
        out["event_resolution"] = er
    return out


def run_ask_pipeline(question: str) -> dict[str, Any]:
    """
    End-to-end flow for ``POST /api/v1/chat/complete``.

    Always returns the stable response envelope; check ``error`` for soft failures.
    """
    q = (question or "").strip()
    if not q:
        return _envelope(
            answer="Please provide a non-empty question.",
            graph_viz={"nodes": [], "edges": []},
            sources={"articles": [], "graph_query": None},
            meta={},
            error="empty_question",
        )

    intent = parse_question_intent(q)
    resolved_id, res_meta = resolve_event_id_for_question(intent, q)
    intent_for_plan = replace(intent, event_id=intent.event_id or resolved_id)
    plan = build_query_plan(intent_for_plan, q)

    meta: dict[str, Any] = {
        "intent": intent.intent,
        "keywords": intent.keywords,
        "reasoning": intent.reasoning,
    }
    er0 = res_meta.get("event_resolution") if isinstance(res_meta, dict) else None
    if isinstance(er0, dict) and er0:
        meta["event_resolution"] = er0

    if plan is None:
        er = meta.get("event_resolution") or {}
        prev = er.get("candidates_preview") or []
        tg_err = er.get("search_error")
        if tg_err:
            hint = (
                "I tried to look up events in TigerGraph for your question, but the search query failed. "
                f"Details: {tg_err[:400]}\n\n"
                "Check that the installed query **event_text_search** is deployed (see `gsql/chintu_event_text_search.gsql`)."
            )
        elif prev:
            hint = (
                "I couldn't confidently pick one CHINTU event for that question. "
                "Closest title matches (try rephrasing with a **specific place, person, or incident**, or paste an `evt_...` id):\n\n"
                + "\n".join(f"- `{p.get('event_id')}` — {p.get('title') or '?'}" for p in prev[:6])
            )
        else:
            hint = (
                "Ask about a **real news-style event** (who / where / what happened) or paste a CHINTU **event id** (`evt_...`). "
                "We search event titles in the graph when you don't give an id — vague or off-topic questions won't match.\n\n"
                "Tip: set **OPENAI_API_KEY** in `.env` for better intent and search needles on messy questions."
            )
        return _envelope(
            answer=hint,
            graph_viz={"nodes": [], "edges": []},
            sources={"articles": [], "graph_query": None},
            meta=meta,
            error="no_query_plan",
        )

    try:
        raw = run_installed_query(plan.query_name, plan.params)
    except Exception as e:
        return _envelope(
            answer=f"The graph query failed. Check TigerGraph credentials and that the query is installed. Details: {e!s}"[
                :2000
            ],
            graph_viz={"nodes": [], "edges": []},
            sources={
                "articles": [],
                "graph_query": {"name": plan.query_name, "params": plan.params},
            },
            meta=meta,
            error="tigergraph_error",
        )

    graph_viz = build_graph_viz(plan.query_name, raw)
    ensure_narrative_focal_node(
        graph_viz,
        plan.query_name,
        event_id=str(plan.params.get("event_id") or ""),
        event_resolution=meta.get("event_resolution") if isinstance(meta.get("event_resolution"), dict) else None,
    )
    urls = collect_source_urls(graph_viz, limit=10)
    excerpts = fetch_many_excerpts(urls, per_url_limit=5)

    compact = compact_graph_json_for_llm(graph_viz)
    article_block_parts = []
    article_sources = []
    for ex in excerpts:
        article_sources.append(
            {
                "url": ex.url,
                "title": ex.title,
                "excerpt": (ex.text[:800] + "…") if len(ex.text) > 800 else ex.text,
                "ok": ex.ok,
                "error": ex.error,
            }
        )
        if ex.ok and ex.text:
            article_block_parts.append(f"URL: {ex.url}\nTitle: {ex.title or ''}\n{ex.text[:3500]}")

    article_block = "\n\n---\n\n".join(article_block_parts) or (
        "(No article text fetched — no usable source_url on nodes, fetch failed, or pages had no extractable text.)"
    )

    n_nodes = len(graph_viz.get("nodes") or [])
    n_edges = len(graph_viz.get("edges") or [])
    graph_stats_line = (
        f"Graph snapshot for this API response: {n_nodes} event node(s), {n_edges} INFLUENCES edge(s). "
        f"Article URLs attempted: {len(urls)}; excerpts assembled: {len(article_block_parts)}."
    )
    er_m = meta.get("event_resolution") or {}
    if er_m.get("low_confidence"):
        graph_stats_line += (
            " Several events matched the text search; the chosen evt_* may not be what the user meant."
        )

    graph_bullets: str
    if _openai_configured():
        try:
            from chintu.llm.client import chat_completion_text

            graph_bullets = chat_completion_text(
                system=prompts.GRAPH_BRIEF_SYSTEM,
                user=prompts.graph_brief_user(q, compact),
                temperature=0.3,
                max_tokens=600,
            )
        except Exception as e:
            graph_bullets = f"(Graph summary LLM step failed: {e!s})"
    else:
        graph_bullets = (
            "(Set OPENAI_API_KEY in `.env` to generate an LLM summary of the graph. "
            f"Raw graph excerpt: {compact[:1500]}…)"
            if len(compact) > 1500
            else f"(Set OPENAI_API_KEY for LLM summary.) Raw graph excerpt: {compact}"
        )

    if _openai_configured():
        try:
            from chintu.llm.client import chat_completion_text

            final = chat_completion_text(
                system=prompts.ANSWER_SYSTEM,
                user=prompts.answer_user_prompt(
                    q, graph_bullets, article_block, compact, graph_stats_line=graph_stats_line
                ),
                temperature=0.35,
                max_tokens=2200,
            )
        except Exception as e:
            final = f"Could not generate a full answer (LLM error: {e!s}).\n\nGraph bullets:\n{graph_bullets}"
    else:
        final = (
            "OPENAI_API_KEY is not set, so the narrative answer is limited.\n\n"
            f"**Graph summary (heuristic / bullets):**\n{graph_bullets}\n\n"
            f"**Fetched articles:** {len([a for a in article_sources if a.get('ok')])} ok / {len(article_sources)} tried."
        )

    return _envelope(
        answer=final,
        graph_viz=graph_viz,
        sources={
            "articles": article_sources,
            "graph_query": {"name": plan.query_name, "params": plan.params},
        },
        meta=meta,
    )


def run_whitelisted_graph_query(query_name: str, params: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    """
    Run a single whitelisted query and return ``(graph_viz, raw_result)``.

    Raises ``ValueError`` if the query name is not allowed.
    """
    if query_name not in ALLOWED_QUERIES:
        raise ValueError(f"Query not allowed: {query_name!r}")
    raw = run_installed_query(query_name, params)
    return build_graph_viz(query_name, raw), raw
