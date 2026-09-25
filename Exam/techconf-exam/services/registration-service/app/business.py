"""app/business.py — registration-service business rules (REQ-REG-*)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from errors import (  # noqa: E402
    ValidationError, NotFoundError, ConflictError,
    InvalidStatusTransitionError, ReferenceNotFoundError,
)
from app.models import new_registration, serialize_registration, utcnow_iso
from app.repository import RegistrationRepository
from app import clients


# Custom error codes
class AlreadyRegisteredError(ConflictError):
    code = "ALREADY_REGISTERED"

class EventFullError(ConflictError):
    code = "EVENT_FULL"

class EventNotOpenError(ValidationError):
    code = "EVENT_NOT_OPEN"


def create_registration(repo: RegistrationRepository, data: dict) -> dict:
    """REQ-REG-01, REQ-REG-B01..B06."""
    # Strip read-only fields (REQ-REG-01 #4)
    data = {k: v for k, v in data.items() if k not in ("id", "created_at", "updated_at", "amount", "status")}

    user_id = data.get("user_id")
    event_id = data.get("event_id")

    if not user_id or not event_id:
        raise ValidationError("'user_id' and 'event_id' are required")

    # REQ-REG-B01: user must exist
    clients.get_user(user_id)

    # REQ-REG-B02: event must exist
    event = clients.get_event(event_id)

    # REQ-REG-B03: event must be published
    if event.get("status") != "published":
        raise EventNotOpenError("Event is not open for registration")

    # REQ-REG-B04: no duplicate confirmed registration
    if repo.find_confirmed(user_id, event_id):
        raise AlreadyRegisteredError("User already registered for this event")

    # REQ-REG-B05: capacity check
    capacity = event.get("capacity", 0)
    confirmed = repo.count_confirmed(event_id)
    if confirmed >= capacity:
        raise EventFullError("Event is full")

    # REQ-REG-B06: amount = event.price
    amount = event.get("price", 0)
    reg = new_registration(user_id, event_id, amount)
    return serialize_registration(repo.create(reg))


def get_registration(repo: RegistrationRepository, reg_id: str) -> dict:
    reg = repo.get(reg_id)
    if not reg:
        raise NotFoundError("Registration not found")
    return serialize_registration(reg)


def list_registrations(repo: RegistrationRepository, filters: dict) -> list[dict]:
    regs = repo.list_all()

    if "user_id" in filters:
        regs = [r for r in regs if r["user_id"] == filters["user_id"]]
    if "event_id" in filters:
        regs = [r for r in regs if r["event_id"] == filters["event_id"]]
    if "status" in filters:
        status = filters["status"]
        from app.models import VALID_STATUSES
        if status not in VALID_STATUSES:
            raise ValidationError(f"'status' must be one of: {', '.join(sorted(VALID_STATUSES))}")
        regs = [r for r in regs if r["status"] == status]

    return [serialize_registration(r) for r in regs]


def patch_registration(repo: RegistrationRepository, reg_id: str, data: dict) -> dict:
    """REQ-REG-B07: only confirmed→cancelled allowed."""
    reg = repo.get(reg_id)
    if not reg:
        raise NotFoundError("Registration not found")

    new_status = data.get("status")
    if not new_status:
        raise ValidationError("'status' is required")

    from app.models import VALID_STATUSES
    if new_status not in VALID_STATUSES:
        raise ValidationError(f"'status' must be one of: {', '.join(sorted(VALID_STATUSES))}")

    old_status = reg["status"]
    if old_status == "confirmed" and new_status == "cancelled":
        pass  # allowed
    else:
        raise InvalidStatusTransitionError(
            f"Transition '{old_status}' → '{new_status}' is not allowed"
        )

    updated = repo.update(reg_id, {"status": new_status, "updated_at": utcnow_iso()})
    return serialize_registration(updated)


def delete_registration(repo: RegistrationRepository, reg_id: str) -> None:
    if not repo.delete(reg_id):
        raise NotFoundError("Registration not found")


def get_stats(repo: RegistrationRepository, event_id: str) -> dict:
    """REQ-REG-B08: stats for an event.

    ReferenceNotFoundError (422) is re-mapped to NotFoundError (404) by the route.
    """
    event = clients.get_event(event_id)  # raises ReferenceNotFoundError or DependencyUnavailableError
    capacity = event.get("capacity", 0)
    confirmed = repo.count_confirmed(event_id)
    available = max(0, capacity - confirmed)
    return {
        "event_id": event_id,
        "capacity": capacity,
        "confirmed": confirmed,
        "available": available,
    }
