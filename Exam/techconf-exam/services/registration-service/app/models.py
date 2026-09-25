"""app/models.py — Registration resource schema."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

VALID_STATUSES = {"confirmed", "cancelled"}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_registration(user_id: str, event_id: str, amount: float) -> dict:
    now = utcnow_iso()
    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "event_id": event_id,
        "amount": round(float(amount), 2),
        "status": "confirmed",
        "created_at": now,
        "updated_at": now,
    }


def serialize_registration(reg: dict) -> dict:
    return {
        "id": reg["id"],
        "user_id": reg["user_id"],
        "event_id": reg["event_id"],
        "amount": reg["amount"],
        "status": reg["status"],
        "created_at": reg["created_at"],
        "updated_at": reg["updated_at"],
    }
