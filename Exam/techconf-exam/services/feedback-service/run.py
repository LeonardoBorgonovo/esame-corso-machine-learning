import sys, os
_SHARED = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared"))
if _SHARED not in sys.path: sys.path.insert(0, _SHARED)

from config import get_port
from app import create_app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=get_port(5004))
