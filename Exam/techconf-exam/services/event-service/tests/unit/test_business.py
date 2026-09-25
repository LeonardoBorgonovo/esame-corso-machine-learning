"""Unit tests for event-service business logic.

Uses `responses` to mock HTTP calls to user-service.
Requirements: REQ-EVT-B01..B06
"""
import sys, os
import pytest
import responses as resp_mock

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "shared"))

from app.repository import MemoryEventRepository
from app import business
from errors import ValidationError, NotFoundError, ReferenceNotFoundError, DependencyUnavailableError, InvalidStatusTransitionError

USER_URL = "http://localhost:5001"
ORGANIZER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
ATTENDEE_ID = "bbbbbbbb-0000-0000-0000-000000000002"

VALID_EVENT = {
    "title": "CloudConf 2026",
    "organizer_id": ORGANIZER_ID,
    "venue": "Auditorium Roma",
    "city": "Roma",
    "start_date": "2026-10-15",
    "end_date": "2026-10-16",
    "capacity": 100,
    "price": 149.00,
}


@pytest.fixture
def repo():
    return MemoryEventRepository()


@pytest.fixture
def mock_organizer():
    with resp_mock.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{ORGANIZER_ID}",
                 json={"id": ORGANIZER_ID, "role": "organizer"}, status=200)
        yield rsps


@pytest.fixture
def mock_attendee():
    with resp_mock.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{ATTENDEE_ID}",
                 json={"id": ATTENDEE_ID, "role": "attendee"}, status=200)
        yield rsps


@pytest.fixture
def mock_missing_user():
    with resp_mock.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{ORGANIZER_ID}",
                 json={"error": {"code": "NOT_FOUND", "message": ""}}, status=404)
        yield rsps


# ── REQ-EVT-01: create ────────────────────────────────────────────────────────

@pytest.mark.req("REQ-EVT-01")
def test_create_valid(repo, mock_organizer):
    e = business.create_event(repo, VALID_EVENT)
    assert e["status"] == "draft"
    assert e["price"] == 149.00
    assert e["id"]


@pytest.mark.req("REQ-EVT-01")
def test_create_missing_required(repo, mock_organizer):
    with pytest.raises(ValidationError):
        business.create_event(repo, {"title": "X", "organizer_id": ORGANIZER_ID})


@pytest.mark.req("REQ-EVT-B03")
def test_create_end_before_start(repo, mock_organizer):
    data = {**VALID_EVENT, "start_date": "2026-10-15", "end_date": "2026-10-14"}
    with pytest.raises(ValidationError):
        business.create_event(repo, data)


# ── REQ-EVT-B01, B02: organizer validation ───────────────────────────────────

@pytest.mark.req("REQ-EVT-B01")
def test_create_organizer_not_found(repo, mock_missing_user):
    with pytest.raises(ReferenceNotFoundError):
        business.create_event(repo, VALID_EVENT)


@pytest.mark.req("REQ-EVT-B02")
def test_create_organizer_wrong_role(repo, mock_attendee):
    data = {**VALID_EVENT, "organizer_id": ATTENDEE_ID}
    with pytest.raises(ValidationError) as exc:
        business.create_event(repo, data)
    assert "INVALID_ORGANIZER" in str(exc.value.code)


@pytest.mark.req("REQ-EVT-B05")
def test_create_user_service_down(repo):
    with resp_mock.RequestsMock() as rsps:
        rsps.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{ORGANIZER_ID}",
                 json={}, status=503)
        with pytest.raises(DependencyUnavailableError):
            business.create_event(repo, VALID_EVENT)


# ── REQ-EVT-B04: status transitions ─────────────────────────────────────────

@pytest.mark.req("REQ-EVT-B04")
def test_draft_to_published(repo, mock_organizer):
    e = business.create_event(repo, VALID_EVENT)
    with resp_mock.RequestsMock():
        updated = business.patch_event(repo, e["id"], {"status": "published"})
    assert updated["status"] == "published"


@pytest.mark.req("REQ-EVT-B04")
def test_published_to_draft_rejected(repo, mock_organizer):
    e = business.create_event(repo, VALID_EVENT)
    with resp_mock.RequestsMock():
        business.patch_event(repo, e["id"], {"status": "published"})
    with pytest.raises(InvalidStatusTransitionError):
        business.patch_event(repo, e["id"], {"status": "draft"})


@pytest.mark.req("REQ-EVT-B04")
def test_cancelled_to_any_rejected(repo, mock_organizer):
    e = business.create_event(repo, VALID_EVENT)
    with resp_mock.RequestsMock():
        business.patch_event(repo, e["id"], {"status": "cancelled"})
    with pytest.raises(InvalidStatusTransitionError):
        business.patch_event(repo, e["id"], {"status": "published"})


# ── REQ-EVT-B06: filters ─────────────────────────────────────────────────────

@pytest.mark.req("REQ-EVT-B06")
def test_filter_by_status(repo, mock_organizer):
    business.create_event(repo, VALID_EVENT)
    events = business.list_events(repo, {"status": "draft"})
    assert all(e["status"] == "draft" for e in events)


@pytest.mark.req("REQ-EVT-B06")
def test_filter_by_city(repo, mock_organizer):
    business.create_event(repo, VALID_EVENT)
    business.create_event(repo, {**VALID_EVENT, "title": "Other", "city": "Milano"})
    events = business.list_events(repo, {"city": "roma"})
    assert all(e["city"].lower() == "roma" for e in events)


# ── delete + get ─────────────────────────────────────────────────────────────

def test_get_not_found(repo):
    with pytest.raises(NotFoundError):
        business.get_event(repo, "bad-id")


def test_delete_not_found(repo):
    with pytest.raises(NotFoundError):
        business.delete_event(repo, "bad-id")
