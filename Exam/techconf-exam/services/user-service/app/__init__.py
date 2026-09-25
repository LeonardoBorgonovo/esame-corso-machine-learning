"""app/__init__.py — Flask app factory for user-service."""
from __future__ import annotations
import sys, os

# Ensure shared/ is importable (handles both direct run and test invocation)
_SHARED = os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared")
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

from flask import Flask, jsonify
from errors import AppError  # noqa: E402 (shared)
from config import get_storage_backend, get_data_dir  # noqa: E402 (shared)
from app.repository import make_repository  # noqa: E402


def create_app(backend: str | None = None, data_dir: str | None = None) -> Flask:
    app = Flask(__name__)

    _backend = backend or get_storage_backend()
    _data_dir = data_dir or get_data_dir()
    app.config["REPO"] = make_repository(_backend, _data_dir)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "user-service"}), 200

    # ── Blueprints ────────────────────────────────────────────────────────────
    from app.routes import bp
    app.register_blueprint(bp)

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        return exc.to_response()

    @app.errorhandler(400)
    def handle_400(_):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Malformed JSON"}}), 400

    @app.errorhandler(404)
    def handle_404(_):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Not found"}}), 404

    @app.errorhandler(405)
    def handle_405(_):
        return jsonify({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed"}}), 405

    return app
