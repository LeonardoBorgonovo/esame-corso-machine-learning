"""app/routes.py — HTTP layer for feedback-service."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from flask import Blueprint, request, jsonify, current_app
from pagination import parse_pagination, paginate
from errors import ReferenceNotFoundError, NotFoundError
from app import business

bp = Blueprint("feedbacks", __name__)


def _repo(): return current_app.config["REPO"]


def _get_json():
    if not request.is_json:
        from flask import abort; abort(400)
    d = request.get_json(silent=True)
    if d is None:
        from flask import abort; abort(400)
    return d


# summary before /<id> to avoid routing conflict
@bp.route("/api/v1/feedbacks/summary", methods=["GET"])
def summary():
    event_id = request.args.get("event_id")
    if not event_id:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "'event_id' is required"}}), 422
    try:
        result = business.get_summary(_repo(), event_id)
    except ReferenceNotFoundError:
        raise NotFoundError("Event not found")
    return jsonify(result), 200


@bp.route("/api/v1/feedbacks", methods=["POST"])
def create_feedback():
    data = _get_json()
    fb = business.create_feedback(_repo(), data)
    resp = jsonify(fb); resp.status_code = 201
    resp.headers["Location"] = f"/api/v1/feedbacks/{fb['id']}"
    return resp


@bp.route("/api/v1/feedbacks", methods=["GET"])
def list_feedbacks():
    page, page_size = parse_pagination(request.args)
    filters = {}
    for f in ("event_id", "user_id"):
        if f in request.args: filters[f] = request.args[f]
    fbs = business.list_feedbacks(_repo(), filters)
    return jsonify(paginate(fbs, page, page_size)), 200


@bp.route("/api/v1/feedbacks/<fb_id>", methods=["GET"])
def get_feedback(fb_id):
    return jsonify(business.get_feedback(_repo(), fb_id)), 200


@bp.route("/api/v1/feedbacks/<fb_id>", methods=["PATCH"])
def patch_feedback(fb_id):
    data = _get_json()
    return jsonify(business.patch_feedback(_repo(), fb_id, data)), 200


@bp.route("/api/v1/feedbacks/<fb_id>", methods=["DELETE"])
def delete_feedback(fb_id):
    business.delete_feedback(_repo(), fb_id)
    return "", 204
