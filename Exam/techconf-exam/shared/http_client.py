"""shared/http_client.py — standard inter-service HTTP client.

Wraps requests with:
  - 2 s timeout (platform standard)
  - 404 from dependency  → raises ReferenceNotFoundError (422)
  - timeout / refused / 5xx → raises DependencyUnavailableError (503)
"""
from __future__ import annotations
import requests
from errors import ReferenceNotFoundError, DependencyUnavailableError

TIMEOUT = 2  # seconds


def get(url: str, **kwargs) -> dict:
    """GET url, return parsed JSON body.

    Raises ReferenceNotFoundError on 404, DependencyUnavailableError on any
    network problem or 5xx.
    """
    try:
        resp = requests.get(url, timeout=TIMEOUT, **kwargs)
    except requests.exceptions.RequestException as exc:
        raise DependencyUnavailableError(f"Dependency unavailable: {exc}") from exc

    if resp.status_code == 404:
        raise ReferenceNotFoundError(f"Reference not found at {url}")
    if resp.status_code >= 500:
        raise DependencyUnavailableError(f"Dependency returned {resp.status_code}")
    return resp.json()
