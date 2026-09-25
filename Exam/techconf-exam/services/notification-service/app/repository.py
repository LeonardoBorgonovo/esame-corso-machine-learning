"""app/repository.py — NotificationRepository + three backends."""
from __future__ import annotations
import json, os, sqlite3
from pathlib import Path
from typing import Protocol


class NotificationRepository(Protocol):
    def create(self, n: dict) -> dict: ...
    def get(self, nid: str) -> dict | None: ...
    def list_all(self) -> list[dict]: ...
    def update(self, nid: str, changes: dict) -> dict | None: ...
    def delete(self, nid: str) -> bool: ...


class MemoryNotificationRepository:
    def __init__(self): self._s: dict[str, dict] = {}
    def create(self, n): self._s[n["id"]] = dict(n); return dict(n)
    def get(self, nid): x = self._s.get(nid); return dict(x) if x else None
    def list_all(self): return [dict(x) for x in self._s.values()]
    def update(self, nid, ch):
        if nid not in self._s: return None
        self._s[nid].update(ch); return dict(self._s[nid])
    def delete(self, nid):
        if nid in self._s: del self._s[nid]; return True
        return False


class JsonNotificationRepository:
    def __init__(self, data_dir):
        self._dir = Path(data_dir) / "notification-service"; self._dir.mkdir(parents=True, exist_ok=True)
        self._f = self._dir / "notifications.json"
        if not self._f.exists(): self._write([])
    def _read(self):
        with self._f.open() as fh: return json.load(fh)
    def _write(self, d):
        t = self._f.with_suffix(".tmp")
        with t.open("w") as fh: json.dump(d, fh)
        os.replace(t, self._f)
    def create(self, n): lst = self._read(); lst.append(dict(n)); self._write(lst); return dict(n)
    def get(self, nid):
        for x in self._read():
            if x["id"] == nid: return dict(x)
        return None
    def list_all(self): return [dict(x) for x in self._read()]
    def update(self, nid, ch):
        lst = self._read()
        for x in lst:
            if x["id"] == nid: x.update(ch); self._write(lst); return dict(x)
        return None
    def delete(self, nid):
        lst = self._read(); nl = [x for x in lst if x["id"] != nid]
        if len(nl) == len(lst): return False
        self._write(nl); return True


_COLS = ["id", "user_id", "channel", "subject", "body", "status", "sent_at", "created_at", "updated_at"]
_CREATE = """CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY, user_id TEXT, channel TEXT, subject TEXT, body TEXT,
    status TEXT, sent_at TEXT, created_at TEXT, updated_at TEXT)"""


class SqliteNotificationRepository:
    def __init__(self, data_dir):
        db_dir = Path(data_dir) / "notification-service"; db_dir.mkdir(parents=True, exist_ok=True)
        self._db = str(db_dir / "notifications.db")
        with self._conn() as c: c.execute(_CREATE)
    def _conn(self):
        conn = sqlite3.connect(self._db); conn.row_factory = sqlite3.Row; return conn
    def _row(self, r): return dict(zip(_COLS, r)) if r else None
    def create(self, n):
        with self._conn() as c: c.execute("INSERT INTO notifications VALUES(?,?,?,?,?,?,?,?,?)", [n.get(k) for k in _COLS])
        return dict(n)
    def get(self, nid):
        with self._conn() as c: r = c.execute("SELECT * FROM notifications WHERE id=?", (nid,)).fetchone()
        return self._row(r)
    def list_all(self):
        with self._conn() as c: rows = c.execute("SELECT * FROM notifications").fetchall()
        return [self._row(r) for r in rows]
    def update(self, nid, ch):
        if not self.get(nid): return None
        cols = [k for k in ch if k in _COLS]; sets = ", ".join(f"{c}=?" for c in cols)
        with self._conn() as c: c.execute(f"UPDATE notifications SET {sets} WHERE id=?", [ch[c] for c in cols] + [nid])
        return self.get(nid)
    def delete(self, nid):
        with self._conn() as c: cur = c.execute("DELETE FROM notifications WHERE id=?", (nid,))
        return cur.rowcount > 0


def make_repository(backend, data_dir):
    if backend == "json": return JsonNotificationRepository(data_dir)
    if backend == "sqlite": return SqliteNotificationRepository(data_dir)
    return MemoryNotificationRepository()
