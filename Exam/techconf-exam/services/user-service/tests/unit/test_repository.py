"""Unit tests for UserRepository — all three backends.

Requirements: REQ-USR-07
"""
import pytest
from app.models import new_user

SAMPLE = {
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice@example.com",
    "role": "attendee",
}


def _run_crud(repo):
    """Common CRUD test suite run against any backend."""
    user = repo.create(new_user(SAMPLE))
    uid = user["id"]

    # get
    fetched = repo.get(uid)
    assert fetched is not None
    assert fetched["email"] == "alice@example.com"

    # list_all
    lst = repo.list_all()
    assert any(u["id"] == uid for u in lst)

    # find_by_email
    found = repo.find_by_email("alice@example.com")
    assert found is not None
    assert found["id"] == uid

    # find_by_email with exclude_id
    not_found = repo.find_by_email("alice@example.com", exclude_id=uid)
    assert not_found is None

    # update
    updated = repo.update(uid, {"first_name": "Alicia", "updated_at": "2026-01-01T00:00:00Z"})
    assert updated["first_name"] == "Alicia"

    # delete
    assert repo.delete(uid) is True
    assert repo.get(uid) is None
    assert repo.delete(uid) is False  # already deleted


@pytest.mark.req("REQ-USR-07")
def test_memory_backend(memory_repo):
    _run_crud(memory_repo)


@pytest.mark.req("REQ-USR-07")
def test_json_backend(json_repo):
    _run_crud(json_repo)


@pytest.mark.req("REQ-USR-07")
def test_sqlite_backend(sqlite_repo):
    _run_crud(sqlite_repo)
