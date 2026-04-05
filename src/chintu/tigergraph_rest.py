"""
TigerGraph **REST++** access via ``requests`` only.

Why this exists
---------------
``pyTigerGraph`` 2.x calls HTTP during ``TigerGraphConnection.__init__`` *before*
it builds internal auth header caches. Hostnames containing ``tgcloud`` trigger
that early request, which raises::

    'TigerGraphConnection' object has no attribute '_cached_token_auth'

This module matches the token flow used in ``experiments/pipeline/load_to_tigergraph.py`` and
avoids the buggy client initializer entirely.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

import requests

# Cloud HTTPS often uses TigerGraph-managed certs; match permissive loader behavior.
_VERIFY_TLS = os.environ.get("TG_VERIFY_SSL", "0").strip().lower() in ("1", "true", "yes")


def sanitize_tigergraph_error_text(text: str, max_len: int = 400) -> str:
    """
    Strip HTML and collapse whitespace so TigerGraph / proxy errors are readable in chat and JSON
    (Cloud sometimes returns HTML pages for 5xx).
    """
    if not text:
        return ""
    s = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", text)
    s = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", s)
    s = re.sub(r"(?is)<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_len:
        return s[: max_len - 1] + "…"
    return s


def user_hint_for_tigergraph_error(detail: str) -> str:
    """
    Accurate operator guidance. Many failures are a **stopped Cloud workspace** or **auth**,
    not a missing GSQL file—avoid blaming ``event_text_search`` for those.
    """
    low = (detail or "").lower()
    if "failed to start workspace" in low or "auto start is not enabled" in low:
        return (
            "TigerGraph Cloud says the **solution workspace is not running**. In the TigerGraph Cloud console, "
            "open this solution and click **Start**, or enable **auto-start** for it. Token and query calls fail "
            "until the workspace is up."
        )
    if "token request failed" in low or "all token strategies failed" in low:
        return (
            "Could not get a REST token. Confirm the workspace is **running**, then check **TG_HOST** and "
            "**TG_SECRET** in `.env` (use the solution secret from the portal, not an unrelated password)."
        )
    if "rest-1000" in low or "endpoint is not found" in low:
        return (
            "The server is reachable but a **named query** may be missing. Install **event_text_search** from "
            "`gsql/chintu_event_text_search.gsql` if you rely on natural-language event lookup (see `src/backend/README.md`)."
        )
    return (
        "Verify TigerGraph is **running**, **TG_HOST** / **TG_SECRET** are correct, and—if you do not paste an "
        "`evt_*` id—that **event_text_search** is installed. See `src/backend/README.md`."
    )


def _normalize_host(url: str) -> str:
    u = (url or "").strip().rstrip("/")
    if not u.startswith(("http://", "https://")):
        return "https://" + u
    return u


def _restpp_root() -> str:
    """``https://{instance}/restpp`` (no extra port for TigerGraph Cloud on 443)."""
    return _normalize_host(os.environ.get("TG_HOST", "")) + "/restpp"


def _graph_name() -> str:
    return os.environ.get("TG_GRAPHNAME", "CHINTU").strip()


def _basic_auth() -> tuple[str, str]:
    return (
        os.environ.get("TG_USERNAME", "").strip(),
        os.environ.get("TG_PASSWORD", "").strip(),
    )


def _secret() -> str:
    return os.environ.get("TG_SECRET", "").strip()


def _basic_auth_header(username: str, password: str) -> dict[str, str]:
    """``Authorization: Basic ...`` for TigerGraph REST."""
    raw = f"{username}:{password}".encode("utf-8")
    return {"Authorization": "Basic " + base64.b64encode(raw).decode("ascii")}


def _extract_token_from_response(data: Any) -> str | None:
    """Handle both legacy REST++ JSON and TigerGraph 4.x shapes."""
    if not isinstance(data, dict):
        return None
    if data.get("error") is True or str(data.get("error")).lower() == "true":
        return None
    inner = data.get("results", data)
    if isinstance(inner, dict):
        t = inner.get("token")
        if t:
            return str(t)
    t = data.get("token")
    return str(t) if t else None


def _post_json_token(
    url: str,
    body: dict,
    auth_headers: dict[str, str],
) -> tuple[int, str, Any]:
    """POST JSON; returns (status, text_snippet, parsed_json_or_none)."""
    h = {**auth_headers, "Content-Type": "application/json", "Accept": "application/json"}
    r = requests.post(url, headers=h, data=json.dumps(body), timeout=60, verify=_VERIFY_TLS)
    text = (r.text or "")[:800]
    try:
        return r.status_code, text, r.json()
    except json.JSONDecodeError:
        return r.status_code, text, None


