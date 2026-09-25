"""Integration tests for event-service.

Starts real user-service + event-service processes.
Tests: 1 happy path, 1 organizer not found (422), 1 user-service down (503).
Requirements: REQ-EVT-B01, REQ-EVT-B05
"""
import subprocess
import sys
import time
import uuid
import os
import socket
import requests as req_lib
import pytest


def _free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _wait_health(base_url: str, timeout: float = 15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = req_lib.get(f"{base_url}/health", timeout=1)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError(f"{base_url} not healthy after {timeout}s")


def _start_service(name: str, port: int, extra_env: dict) -> subprocess.Popen:
    repo_root = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
    svc_dir = os.path.join(repo_root, "services", name)
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["STORAGE_BACKEND"] = "memory"
    env["PYTHONPATH"] = os.path.join(repo_root, "shared")
    env.update(extra_env)
    return subprocess.Popen(
        [sys.executable, "-m", "app"],
        cwd=svc_dir,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@pytest.fixture(scope="module")
def platform():
    user_port = _free_port()
    event_port = _free_port()

    user_proc = _start_service("user-service", user_port, {})
    _wait_health(f"http://127.0.0.1:{user_port}")

    event_proc = _start_service("event-service", event_port, {
        "USER_SERVICE_URL": f"http://127.0.0.1:{user_port}"
    })
    _wait_health(f"http://127.0.0.1:{event_port}")

    yield {
        "user": f"http://127.0.0.1:{user_port}",
        "event": f"http://127.0.0.1:{event_port}",
    }

    event_proc.terminate(); event_proc.wait(timeout=5)
    user_proc.terminate(); user_proc.wait(timeout=5)


def _make_organizer(user_base: str) -> str:
    r = req_lib.post(f"{user_base}/api/v1/users", json={
        "first_name": "Org", "last_name": "Test",
        "email": f"org_{uuid.uuid4().hex[:6]}@test.com",
        "role": "organizer"
    })
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.req("REQ-EVT-B01")
def test_create_event_happy_path(platform):
    org_id = _make_organizer(platform["user"])
    r = req_lib.post(f"{platform['event']}/api/v1/events", json={
        "title": "IT Integration Conf",
        "organizer_id": org_id,
        "venue": "Hall A", "city": "Roma",
        "start_date": "2026-11-01", "end_date": "2026-11-02",
        "capacity": 50, "price": 99.0,
    })
    assert r.status_code == 201
    assert r.json()["status"] == "draft"


@pytest.mark.req("REQ-EVT-B01")
def test_create_event_organizer_not_found(platform):
    r = req_lib.post(f"{platform['event']}/api/v1/events", json={
        "title": "Bad Event",
        "organizer_id": str(uuid.uuid4()),  # non-existent
        "venue": "Hall B", "city": "Roma",
        "start_date": "2026-11-01", "end_date": "2026-11-02",
        "capacity": 50, "price": 0.0,
    })
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "REFERENCE_NOT_FOUND"


@pytest.mark.req("REQ-EVT-B05")
def test_create_event_user_service_down():
    """Start event-service with a dead user-service URL → 503."""
    event_port = _free_port()
    proc = _start_service("event-service", event_port, {
        "USER_SERVICE_URL": "http://127.0.0.1:1"  # closed port
    })
    _wait_health(f"http://127.0.0.1:{event_port}")
    try:
        r = req_lib.post(f"http://127.0.0.1:{event_port}/api/v1/events", json={
            "title": "Unavail Event",
            "organizer_id": str(uuid.uuid4()),
            "venue": "Hall C", "city": "Roma",
            "start_date": "2026-11-01", "end_date": "2026-11-02",
            "capacity": 10, "price": 0.0,
        })
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    finally:
        proc.terminate(); proc.wait(timeout=5)
