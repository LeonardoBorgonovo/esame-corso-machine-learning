"""app/repository.py — RegistrationRepository interface + three backends."""
from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from typing import Protocol


class RegistrationRepository(Protocol):
    def create(self, reg: dict) -> dict: ...
    def get(self, reg_id: str) -> dict | None: ...
    def list_all(self) -> list[dict]: ...
    def update(self, reg_id: str, changes: dict) -> dict | None: ...
    def delete(self, reg_id: str) -> bool: ...
    def count_confirmed(self, event_id: str) -> int: ...
    def find_confirmed(self, user_id: str, event_id: str) -> dict | None: ...


# ── Memory ────────────────────────────────────────────────────────────────────

class MemoryRegistrationRepository:
    def __init__(self):
        self._store: dict[str, dict] = {}

    def create(self, reg: dict) -> dict:
        self._store[reg["id"]] = dict(reg)
        return dict(reg)

    def get(self, reg_id: str) -> dict | None:
        r = self._store.get(reg_id)
        return dict(r) if r else None

    def list_all(self) -> list[dict]:
        return [dict(r) for r in self._store.values()]

    def update(self, reg_id: str, changes: dict) -> dict | None:
        if reg_id not in self._store:
            return None
        self._store[reg_id].update(changes)
        return dict(self._store[reg_id])

    def delete(self, reg_id: str) -> bool:
        if reg_id in self._store:
            del self._store[reg_id]
            return True
        return False

    def count_confirmed(self, event_id: str) -> int:
        return sum(1 for r in self._store.values()
                   if r["event_id"] == event_id and r["status"] == "confirmed")

    def find_confirmed(self, user_id: str, event_id: str) -> dict | None:
        for r in self._store.values():
            if r["user_id"] == user_id and r["event_id"] == event_id and r["status"] == "confirmed":
                return dict(r)
        return None


# ── JSON ──────────────────────────────────────────────────────────────────────

class JsonRegistrationRepository:
    def __init__(self, data_dir: str):
        self._dir = Path(data_dir) / "registration-service"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "registrations.json"
        if not self._file.exists():
            self._write([])

    def _read(self) -> list[dict]:
        with self._file.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _write(self, data: list[dict]) -> None:
        tmp = self._file.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh)
        os.replace(tmp, self._file)

    def create(self, reg: dict) -> dict:
        lst = self._read(); lst.append(dict(reg)); self._write(lst); return dict(reg)

    def get(self, reg_id: str) -> dict | None:
        for r in self._read():
            if r["id"] == reg_id: return dict(r)
        return None

    def list_all(self) -> list[dict]:
        return [dict(r) for r in self._read()]

    def update(self, reg_id: str, changes: dict) -> dict | None:
        lst = self._read()
        for r in lst:
            if r["id"] == reg_id:
                r.update(changes); self._write(lst); return dict(r)
        return None

    def delete(self, reg_id: str) -> bool:
        lst = self._read()
        new_lst = [r for r in lst if r["id"] != reg_id]
        if len(new_lst) == len(lst): return False
        self._write(new_lst); return True

    def count_confirmed(self, event_id: str) -> int:
        return sum(1 for r in self._read()
                   if r["event_id"] == event_id and r["status"] == "confirmed")

    def find_confirmed(self, user_id: str, event_id: str) -> dict | None:
        for r in self._read():
            if r["user_id"] == user_id and r["event_id"] == event_id and r["status"] == "confirmed":
                return dict(r)
        return None


# ── SQLite ────────────────────────────────────────────────────────────────────

_COLS = ["id", "user_id", "event_id", "amount", "status", "created_at", "updated_at"]

_CREATE = """
CREATE TABLE IF NOT EXISTS registrations (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL,
    event_id   TEXT NOT NULL,
    amount     REAL NOT NULL,
    status     TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def _row(r) -> dict:
    d = dict(zip(_COLS, r))
    d["amount"] = float(d["amount"])
    return d


class SqliteRegistrationRepository:
    def __init__(self, data_dir: str):
        db_dir = Path(data_dir) / "registration-service"
        db_dir.mkdir(parents=True, exist_ok=True)
        self._db = str(db_dir / "registrations.db")
        with self._conn() as c: c.execute(_CREATE)

    def _conn(self):
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, reg: dict) -> dict:
        with self._conn() as c:
            c.execute("INSERT INTO registrations VALUES (?,?,?,?,?,?,?)",
                      [reg.get(col) for col in _COLS])
        return dict(reg)

    def get(self, reg_id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM registrations WHERE id=?", (reg_id,)).fetchone()
        return _row(row) if row else None

    def list_all(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM registrations").fetchall()
        return [_row(r) for r in rows]

    def update(self, reg_id: str, changes: dict) -> dict | None:
        if not self.get(reg_id): return None
        cols = [k for k in changes if k in _COLS]
        if not cols: return self.get(reg_id)
        sets = ", ".join(f"{col}=?" for col in cols)
        vals = [changes[c] for c in cols] + [reg_id]
        with self._conn() as c: c.execute(f"UPDATE registrations SET {sets} WHERE id=?", vals)
        return self.get(reg_id)

    def delete(self, reg_id: str) -> bool:
        with self._conn() as c:
            cur = c.execute("DELETE FROM registrations WHERE id=?", (reg_id,))
        return cur.rowcount > 0

    def count_confirmed(self, event_id: str) -> int:
        with self._conn() as c:
            row = c.execute("SELECT COUNT(*) FROM registrations WHERE event_id=? AND status='confirmed'",
                            (event_id,)).fetchone()
        return row[0]

    def find_confirmed(self, user_id: str, event_id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM registrations WHERE user_id=? AND event_id=? AND status='confirmed'",
                (user_id, event_id)).fetchone()
        return _row(row) if row else None


def make_repository(backend: str, data_dir: str) -> RegistrationRepository:
    if backend == "json": return JsonRegistrationRepository(data_dir)
    if backend == "sqlite": return SqliteRegistrationRepository(data_dir)
    return MemoryRegistrationRepository()