@lru_cache(maxsize=1)
def _get_bearer_token() -> str:
    """
    Request a REST++ bearer token (cached per process).

    TigerGraph expects **secret-based** token requests to use HTTP Basic auth with
    username ``__GSQL__secret`` and password equal to the **secret string** (not your
    portal password). See pyTigerGraph's ``PyTigerGraphCore`` initializer.

    We then try, in order:

    1. ``POST .../gsql/v1/tokens`` (TigerGraph 4.x GSQL API on port 443)
    2. ``POST .../restpp/requesttoken`` with the same Basic auth (3.5+)
    3. ``POST .../restpp/requesttoken`` with **TG_USERNAME** / **TG_PASSWORD** (some Cloud setups)
    4. ``GET .../restpp/requesttoken?secret=...&graph=...`` for both auth styles
    """
    host_base = _normalize_host(os.environ.get("TG_HOST", ""))
    graph = _graph_name()
    secret = _secret()
    user, password = _basic_auth()
    if not host_base or not secret:
        raise RuntimeError("TG_HOST and TG_SECRET are required.")

    gsql_secret_headers = _basic_auth_header("__GSQL__secret", secret)
    body_full = {"secret": secret, "graph": graph}
    body_graph_only = {"graph": graph}
    body_secret_only = {"secret": secret}

    errors: list[str] = []

    def record(name: str, status: int, snippet: str) -> None:
        if status != 200 or "<html" in snippet.lower():
            errors.append(f"{name}: HTTP {status} {snippet[:200]}")

    # --- TigerGraph 4.x GSQL tokens (global secret often omits graph) ---
    url_gsql = f"{host_base}/gsql/v1/tokens"
    for label, body in (
        ("gsql/v1/tokens secret_only", body_secret_only),
        ("gsql/v1/tokens full", body_full),
        ("gsql/v1/tokens graph_only", body_graph_only),
    ):
        st, snip, data = _post_json_token(url_gsql, body, gsql_secret_headers)
        record(label, st, snip)
        if st == 200 and data is not None:
            tok = _extract_token_from_response(data)
            if tok:
                return tok

    # --- REST++ POST (TigerGraph 3.5+) ---
    url_rt = f"{host_base}/restpp/requesttoken"
    for label, body, hdrs in (
        ("restpp+gsql_basic+full", body_full, gsql_secret_headers),
        ("restpp+gsql_basic+secret_only", body_secret_only, gsql_secret_headers),
        ("restpp+gsql_basic+graph_only", body_graph_only, gsql_secret_headers),
    ):
        st, snip, data = _post_json_token(url_rt, body, hdrs)
        record(label, st, snip)
        if st == 200 and data is not None:
            tok = _extract_token_from_response(data)
            if tok:
                return tok

    if user and password:
        user_headers = _basic_auth_header(user, password)
        for label, body in (
            ("restpp+user_basic+full", body_full),
            ("restpp+user_basic+secret_only", body_secret_only),
        ):
            st, snip, data = _post_json_token(url_rt, body, user_headers)
            record(label, st, snip)
            if st == 200 and data is not None:
                tok = _extract_token_from_response(data)
                if tok:
                    return tok

    # --- GET (TigerGraph < 3.5) ---
    q = f"secret={quote(secret, safe='')}&graph={quote(graph, safe='')}"
    url_get = f"{host_base}/restpp/requesttoken?{q}"
    for label, hdrs in (
        ("GET+gsql_basic", gsql_secret_headers),
        ("GET+user_basic", _basic_auth_header(user, password) if user and password else None),
    ):
        if hdrs is None:
            continue
        gr = requests.get(url_get, headers={**hdrs, "Accept": "application/json"}, timeout=60, verify=_VERIFY_TLS)
        snip = (gr.text or "")[:800]
        record(label, gr.status_code, snip)
        if gr.status_code == 200:
            try:
                tok = _extract_token_from_response(gr.json())
            except json.JSONDecodeError:
                tok = None
            if tok:
                return tok

    detail_raw = "; ".join(errors) if errors else "all token strategies failed"
    detail = sanitize_tigergraph_error_text(detail_raw, 700)
    raise RuntimeError(
        "TigerGraph token request failed. Tried GSQL /gsql/v1/tokens and REST++ /restpp/requesttoken "
        f"with __GSQL__secret basic auth and (if set) TG_USERNAME. Detail: {detail}"
    )


