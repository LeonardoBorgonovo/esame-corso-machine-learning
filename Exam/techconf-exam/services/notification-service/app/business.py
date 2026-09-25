"""app/business.py — notification-service business rules (REQ-NTF-*)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from errors import ValidationError, NotFoundError, InvalidStatusTransitionError
from app.models import (new_notification, serialize_notification, utcnow_iso,
                         VALID_CHANNELS, VALID_STATUSES, ALLOWED_TRANSITIONS)
from app.repository import NotificationRepository
from app import clients


def _validate_notification(data: dict, partial: bool = False) -> None:
    if not partial:
        for f in ("user_id", "channel", "subject", "body"):
            if not data.get(f):
                raise ValidationError(f"'{f}' is required")

    if "channel" in data and data["channel"] not in VALID_CHANNELS:
        raise ValidationError(f"'channel' must be one of: {', '.join(sorted(VALID_CHANNELS))}")

    if "subject" in data:
        v = data["subject"]
        if not isinstance(v, str) or not (1 <= len(v) <= 150):
            raise ValidationError("'subject' must be 1–150 characters")

    if "body" in data:
        v = data["body"]
        if not isinstance(v, str) or not (1 <= len(v) <= 5000):
            raise ValidationError("'body' must be 1–5000 characters")


def create_notification(repo: NotificationRepository, data: dict) -> dict:
    """REQ-NTF-01, REQ-NTF-B01."""
    data = {k: v for k, v in data.items() if k not in ("id", "created_at", "updated_at", "sent_at", "status")}
    _validate_notification(data)
    # REQ-NTF-B01: user must exist
    clients.get_user(data["user_id"])
    n = new_notification(data["user_id"], data["channel"], data["subject"], data["body"])
    return serialize_notification(repo.create(n))


def get_notification(repo: NotificationRepository, nid: str) -> dict:
    n = repo.get(nid)
    if not n: raise NotFoundError("Notification not found")
    return serialize_notification(n)


def list_notifications(repo: NotificationRepository, filters: dict) -> list[dict]:
    ns = repo.list_all()
    if "user_id" in filters:
        ns = [n for n in ns if n["user_id"] == filters["user_id"]]
    if "status" in filters:
        s = filters["status"]
        if s not in VALID_STATUSES:
            raise ValidationError(f"'status' must be one of: {', '.join(sorted(VALID_STATUSES))}")
        ns = [n for n in ns if n["status"] == s]
    return [serialize_notification(n) for n in ns]


def patch_notification(repo: NotificationRepository, nid: str, data: dict) -> dict:
    """REQ-NTF-B02: status transitions."""
    n = repo.get(nid)
    if not n: raise NotFoundError("Notification not found")
    new_status = data.get("status")
    if not new_status: raise ValidationError("'status' is required")
    if new_status not in VALID_STATUSES:
        raise ValidationError(f"'status' must be one of: {', '.join(sorted(VALID_STATUSES))}")
    old_status = n["status"]
    if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
        raise InvalidStatusTransitionError(f"Transition '{old_status}' → '{new_status}' is not allowed")
    changes = {"status": new_status, "updated_at": utcnow_iso()}
    if new_status == "sent":
        changes["sent_at"] = utcnow_iso()
    updated = repo.update(nid, changes)
    return serialize_notification(updated)


def delete_notification(repo: NotificationRepository, nid: str) -> None:
    if not repo.delete(nid): raise NotFoundError("Notification not found")


def broadcast(repo: NotificationRepository, data: dict) -> dict:
    """REQ-NTF-B03: create one notification per confirmed registrant."""
    event_id = data.get("event_id")
    channel = data.get("channel")
    subject = data.get("subject")
    body = data.get("body")
    if not all([event_id, channel, subject, body]):
        raise ValidationError("'event_id', 'channel', 'subject', 'body' are required")
    _validate_notification({"channel": channel, "subject": subject, "body": body}, partial=True)

    registrations = clients.get_confirmed_registrations(event_id)
    created = 0
    for reg in registrations:
        uid = reg.get("user_id")
        if uid:
            n = new_notification(uid, channel, subject, body)
            repo.create(n)
            created += 1
    return {"event_id": event_id, "created": created}
