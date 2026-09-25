"""Contract + HTTP tests for event-service.  REQ-EVT-01..REQ-EVT-05"""
import sys, os
import pytest
import responses as resp_mock

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "contracts"))
sys.path.insert(0, os.path.join(_ROOT, "shared"))

from validator import assert_matches_contract

USER_URL = "http://localhost:5001"
ORGANIZER_ID = "aaaaaaaa-0000-0000-0000-000000000001"

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


def _resp(r):
    return {"status_code": r.status_code, "headers": dict(r.headers), "json": r.get_json(silent=True)}


def _mock_organizer(rsps):
    rsps.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{ORGANIZER_ID}",
             json={"id": ORGANIZER_ID, "role": "organizer"}, status=200)


@pytest.mark.req("REQ-EVT-05")
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert_matches_contract("event-service", "GET", "/health", _resp(r))


@pytest.mark.req("REQ-EVT-01")
@resp_mock.activate
def test_create_event(client):
    _mock_organizer(resp_mock)
    r = client.post("/api/v1/events", json=VALID_EVENT)
    assert r.status_code == 201
    assert "Location" in r.headers
    assert_matches_contract("event-service", "POST", "/api/v1/events", _resp(r))


@pytest.mark.req("REQ-EVT-01")
def test_create_event_bad_json(client):
    r = client.post("/api/v1/events", data="bad", content_type="application/json")
    assert r.status_code == 400
    assert_matches_contract("event-service", "POST", "/api/v1/events", _resp(r))


@pytest.mark.req("REQ-EVT-B01")
@resp_mock.activate
def test_create_event_organizer_not_found(client):
    resp_mock.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{ORGANIZER_ID}",
                  json={"error": {"code": "NOT_FOUND", "message": ""}}, status=404)
    r = client.post("/api/v1/events", json=VALID_EVENT)
    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "REFERENCE_NOT_FOUND"


@pytest.mark.req("REQ-EVT-B05")
@resp_mock.activate
def test_create_event_user_service_down(client):
    resp_mock.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{ORGANIZER_ID}",
                  json={}, status=503)
    r = client.post("/api/v1/events", json=VALID_EVENT)
    assert r.status_code == 503
    assert_matches_contract("event-service", "POST", "/api/v1/events", _resp(r))


@pytest.mark.req("REQ-EVT-B06")
@resp_mock.activate
def test_list_events(client):
    _mock_organizer(resp_mock)
    client.post("/api/v1/events", json=VALID_EVENT)
    r = client.get("/api/v1/events")
    assert r.status_code == 200
    assert_matches_contract("event-service", "GET", "/api/v1/events", _resp(r))


@pytest.mark.req("REQ-EVT-02")
@resp_mock.activate
def test_get_event(client):
    _mock_organizer(resp_mock)
    cr = client.post("/api/v1/events", json=VALID_EVENT)
    eid = cr.get_json()["id"]
    r = client.get(f"/api/v1/events/{eid}")
    assert r.status_code == 200
    assert_matches_contract("event-service", "GET", f"/api/v1/events/{eid}", _resp(r))


@pytest.mark.req("REQ-EVT-02")
def test_get_event_not_found(client):
    r = client.get("/api/v1/events/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert_matches_contract("event-service", "GET", "/api/v1/events/00000000-0000-0000-0000-000000000000", _resp(r))


@pytest.mark.req("REQ-EVT-B04")
@resp_mock.activate
def test_patch_status_transition(client):
    _mock_organizer(resp_mock)
    cr = client.post("/api/v1/events", json=VALID_EVENT)
    eid = cr.get_json()["id"]
    r = client.patch(f"/api/v1/events/{eid}", json={"status": "published"})
    assert r.status_code == 200
    assert r.get_json()["status"] == "published"
    assert_matches_contract("event-service", "PATCH", f"/api/v1/events/{eid}", _resp(r))


@pytest.mark.req("REQ-EVT-B04")
@resp_mock.activate
def test_invalid_transition(client):
    _mock_organizer(resp_mock)
    cr = client.post("/api/v1/events", json=VALID_EVENT)
    eid = cr.get_json()["id"]
    client.patch(f"/api/v1/events/{eid}", json={"status": "published"})
    r = client.patch(f"/api/v1/events/{eid}", json={"status": "draft"})
    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


@pytest.mark.req("REQ-EVT-04")
@resp_mock.activate
def test_delete_event(client):
    _mock_organizer(resp_mock)
    cr = client.post("/api/v1/events", json=VALID_EVENT)
    eid = cr.get_json()["id"]
    r = client.delete(f"/api/v1/events/{eid}")
    assert r.status_code == 204


@pytest.mark.req("REQ-EVT-03")
@resp_mock.activate
def test_put_event(client):
    _mock_organizer(resp_mock)
    cr = client.post("/api/v1/events", json=VALID_EVENT)
    eid = cr.get_json()["id"]
    _mock_organizer(resp_mock)
    r = client.put(f"/api/v1/events/{eid}", json={**VALID_EVENT, "title": "Updated Conf"})
    assert r.status_code == 200
    assert r.get_json()["title"] == "Updated Conf"
    assert_matches_contract("event-service", "PUT", f"/api/v1/events/{eid}", _resp(r))
