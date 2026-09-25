"""app/clients.py — HTTP calls to registration-service and event-service."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from config import get_registration_service_url, get_event_service_url
import http_client as hc


def check_confirmed_registration(user_id: str, event_id: str) -> bool:
    """Return True if a confirmed registration exists for (user_id, event_id)."""
    url = f"{get_registration_service_url()}/api/v1/registrations?user_id={user_id}&event_id={event_id}&status=confirmed&page_size=1"
    # We don't want 404 here — this always returns 200 with items list
    import requests
    try:
        resp = requests.get(url, timeout=2)
    except requests.exceptions.RequestException as exc:
        from errors import DependencyUnavailableError
        raise DependencyUnavailableError(f"Registration service unavailable: {exc}")
    if resp.status_code >= 500:
        from errors import DependencyUnavailableError
        raise DependencyUnavailableError("Registration service returned 5xx")
    data = resp.json()
    return len(data.get("items", [])) > 0


def get_event(event_id: str) -> dict:
    return hc.get(f"{get_event_service_url()}/api/v1/events/{event_id}")
