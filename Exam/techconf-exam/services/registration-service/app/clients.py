"""app/clients.py — HTTP calls to user-service and event-service."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from config import get_user_service_url, get_event_service_url
import http_client as hc


def get_user(user_id: str) -> dict:
    return hc.get(f"{get_user_service_url()}/api/v1/users/{user_id}")


def get_event(event_id: str) -> dict:
    return hc.get(f"{get_event_service_url()}/api/v1/events/{event_id}")
