# Pipeline data (local only)

Large or regenerated files belong here, not under `data/chintu/` (committed graph CSV samples).

- `gdelt_raw/` — unzipped GDELT `.export.CSV` files from `experiments/pipeline/data_download.py`
- `gdelt_zips/` — downloaded archives (optional)
- `generated/` — batch GSQL snippets, `entity_batches.json`, etc.

These directories are mostly **gitignored**; recreate them by running the pipeline scripts.
