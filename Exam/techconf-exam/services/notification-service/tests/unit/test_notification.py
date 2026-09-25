"""Tests for notification-service.  REQ-NTF-B01..B04"""
import sys, os
import pytest
import responses as resp_mock

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "contracts"))
sys.path.insert(0, os.path.join(_ROOT, "shared"))

from validator import assert_matches_contract

USER_URL = "http://localhost:5001"
REG_URL = "http://localhost:5003"
USER_ID = "aaaa0000-0000-0000-0000-000000000001"
EVENT_ID = "bbbb0000-0000-0000-0000-000000000002"

VALID_NTF = {"user_id": USER_ID, "channel": "email", "subject": "Hello", "body": "World"}


def _resp(r):
    return {"status_code": r.status_code, "headers": dict(r.headers), "json": r.get_json(silent=True)}


def _mock_user(rsps, uid=USER_ID, status=200):
    rsps.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{uid}",
             json={"id": uid, "role": "attendee"}, status=status)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert_matches_contract("notification-service", "GET", "/health", _resp(r))


@pytest.mark.req("REQ-NTF-01")
@resp_mock.activate
def test_create_notification(client):
    _mock_user(resp_mock)
    r = client.post("/api/v1/notifications", json=VALID_NTF)
    assert r.status_code == 201
    body = r.get_json()
    assert body["status"] == "queued"
    assert body["sent_at"] is None
    assert "Location" in r.headers
    assert_matches_contract("notification-service", "POST", "/api/v1/notifications", _resp(r))


@pytest.mark.req("REQ-NTF-B01")
@resp_mock.activate
def test_user_not_found(client):
    _mock_user(resp_mock, status=404)
    r = client.post("/api/v1/notifications", json=VALID_NTF)
    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "REFERENCE_NOT_FOUND"
    assert_matches_contract("notification-service", "POST", "/api/v1/notifications", _resp(r))


@pytest.mark.req("REQ-NTF-B02")
@resp_mock.activate
def test_patch_queued_to_sent(client):
    _mock_user(resp_mock)
    cr = client.post("/api/v1/notifications", json=VALID_NTF)
    nid = cr.get_json()["id"]
    r = client.patch(f"/api/v1/notifications/{nid}", json={"status": "sent"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "sent"
    assert body["sent_at"] is not None
    assert_matches_contract("notification-service", "PATCH", f"/api/v1/notifications/{nid}", _resp(r))


@pytest.mark.req("REQ-NTF-B02")
@resp_mock.activate
def test_patch_sent_to_queued_rejected(client):
    _mock_user(resp_mock)
    cr = client.post("/api/v1/notifications", json=VALID_NTF)
    nid = cr.get_json()["id"]
    client.patch(f"/api/v1/notifications/{nid}", json={"status": "sent"})
    r = client.patch(f"/api/v1/notifications/{nid}", json={"status": "queued"})
    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


@pytest.mark.req("REQ-NTF-B04")
@resp_mock.activate
def test_user_service_down(client):
    resp_mock.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{USER_ID}", json={}, status=503)
    r = client.post("/api/v1/notifications", json=VALID_NTF)
    assert r.status_code == 503
    assert_matches_contract("notification-service", "POST", "/api/v1/notifications", _resp(r))


@pytest.mark.req("REQ-NTF-B03")
@resp_mock.activate
def test_broadcast(client):
    # Mock 2 confirmed registrations
    resp_mock.add(resp_mock.GET, f"{REG_URL}/api/v1/registrations",
                  json={"items": [{"user_id": "uid-1"}, {"user_id": "uid-2"}], "page": 1, "page_size": 100, "total": 2},
                  status=200)
    r = client.post("/api/v1/notifications/broadcast", json={
        "event_id": EVENT_ID, "channel": "email", "subject": "Thanks", "body": "Thank you!"
    })
    assert r.status_code == 201
    body = r.get_json()
    assert body["created"] == 2
    assert body["event_id"] == EVENT_ID
    assert_matches_contract("notification-service", "POST", "/api/v1/notifications/broadcast", _resp(r))


@pytest.mark.req("REQ-NTF-B04")
@resp_mock.activate
def test_broadcast_reg_service_down(client):
    resp_mock.add(resp_mock.GET, f"{REG_URL}/api/v1/registrations", json={}, status=503)
    r = client.post("/api/v1/notifications/broadcast", json={
        "event_id": EVENT_ID, "channel": "email", "subject": "X", "body": "Y"
    })
    assert r.status_code == 503
    assert_matches_contract("notification-service", "POST", "/api/v1/notifications/broadcast", _resp(r))


@pytest.mark.req("REQ-NTF-02")
@resp_mock.activate
def test_list_notifications(client):
    _mock_user(resp_mock)
    client.post("/api/v1/notifications", json=VALID_NTF)
    r = client.get("/api/v1/notifications")
    assert r.status_code == 200
    assert_matches_contract("notification-service", "GET", "/api/v1/notifications", _resp(r))


@pytest.mark.req("REQ-NTF-02")
@resp_mock.activate
def test_delete_notification(client):
    _mock_user(resp_mock)
    cr = client.post("/api/v1/notifications", json=VALID_NTF)
    nid = cr.get_json()["id"]
    r = client.delete(f"/api/v1/notifications/{nid}")
    assert r.status_code == 204
