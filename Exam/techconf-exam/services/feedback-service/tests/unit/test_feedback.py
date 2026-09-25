"""Tests for feedback-service.  REQ-FBK-B01..B04"""
import sys, os
import pytest
import responses as resp_mock

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "contracts"))
sys.path.insert(0, os.path.join(_ROOT, "shared"))

from validator import assert_matches_contract

REG_URL = "http://localhost:5003"
EVT_URL = "http://localhost:5002"
USER_ID = "aaaa0000-0000-0000-0000-000000000001"
EVENT_ID = "bbbb0000-0000-0000-0000-000000000002"


def _resp(r):
    return {"status_code": r.status_code, "headers": dict(r.headers), "json": r.get_json(silent=True)}


def _mock_confirmed(rsps, confirmed=True):
    items = [{"id": "r1", "user_id": USER_ID, "event_id": EVENT_ID}] if confirmed else []
    rsps.add(resp_mock.GET,
             f"{REG_URL}/api/v1/registrations",
             json={"items": items, "page": 1, "page_size": 1, "total": len(items)},
             status=200)


def _mock_event(rsps, http_status=200):
    rsps.add(resp_mock.GET, f"{EVT_URL}/api/v1/events/{EVENT_ID}",
             json={"id": EVENT_ID, "status": "published", "capacity": 10, "price": 50.0},
             status=http_status)


VALID_FB = {"user_id": USER_ID, "event_id": EVENT_ID, "rating": 4}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert_matches_contract("feedback-service", "GET", "/health", _resp(r))


@pytest.mark.req("REQ-FBK-01")
@resp_mock.activate
def test_create_feedback(client):
    _mock_confirmed(resp_mock)
    r = client.post("/api/v1/feedbacks", json=VALID_FB)
    assert r.status_code == 201
    assert "Location" in r.headers
    assert_matches_contract("feedback-service", "POST", "/api/v1/feedbacks", _resp(r))


@pytest.mark.req("REQ-FBK-B01")
@resp_mock.activate
def test_not_registered(client):
    _mock_confirmed(resp_mock, confirmed=False)
    r = client.post("/api/v1/feedbacks", json=VALID_FB)
    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "NOT_REGISTERED"
    assert_matches_contract("feedback-service", "POST", "/api/v1/feedbacks", _resp(r))


@pytest.mark.req("REQ-FBK-B02")
@resp_mock.activate
def test_duplicate_feedback(client):
    _mock_confirmed(resp_mock)
    client.post("/api/v1/feedbacks", json=VALID_FB)
    _mock_confirmed(resp_mock)
    r = client.post("/api/v1/feedbacks", json=VALID_FB)
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "FEEDBACK_ALREADY_EXISTS"


@pytest.mark.req("REQ-FBK-01")
def test_invalid_rating(client):
    # No HTTP mock needed for validation errors caught before client call
    r = client.post("/api/v1/feedbacks", json={**VALID_FB, "rating": 6})
    assert r.status_code == 422


@pytest.mark.req("REQ-FBK-B03")
@resp_mock.activate
def test_summary(client):
    _mock_confirmed(resp_mock)
    client.post("/api/v1/feedbacks", json=VALID_FB)
    _mock_event(resp_mock)
    r = client.get(f"/api/v1/feedbacks/summary?event_id={EVENT_ID}")
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 1
    assert body["average_rating"] == 4.0
    assert_matches_contract("feedback-service", "GET", "/api/v1/feedbacks/summary", _resp(r))


@pytest.mark.req("REQ-FBK-B03")
@resp_mock.activate
def test_summary_event_not_found(client):
    resp_mock.add(resp_mock.GET, f"{EVT_URL}/api/v1/events/{EVENT_ID}",
                  json={"error": {"code": "NOT_FOUND", "message": ""}}, status=404)
    r = client.get(f"/api/v1/feedbacks/summary?event_id={EVENT_ID}")
    assert r.status_code == 404


@pytest.mark.req("REQ-FBK-B04")
@resp_mock.activate
def test_reg_service_down(client):
    resp_mock.add(resp_mock.GET, f"{REG_URL}/api/v1/registrations", json={}, status=503)
    r = client.post("/api/v1/feedbacks", json=VALID_FB)
    assert r.status_code == 503
    assert_matches_contract("feedback-service", "POST", "/api/v1/feedbacks", _resp(r))


@pytest.mark.req("REQ-FBK-02")
@resp_mock.activate
def test_list_feedbacks(client):
    _mock_confirmed(resp_mock)
    client.post("/api/v1/feedbacks", json=VALID_FB)
    r = client.get("/api/v1/feedbacks")
    assert r.status_code == 200
    assert_matches_contract("feedback-service", "GET", "/api/v1/feedbacks", _resp(r))


@pytest.mark.req("REQ-FBK-02")
@resp_mock.activate
def test_patch_feedback(client):
    _mock_confirmed(resp_mock)
    cr = client.post("/api/v1/feedbacks", json=VALID_FB)
    fid = cr.get_json()["id"]
    r = client.patch(f"/api/v1/feedbacks/{fid}", json={"rating": 5, "comment": "Great!"})
    assert r.status_code == 200
    assert r.get_json()["rating"] == 5
    assert_matches_contract("feedback-service", "PATCH", f"/api/v1/feedbacks/{fid}", _resp(r))


@pytest.mark.req("REQ-FBK-02")
@resp_mock.activate
def test_delete_feedback(client):
    _mock_confirmed(resp_mock)
    cr = client.post("/api/v1/feedbacks", json=VALID_FB)
    fid = cr.get_json()["id"]
    r = client.delete(f"/api/v1/feedbacks/{fid}")
    assert r.status_code == 204
