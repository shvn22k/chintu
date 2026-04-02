"""
Download HTML and extract **main article text** using trafilatura.

Safety defaults:

- Only ``http`` / ``https`` URLs
- Response size cap (avoid huge downloads)
- Short timeout
- Plain text truncated before passing to an LLM
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
import trafilatura

DEFAULT_TIMEOUT_S = 12.0
DEFAULT_MAX_BYTES = 2_000_000
DEFAULT_MAX_CHARS = 6000
USER_AGENT = "CHINTU-Backend/0.1 (+https://github.com)"


@dataclass
class ArticleExcerpt:
    url: str
    title: str | None
    text: str
    ok: bool
    error: str | None = None


def _jina_reader_enabled() -> bool:
    """When not ``0``, retry failed HTML fetches via Jina Reader (``https://r.jina.ai/<url>``)."""
    return os.environ.get("CHINTU_JINA_READER", "1").strip() != "0"


def _fetch_via_jina_reader(
    url: str,
    *,
    timeout_s: float,
    max_bytes: int,
    max_chars: int,
) -> ArticleExcerpt | None:
    if not _jina_reader_enabled():
        return None
    ju = "https://r.jina.ai/" + url.strip()
    try:
        with httpx.Client(
            timeout=timeout_s,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            r = client.get(ju)
            r.raise_for_status()
            raw = r.content[:max_bytes]
    except Exception:
        return None
    text = raw.decode("utf-8", errors="replace").strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n…"
    if len(text) < 80:
        return None
    return ArticleExcerpt(url=url, title=None, text=text, ok=True, error=None)


def _allowed_url(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc)


def fetch_article_excerpt(
    url: str,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> ArticleExcerpt:
    """
    Fetch one URL and return extracted plain text (or error info).

    This is intentionally boring and defensive — not a full browser.
    """
    u = (url or "").strip()
    if not _allowed_url(u):
        return ArticleExcerpt(url=u, title=None, text="", ok=False, error="invalid_or_unsupported_url")

    try:
        with httpx.Client(
            timeout=timeout_s,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            with client.stream("GET", u) as resp:
                resp.raise_for_status()
                chunks: list[bytes] = []
                total = 0
                for chunk in resp.iter_bytes():
                    chunks.append(chunk)
                    total += len(chunk)
                    if total > max_bytes:
                        break
                raw = b"".join(chunks)
    except Exception as e:
        jina = _fetch_via_jina_reader(u, timeout_s=timeout_s, max_bytes=max_bytes, max_chars=max_chars)
        if jina:
            return ArticleExcerpt(url=jina.url, title=jina.title, text=jina.text, ok=True, error=None)
        return ArticleExcerpt(url=u, title=None, text="", ok=False, error=str(e)[:300])

    html = raw.decode("utf-8", errors="replace")
    extracted = trafilatura.extract(html, url=u, include_comments=False, include_tables=False)
    text = (extracted or "").strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n…"

    title_s: str | None = None
    try:
        from trafilatura.metadata import extract_metadata as _meta

        doc = _meta(html)
        if doc and getattr(doc, "title", None):
            title_s = str(doc.title).strip() or None
    except Exception:
        pass

    if not text:
        jina = _fetch_via_jina_reader(u, timeout_s=timeout_s, max_bytes=max_bytes, max_chars=max_chars)
        if jina:
            return ArticleExcerpt(
                url=jina.url,
                title=title_s or jina.title,
                text=jina.text,
                ok=True,
                error=None,
            )
        return ArticleExcerpt(url=u, title=title_s, text="", ok=False, error="no_extractable_text")

    return ArticleExcerpt(url=u, title=title_s, text=text, ok=True)


def fetch_many_excerpts(urls: list[str], *, per_url_limit: int = 3) -> list[ArticleExcerpt]:
    """Fetch up to ``per_url_limit`` URLs sequentially (simple and predictable)."""
    out: list[ArticleExcerpt] = []
    for u in urls[:per_url_limit]:
        out.append(fetch_article_excerpt(u))
    return out
