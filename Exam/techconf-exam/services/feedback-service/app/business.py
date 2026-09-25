"""app/business.py — feedback-service business rules (REQ-FBK-*)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from errors import ValidationError, NotFoundError, ConflictError
from app.models import new_feedback, serialize_feedback, utcnow_iso
from app.repository import FeedbackRepository
from app import clients


class FeedbackAlreadyExistsError(ConflictError):
    code = "FEEDBACK_ALREADY_EXISTS"


class NotRegisteredError(ValidationError):
    code = "NOT_REGISTERED"


def _validate_feedback(data: dict, partial: bool = False) -> None:
    if not partial:
        for f in ("user_id", "event_id", "rating"):
            if f not in data or data[f] is None:
                raise ValidationError(f"'{f}' is required")

    if "rating" in data:
        try:
            r = int(data["rating"])
        except (TypeError, ValueError):
            raise ValidationError("'rating' must be an integer 1–5")
        if not (1 <= r <= 5):
            raise ValidationError("'rating' must be between 1 and 5")

    if "comment" in data and data["comment"] is not None:
        if not isinstance(data["comment"], str) or len(data["comment"]) > 500:
            raise ValidationError("'comment' must be at most 500 characters")


def create_feedback(repo: FeedbackRepository, data: dict) -> dict:
    """REQ-FBK-01, REQ-FBK-B01, REQ-FBK-B02."""
    data = {k: v for k, v in data.items() if k not in ("id", "created_at", "updated_at")}
    _validate_feedback(data)

    user_id = data["user_id"]
    event_id = data["event_id"]

    # REQ-FBK-B01: must have confirmed registration
    if not clients.check_confirmed_registration(user_id, event_id):
        raise NotRegisteredError("User does not have a confirmed registration for this event")

    # REQ-FBK-B02: one feedback per (user_id, event_id)
    if repo.find_by_user_event(user_id, event_id):
        raise FeedbackAlreadyExistsError("Feedback already exists for this user/event")

    fb = new_feedback(user_id, event_id, int(data["rating"]), data.get("comment"))
    return serialize_feedback(repo.create(fb))


def get_feedback(repo: FeedbackRepository, fb_id: str) -> dict:
    fb = repo.get(fb_id)
    if not fb:
        raise NotFoundError("Feedback not found")
    return serialize_feedback(fb)


def list_feedbacks(repo: FeedbackRepository, filters: dict) -> list[dict]:
    fbs = repo.list_all()
    if "event_id" in filters:
        fbs = [f for f in fbs if f["event_id"] == filters["event_id"]]
    if "user_id" in filters:
        fbs = [f for f in fbs if f["user_id"] == filters["user_id"]]
    return [serialize_feedback(f) for f in fbs]


def patch_feedback(repo: FeedbackRepository, fb_id: str, data: dict) -> dict:
    fb = repo.get(fb_id)
    if not fb:
        raise NotFoundError("Feedback not found")
    data = {k: v for k, v in data.items() if k not in ("id", "created_at", "updated_at")}
    _validate_feedback(data, partial=True)
    changes = {**data, "updated_at": utcnow_iso()}
    if "rating" in changes:
        changes["rating"] = int(changes["rating"])
    updated = repo.update(fb_id, changes)
    return serialize_feedback(updated)


def delete_feedback(repo: FeedbackRepository, fb_id: str) -> None:
    if not repo.delete(fb_id):
        raise NotFoundError("Feedback not found")


def get_summary(repo: FeedbackRepository, event_id: str) -> dict:
    """REQ-FBK-B03."""
    # Verify event exists
    clients.get_event(event_id)  # raises ReferenceNotFoundError or DependencyUnavailableError
    fbs = [f for f in repo.list_all() if f["event_id"] == event_id]
    count = len(fbs)
    avg = round(sum(f["rating"] for f in fbs) / count, 2) if count > 0 else None
    return {"event_id": event_id, "count": count, "average_rating": avg}
