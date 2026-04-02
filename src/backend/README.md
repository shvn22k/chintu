# CHINTU Flask API

## Setup

From the repository root:

```bash
pip install -e ".[api]"
```

Copy `.env.example` to `.env` and fill in at least:

- **TigerGraph:** `TG_HOST`, `TG_SECRET` (and usually `TG_USERNAME`, `TG_PASSWORD`)
- **LLM (optional but recommended):** `OPENAI_API_KEY`
- **Project keys (`sk-proj-...`):** also set `OPENAI_PROJECT` (`proj_...`) and, if your dashboard shows one, `OPENAI_ORGANIZATION` (`org_...`). The OpenAI API expects these as `OpenAI-Project` / `OpenAI-Organization` headers; the Python client sends them when those env vars are set.

## Run (development)

```bash
python -m backend
```

Or:

```bash
flask --app backend.app:create_app run --debug
```

Default URL: `http://127.0.0.1:5000`

Set `CHINTU_CORS=1` in `.env` if a separate frontend origin needs CORS.

## Frontend integration (API contract)

Use this section as the **source of truth** for UI work. There is **no separate OpenAPI file** yet; all routes are under **`/api/v1`** except **`GET /health`**.

| Concern | Detail |
|--------|--------|
| **Auth** | No per-request API keys on these routes today. The Flask app reads TigerGraph + OpenAI secrets from **server** `.env` only — do **not** expose those keys in the browser. |
| **CORS** | Cross-origin browsers need `CHINTU_CORS=1` on the server (or a reverse proxy adding CORS headers). |
| **Streaming** | Not supported. One JSON object per request/response. |
| **Content-Type** | Send `Content-Type: application/json` on every POST body. |

### `POST /api/v1/chat/complete` — response envelope

**HTTP status:** almost always **`200`**. Failures are indicated by the optional **`error`** string; the UI should still read **`answer`**, **`graph_viz`**, and **`meta`** (they are always present).

| Field | Type | Meaning |
|-------|------|--------|
| `version` | string | Stable envelope version (currently `"1"`). |
| `answer` | string | User-facing text (Markdown). **Only this field is free-form LLM prose**; the rest is structured. |
| `graph_viz` | object | `{ "nodes": [...], "edges": [...] }` for force-directed / graph UIs. |
| `sources` | object | `{ "articles": [...], "graph_query": object \| null }` — provenance for citations / debug. |
| `meta` | object | Routing + resolution metadata (intent, keywords, optional `event_resolution`). |
| `error` | string \| omitted | Soft failure code; see table below. |

**`error` values (non-exhaustive; treat unknown values gracefully):**

| `error` | When |
|---------|------|
| `empty_question` | Body missing/empty `question`. |
| `no_query_plan` | Could not map the question to a graph query (vague question, no `evt_*`, search missed, or `event_text_search` failed). |
| `tigergraph_error` | Installed graph query threw or REST error (bad id, query not installed, etc.). |

### `graph_viz` node and edge shape

Nodes and edges are normalized for visualization libraries (e.g. Cytoscape.js, react-force-graph).

**Node** (event):

```json
{
  "id": "evt_…",
  "label": "Short title",
  "type": "Event",
  "attributes": { }
}
```

`attributes` may include graph fields such as `source_url`, `timestamp`, `location`, `description`, etc., depending on what TigerGraph returned.

**Edge** (influence):

```json
{
  "source": "evt_from",
  "target": "evt_to",
  "type": "INFLUENCES",
  "attributes": { "strength": "…", "lag_days": "…", "polarity": "…", "influence_type": "…" }
}
```

`event_text_search` returns **nodes only** (candidate events), **edges: []**.

### `sources`

- **`articles`:** array of `{ "url", "title", "excerpt", "ok", "error" }` — URLs taken from graph nodes, fetched server-side; `ok: false` means fetch/extract failed.
- **`graph_query`:** `{ "name": "<query>", "params": { ... } }` or `null` when no query ran.

### `meta` and `event_resolution`

`meta` always includes at least:

- `intent` — `"causal_explore"` \| `"narrative_trace"` \| `"unknown"`
- `keywords` — string array
- `reasoning` — short model/heuristic note (may be empty)

