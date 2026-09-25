"""app/business.py — user-service business rules (REQ-USR-*).

No Flask imports here. Receives/returns plain dicts.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone

from app.models import new_user, serialize_user, utcnow_iso, VALID_ROLES
from app.repository import UserRepository

# REQ-USR-B01, REQ-USR-B02 (email rules)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ── Import shared errors via sys.path (shared/ is on PYTHONPATH) ──────────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from errors import (  # noqa: E402
    ValidationError,
    NotFoundError,
    EmailAlreadyExistsError,
)


def _validate_user_fields(data: dict, partial: bool = False) -> None:
    """Validate user input. Raises ValidationError on any violation."""
    if not partial:
        for field in ("first_name", "last_name", "email"):
            if not data.get(field):
                raise ValidationError(f"'{field}' is required")

    if "first_name" in data:
        v = data["first_name"]
        if not isinstance(v, str) or not (1 <= len(v) <= 50):
            raise ValidationError("'first_name' must be 1–50 characters")

    if "last_name" in data:
        v = data["last_name"]
        if not isinstance(v, str) or not (1 <= len(v) <= 50):
            raise ValidationError("'last_name' must be 1–50 characters")

    if "email" in data:
        v = data["email"]
        if not isinstance(v, str) or not EMAIL_RE.match(v):
            raise ValidationError("'email' must be a valid email address")

    if "company" in data and data["company"] is not None:
        v = data["company"]
        if not isinstance(v, str) or len(v) > 100:
            raise ValidationError("'company' must be at most 100 characters")

    if "role" in data:
        if data["role"] not in VALID_ROLES:
            raise ValidationError(f"'role' must be one of: {', '.join(sorted(VALID_ROLES))}")


# ── CRUD operations ───────────────────────────────────────────────────────────

def create_user(repo: UserRepository, data: dict) -> dict:
    """REQ-USR-01, REQ-USR-B01, REQ-USR-B02."""
    # Strip read-only fields silently (REQ-USR-01 #5)
    data = {k: v for k, v in data.items() if k not in ("id", "created_at", "updated_at")}
    _validate_user_fields(data, partial=False)

    # REQ-USR-B01 — email uniqueness (case-insensitive)
    email_lower = data["email"].lower()
    if repo.find_by_email(email_lower):
        raise EmailAlreadyExistsError("Email already exists")

    user = new_user({**data, "email": email_lower})
    return serialize_user(repo.create(user))


def get_user(repo: UserRepository, user_id: str) -> dict:
    """REQ-USR-02."""
    user = repo.get(user_id)
    if not user:
        raise NotFoundError("User not found")
    return serialize_user(user)


def list_users(repo: UserRepository, filters: dict) -> list[dict]:
    """REQ-USR-B03 — filter by role and/or email."""
    users = repo.list_all()

    role_filter = filters.get("role")
    if role_filter:
        if role_filter not in VALID_ROLES:
            raise ValidationError(f"'role' must be one of: {', '.join(sorted(VALID_ROLES))}")
        users = [u for u in users if u["role"] == role_filter]

    email_filter = filters.get("email")
    if email_filter:
        email_lower = email_filter.lower()
        users = [u for u in users if u["email"] == email_lower]

    return [serialize_user(u) for u in users]


def replace_user(repo: UserRepository, user_id: str, data: dict) -> dict:
    """REQ-USR-03 — PUT (full replace)."""
    data = {k: v for k, v in data.items() if k not in ("id", "created_at", "updated_at")}
    _validate_user_fields(data, partial=False)

    existing = repo.get(user_id)
    if not existing:
        raise NotFoundError("User not found")

    email_lower = data["email"].lower()
    conflict = repo.find_by_email(email_lower, exclude_id=user_id)
    if conflict:
        raise EmailAlreadyExistsError("Email already exists")

    changes = {
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": email_lower,
        "company": data.get("company"),
        "role": data.get("role", "attendee"),
        "updated_at": utcnow_iso(),
    }
    updated = repo.update(user_id, changes)
    return serialize_user(updated)


def patch_user(repo: UserRepository, user_id: str, data: dict) -> dict:
    """REQ-USR-03 — PATCH (partial update)."""
    data = {k: v for k, v in data.items() if k not in ("id", "created_at", "updated_at")}
    _validate_user_fields(data, partial=True)

    existing = repo.get(user_id)
    if not existing:
        raise NotFoundError("User not found")

    if "email" in data:
        email_lower = data["email"].lower()
        conflict = repo.find_by_email(email_lower, exclude_id=user_id)
        if conflict:
            raise EmailAlreadyExistsError("Email already exists")
        data["email"] = email_lower

    changes = {**data, "updated_at": utcnow_iso()}
    updated = repo.update(user_id, changes)
    return serialize_user(updated)


def delete_user(repo: UserRepository, user_id: str) -> None:
    """REQ-USR-04."""
    if not repo.delete(user_id):
        raise NotFoundError("User not found")
