import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
from config import get_port
from app import create_app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=get_port(5005))
