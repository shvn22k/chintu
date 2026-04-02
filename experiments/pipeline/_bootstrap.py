"""Add ``src/`` to ``sys.path`` when running pipeline scripts from this directory."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_src = REPO_ROOT / "src"
_s = str(_src)
if _s not in sys.path:
    sys.path.insert(0, _s)
