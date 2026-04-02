"""
Thin wrapper around the OpenAI **Chat Completions** API.

Environment:

- ``OPENAI_API_KEY`` — required for LLM features (any valid key shape, including ``sk-proj-...``)
- ``OPENAI_BASE_URL`` — optional; default ``https://api.openai.com/v1``
- ``OPENAI_MODEL`` — optional; default ``gpt-4o-mini``
- ``OPENAI_ORGANIZATION`` — optional; OpenAI org id (``org_...``). Sent as ``OpenAI-Organization``.
- ``OPENAI_PROJECT`` — optional but **recommended for project API keys** (``sk-proj-...``). Sent as
  ``OpenAI-Project`` (see OpenAI authentication docs; the Python SDK maps these to the same headers).

Project keys are not a different protocol than ``sk-...`` keys: they still use ``Authorization: Bearer``.
If you see 401 ``invalid_api_key`` with a new ``sk-proj-`` key, set ``OPENAI_PROJECT`` (and org if needed)
to match the key’s scope in the OpenAI dashboard.
"""

from __future__ import annotations

import json
import os
from typing import Any

_client = None
_client_env_fingerprint: str | None = None


def _strip_api_key(raw: str) -> str:
    """Trim whitespace, BOM, newlines, and one pair of surrounding quotes."""
    s = (raw or "").strip().lstrip("\ufeff")
    s = s.replace("\r", "").replace("\n", "").strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    return s


def _normalize_base_url(url: str) -> str:
    """Avoid double ``/v1`` if the base already includes it."""
    u = (url or "").strip().rstrip("/")
    if not u:
        return "https://api.openai.com/v1"
    return u


def _client_fingerprint() -> str:
    """Rebuild OpenAI client when any of these change (e.g. after editing ``.env`` + restart)."""
    return "|".join(
        [
            _strip_api_key(os.environ.get("OPENAI_API_KEY", "")),
            _normalize_base_url(os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")),
            _optional_env("OPENAI_ORGANIZATION") or "",
            _optional_env("OPENAI_PROJECT") or "",
        ]
    )


def _optional_env(name: str) -> str | None:
    v = os.environ.get(name, "").strip()
    return v if v else None


def _get_client():
    global _client, _client_env_fingerprint
    fp = _client_fingerprint()
    if _client is not None and fp == _client_env_fingerprint:
        return _client

    key = _strip_api_key(os.environ.get("OPENAI_API_KEY", ""))
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")
    from openai import OpenAI

    base = _normalize_base_url(os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    kwargs: dict[str, Any] = {"api_key": key, "base_url": base}
    org = _optional_env("OPENAI_ORGANIZATION")
    proj = _optional_env("OPENAI_PROJECT")
    if org is not None:
        kwargs["organization"] = org
    if proj is not None:
        kwargs["project"] = proj

    _client = OpenAI(**kwargs)
    _client_env_fingerprint = fp
    return _client


def reset_client() -> None:
    """Drop cached client (e.g. after tests change env vars)."""
    global _client, _client_env_fingerprint
    _client = None
    _client_env_fingerprint = None


def openai_healthcheck() -> dict[str, Any]:
    """
    Diagnostic for Postman: confirms env + a real ``models.list`` call (no key material returned).
    """
    key = _strip_api_key(os.environ.get("OPENAI_API_KEY", ""))
    org = _optional_env("OPENAI_ORGANIZATION")
    proj = _optional_env("OPENAI_PROJECT")
    base = _normalize_base_url(os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    out: dict[str, Any] = {
        "api_key_configured": bool(key),
        "key_shape": "sk-proj"
        if key.startswith("sk-proj")
        else ("sk-" if key.startswith("sk-") else ("set" if key else "missing")),
        "key_length": len(key),
        "organization_set": org is not None,
        "project_set": proj is not None,
        "base_url": base,
    }
    if not key:
        out["ok"] = False
        out["error"] = "OPENAI_API_KEY missing or empty after sanitization"
        return out

    reset_client()
    try:
        c = _get_client()
        # Lightweight authenticated call
        c.models.list()
        out["ok"] = True
        out["message"] = "OpenAI API accepted the key (models.list ok)."
        return out
    except Exception as e:
        err = str(e)
        out["ok"] = False
        out["error"] = err[:800]
        low = err.lower()
        if "401" in err or "invalid_api_key" in low or "incorrect api key" in low:
            out["hints"] = [
                "Confirm no old OPENAI_API_KEY in Windows/macOS User or System environment variables "
                "(they override .env unless CHINTU_DOTENV_OVERRIDE=1 — now the default).",
                "Restart the Flask process after changing .env.",
                "If OPENAI_PROJECT / OPENAI_ORGANIZATION are set, verify they match the key's project in "
                "platform.openai.com; if unsure, comment both lines out and retry.",
                "Paste the key again with no spaces or line breaks; file should be UTF-8.",
            ]
        return out


def _model_name() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"


def chat_completion_json(
    *,
    system: str,
    user: str,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """
    Ask the model for a **single JSON object** (parsed).

    Uses ``response_format`` JSON mode when the SDK supports it.
    """
    client = _get_client()
    resp = client.chat.completions.create(
        model=_model_name(),
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    text = (resp.choices[0].message.content or "").strip()
    return json.loads(text)


def chat_completion_text(
    *,
    system: str,
    user: str,
    temperature: float = 0.4,
    max_tokens: int = 1200,
) -> str:
    """Plain-text assistant reply."""
    client = _get_client()
    resp = client.chat.completions.create(
        model=_model_name(),
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()
