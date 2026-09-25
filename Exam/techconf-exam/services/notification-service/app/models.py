"""app/models.py — Notification resource schema."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

VALID_CHANNELS = {"email", "sms", "push"}
VALID_STATUSES = {"queued", "sent", "failed"}
ALLOWED_TRANSITIONS = {"queued": {"sent", "failed"}, "sent": set(), "failed": set()}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_notification(user_id, channel, subject, body) -> dict:
    now = utcnow_iso()
    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "channel": channel,
        "subject": subject,
        "body": body,
        "status": "queued",
        "sent_at": None,
        "created_at": now,
        "updated_at": now,
    }


def serialize_notification(n: dict) -> dict:
    return {
        "id": n["id"],
        "user_id": n["user_id"],
        "channel": n["channel"],
        "subject": n["subject"],
        "body": n["body"],
        "status": n["status"],
        "sent_at": n.get("sent_at"),
        "created_at": n["created_at"],
        "updated_at": n["updated_at"],
    }