When the backend searched for an `evt_*` from natural language, **`meta.event_resolution`** may include:

- `source` — how the id was chosen (e.g. `user_or_heuristic_id`, `search_unique`, `search_llm_pick`)
- `needles_tried` — search strings used against `event_text_search`
- `candidate_count`, `candidates_preview` — top matches for **pick-one** UIs (`event_id`, `title`, `timestamp`, `location`, `source_url`)
- `picked_event_id`, `confidence`, `low_confidence` — when multiple candidates existed
- `search_error`, `llm_pick_error` — when something failed (strings truncated)

### Other routes (summary)

- **`POST /api/v1/nlp/parse`** — `200` JSON: `question`, `intent` (full object with `max_hops`, `top_k`, needles), `query_plan` or `null`, optional `event_resolution`. No graph run, no `answer`.
- **`POST /api/v1/graph/query`** — `200` `{ "graph_viz", "raw" }`; **`400`** invalid body or disallowed `query`; **`502`** TigerGraph error. Whitelisted `query` names: `causal_explosion_viz`, `narrative_trace`, `event_text_search`.
- **`GET /api/v1/health/graph`**, **`GET /api/v1/health/openai`** — `200` / **`503`** for status dashboards.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Process up |
| GET | `/api/v1/health/graph` | TigerGraph ping + vertex counts |
| GET | `/api/v1/health/openai` | OpenAI key check (`models.list`); hints on 401 (no secrets in JSON) |
| POST | `/api/v1/chat/complete` | Full pipeline: question → graph → articles → LLM |
| POST | `/api/v1/nlp/parse` | Intent + query plan only (debug) |
| POST | `/api/v1/graph/query` | Run one whitelisted installed query (debug) |

### `POST /api/v1/chat/complete`

Body:

```json
{"question": "What happened after evt_abc123?"}
```

