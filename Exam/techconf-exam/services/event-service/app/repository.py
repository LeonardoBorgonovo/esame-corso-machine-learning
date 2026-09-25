"""app/repository.py — EventRepository interface + three storage backends."""
from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from typing import Protocol

# ── Protocol ──────────────────────────────────────────────────────────────────

class EventRepository(Protocol):
    def create(self, event: dict) -> dict: ...
    def get(self, event_id: str) -> dict | None: ...
    def list_all(self) -> list[dict]: ...
    def update(self, event_id: str, changes: dict) -> dict | None: ...
    def delete(self, event_id: str) -> bool: ...


# ── Memory ────────────────────────────────────────────────────────────────────

class MemoryEventRepository:
    def __init__(self):
        self._store: dict[str, dict] = {}

    def create(self, event: dict) -> dict:
        self._store[event["id"]] = dict(event)
        return dict(event)

    def get(self, event_id: str) -> dict | None:
        e = self._store.get(event_id)
        return dict(e) if e else None

    def list_all(self) -> list[dict]:
        return [dict(e) for e in self._store.values()]

    def update(self, event_id: str, changes: dict) -> dict | None:
        if event_id not in self._store:
            return None
        self._store[event_id].update(changes)
        return dict(self._store[event_id])

    def delete(self, event_id: str) -> bool:
        if event_id in self._store:
            del self._store[event_id]
            return True
        return False


# ── JSON ──────────────────────────────────────────────────────────────────────

class JsonEventRepository:
    def __init__(self, data_dir: str):
        self._dir = Path(data_dir) / "event-service"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "events.json"
        if not self._file.exists():
            self._write([])

    def _read(self) -> list[dict]:
        with self._file.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _write(self, events: list[dict]) -> None:
        tmp = self._file.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(events, fh, ensure_ascii=False)
        os.replace(tmp, self._file)

    def create(self, event: dict) -> dict:
        events = self._read()
        events.append(dict(event))
        self._write(events)
        return dict(event)

    def get(self, event_id: str) -> dict | None:
        for e in self._read():
            if e["id"] == event_id:
                return dict(e)
        return None

    def list_all(self) -> list[dict]:
        return [dict(e) for e in self._read()]

    def update(self, event_id: str, changes: dict) -> dict | None:
        events = self._read()
        for e in events:
            if e["id"] == event_id:
                e.update(changes)
                self._write(events)
                return dict(e)
        return None

    def delete(self, event_id: str) -> bool:
        events = self._read()
        new_events = [e for e in events if e["id"] != event_id]
        if len(new_events) == len(events):
            return False
        self._write(new_events)
        return True


# ── SQLite ────────────────────────────────────────────────────────────────────

_COLS = ["id", "title", "description", "organizer_id", "venue", "city",
         "start_date", "end_date", "capacity", "price", "status", "created_at", "updated_at"]

_CREATE = """
CREATE TABLE IF NOT EXISTS events (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT,
    organizer_id TEXT NOT NULL,
    venue        TEXT NOT NULL,
    city         TEXT NOT NULL,
    start_date   TEXT NOT NULL,
    end_date     TEXT NOT NULL,
    capacity     INTEGER NOT NULL,
    price        REAL NOT NULL,
    status       TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
)
"""


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(zip(_COLS, row))
    d["capacity"] = int(d["capacity"])
    d["price"] = float(d["price"])
    return d


class SqliteEventRepository:
    def __init__(self, data_dir: str):
        db_dir = Path(data_dir) / "event-service"
        db_dir.mkdir(parents=True, exist_ok=True)
        self._db = str(db_dir / "events.db")
        with self._conn() as c:
            c.execute(_CREATE)

    def _conn(self):
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, event: dict) -> dict:
        with self._conn() as c:
            c.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      [event.get(col) for col in _COLS])
        return dict(event)

    def get(self, event_id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        return _row_to_dict(row) if row else None

    def list_all(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM events").fetchall()
        return [_row_to_dict(r) for r in rows]

    def update(self, event_id: str, changes: dict) -> dict | None:
        if not self.get(event_id):
            return None
        cols = [k for k in changes if k in _COLS]
        if not cols:
            return self.get(event_id)
        sets = ", ".join(f"{col}=?" for col in cols)
        vals = [changes[col] for col in cols] + [event_id]
        with self._conn() as c:
            c.execute(f"UPDATE events SET {sets} WHERE id=?", vals)
        return self.get(event_id)

    def delete(self, event_id: str) -> bool:
        with self._conn() as c:
            cur = c.execute("DELETE FROM events WHERE id=?", (event_id,))
        return cur.rowcount > 0


# ── Factory ───────────────────────────────────────────────────────────────────

def make_repository(backend: str, data_dir: str) -> EventRepository:
    if backend == "json":
        return JsonEventRepository(data_dir)
    if backend == "sqlite":
        return SqliteEventRepository(data_dir)
    return MemoryEventRepository()
