"""app/__init__.py — Flask app factory for feedback-service."""
from __future__ import annotations
import sys, os

_SHARED = os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared")
if _SHARED not in sys.path: sys.path.insert(0, _SHARED)

from flask import Flask, jsonify
from errors import AppError
from config import get_storage_backend, get_data_dir
from app.repository import make_repository


def create_app(backend=None, data_dir=None):
    app = Flask(__name__)
    app.config["REPO"] = make_repository(backend or get_storage_backend(), data_dir or get_data_dir())

    @app.get("/health")
    def health(): return jsonify({"status": "ok", "service": "feedback-service"}), 200

    from app.routes import bp
    app.register_blueprint(bp)

    @app.errorhandler(AppError)
    def handle_app_error(exc): return exc.to_response()

    @app.errorhandler(400)
    def handle_400(_): return jsonify({"error": {"code": "BAD_REQUEST", "message": "Malformed JSON"}}), 400

    @app.errorhandler(404)
    def handle_404(_): return jsonify({"error": {"code": "NOT_FOUND", "message": "Not found"}}), 404

    @app.errorhandler(405)
    def handle_405(_): return jsonify({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed"}}), 405

    return app
