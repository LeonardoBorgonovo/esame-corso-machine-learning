"""app/routes.py — HTTP layer for event-service."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from flask import Blueprint, request, jsonify, current_app
from pagination import parse_pagination, paginate  # noqa: E402
from app import business

bp = Blueprint("events", __name__)


def _repo():
    return current_app.config["REPO"]


def _get_json():
    if not request.is_json:
        from flask import abort
        abort(400)
    data = request.get_json(silent=True)
    if data is None:
        from flask import abort
        abort(400)
    return data


@bp.route("/api/v1/events", methods=["POST"])
def create_event():
    data = _get_json()
    event = business.create_event(_repo(), data)
    resp = jsonify(event)
    resp.status_code = 201
    resp.headers["Location"] = f"/api/v1/events/{event['id']}"
    return resp


@bp.route("/api/v1/events", methods=["GET"])
def list_events():
    page, page_size = parse_pagination(request.args)
    filters = {}
    if "status" in request.args:
        filters["status"] = request.args["status"]
    if "city" in request.args:
        filters["city"] = request.args["city"]
    events = business.list_events(_repo(), filters)
    return jsonify(paginate(events, page, page_size)), 200


@bp.route("/api/v1/events/<event_id>", methods=["GET"])
def get_event(event_id: str):
    event = business.get_event(_repo(), event_id)
    return jsonify(event), 200


@bp.route("/api/v1/events/<event_id>", methods=["PUT"])
def replace_event(event_id: str):
    data = _get_json()
    event = business.replace_event(_repo(), event_id, data)
    return jsonify(event), 200


@bp.route("/api/v1/events/<event_id>", methods=["PATCH"])
def patch_event(event_id: str):
    data = _get_json()
    event = business.patch_event(_repo(), event_id, data)
    return jsonify(event), 200


@bp.route("/api/v1/events/<event_id>", methods=["DELETE"])
def delete_event(event_id: str):
    business.delete_event(_repo(), event_id)
    return "", 204
