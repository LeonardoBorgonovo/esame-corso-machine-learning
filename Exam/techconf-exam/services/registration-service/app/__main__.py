"""Entry point: python -m app"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
from config import get_port
from app import create_app

if __name__ == "__main__":
    app = create_app()
    port = get_port(5003)
    app.run(host="0.0.0.0", port=port)
