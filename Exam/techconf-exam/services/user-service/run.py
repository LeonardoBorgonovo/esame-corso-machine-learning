"""run.py — entry point for user-service.

Adds shared/ to sys.path before importing app, so no PYTHONPATH env var is needed.
The harness launches this with: python run.py (from services/user-service/)
"""
import sys
import os

# Resolve shared/ relative to this file: services/user-service/ -> ../../shared
_HERE = os.path.dirname(os.path.abspath(__file__))
_SHARED = os.path.normpath(os.path.join(_HERE, "..", "..", "shared"))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

from config import get_port  # noqa: E402
from app import create_app   # noqa: E402

if __name__ == "__main__":
    app = create_app()
    port = get_port(5001)
    app.run(host="0.0.0.0", port=port)