def _auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_bearer_token()}",
        "Content-Type": "application/json",
    }


def clear_token_cache() -> None:
    """Call after integration tests change ``TG_*`` env vars."""
    _get_bearer_token.cache_clear()


def _parse_builtin_vertex_count(data: Any, vertex_type: str) -> int:
    """
    Parse ``stat_vertex_number`` JSON.

    TigerGraph REST++ often wraps the payload::

        {"error": false, "results": [{"v_type": "Topic", "count": 5}], ...}

    Older responses may be a bare list or a flat dict.
    """
    if isinstance(data, dict) and "results" in data:
        rows = data["results"]
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                if "count" not in row:
                    continue
                vt = row.get("v_type")
                if vt is None or vt == vertex_type:
                    return int(row["count"])
            if rows and isinstance(rows[0], dict) and "count" in rows[0]:
                return int(rows[0]["count"])
    if isinstance(data, list) and data:
        row = data[0]
        if isinstance(row, dict) and "count" in row:
            return int(row["count"])
    if isinstance(data, dict) and "count" in data and "results" not in data:
        return int(data["count"])
    raise RuntimeError(f"unexpected count response: {data!r}"[:500])


def vertex_type_count(vertex_type: str) -> int:
    """Vertex count for one type via ``/builtins`` ``stat_vertex_number``."""
    root = _restpp_root()
    graph = _graph_name()
    url = f"{root}/builtins/{graph}"
    body = {"function": "stat_vertex_number", "type": vertex_type}
    r = requests.post(
        url,
        json=body,
        headers=_auth_headers(),
        timeout=120,
        verify=_VERIFY_TLS,
    )
    if r.status_code != 200:
        raise RuntimeError(f"vertex count failed: {r.status_code} {r.text[:800]}")
    return _parse_builtin_vertex_count(r.json(), vertex_type)


def ping_graph() -> dict[str, Any]:
    """REST-based health: token + per-type vertex counts."""
    out: dict[str, Any] = {"ok": True, "graph": _graph_name()}
    try:
        _get_bearer_token()
    except Exception as e:
        return {"ok": False, "graph": _graph_name(), "error": str(e)[:800]}
    for vt in ("Topic", "Entity", "Event"):
        try:
            out[f"{vt.lower()}_count"] = vertex_type_count(vt)
        except Exception as e:
            out["ok"] = False
            out["error"] = str(e)[:800]
            break
    return out


def run_installed_query(query_name: str, params: dict[str, Any] | None = None) -> Any:
    """
    Run an installed query via REST++ GET.

    Query parameters are passed as URL query string (TigerGraph REST convention).
    """
    params = params or {}
    root = _restpp_root()
    graph = _graph_name()
    # All parameter values must be strings in the URL.
    q = urlencode({k: str(v) for k, v in params.items()})
    url = f"{root}/query/{graph}/{query_name}"
    if q:
        url = f"{url}?{q}"
    r = requests.get(url, headers=_auth_headers(), timeout=300, verify=_VERIFY_TLS)
    if r.status_code != 200:
        raise RuntimeError(f"query {query_name!r} failed: {r.status_code} {r.text[:1200]}")
    return r.json()


def _gsql_http_base() -> str:
    """TigerGraph GSQL v1 API lives on the instance root (not under ``/restpp``)."""
    return _normalize_host(os.environ.get("TG_HOST", "")).rstrip("/")


def _gsql_bearer_get_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_bearer_token()}",
        "Accept": "application/json",
    }


def gsql_v1_delete_query(query_name: str) -> Any:
    """
    Drop one query definition via ``DELETE /gsql/v1/queries``.

    Ignores HTTP errors when the query did not exist (best-effort refresh).
    """
    graph = quote(_graph_name(), safe="")
    qn = quote(query_name, safe="")
    url = f"{_gsql_http_base()}/gsql/v1/queries?query={qn}&graph={graph}"
    r = requests.delete(url, headers=_auth_headers(), timeout=120, verify=_VERIFY_TLS)
    if r.status_code == 404:
        return {"error": False, "message": "not found", "dropped": []}
    if r.status_code != 200:
        return {"error": True, "http_status": r.status_code, "text": (r.text or "")[:800]}
    try:
        return r.json()
    except json.JSONDecodeError:
        return {"error": False, "raw": (r.text or "")[:500]}