Response: stable JSON envelope — field names, node/edge shapes, `error` semantics, and `meta.event_resolution` are documented in **[Frontend integration (API contract)](#frontend-integration-api-contract)** above.

## Testing in Postman

1. Start the server: `python -m backend` (listens on **http://127.0.0.1:5000**).
2. In Postman, create an environment variable **`base_url`** = `http://127.0.0.1:5000` (or paste the full URL in each request).

**For every POST request below:** tab **Body** → **raw** → type **JSON**. In the **Headers** tab, ensure **`Content-Type`** is **`application/json`** (Postman often sets this automatically when you pick raw JSON).

### 1. Process health (GET)

- **Method:** GET  
- **URL:** `{{base_url}}/health`  
- **Body:** none  

Expect `200` and JSON like `{"status":"ok","service":"chintu-backend"}`.

### 2. TigerGraph health (GET)

- **Method:** GET  
- **URL:** `{{base_url}}/api/v1/health/graph`  
- **Body:** none  

Expect `200` with `ok: true` and vertex counts if `.env` TigerGraph settings are valid; `503` if the graph is unreachable.

The backend talks to TigerGraph over **REST++** (`requests`), not `pyTigerGraph`’s `TigerGraphConnection`, because pyTigerGraph 2.x can crash during `__init__` on `*.tgcloud.io` hosts (it sends an HTTP ping before internal auth headers are built).

**Natural language → `evt_*`:** The API calls the installed query **`event_text_search`**. If TigerGraph returns **`REST-1000` / `Endpoint is not found`** for `/query/CHINTU/event_text_search`, that query was never **installed** on your cluster (copying the `.gsql` file into the repo is not enough).

#### Installing `event_text_search` (TigerGraph Cloud / Studio)

1. Open **TigerGraph Studio** for your solution → select graph **CHINTU** (same name as `TG_GRAPHNAME` in `.env`).
2. **Write queries** → **Create query** (or open GSQL editor).
3. Paste the full contents of repo file **`gsql/chintu_event_text_search.gsql`**.
4. Click **Install** (or **Save** then **Install**). Wait until the install finishes without errors.

#### Installing via GSQL shell (alternative)

```text
USE GRAPH CHINTU
DROP QUERY event_text_search   // omit if first install; ignore error if query did not exist
```

Then run the entire `CREATE QUERY event_text_search ...` from `gsql/chintu_event_text_search.gsql`, and:

```text
INSTALL QUERY event_text_search
```

#### Verify

After install, this pattern should exist on REST++ (exact host/port from `TG_HOST` / `TG_RESTPP_PORT`):  
`GET .../restpp/query/CHINTU/event_text_search?needle=test&max_results=5`  
(with your usual TigerGraph auth). Or call **`POST /api/v1/graph/query`** with `"query": "event_text_search"` and `"params": {"needle": "iran", "max_results": 5}` — expect `200` and nodes in `graph_viz`, not `502`.

Until **`event_text_search`** is installed, you can still test the rest of the pipeline by **including an `evt_...` id** in the question (resolution skips search and calls `narrative_trace` / `causal_explosion_viz` only).

**`narrative_trace` update (seed node):** If you installed CHINTU before this change, reinstall **`gsql/chintu_narrative_trace.gsql`**. Older versions only returned predecessor events, so when there were **no incoming INFLUENCES** the API showed **zero nodes** even though the seed id was valid. The current query also **PRINT**s the focal **seed** event. Until you reinstall, the Python API still **injects a minimal focal node** from search metadata when the graph response is empty.

**Install from the repo (REST, same as the API):** With `.env` containing **`TG_HOST`** + **`TG_SECRET`** (and optional user/pass if your cloud tier needs them), run from the repo root:

```bash
python scripts/install_chintu_query.py gsql/chintu_narrative_trace.gsql
python scripts/install_chintu_query.py gsql/chintu_event_text_search.gsql
```

This uses TigerGraph’s **GSQL v1 HTTP API** (`POST /gsql/v1/queries`, install endpoint) and the same bearer token as **`run_installed_query`** — no pyTigerGraph.

**TigerGraph MCP in Cursor:** If tools like `tigergraph__install_query` return **`REST-10016`** (*input token is empty*), the MCP server process does not have a valid **API token / password** in its environment. Fix the MCP server config (variables are defined in that MCP’s README; often **`TG_API_TOKEN`** or mirroring **`TG_PASSWORD`** + **`TG_USERNAME`**). The MCP is separate from the Flask app’s `.env` unless you wire the same vars into the MCP block in Cursor settings.

### 3. Full chat pipeline (POST)

- **Method:** POST  
- **URL:** `{{base_url}}/api/v1/chat/complete`  
- **Body (raw JSON):**

```json
{
  "question": "What were the downstream effects of evt_YOUR_EVENT_ID?"
}
```

You can paste a real `evt_...` id **or** describe the event in plain language (place, leader, incident). The response `meta.event_resolution` shows needles tried, match count, and confidence when resolution ran.  
Expect `200` with `answer`, `graph_viz`, `sources`, `meta`. You get `error: "no_query_plan"` when the question is off-topic, too vague, or **`event_text_search`** is not installed / failed.

### 4. NLP parse only — no TigerGraph run (POST)

- **Method:** POST  
- **URL:** `{{base_url}}/api/v1/nlp/parse`  
- **Body (raw JSON):**

```json
{
  "question": "Why did evt_YOUR_EVENT_ID happen?"
}
```

Expect `200` with `intent`, `query_plan` (or `null` if routing failed).

### 5. Direct graph query — debug (POST)

- **Method:** POST  
- **URL:** `{{base_url}}/api/v1/graph/query`  
- **Body (raw JSON)** — `query` must be one of `causal_explosion_viz`, `narrative_trace`, or `event_text_search`:

```json
{
  "query": "causal_explosion_viz",
  "params": {
    "event_id": "evt_YOUR_EVENT_ID",
    "max_hops": 3,
    "top_k": 50
  }
}
```

For backward / “why” style exploration, use `"query": "narrative_trace"` with the same `params` shape.

Substring search (candidate events, no edges):

```json
{
  "query": "event_text_search",
  "params": {
    "needle": "brazil flood",
    "max_results": 25
  }
}
```

Expect `200` with `graph_viz` and `raw` (TigerGraph’s native structure). `502` means TigerGraph returned an error (wrong id, query not installed, etc.).

### Postman collection (optional)

Create a new Collection **CHINTU API**, add the five requests above, and set the collection or folder variable `base_url` so you can switch between `localhost` and a deployed host later.
