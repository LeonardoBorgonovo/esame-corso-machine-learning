"""Unit tests for EventRepository — all three backends.  REQ-EVT-06"""
import pytest
from app.models import new_event

SAMPLE = {
    "title": "Test Conf", "organizer_id": "uid-1", "venue": "Hall A",
    "city": "Milano", "start_date": "2026-10-01", "end_date": "2026-10-02",
    "capacity": 50, "price": 99.0, "status": "draft",
}


def _run_crud(repo):
    event = repo.create(new_event(SAMPLE))
    eid = event["id"]
    assert repo.get(eid) is not None
    lst = repo.list_all()
    assert any(e["id"] == eid for e in lst)
    updated = repo.update(eid, {"title": "Updated", "updated_at": "2026-01-01T00:00:00Z"})
    assert updated["title"] == "Updated"
    assert repo.delete(eid) is True
    assert repo.get(eid) is None
    assert repo.delete(eid) is False


@pytest.mark.req("REQ-EVT-06")
def test_memory(memory_repo): _run_crud(memory_repo)

@pytest.mark.req("REQ-EVT-06")
def test_json(json_repo): _run_crud(json_repo)

@pytest.mark.req("REQ-EVT-06")
def test_sqlite(sqlite_repo): _run_crud(sqlite_repo)
