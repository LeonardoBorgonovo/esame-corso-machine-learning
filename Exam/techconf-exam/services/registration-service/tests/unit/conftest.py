"""conftest for registration-service unit tests."""
import sys, os

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "shared"))

import pytest
from app import create_app
from app.repository import MemoryRegistrationRepository, JsonRegistrationRepository, SqliteRegistrationRepository

USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
EVENT_ID = "bbbbbbbb-0000-0000-0000-000000000002"
USER_URL = "http://localhost:5001"
EVENT_URL = "http://localhost:5002"


@pytest.fixture
def memory_repo():
    return MemoryRegistrationRepository()


@pytest.fixture
def json_repo(tmp_path):
    return JsonRegistrationRepository(str(tmp_path))


@pytest.fixture
def sqlite_repo(tmp_path):
    return SqliteRegistrationRepository(str(tmp_path))


@pytest.fixture
def app():
    return create_app(backend="memory", data_dir="/tmp/test-reg")


@pytest.fixture
def client(app):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
