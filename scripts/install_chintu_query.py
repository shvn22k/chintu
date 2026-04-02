"""
Install or refresh a single CHINTU packaged query on TigerGraph via **REST** (GSQL v1 API).

Uses the same ``TG_HOST`` + ``TG_SECRET`` token flow as the Flask backend — **no pyTigerGraph**
(so ``*.tgcloud.io`` works).

Use this when the Cursor TigerGraph MCP returns **REST-10016** (empty API token): configure
``TG_API_TOKEN`` / password on the MCP server, **or** run this script with your ``.env``.

From repo root::

  python scripts/install_chintu_query.py gsql/chintu_narrative_trace.gsql
  python scripts/install_chintu_query.py gsql/chintu_event_text_search.gsql
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import _repo  # noqa: F401

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env", override=True)

from chintu.tigergraph_rest import install_query_from_gsql_file


def main() -> None:
    ap = argparse.ArgumentParser(description="Install one CHINTU .gsql query via TigerGraph REST GSQL v1 API.")
    ap.add_argument(
        "gsql_file",
        type=Path,
        help="Path to .gsql file (e.g. gsql/chintu_narrative_trace.gsql)",
    )
    ap.add_argument(
        "--no-drop",
        action="store_true",
        help="Skip DROP QUERY (first install on empty graph).",
    )
    args = ap.parse_args()
    path = args.gsql_file if args.gsql_file.is_absolute() else _ROOT / args.gsql_file
    if not path.is_file():
        sys.exit(f"File not found: {path}")
    try:
        out = install_query_from_gsql_file(path, skip_drop=args.no_drop)
    except Exception as e:
        sys.exit(f"Install failed: {e!s}")
    print(json.dumps(out, indent=2, default=str))
    print("Done.")


if __name__ == "__main__":
    main()
