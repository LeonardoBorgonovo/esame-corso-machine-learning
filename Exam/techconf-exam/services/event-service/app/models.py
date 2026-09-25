"""app/models.py — Event resource schema."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

VALID_STATUSES = {"draft", "published", "cancelled"}

# Allowed status transitions: current → set of allowed next
ALLOWED_TRANSITIONS = {
    "draft": {"published", "cancelled"},
    "published": {"cancelled"},
    "cancelled": set(),
}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_event(data: dict) -> dict:
    now = utcnow_iso()
    return {
        "id": str(uuid.uuid4()),
        "title": data["title"],
        "description": data.get("description"),
        "organizer_id": data["organizer_id"],
        "venue": data["venue"],
        "city": data["city"],
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "capacity": int(data["capacity"]),
        "price": float(data["price"]),
        "status": data.get("status", "draft"),
        "created_at": now,
        "updated_at": now,
    }


def serialize_event(event: dict) -> dict:
    return {
        "id": event["id"],
        "title": event["title"],
        "description": event.get("description"),
        "organizer_id": event["organizer_id"],
        "venue": event["venue"],
        "city": event["city"],
        "start_date": event["start_date"],
        "end_date": event["end_date"],
        "capacity": event["capacity"],
        "price": event["price"],
        "status": event["status"],
        "created_at": event["created_at"],
        "updated_at": event["updated_at"],
    }
