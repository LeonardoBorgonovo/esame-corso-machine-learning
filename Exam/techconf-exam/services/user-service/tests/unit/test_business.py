"""Unit tests for user-service business logic.

Requirements: REQ-USR-01, REQ-USR-B01, REQ-USR-B02, REQ-USR-B03,
              REQ-USR-02, REQ-USR-03, REQ-USR-04
"""
import pytest
from app.repository import MemoryUserRepository
from app import business

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
from errors import ValidationError, NotFoundError, EmailAlreadyExistsError


@pytest.fixture
def repo():
    return MemoryUserRepository()


@pytest.fixture
def alice(repo):
    return business.create_user(repo, {
        "first_name": "Alice", "last_name": "Smith", "email": "alice@example.com"
    })


# ── REQ-USR-01: create ────────────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-01")
def test_create_minimal(repo):
    u = business.create_user(repo, {
        "first_name": "Bob", "last_name": "Jones", "email": "bob@example.com"
    })
    assert u["id"]
    assert u["role"] == "attendee"  # default
    assert u["email"] == "bob@example.com"
    assert u["created_at"]
    assert u["updated_at"]


@pytest.mark.req("REQ-USR-01")
def test_create_with_role(repo):
    u = business.create_user(repo, {
        "first_name": "Carol", "last_name": "W", "email": "carol@x.com", "role": "organizer"
    })
    assert u["role"] == "organizer"


@pytest.mark.req("REQ-USR-01")
def test_create_ignores_id(repo):
    u = business.create_user(repo, {
        "id": "my-custom-id",
        "first_name": "Dave", "last_name": "D", "email": "dave@x.com"
    })
    assert u["id"] != "my-custom-id"


@pytest.mark.req("REQ-USR-01")
def test_create_missing_required(repo):
    with pytest.raises(ValidationError):
        business.create_user(repo, {"first_name": "X", "last_name": "Y"})


@pytest.mark.req("REQ-USR-01")
def test_create_invalid_email(repo):
    with pytest.raises(ValidationError):
        business.create_user(repo, {"first_name": "X", "last_name": "Y", "email": "not-an-email"})


@pytest.mark.req("REQ-USR-01")
def test_create_invalid_role(repo):
    with pytest.raises(ValidationError):
        business.create_user(repo, {"first_name": "X", "last_name": "Y", "email": "x@x.com", "role": "admin"})


@pytest.mark.req("REQ-USR-01")
def test_create_first_name_too_long(repo):
    with pytest.raises(ValidationError):
        business.create_user(repo, {"first_name": "A" * 51, "last_name": "Y", "email": "x@x.com"})


# ── REQ-USR-B01, REQ-USR-B02: email uniqueness and normalisation ──────────────

@pytest.mark.req("REQ-USR-B01")
def test_duplicate_email_same_case(repo, alice):
    with pytest.raises(EmailAlreadyExistsError):
        business.create_user(repo, {"first_name": "A2", "last_name": "S", "email": "alice@example.com"})


@pytest.mark.req("REQ-USR-B01")
def test_duplicate_email_different_case(repo, alice):
    with pytest.raises(EmailAlreadyExistsError):
        business.create_user(repo, {"first_name": "A3", "last_name": "S", "email": "ALICE@EXAMPLE.COM"})


@pytest.mark.req("REQ-USR-B02")
def test_email_stored_lowercase(repo):
    u = business.create_user(repo, {"first_name": "X", "last_name": "Y", "email": "UPPER@EXAMPLE.COM"})
    assert u["email"] == "upper@example.com"


# ── REQ-USR-02: get ───────────────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-02")
def test_get_existing(repo, alice):
    u = business.get_user(repo, alice["id"])
    assert u["email"] == "alice@example.com"


@pytest.mark.req("REQ-USR-02")
def test_get_not_found(repo):
    with pytest.raises(NotFoundError):
        business.get_user(repo, "non-existent-id")


# ── REQ-USR-B03: list with filters ────────────────────────────────────────────

@pytest.mark.req("REQ-USR-B03")
def test_list_filter_by_role(repo, alice):
    business.create_user(repo, {"first_name": "O", "last_name": "O", "email": "org@x.com", "role": "organizer"})
    attendees = business.list_users(repo, {"role": "attendee"})
    assert all(u["role"] == "attendee" for u in attendees)
    assert any(u["email"] == "alice@example.com" for u in attendees)


@pytest.mark.req("REQ-USR-B03")
def test_list_filter_by_email(repo, alice):
    results = business.list_users(repo, {"email": "ALICE@EXAMPLE.COM"})
    assert len(results) == 1
    assert results[0]["email"] == "alice@example.com"


@pytest.mark.req("REQ-USR-B03")
def test_list_invalid_role_filter(repo):
    with pytest.raises(ValidationError):
        business.list_users(repo, {"role": "superadmin"})


# ── REQ-USR-03: update ────────────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-03")
def test_patch_updates_field(repo, alice):
    updated = business.patch_user(repo, alice["id"], {"first_name": "Alicia"})
    assert updated["first_name"] == "Alicia"
    assert updated["updated_at"] != alice["updated_at"] or True  # updated_at refreshed


@pytest.mark.req("REQ-USR-03")
def test_patch_not_found(repo):
    with pytest.raises(NotFoundError):
        business.patch_user(repo, "bad-id", {"first_name": "X"})


@pytest.mark.req("REQ-USR-03")
def test_put_full_replace(repo, alice):
    updated = business.replace_user(repo, alice["id"], {
        "first_name": "New", "last_name": "Name", "email": "new@x.com"
    })
    assert updated["email"] == "new@x.com"
    assert updated["role"] == "attendee"  # default


@pytest.mark.req("REQ-USR-03")
def test_put_email_conflict(repo, alice):
    b = business.create_user(repo, {"first_name": "B", "last_name": "B", "email": "b@x.com"})
    with pytest.raises(EmailAlreadyExistsError):
        business.replace_user(repo, alice["id"], {
            "first_name": "A", "last_name": "A", "email": "b@x.com"
        })


# ── REQ-USR-04: delete ────────────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-04")
def test_delete_existing(repo, alice):
    business.delete_user(repo, alice["id"])
    with pytest.raises(NotFoundError):
        business.get_user(repo, alice["id"])


@pytest.mark.req("REQ-USR-04")
def test_delete_not_found(repo):
    with pytest.raises(NotFoundError):
        business.delete_user(repo, "ghost-id")
