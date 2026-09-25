"""Integration tests for user-service — launches real process on a free port.

Requirements: REQ-USR-01, REQ-USR-02, REQ-USR-03, REQ-USR-04
"""
import subprocess
import sys
import time
import uuid
import requests as req_lib
import pytest


SERVICE_DIR = __file__  # used to locate the service root


def wait_health(base_url: str, timeout: float = 10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = req_lib.get(f"{base_url}/health", timeout=1)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"Service at {base_url} did not become healthy in {timeout}s")


@pytest.fixture(scope="module")
def svc(tmp_path_factory):
    """Start user-service on a free port, yield base_url, then stop."""
    import socket
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    import os
    svc_dir = os.path.join(os.path.dirname(__file__), "..", "..")
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["STORAGE_BACKEND"] = "memory"
    env["PYTHONPATH"] = os.path.join(svc_dir, "..", "..", "..", "shared")

    proc = subprocess.Popen(
        [sys.executable, "-m", "app"],
        cwd=svc_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        wait_health(base)
        yield base
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def rand_email():
    return f"it_{uuid.uuid4().hex[:8]}@example.com"


@pytest.mark.req("REQ-USR-01")
def test_create_user(svc):
    r = req_lib.post(f"{svc}/api/v1/users", json={
        "first_name": "Alice", "last_name": "It", "email": rand_email()
    })
    assert r.status_code == 201
    body = r.json()
    assert "id" in body
    assert "Location" in r.headers


@pytest.mark.req("REQ-USR-02")
def test_get_user(svc):
    email = rand_email()
    cr = req_lib.post(f"{svc}/api/v1/users", json={"first_name": "B", "last_name": "B", "email": email})
    uid = cr.json()["id"]
    r = req_lib.get(f"{svc}/api/v1/users/{uid}")
    assert r.status_code == 200
    assert r.json()["email"] == email


@pytest.mark.req("REQ-USR-B03")
def test_list_users(svc):
    req_lib.post(f"{svc}/api/v1/users", json={"first_name": "C", "last_name": "C", "email": rand_email()})
    r = req_lib.get(f"{svc}/api/v1/users")
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.req("REQ-USR-03")
def test_update_user(svc):
    email = rand_email()
    cr = req_lib.post(f"{svc}/api/v1/users", json={"first_name": "D", "last_name": "D", "email": email})
    uid = cr.json()["id"]
    r = req_lib.patch(f"{svc}/api/v1/users/{uid}", json={"first_name": "Updated"})
    assert r.status_code == 200
    assert r.json()["first_name"] == "Updated"


@pytest.mark.req("REQ-USR-04")
def test_delete_user(svc):
    email = rand_email()
    cr = req_lib.post(f"{svc}/api/v1/users", json={"first_name": "E", "last_name": "E", "email": email})
    uid = cr.json()["id"]
    r = req_lib.delete(f"{svc}/api/v1/users/{uid}")
    assert r.status_code == 204
    r2 = req_lib.get(f"{svc}/api/v1/users/{uid}")
    assert r2.status_code == 404
