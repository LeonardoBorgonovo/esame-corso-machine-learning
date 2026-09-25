"""conftest.py for user-service unit tests."""
import sys, os

# Make shared/ and services/user-service importable
_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "shared"))

import pytest
from app import create_app
from app.repository import MemoryUserRepository, JsonUserRepository, SqliteUserRepository


@pytest.fixture
def memory_repo():
    return MemoryUserRepository()


@pytest.fixture
def json_repo(tmp_path):
    return JsonUserRepository(str(tmp_path))


@pytest.fixture
def sqlite_repo(tmp_path):
    return SqliteUserRepository(str(tmp_path))


@pytest.fixture
def app():
    return create_app(backend="memory", data_dir="/tmp/test-user")


@pytest.fixture
def client(app):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
