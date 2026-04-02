"""
TigerGraph helpers for the CHINTU backend and tools.

Uses **REST++ via ``requests``** (see :mod:`chintu.tigergraph_rest`) so TigerGraph Cloud
hostnames work reliably. The ``pyTigerGraph`` library is **not** used here because
version 2.x can fail during ``TigerGraphConnection.__init__`` on ``*.tgcloud.io`` hosts
(HTTP is sent before internal auth caches exist).

Scripts such as ``load_all_gsql_batches.py`` may still use ``pyTigerGraph`` for GSQL;
that is separate from this module.
"""

from __future__ import annotations

from typing import Any

from chintu.tigergraph_rest import (
    clear_token_cache,
    install_query_from_gsql_file,
    ping_graph,
    run_installed_query,
)

__all__ = [
    "ping_graph",
    "run_installed_query",
    "clear_connection_cache",
    "install_query_from_gsql_file",
]


def clear_connection_cache() -> None:
    """Drop cached REST token (e.g. after tests change ``TG_*``)."""
    clear_token_cache()
