"""app/routes.py — HTTP layer for registration-service."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from flask import Blueprint, request, jsonify, current_app
from pagination import parse_pagination, paginate
from errors import ReferenceNotFoundError, NotFoundError
from app import business

bp = Blueprint("registrations", __name__)


def _repo():
    return current_app.config["REPO"]


def _get_json():
    if not request.is_json:
        from flask import abort; abort(400)
    data = request.get_json(silent=True)
    if data is None:
        from flask import abort; abort(400)
    return data


# ── stats (must be before /<id> to avoid routing conflict) ───────────────────
@bp.route("/api/v1/registrations/stats", methods=["GET"])
def stats():
    event_id = request.args.get("event_id")
    if not event_id:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "'event_id' is required"}}), 422

    # Remap ReferenceNotFoundError → 404 for stats endpoint (REQ-REG-B08)
    try:
        result = business.get_stats(_repo(), event_id)
    except ReferenceNotFoundError:
        raise NotFoundError("Event not found")

    return jsonify(result), 200


# ── POST /api/v1/registrations ────────────────────────────────────────────────
@bp.route("/api/v1/registrations", methods=["POST"])
def create_registration():
    data = _get_json()
    reg = business.create_registration(_repo(), data)
    resp = jsonify(reg)
    resp.status_code = 201
    resp.headers["Location"] = f"/api/v1/registrations/{reg['id']}"
    return resp


# ── GET /api/v1/registrations ─────────────────────────────────────────────────
@bp.route("/api/v1/registrations", methods=["GET"])
def list_registrations():
    page, page_size = parse_pagination(request.args)
    filters = {}
    for f in ("user_id", "event_id", "status"):
        if f in request.args:
            filters[f] = request.args[f]
    regs = business.list_registrations(_repo(), filters)
    return jsonify(paginate(regs, page, page_size)), 200


# ── GET /api/v1/registrations/<id> ───────────────────────────────────────────
@bp.route("/api/v1/registrations/<reg_id>", methods=["GET"])
def get_registration(reg_id: str):
    reg = business.get_registration(_repo(), reg_id)
    return jsonify(reg), 200


# ── PUT /api/v1/registrations/<id> — 405 not allowed ────────────────────────
@bp.route("/api/v1/registrations/<reg_id>", methods=["PUT"])
def put_not_allowed(reg_id: str):
    return jsonify({"error": {"code": "METHOD_NOT_ALLOWED", "message": "PUT is not allowed"}}), 405


# ── PATCH /api/v1/registrations/<id> ─────────────────────────────────────────
@bp.route("/api/v1/registrations/<reg_id>", methods=["PATCH"])
def patch_registration(reg_id: str):
    data = _get_json()
    reg = business.patch_registration(_repo(), reg_id, data)
    return jsonify(reg), 200


# ── DELETE /api/v1/registrations/<id> ────────────────────────────────────────
@bp.route("/api/v1/registrations/<reg_id>", methods=["DELETE"])
def delete_registration(reg_id: str):
    business.delete_registration(_repo(), reg_id)
    return "", 204
