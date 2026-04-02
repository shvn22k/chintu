"""Bootstrap ``sys.path`` when running files under ``scripts/`` (e.g. ``install_chintu_query.py``)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
