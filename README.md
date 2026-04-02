# CHINTU

Backend stack: **TigerGraph** (CHINTU graph) + **Flask API** for natural-language Q&A. A separate **GDELT → CSV → graph** pipeline lives under `experiments/` and is optional for API-only workflows.

## Layout

| Path | Purpose |
|------|---------|
| `src/chintu/` | Installable Python package (config, NLP, pipeline, TigerGraph helpers) |
| `src/backend/` | Flask HTTP API (`python -m backend` after `pip install -e ".[api]"`) |
| `tests/` | Pytest |
| `gsql/` | **Production** TigerGraph queries used by the API (`narrative_trace`, `event_text_search`, `causal_explosion_viz`) |
| `scripts/` | Small deploy helpers (e.g. install a `.gsql` query via REST) |
| `experiments/` | GDELT ingest, batch loaders, and **alternate** GSQL — not needed for frontend integration |
| `data/chintu/` | Sample graph CSV exports (dev / fixtures) |
| `docs/` | Schema notes (`CHINTU_SCHEMA.md`) |

Paths are centralized in `chintu.config`. Override with environment variables (see `.env.example`).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e ".[tigergraph]"   # optional: pyTigerGraph for batch GSQL loading
pip install -e ".[api]"          # Flask API + TigerGraph client + OpenAI + article extraction
```

Copy `.env.example` to `.env`. Set `TG_HOST`, `TG_SECRET`, and optionally `OPENAI_API_KEY` for the backend.

## HTTP API

```bash
python -m backend
```

See [`src/backend/README.md`](src/backend/README.md) for routes and the `chat/complete` JSON contract.

## GDELT pipeline (optional)

Run from the **repository root** so paths resolve:

```bash
python experiments/pipeline/data_download.py
python experiments/pipeline/extract_csv.py
python experiments/pipeline/parse.py
python experiments/pipeline/load_to_tigergraph.py
python experiments/pipeline/load_all_gsql_batches.py
```

Each script imports `experiments/pipeline/_bootstrap.py` first so `from chintu.config import …` works without setting `PYTHONPATH`.

## Security note

If this repository ever contained real TigerGraph credentials in source files, rotate the secret on the server side; `.env` is gitignored and should hold secrets locally.
