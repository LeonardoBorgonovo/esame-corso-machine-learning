"""Contract + HTTP layer tests for user-service.

Each endpoint tested at least once with assert_matches_contract.
Requirements: REQ-USR-01 through REQ-USR-06.
"""
import sys, os
import json
import pytest

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "contracts"))
sys.path.insert(0, os.path.join(_ROOT, "shared"))

from validator import assert_matches_contract


def _resp(client_resp):
    """Adapt Flask test_client response to validator interface."""
    return {
        "status_code": client_resp.status_code,
        "headers": dict(client_resp.headers),
        "json": client_resp.get_json(silent=True),
    }


VALID_USER = {"first_name": "Test", "last_name": "User", "email": "test@example.com"}


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-06")
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert_matches_contract("user-service", "GET", "/health", _resp(r))


# ── POST /api/v1/users ────────────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-01")
def test_create_valid(client):
    r = client.post("/api/v1/users", json=VALID_USER)
    assert r.status_code == 201
    assert "Location" in r.headers
    assert_matches_contract("user-service", "POST", "/api/v1/users", _resp(r))


@pytest.mark.req("REQ-USR-01")
def test_create_missing_field(client):
    r = client.post("/api/v1/users", json={"first_name": "X"})
    assert r.status_code == 422
    assert_matches_contract("user-service", "POST", "/api/v1/users", _resp(r))


@pytest.mark.req("REQ-USR-01")
def test_create_malformed_json(client):
    r = client.post("/api/v1/users", data="not json", content_type="application/json")
    assert r.status_code == 400
    assert_matches_contract("user-service", "POST", "/api/v1/users", _resp(r))


@pytest.mark.req("REQ-USR-B01")
def test_create_duplicate_email(client):
    client.post("/api/v1/users", json=VALID_USER)
    r = client.post("/api/v1/users", json={**VALID_USER, "email": "TEST@EXAMPLE.COM"})
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"
    assert_matches_contract("user-service", "POST", "/api/v1/users", _resp(r))


# ── GET /api/v1/users ─────────────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-B03")
def test_list_users(client):
    client.post("/api/v1/users", json=VALID_USER)
    r = client.get("/api/v1/users")
    assert r.status_code == 200
    assert_matches_contract("user-service", "GET", "/api/v1/users", _resp(r))


@pytest.mark.req("REQ-USR-B03")
def test_list_filter_role(client):
    client.post("/api/v1/users", json={**VALID_USER, "email": "org@x.com", "role": "organizer"})
    r = client.get("/api/v1/users?role=organizer")
    assert r.status_code == 200
    data = r.get_json()
    assert all(u["role"] == "organizer" for u in data["items"])


@pytest.mark.req("REQ-USR-B03")
def test_list_invalid_role_filter(client):
    r = client.get("/api/v1/users?role=badval")
    assert r.status_code == 422


# ── GET /api/v1/users/<id> ────────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-02")
def test_get_by_id(client):
    cr = client.post("/api/v1/users", json=VALID_USER)
    uid = cr.get_json()["id"]
    r = client.get(f"/api/v1/users/{uid}")
    assert r.status_code == 200
    assert_matches_contract("user-service", "GET", f"/api/v1/users/{uid}", _resp(r))


@pytest.mark.req("REQ-USR-02")
def test_get_not_found(client):
    r = client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert_matches_contract("user-service", "GET", "/api/v1/users/00000000-0000-0000-0000-000000000000", _resp(r))


# ── PUT /api/v1/users/<id> ────────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-03")
def test_put_user(client):
    cr = client.post("/api/v1/users", json=VALID_USER)
    uid = cr.get_json()["id"]
    r = client.put(f"/api/v1/users/{uid}", json={
        "first_name": "Updated", "last_name": "User", "email": "updated@example.com"
    })
    assert r.status_code == 200
    assert_matches_contract("user-service", "PUT", f"/api/v1/users/{uid}", _resp(r))


# ── PATCH /api/v1/users/<id> ─────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-03")
def test_patch_user(client):
    cr = client.post("/api/v1/users", json=VALID_USER)
    uid = cr.get_json()["id"]
    r = client.patch(f"/api/v1/users/{uid}", json={"first_name": "Patched"})
    assert r.status_code == 200
    assert r.get_json()["first_name"] == "Patched"
    assert_matches_contract("user-service", "PATCH", f"/api/v1/users/{uid}", _resp(r))


@pytest.mark.req("REQ-USR-03")
def test_patch_updated_at_changes(client):
    cr = client.post("/api/v1/users", json=VALID_USER)
    created = cr.get_json()
    r = client.patch(f"/api/v1/users/{created['id']}", json={"first_name": "New"})
    # updated_at should be present
    assert r.get_json()["updated_at"]


# ── DELETE /api/v1/users/<id> ────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-04")
def test_delete_user(client):
    cr = client.post("/api/v1/users", json=VALID_USER)
    uid = cr.get_json()["id"]
    r = client.delete(f"/api/v1/users/{uid}")
    assert r.status_code == 204
    # subsequent GET should 404
    r2 = client.get(f"/api/v1/users/{uid}")
    assert r2.status_code == 404


@pytest.mark.req("REQ-USR-04")
def test_delete_not_found(client):
    r = client.delete("/api/v1/users/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert_matches_contract("user-service", "DELETE", "/api/v1/users/00000000-0000-0000-0000-000000000000", _resp(r))


# ── Method not allowed ────────────────────────────────────────────────────────

@pytest.mark.req("REQ-USR-05")
def test_method_not_allowed(client):
    r = client.delete("/api/v1/users")   # DELETE on collection not supported
    assert r.status_code == 405
