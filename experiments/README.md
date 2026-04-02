# Experiments

Material here is **not** required to run the Flask API or integrate a frontend. It is kept for graph-building, alternate queries, and local GDELT ingest.

| Path | Purpose |
|------|---------|
| `pipeline/` | GDELT download → parse → CSV export → TigerGraph load helpers. Run from repo root: `python experiments/pipeline/<script>.py` |
| `gsql/` | Extra TigerGraph query sources (not wired into the default API allowlist). Install manually if you need them. |
| `data/` | Default locations for raw GDELT files, zips, and generated batch snippets (see `experiments/data/README.md`). |

Defaults for these paths are set in `chintu.config` (`GDELT_RAW_DIR`, `GDELT_ZIPS_DIR`, `GENERATED_DATA_DIR`).
