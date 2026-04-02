"""
Flask application factory for CHINTU.

Loads ``.env`` from the repository root once at startup.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask


def _load_dotenv() -> None:
    """``src/backend/app.py`` → repo root is three levels up."""
    here = Path(__file__).resolve()
    root = here.parents[2]
    # Default override=True so values in repo `.env` win over stale user/system env vars
    # (a common cause of persistent 401s after rotating OPENAI_API_KEY).
    _ov = os.environ.get("CHINTU_DOTENV_OVERRIDE", "1").strip().lower()
    _override = _ov not in ("0", "false", "no", "off")
    load_dotenv(root / ".env", override=_override)


def create_app(test_config: dict | None = None) -> Flask:
    """
    Create and configure the Flask app.

    ``test_config`` can override settings in unit tests (e.g. ``{"TESTING": True}``).
    """
    _load_dotenv()

    app = Flask(__name__)
    app.config.from_mapping(
        JSON_SORT_KEYS=False,
    )
    if test_config:
        app.config.update(test_config)

    if os.environ.get("CHINTU_CORS", "").strip().lower() in ("1", "true", "yes"):
        from flask_cors import CORS

        CORS(app)

    from backend.routes import api_bp

    app.register_blueprint(api_bp, url_prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "chintu-backend"}

    return app
