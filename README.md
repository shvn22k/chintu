# CHINTU

Experimental pipeline: GDELT → graph-shaped CSVs → TigerGraph (CHINTU graph). This layout is structured for a future HTTP backend under `backend/`.

## Layout

| Path | Purpose |
|------|---------|
| `src/chintu/` | Installable Python package (`config`, shared code for scripts and API) |
| `scripts/` | CLI: download, extract, parse, load |
| `gsql/` | TigerGraph query definitions (`.gsql`) |
| `data/chintu/` | Exported graph CSVs (vertices/edges) |
| `data/gdelt_raw/` | Unzipped GDELT `.CSV` files |
| `data/gdelt_zips/` | Downloaded GDELT zip archives |
| `data/generated/` | Generated artifacts (e.g. batched GSQL snippets) |
| `docs/` | Schema and design notes (`CHINTU_SCHEMA.md`) |
| `backend/` | Placeholder for the future API |

Paths are centralized in `chintu.config`. Override with environment variables (see `.env.example`).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e ".[tigergraph]"   # optional: pyTigerGraph for batch GSQL loading
```

Copy `.env.example` to `.env` and set `TG_HOST`, `TG_SECRET`, and related variables before running loaders that talk to TigerGraph.

## Running scripts

Run from the **repository root** so paths resolve correctly:

```bash
python scripts/data_download.py
python scripts/extract_csv.py
python scripts/parse.py
python scripts/load_to_tigergraph.py
python scripts/load_all_gsql_batches.py
```

Each script imports `scripts/_repo.py` first so `from chintu.config import …` works without manually setting `PYTHONPATH`.

## Security note

If this repository ever contained real TigerGraph credentials in source files, rotate the secret on the server side; `.env` is gitignored and should hold secrets locally.
