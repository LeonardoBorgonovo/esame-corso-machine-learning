"""Unit tests for RegistrationRepository — all backends.  REQ-REG-*"""
import pytest
from app.models import new_registration


def _run_crud(repo):
    reg = repo.create(new_registration("uid-1", "eid-1", 99.0))
    rid = reg["id"]
    assert repo.get(rid) is not None
    assert any(r["id"] == rid for r in repo.list_all())
    assert repo.count_confirmed("eid-1") == 1
    assert repo.find_confirmed("uid-1", "eid-1") is not None
    repo.update(rid, {"status": "cancelled", "updated_at": "2026-01-01T00:00:00Z"})
    assert repo.count_confirmed("eid-1") == 0
    assert repo.delete(rid) is True
    assert repo.get(rid) is None
    assert repo.delete(rid) is False


def test_memory(memory_repo): _run_crud(memory_repo)
def test_json(json_repo): _run_crud(json_repo)
def test_sqlite(sqlite_repo): _run_crud(sqlite_repo)
