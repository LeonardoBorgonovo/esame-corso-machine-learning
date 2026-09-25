"""Contract + HTTP tests for registration-service.  REQ-REG-*"""
import sys, os
import pytest
import responses as resp_mock

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "contracts"))
sys.path.insert(0, os.path.join(_ROOT, "shared"))

from validator import assert_matches_contract

USER_URL = "http://localhost:5001"
EVENT_URL = "http://localhost:5002"
USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
EVENT_ID = "bbbbbbbb-0000-0000-0000-000000000002"


def _resp(r):
    return {"status_code": r.status_code, "headers": dict(r.headers), "json": r.get_json(silent=True)}


def _mock_deps(rsps, event_status="published", capacity=10, price=99.0):
    rsps.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{USER_ID}",
             json={"id": USER_ID, "role": "attendee"}, status=200)
    rsps.add(resp_mock.GET, f"{EVENT_URL}/api/v1/events/{EVENT_ID}",
             json={"id": EVENT_ID, "status": event_status, "capacity": capacity, "price": price},
             status=200)


@pytest.mark.req("REQ-REG-05")
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert_matches_contract("registration-service", "GET", "/health", _resp(r))


@pytest.mark.req("REQ-REG-01")
@resp_mock.activate
def test_create_registration(client):
    _mock_deps(resp_mock)
    r = client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    assert r.status_code == 201
    body = r.get_json()
    assert body["status"] == "confirmed"
    assert body["amount"] == 99.0
    assert "Location" in r.headers
    assert_matches_contract("registration-service", "POST", "/api/v1/registrations", _resp(r))


@pytest.mark.req("REQ-REG-01")
def test_create_missing_fields(client):
    r = client.post("/api/v1/registrations", json={"user_id": USER_ID})
    assert r.status_code == 422


@pytest.mark.req("REQ-REG-B03")
@resp_mock.activate
def test_create_event_not_published(client):
    _mock_deps(resp_mock, event_status="draft")
    r = client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "EVENT_NOT_OPEN"


@pytest.mark.req("REQ-REG-B04")
@resp_mock.activate
def test_already_registered(client):
    _mock_deps(resp_mock)
    client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    _mock_deps(resp_mock)
    r = client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "ALREADY_REGISTERED"


@pytest.mark.req("REQ-REG-B05")
@resp_mock.activate
def test_event_full(client):
    _mock_deps(resp_mock, capacity=1)
    client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    uid2 = "cccccccc-0000-0000-0000-000000000003"
    resp_mock.add(resp_mock.GET, f"{USER_URL}/api/v1/users/{uid2}",
                  json={"id": uid2, "role": "attendee"}, status=200)
    resp_mock.add(resp_mock.GET, f"{EVENT_URL}/api/v1/events/{EVENT_ID}",
                  json={"id": EVENT_ID, "status": "published", "capacity": 1, "price": 99.0}, status=200)
    r = client.post("/api/v1/registrations", json={"user_id": uid2, "event_id": EVENT_ID})
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "EVENT_FULL"
    assert_matches_contract("registration-service", "POST", "/api/v1/registrations", _resp(r))


@pytest.mark.req("REQ-REG-02")
@resp_mock.activate
def test_get_registration(client):
    _mock_deps(resp_mock)
    cr = client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    rid = cr.get_json()["id"]
    r = client.get(f"/api/v1/registrations/{rid}")
    assert r.status_code == 200
    assert_matches_contract("registration-service", "GET", f"/api/v1/registrations/{rid}", _resp(r))


@pytest.mark.req("REQ-REG-02")
def test_get_not_found(client):
    r = client.get("/api/v1/registrations/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


@pytest.mark.req("REQ-REG-03")
@resp_mock.activate
def test_put_not_allowed(client):
    _mock_deps(resp_mock)
    cr = client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    rid = cr.get_json()["id"]
    r = client.put(f"/api/v1/registrations/{rid}", json={})
    assert r.status_code == 405
    assert_matches_contract("registration-service", "PUT", f"/api/v1/registrations/{rid}", _resp(r))


@pytest.mark.req("REQ-REG-B07")
@resp_mock.activate
def test_patch_cancel(client):
    _mock_deps(resp_mock)
    cr = client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    rid = cr.get_json()["id"]
    r = client.patch(f"/api/v1/registrations/{rid}", json={"status": "cancelled"})
    assert r.status_code == 200
    assert r.get_json()["status"] == "cancelled"
    assert_matches_contract("registration-service", "PATCH", f"/api/v1/registrations/{rid}", _resp(r))


@pytest.mark.req("REQ-REG-B08")
@resp_mock.activate
def test_stats(client):
    _mock_deps(resp_mock, capacity=5)
    client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    resp_mock.add(resp_mock.GET, f"{EVENT_URL}/api/v1/events/{EVENT_ID}",
                  json={"id": EVENT_ID, "status": "published", "capacity": 5, "price": 99.0}, status=200)
    r = client.get(f"/api/v1/registrations/stats?event_id={EVENT_ID}")
    assert r.status_code == 200
    body = r.get_json()
    assert body["confirmed"] == 1
    assert body["available"] == 4
    assert_matches_contract("registration-service", "GET", "/api/v1/registrations/stats", _resp(r))


@pytest.mark.req("REQ-REG-04")
@resp_mock.activate
def test_delete_registration(client):
    _mock_deps(resp_mock)
    cr = client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    rid = cr.get_json()["id"]
    r = client.delete(f"/api/v1/registrations/{rid}")
    assert r.status_code == 204


@pytest.mark.req("REQ-REG-02")
@resp_mock.activate
def test_list_registrations(client):
    _mock_deps(resp_mock)
    client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})
    r = client.get("/api/v1/registrations")
    assert r.status_code == 200
    assert_matches_contract("registration-service", "GET", "/api/v1/registrations", _resp(r))
