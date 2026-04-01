"""Repository paths. All tooling should use these instead of hard-coded strings."""

from __future__ import annotations

import os
from pathlib import Path

# Repository root (parent of src/)
ROOT: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = ROOT / "data"


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    if raw:
        return Path(raw).expanduser()
    return default


CHINTU_EXPORT_DIR: Path = _env_path("CHINTU_EXPORT_DIR", DATA_DIR / "chintu")
GDELT_RAW_DIR: Path = _env_path("GDELT_RAW_DIR", DATA_DIR / "gdelt_raw")
GDELT_ZIPS_DIR: Path = _env_path("GDELT_ZIPS_DIR", DATA_DIR / "gdelt_zips")
GSQL_DIR: Path = ROOT / "gsql"
DOCS_DIR: Path = ROOT / "docs"
GENERATED_DATA_DIR: Path = _env_path("GENERATED_DATA_DIR", DATA_DIR / "generated")
GSQL_LOAD_DIR: Path = GENERATED_DATA_DIR / "gsql_load"
GSQL_BATCHES_DIR: Path = GENERATED_DATA_DIR / "gsql_batches"
