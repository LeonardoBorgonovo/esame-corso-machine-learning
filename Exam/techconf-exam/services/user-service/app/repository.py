"""app/repository.py — UserRepository interface + three storage backends.

All backends expose the same interface so business.py never changes.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Protocol

# ── Protocol (interface) ──────────────────────────────────────────────────────

class UserRepository(Protocol):
    def create(self, user: dict) -> dict: ...
    def get(self, user_id: str) -> dict | None: ...
    def list_all(self) -> list[dict]: ...
    def update(self, user_id: str, changes: dict) -> dict | None: ...
    def delete(self, user_id: str) -> bool: ...
    def find_by_email(self, email_lower: str, exclude_id: str | None = None) -> dict | None: ...


# ── Memory backend ────────────────────────────────────────────────────────────

class MemoryUserRepository:
    def __init__(self):
        self._store: dict[str, dict] = {}

    def create(self, user: dict) -> dict:
        self._store[user["id"]] = dict(user)
        return dict(user)

    def get(self, user_id: str) -> dict | None:
        u = self._store.get(user_id)
        return dict(u) if u else None

    def list_all(self) -> list[dict]:
        return [dict(u) for u in self._store.values()]

    def update(self, user_id: str, changes: dict) -> dict | None:
        if user_id not in self._store:
            return None
        self._store[user_id].update(changes)
        return dict(self._store[user_id])

    def delete(self, user_id: str) -> bool:
        if user_id in self._store:
            del self._store[user_id]
            return True
        return False

    def find_by_email(self, email_lower: str, exclude_id: str | None = None) -> dict | None:
        for u in self._store.values():
            if u["email"] == email_lower and u["id"] != exclude_id:
                return dict(u)
        return None


# ── JSON backend ──────────────────────────────────────────────────────────────

class JsonUserRepository:
    def __init__(self, data_dir: str):
        self._dir = Path(data_dir) / "user-service"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "users.json"
        if not self._file.exists():
            self._write([])

    def _read(self) -> list[dict]:
        with self._file.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _write(self, users: list[dict]) -> None:
        tmp = self._file.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(users, fh, ensure_ascii=False)
        os.replace(tmp, self._file)

    def create(self, user: dict) -> dict:
        users = self._read()
        users.append(dict(user))
        self._write(users)
        return dict(user)

    def get(self, user_id: str) -> dict | None:
        for u in self._read():
            if u["id"] == user_id:
                return dict(u)
        return None

    def list_all(self) -> list[dict]:
        return [dict(u) for u in self._read()]

    def update(self, user_id: str, changes: dict) -> dict | None:
        users = self._read()
        for u in users:
            if u["id"] == user_id:
                u.update(changes)
                self._write(users)
                return dict(u)
        return None

    def delete(self, user_id: str) -> bool:
        users = self._read()
        new_users = [u for u in users if u["id"] != user_id]
        if len(new_users) == len(users):
            return False
        self._write(new_users)
        return True

    def find_by_email(self, email_lower: str, exclude_id: str | None = None) -> dict | None:
        for u in self._read():
            if u["email"] == email_lower and u["id"] != exclude_id:
                return dict(u)
        return None


# ── SQLite backend ────────────────────────────────────────────────────────────

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id         TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name  TEXT NOT NULL,
    email      TEXT NOT NULL,
    company    TEXT,
    role       TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_COLS = ["id", "first_name", "last_name", "email", "company", "role", "created_at", "updated_at"]


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(zip(_COLS, row))


class SqliteUserRepository:
    def __init__(self, data_dir: str):
        db_dir = Path(data_dir) / "user-service"
        db_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = str(db_dir / "users.db")
        with self._conn() as conn:
            conn.execute(_CREATE_TABLE)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, user: dict) -> dict:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                [user.get(c) for c in _COLS],
            )
        return dict(user)

    def get(self, user_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return _row_to_dict(row) if row else None

    def list_all(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM users").fetchall()
        return [_row_to_dict(r) for r in rows]

    def update(self, user_id: str, changes: dict) -> dict | None:
        if not self.get(user_id):
            return None
        cols = [k for k in changes if k in _COLS]
        if not cols:
            return self.get(user_id)
        sets = ", ".join(f"{c}=?" for c in cols)
        vals = [changes[c] for c in cols] + [user_id]
        with self._conn() as conn:
            conn.execute(f"UPDATE users SET {sets} WHERE id=?", vals)
        return self.get(user_id)

    def delete(self, user_id: str) -> bool:
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        return cur.rowcount > 0

    def find_by_email(self, email_lower: str, exclude_id: str | None = None) -> dict | None:
        with self._conn() as conn:
            if exclude_id:
                row = conn.execute(
                    "SELECT * FROM users WHERE email=? AND id!=?", (email_lower, exclude_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM users WHERE email=?", (email_lower,)
                ).fetchone()
        return _row_to_dict(row) if row else None


# ── Factory ───────────────────────────────────────────────────────────────────

def make_repository(backend: str, data_dir: str) -> UserRepository:
    if backend == "json":
        return JsonUserRepository(data_dir)
    if backend == "sqlite":
        return SqliteUserRepository(data_dir)
    return MemoryUserRepository()
