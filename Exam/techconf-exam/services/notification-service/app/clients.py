"""app/clients.py — HTTP calls to user-service and registration-service."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from config import get_user_service_url, get_registration_service_url
import http_client as hc
import requests


def get_user(user_id: str) -> dict:
    return hc.get(f"{get_user_service_url()}/api/v1/users/{user_id}")


def get_confirmed_registrations(event_id: str) -> list[dict]:
    """Return list of confirmed registrations for an event (handles pagination up to 1000)."""
    from errors import DependencyUnavailableError
    url = f"{get_registration_service_url()}/api/v1/registrations?event_id={event_id}&status=confirmed&page_size=100"
    try:
        resp = requests.get(url, timeout=2)
    except requests.exceptions.RequestException as exc:
        raise DependencyUnavailableError(f"Registration service unavailable: {exc}")
    if resp.status_code >= 500:
        raise DependencyUnavailableError("Registration service returned 5xx")
    return resp.json().get("items", [])