def gsql_v1_post_query_definition(gsql_text: str) -> Any:
    """Create or replace query source via ``POST /gsql/v1/queries`` (body = GSQL text)."""
    graph = quote(_graph_name(), safe="")
    url = f"{_gsql_http_base()}/gsql/v1/queries?graph={graph}"
    hdr = {
        "Authorization": f"Bearer {_get_bearer_token()}",
        "Content-Type": "text/plain; charset=utf-8",
        "Accept": "application/json",
    }
    r = requests.post(
        url,
        data=gsql_text.encode("utf-8"),
        headers=hdr,
        timeout=300,
        verify=_VERIFY_TLS,
    )
    if r.status_code != 200:
        raise RuntimeError(f"gsql POST /queries failed: {r.status_code} {r.text[:2000]}")
    try:
        out = r.json()
    except json.JSONDecodeError as e:
        raise RuntimeError(f"gsql POST returned non-JSON: {r.text[:800]}") from e
    if out.get("error") is True or str(out.get("error")).lower() == "true":
        raise RuntimeError(f"gsql POST error: {out}")
    return out


def _gsql_v1_poll_install(request_id: str, *, timeout_s: float = 600.0, interval_s: float = 2.0) -> dict[str, Any]:
    rid = str(request_id).strip().strip('"').strip("'")
    base = _gsql_http_base()
    url = f"{base}/gsql/v1/queries/install/{quote(rid, safe='')}"
    deadline = time.monotonic() + timeout_s
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        r = requests.get(url, headers=_gsql_bearer_get_headers(), timeout=120, verify=_VERIFY_TLS)
        if r.status_code != 200:
            raise RuntimeError(f"install status HTTP {r.status_code}: {r.text[:1200]}")
        try:
            last = r.json()
        except json.JSONDecodeError:
            raise RuntimeError(f"install status non-JSON: {r.text[:800]}")
        if last.get("error") is True or str(last.get("error")).lower() == "true":
            raise RuntimeError(f"query install failed: {last}")
        msg = str(last.get("message") or "").lower()
        if "fail" in msg and "running" not in msg:
            raise RuntimeError(f"query install failed: {last}")
        if "finished" in msg and "success" in msg:
            return last
        time.sleep(interval_s)
    raise TimeoutError(f"query install timed out after {timeout_s}s; last={last!r}")


def gsql_v1_install_query(query_name: str, *, timeout_s: float = 600.0) -> dict[str, Any]:
    """
    Compile/install one query: ``GET /gsql/v1/queries/install`` then poll status.

    Uses the same bearer token as REST++ (``TG_SECRET`` / ``__GSQL__secret`` flow).
    """
    graph = quote(_graph_name(), safe="")
    qn = quote(query_name, safe="")
    url = f"{_gsql_http_base()}/gsql/v1/queries/install?graph={graph}&queries={qn}&flag=-force"
    r = requests.get(url, headers=_gsql_bearer_get_headers(), timeout=120, verify=_VERIFY_TLS)
    if r.status_code != 200:
        raise RuntimeError(f"gsql install submit failed: {r.status_code} {r.text[:2000]}")
    data = r.json()
    if data.get("error") is True or str(data.get("error")).lower() == "true":
        raise RuntimeError(f"gsql install submit error: {data}")
    rid = data.get("requestId") or data.get("requestid")
    if not rid:
        return data
    return _gsql_v1_poll_install(str(rid), timeout_s=timeout_s)


def install_query_from_gsql_file(path: str | Path, *, skip_drop: bool = False) -> dict[str, Any]:
    """
    High-level: optional DROP, POST ``CREATE QUERY`` from file, INSTALL.

    Same credentials as the Flask API / ``run_installed_query`` (no pyTigerGraph).
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    m = re.search(r"CREATE\s+QUERY\s+(\w+)\s*\(", text, re.IGNORECASE)
    if not m:
        raise ValueError("Could not find CREATE QUERY name in file")
    qn = m.group(1)
    graph = _graph_name()
    out: dict[str, Any] = {"query": qn, "graph": graph}
    if not skip_drop:
        out["drop"] = gsql_v1_delete_query(qn)
    out["create"] = gsql_v1_post_query_definition(text.strip() + "\n")
    out["install"] = gsql_v1_install_query(qn)
    return out
