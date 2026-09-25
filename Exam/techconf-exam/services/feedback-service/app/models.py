"""app/models.py — Feedback resource schema."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_feedback(user_id: str, event_id: str, rating: int, comment: str | None) -> dict:
    now = utcnow_iso()
    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "event_id": event_id,
        "rating": rating,
        "comment": comment,
        "created_at": now,
        "updated_at": now,
    }


def serialize_feedback(fb: dict) -> dict:
    return {
        "id": fb["id"],
        "user_id": fb["user_id"],
        "event_id": fb["event_id"],
        "rating": fb["rating"],
        "comment": fb.get("comment"),
        "created_at": fb["created_at"],
        "updated_at": fb["updated_at"],
    }
