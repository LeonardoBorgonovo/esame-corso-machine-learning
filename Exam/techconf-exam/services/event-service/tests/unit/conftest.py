"""conftest for event-service unit tests."""
import sys, os

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "shared"))

import pytest
from app import create_app
from app.repository import MemoryEventRepository, JsonEventRepository, SqliteEventRepository


@pytest.fixture
def memory_repo():
    return MemoryEventRepository()


@pytest.fixture
def json_repo(tmp_path):
    return JsonEventRepository(str(tmp_path))


@pytest.fixture
def sqlite_repo(tmp_path):
    return SqliteEventRepository(str(tmp_path))


@pytest.fixture
def app():
    return create_app(backend="memory", data_dir="/tmp/test-event")


@pytest.fixture
def client(app):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


VALID_EVENT = {
    "title": "CloudConf 2026",
    "organizer_id": "00000000-0000-0000-0000-000000000001",
    "venue": "Auditorium Roma",
    "city": "Roma",
    "start_date": "2026-10-15",
    "end_date": "2026-10-16",
    "capacity": 100,
    "price": 149.00,
}
