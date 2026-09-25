"""app/clients.py — HTTP calls to user-service (isolated for mocking in tests)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from config import get_user_service_url  # noqa: E402
import http_client as hc  # noqa: E402


def get_user(user_id: str) -> dict:
    """Fetch user from user-service. Raises ReferenceNotFoundError or DependencyUnavailableError."""
    url = f"{get_user_service_url()}/api/v1/users/{user_id}"
    return hc.get(url)
