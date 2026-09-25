"""app/models.py — User resource schema and serialisation helpers."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

VALID_ROLES = {"attendee", "speaker", "organizer"}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_user(data: dict) -> dict:
    """Build a new user dict from validated input data."""
    now = utcnow_iso()
    return {
        "id": str(uuid.uuid4()),
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": data["email"].lower(),
        "company": data.get("company"),
        "role": data.get("role", "attendee"),
        "created_at": now,
        "updated_at": now,
    }


def serialize_user(user: dict) -> dict:
    """Return a JSON-serialisable representation of a user."""
    return {
        "id": user["id"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
        "company": user.get("company"),
        "role": user["role"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }
