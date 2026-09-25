"""app/routes.py — HTTP layer for user-service.

Parses requests, delegates to business.py, maps domain exceptions to HTTP.
Contains no business logic.
"""
from __future__ import annotations
from flask import Blueprint, request, jsonify, current_app

from app import business
from app.models import serialize_user

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from errors import AppError, ValidationError  # noqa: E402
from pagination import parse_pagination, paginate  # noqa: E402

bp = Blueprint("users", __name__)


def _repo():
    return current_app.config["REPO"]


# ── POST /api/v1/users ────────────────────────────────────────────────────────
@bp.route("/api/v1/users", methods=["POST"])
def create_user():
    data = _get_json()
    user = business.create_user(_repo(), data)
    resp = jsonify(user)
    resp.status_code = 201
    resp.headers["Location"] = f"/api/v1/users/{user['id']}"
    return resp


# ── GET /api/v1/users ─────────────────────────────────────────────────────────
@bp.route("/api/v1/users", methods=["GET"])
def list_users():
    page, page_size = parse_pagination(request.args)
    filters = {}
    if "role" in request.args:
        filters["role"] = request.args["role"]
    if "email" in request.args:
        filters["email"] = request.args["email"]
    users = business.list_users(_repo(), filters)
    return jsonify(paginate(users, page, page_size)), 200


# ── GET /api/v1/users/<id> ────────────────────────────────────────────────────
@bp.route("/api/v1/users/<user_id>", methods=["GET"])
def get_user(user_id: str):
    user = business.get_user(_repo(), user_id)
    return jsonify(user), 200


# ── PUT /api/v1/users/<id> ────────────────────────────────────────────────────
@bp.route("/api/v1/users/<user_id>", methods=["PUT"])
def replace_user(user_id: str):
    data = _get_json()
    user = business.replace_user(_repo(), user_id, data)
    return jsonify(user), 200


# ── PATCH /api/v1/users/<id> ─────────────────────────────────────────────────
@bp.route("/api/v1/users/<user_id>", methods=["PATCH"])
def patch_user(user_id: str):
    data = _get_json()
    user = business.patch_user(_repo(), user_id, data)
    return jsonify(user), 200


# ── DELETE /api/v1/users/<id> ────────────────────────────────────────────────
@bp.route("/api/v1/users/<user_id>", methods=["DELETE"])
def delete_user(user_id: str):
    business.delete_user(_repo(), user_id)
    return "", 204


# ── Helper ────────────────────────────────────────────────────────────────────
def _get_json() -> dict:
    """Parse JSON body; raise 400 if malformed."""
    if not request.is_json:
        from flask import abort
        abort(400)
    data = request.get_json(silent=True)
    if data is None:
        from flask import abort
        abort(400)
    return data
