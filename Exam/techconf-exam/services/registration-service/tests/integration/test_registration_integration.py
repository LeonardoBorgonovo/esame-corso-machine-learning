"""Integration tests for registration-service.

Starts user-service + event-service + registration-service as real processes.
Tests: happy path (201), user missing (422), event not published (422), dependency down (503).
Requirements: REQ-REG-B01, REQ-REG-B03, REQ-REG-B09
"""
import subprocess, sys, time, uuid, os, socket
import requests as req_lib
import pytest


def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def _wait(url, timeout=15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if req_lib.get(f"{url}/health", timeout=1).status_code == 200: return
        except Exception: pass
        time.sleep(0.25)
    raise RuntimeError(f"{url} not healthy")


def _start(name, port, extra):
    root = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
    env = os.environ.copy()
    env.update({"PORT": str(port), "STORAGE_BACKEND": "memory",
                "PYTHONPATH": os.path.join(root, "shared"), **extra})
    return subprocess.Popen([sys.executable, "-m", "app"],
                            cwd=os.path.join(root, "services", name),
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


@pytest.fixture(scope="module")
def platform():
    up = _free_port(); ep = _free_port(); rp = _free_port()
    u = _start("user-service", up, {}); _wait(f"http://127.0.0.1:{up}")
    e = _start("event-service", ep, {"USER_SERVICE_URL": f"http://127.0.0.1:{up}"}); _wait(f"http://127.0.0.1:{ep}")
    r = _start("registration-service", rp, {
        "USER_SERVICE_URL": f"http://127.0.0.1:{up}",
        "EVENT_SERVICE_URL": f"http://127.0.0.1:{ep}",
    }); _wait(f"http://127.0.0.1:{rp}")
    yield {"user": f"http://127.0.0.1:{up}", "event": f"http://127.0.0.1:{ep}", "reg": f"http://127.0.0.1:{rp}"}
    r.terminate(); r.wait(5); e.terminate(); e.wait(5); u.terminate(); u.wait(5)


def _make_user(base, role="attendee"):
    r = req_lib.post(f"{base}/api/v1/users", json={
        "first_name": "T", "last_name": "T",
        "email": f"u_{uuid.uuid4().hex[:6]}@t.com", "role": role})
    assert r.status_code == 201
    return r.json()["id"]


def _make_event(base, org_id, status="published", capacity=10):
    r = req_lib.post(f"{base}/api/v1/events", json={
        "title": f"E {uuid.uuid4().hex[:4]}", "organizer_id": org_id,
        "venue": "V", "city": "C", "start_date": "2026-10-01", "end_date": "2026-10-02",
        "capacity": capacity, "price": 50.0})
    assert r.status_code == 201
    eid = r.json()["id"]
    if status == "published":
        req_lib.patch(f"{base}/api/v1/events/{eid}", json={"status": "published"})
    return eid


@pytest.mark.req("REQ-REG-01")
def test_happy_path(platform):
    org = _make_user(platform["user"], "organizer")
    att = _make_user(platform["user"])
    eid = _make_event(platform["event"], org)
    r = req_lib.post(f"{platform['reg']}/api/v1/registrations", json={"user_id": att, "event_id": eid})
    assert r.status_code == 201
    assert r.json()["status"] == "confirmed"
    assert r.json()["amount"] == 50.0


@pytest.mark.req("REQ-REG-B01")
def test_user_not_found(platform):
    org = _make_user(platform["user"], "organizer")
    eid = _make_event(platform["event"], org)
    r = req_lib.post(f"{platform['reg']}/api/v1/registrations",
                     json={"user_id": str(uuid.uuid4()), "event_id": eid})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "REFERENCE_NOT_FOUND"


@pytest.mark.req("REQ-REG-B03")
def test_event_not_published(platform):
    org = _make_user(platform["user"], "organizer")
    att = _make_user(platform["user"])
    eid = _make_event(platform["event"], org, status="draft")
    r = req_lib.post(f"{platform['reg']}/api/v1/registrations", json={"user_id": att, "event_id": eid})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "EVENT_NOT_OPEN"


@pytest.mark.req("REQ-REG-B09")
def test_dependency_down():
    rp = _free_port()
    proc = _start("registration-service", rp, {
        "USER_SERVICE_URL": "http://127.0.0.1:1",
        "EVENT_SERVICE_URL": "http://127.0.0.1:1",
    })
    _wait(f"http://127.0.0.1:{rp}")
    try:
        r = req_lib.post(f"http://127.0.0.1:{rp}/api/v1/registrations",
                         json={"user_id": str(uuid.uuid4()), "event_id": str(uuid.uuid4())})
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    finally:
        proc.terminate(); proc.wait(5)
