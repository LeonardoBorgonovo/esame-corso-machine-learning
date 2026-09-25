"""shared/config.py — centralised environment variable reading.

Every service imports from here. No service reads os.environ directly.
"""
import os

# ── Port ─────────────────────────────────────────────────────────────────────
def get_port(default: int) -> int:
    return int(os.environ.get("PORT", default))

# ── Storage ───────────────────────────────────────────────────────────────────
def get_storage_backend() -> str:
    return os.environ.get("STORAGE_BACKEND", "memory").lower()

def get_data_dir() -> str:
    return os.environ.get("DATA_DIR", "./data")

# ── Inter-service URLs ────────────────────────────────────────────────────────
def get_user_service_url() -> str:
    return os.environ.get("USER_SERVICE_URL", "http://localhost:5001")

def get_event_service_url() -> str:
    return os.environ.get("EVENT_SERVICE_URL", "http://localhost:5002")

def get_registration_service_url() -> str:
    return os.environ.get("REGISTRATION_SERVICE_URL", "http://localhost:5003")

def get_feedback_service_url() -> str:
    return os.environ.get("FEEDBACK_SERVICE_URL", "http://localhost:5004")

def get_notification_service_url() -> str:
    return os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5005")
