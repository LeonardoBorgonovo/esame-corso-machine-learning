import sys, os
_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "shared"))
import pytest
from app import create_app

@pytest.fixture
def app(): return create_app(backend="memory", data_dir="/tmp/test-ntf")

@pytest.fixture
def client(app):
    app.config["TESTING"] = True
    with app.test_client() as c: yield c
