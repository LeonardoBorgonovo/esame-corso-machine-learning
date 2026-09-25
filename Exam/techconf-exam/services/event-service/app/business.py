"""app/business.py — event-service business rules (REQ-EVT-*).

No Flask imports. Receives/returns plain dicts.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from errors import ValidationError, NotFoundError, InvalidStatusTransitionError, ReferenceNotFoundError  # noqa: E402
from app.models import new_event, serialize_event, utcnow_iso, VALID_STATUSES, ALLOWED_TRANSITIONS
from app.repository import EventRepository
from app import clients


def _validate_event_fields(data: dict, partial: bool = False) -> None:
    if not partial:
        for field in ("title", "organizer_id", "venue", "city", "start_date", "end_date", "capacity", "price"):
            if field not in data or data[field] is None:
                raise ValidationError(f"'{field}' is required")

    if "title" in data:
        v = data["title"]
        if not isinstance(v, str) or not (3 <= len(v) <= 120):
            raise ValidationError("'title' must be 3–120 characters")

    if "description" in data and data["description"] is not None:
        if not isinstance(data["description"], str) or len(data["description"]) > 2000:
            raise ValidationError("'description' must be at most 2000 characters")

    if "venue" in data:
        v = data["venue"]
        if not isinstance(v, str) or len(v) > 100:
            raise ValidationError("'venue' must be at most 100 characters")

    if "city" in data:
        v = data["city"]
        if not isinstance(v, str) or len(v) > 60:
            raise ValidationError("'city' must be at most 60 characters")

    if "capacity" in data:
        try:
            cap = int(data["capacity"])
        except (ValueError, TypeError):
            raise ValidationError("'capacity' must be an integer 1–10000")
        if not (1 <= cap <= 10000):
            raise ValidationError("'capacity' must be between 1 and 10000")

    if "price" in data:
        try:
            price = float(data["price"])
        except (ValueError, TypeError):
            raise ValidationError("'price' must be a non-negative number")
        if price < 0:
            raise ValidationError("'price' must be >= 0")

    if "status" in data and data["status"] is not None:
        if data["status"] not in VALID_STATUSES:
            raise ValidationError(f"'status' must be one of: {', '.join(sorted(VALID_STATUSES))}")

    # REQ-EVT-B03: date coherence (only when both present)
    start = data.get("start_date")
    end = data.get("end_date")
    if start and end and end < start:
        raise ValidationError("'end_date' must be >= 'start_date'")


class InvalidOrganizerError(ValidationError):
    code = "INVALID_ORGANIZER"


def _validate_organizer(organizer_id: str) -> None:
    """REQ-EVT-B01, REQ-EVT-B02: check organizer exists and has role=organizer."""
    user = clients.get_user(organizer_id)  # raises ReferenceNotFoundError or DependencyUnavailableError
    if user.get("role") != "organizer":
        raise InvalidOrganizerError("User is not an organizer")


def create_event(repo: EventRepository, data: dict) -> dict:
    """REQ-EVT-01, REQ-EVT-B01..B05."""
    data = {k: v for k, v in data.items() if k not in ("id", "created_at", "updated_at")}
    _validate_event_fields(data, partial=False)
    _validate_organizer(data["organizer_id"])
    event = new_event(data)
    return serialize_event(repo.create(event))


def get_event(repo: EventRepository, event_id: str) -> dict:
    event = repo.get(event_id)
    if not event:
        raise NotFoundError("Event not found")
    return serialize_event(event)


def list_events(repo: EventRepository, filters: dict) -> list[dict]:
    """REQ-EVT-B06."""
    events = repo.list_all()

    status_filter = filters.get("status")
    if status_filter:
        if status_filter not in VALID_STATUSES:
            raise ValidationError(f"'status' must be one of: {', '.join(sorted(VALID_STATUSES))}")
        events = [e for e in events if e["status"] == status_filter]

    city_filter = filters.get("city")
    if city_filter:
        city_lower = city_filter.lower()
        events = [e for e in events if e["city"].lower() == city_lower]

    return [serialize_event(e) for e in events]


def replace_event(repo: EventRepository, event_id: str, data: dict) -> dict:
    """PUT — full replace. REQ-EVT-03."""
    data = {k: v for k, v in data.items() if k not in ("id", "created_at", "updated_at")}
    existing = repo.get(event_id)
    if not existing:
        raise NotFoundError("Event not found")

    _validate_event_fields(data, partial=False)

    # Check status transition if status changes
    new_status = data.get("status", "draft")
    old_status = existing["status"]
    if new_status != old_status:
        _check_transition(old_status, new_status)

    if "organizer_id" in data:
        _validate_organizer(data["organizer_id"])

    changes = {
        "title": data["title"],
        "description": data.get("description"),
        "organizer_id": data["organizer_id"],
        "venue": data["venue"],
        "city": data["city"],
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "capacity": int(data["capacity"]),
        "price": float(data["price"]),
        "status": new_status,
        "updated_at": utcnow_iso(),
    }
    updated = repo.update(event_id, changes)
    return serialize_event(updated)


def patch_event(repo: EventRepository, event_id: str, data: dict) -> dict:
    """PATCH — partial update. REQ-EVT-03."""
    data = {k: v for k, v in data.items() if k not in ("id", "created_at", "updated_at")}
    existing = repo.get(event_id)
    if not existing:
        raise NotFoundError("Event not found")

    _validate_event_fields(data, partial=True)

    # REQ-EVT-B04: status transition check
    if "status" in data:
        _check_transition(existing["status"], data["status"])

    # REQ-EVT-B01/B02: validate organizer if changed
    if "organizer_id" in data:
        _validate_organizer(data["organizer_id"])

    # If partial dates provided, check coherence against stored values
    start = data.get("start_date", existing["start_date"])
    end = data.get("end_date", existing["end_date"])
    if end < start:
        raise ValidationError("'end_date' must be >= 'start_date'")

    changes = {**data, "updated_at": utcnow_iso()}
    if "capacity" in changes:
        changes["capacity"] = int(changes["capacity"])
    if "price" in changes:
        changes["price"] = float(changes["price"])
    updated = repo.update(event_id, changes)
    return serialize_event(updated)


def delete_event(repo: EventRepository, event_id: str) -> None:
    if not repo.delete(event_id):
        raise NotFoundError("Event not found")


def _check_transition(old: str, new: str) -> None:
    """REQ-EVT-B04: raise InvalidStatusTransitionError if transition not allowed."""
    if new not in ALLOWED_TRANSITIONS.get(old, set()):
        raise InvalidStatusTransitionError(
            f"Transition '{old}' → '{new}' is not allowed"
        )
