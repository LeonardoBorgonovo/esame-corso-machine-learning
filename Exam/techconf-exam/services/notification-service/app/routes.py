"""app/routes.py — HTTP layer for notification-service."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from flask import Blueprint, request, jsonify, current_app
from pagination import parse_pagination, paginate
from app import business

bp = Blueprint("notifications", __name__)


def _repo(): return current_app.config["REPO"]


def _get_json():
    if not request.is_json:
        from flask import abort; abort(400)
    d = request.get_json(silent=True)
    if d is None:
        from flask import abort; abort(400)
    return d


# broadcast before /<id>
@bp.route("/api/v1/notifications/broadcast", methods=["POST"])
def broadcast():
    data = _get_json()
    result = business.broadcast(_repo(), data)
    return jsonify(result), 201


@bp.route("/api/v1/notifications", methods=["POST"])
def create_notification():
    data = _get_json()
    n = business.create_notification(_repo(), data)
    resp = jsonify(n); resp.status_code = 201
    resp.headers["Location"] = f"/api/v1/notifications/{n['id']}"
    return resp


@bp.route("/api/v1/notifications", methods=["GET"])
def list_notifications():
    page, page_size = parse_pagination(request.args)
    filters = {}
    for f in ("user_id", "status"):
        if f in request.args: filters[f] = request.args[f]
    ns = business.list_notifications(_repo(), filters)
    return jsonify(paginate(ns, page, page_size)), 200


@bp.route("/api/v1/notifications/<nid>", methods=["GET"])
def get_notification(nid):
    return jsonify(business.get_notification(_repo(), nid)), 200


@bp.route("/api/v1/notifications/<nid>", methods=["PATCH"])
def patch_notification(nid):
    data = _get_json()
    return jsonify(business.patch_notification(_repo(), nid, data)), 200


@bp.route("/api/v1/notifications/<nid>", methods=["DELETE"])
def delete_notification(nid):
    business.delete_notification(_repo(), nid)
    return "", 204
