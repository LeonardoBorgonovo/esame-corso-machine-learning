"""Unit tests for registration-service business logic.  REQ-REG-B01..B09"""
import sys, os
import pytest
import responses as resp_mock

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "shared"))

from app.repository import MemoryRegistrationRepository
from app import business
from errors import ValidationError, NotFoundError, InvalidStatusTransitionError

USER_URL = "http://localhost:5001"
EVENT_URL = "http://localhost:5002"
USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
EVENT_ID = "bbbbbbbb-0000-0000-0000-000000000002"


@pytest.fixture
def repo():
    return MemoryRegistrationRepository()


def _mock_user(rsps, user_id=USER_ID, status=200):
    rsps.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{user_id}",
             json={"id": user_id, "role": "attendee"}, status=status)


def _mock_event(rsps, event_id=EVENT_ID, ev_status="published", capacity=10, price=99.0, http_status=200):
    rsps.add(resp_mock.GET, f"{EVENT_URL}/api/v1/events/{event_id}",
             json={"id": event_id, "status": ev_status, "capacity": capacity, "price": price},
             status=http_status)


# ── REQ-REG-B01, B02: references ─────────────────────────────────────────────

@pytest.mark.req("REQ-REG-B01")
@resp_mock.activate
def test_user_not_found(repo):
    _mock_user(resp_mock, status=404)
    from errors import ReferenceNotFoundError
    with pytest.raises(ReferenceNotFoundError):
        business.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})


@pytest.mark.req("REQ-REG-B02")
@resp_mock.activate
def test_event_not_found(repo):
    _mock_user(resp_mock)
    _mock_event(resp_mock, http_status=404)
    from errors import ReferenceNotFoundError
    with pytest.raises(ReferenceNotFoundError):
        business.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})


# ── REQ-REG-B03: event must be published ─────────────────────────────────────

@pytest.mark.req("REQ-REG-B03")
@resp_mock.activate
def test_event_not_published(repo):
    _mock_user(resp_mock)
    _mock_event(resp_mock, ev_status="draft")
    with pytest.raises(business.EventNotOpenError):
        business.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})


# ── REQ-REG-B04: no duplicate ────────────────────────────────────────────────

@pytest.mark.req("REQ-REG-B04")
@resp_mock.activate
def test_already_registered(repo):
    _mock_user(resp_mock)
    _mock_event(resp_mock)
    business.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})

    _mock_user(resp_mock)
    _mock_event(resp_mock)
    with pytest.raises(business.AlreadyRegisteredError):
        business.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})


# ── REQ-REG-B05: capacity ────────────────────────────────────────────────────

@pytest.mark.req("REQ-REG-B05")
@resp_mock.activate
def test_event_full(repo):
    # Register user 1
    _mock_user(resp_mock, "uid-1")
    _mock_event(resp_mock, capacity=1)
    business.create_registration(repo, {"user_id": "uid-1", "event_id": EVENT_ID})

    # Try user 2 → full
    _mock_user(resp_mock, "uid-2")
    _mock_event(resp_mock, capacity=1)
    with pytest.raises(business.EventFullError):
        business.create_registration(repo, {"user_id": "uid-2", "event_id": EVENT_ID})


@pytest.mark.req("REQ-REG-B05")
@resp_mock.activate
def test_cancel_frees_slot(repo):
    # Register user 1
    _mock_user(resp_mock, "uid-1")
    _mock_event(resp_mock, capacity=1)
    reg = business.create_registration(repo, {"user_id": "uid-1", "event_id": EVENT_ID})

    # Cancel
    business.patch_registration(repo, reg["id"], {"status": "cancelled"})

    # Now user 2 can register
    _mock_user(resp_mock, "uid-2")
    _mock_event(resp_mock, capacity=1)
    reg2 = business.create_registration(repo, {"user_id": "uid-2", "event_id": EVENT_ID})
    assert reg2["status"] == "confirmed"


# ── REQ-REG-B06: amount = event.price ────────────────────────────────────────

@pytest.mark.req("REQ-REG-B06")
@resp_mock.activate
def test_amount_equals_event_price(repo):
    _mock_user(resp_mock)
    _mock_event(resp_mock, price=149.00)
    reg = business.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    assert reg["amount"] == 149.00


# ── REQ-REG-B07: status transitions ─────────────────────────────────────────

@pytest.mark.req("REQ-REG-B07")
@resp_mock.activate
def test_patch_confirmed_to_cancelled(repo):
    _mock_user(resp_mock)
    _mock_event(resp_mock)
    reg = business.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    updated = business.patch_registration(repo, reg["id"], {"status": "cancelled"})
    assert updated["status"] == "cancelled"


@pytest.mark.req("REQ-REG-B07")
@resp_mock.activate
def test_patch_cancelled_to_confirmed_rejected(repo):
    _mock_user(resp_mock)
    _mock_event(resp_mock)
    reg = business.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    business.patch_registration(repo, reg["id"], {"status": "cancelled"})
    with pytest.raises(InvalidStatusTransitionError):
        business.patch_registration(repo, reg["id"], {"status": "confirmed"})


# ── REQ-REG-B08: stats ───────────────────────────────────────────────────────

@pytest.mark.req("REQ-REG-B08")
@resp_mock.activate
def test_stats(repo):
    _mock_user(resp_mock)
    _mock_event(resp_mock, capacity=5)
    business.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    _mock_event(resp_mock, capacity=5)  # mock again for stats call
    stats = business.get_stats(repo, EVENT_ID)
    assert stats["confirmed"] == 1
    assert stats["capacity"] == 5
    assert stats["available"] == 4


# ── REQ-REG-B09: dependency unavailable ──────────────────────────────────────

@pytest.mark.req("REQ-REG-B09")
@resp_mock.activate
def test_user_service_down(repo):
    resp_mock.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{USER_ID}", json={}, status=503)
    from errors import DependencyUnavailableError
    with pytest.raises(DependencyUnavailableError):
        business.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
