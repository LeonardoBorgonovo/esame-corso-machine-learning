"""app/repository.py — FeedbackRepository + three backends."""
from __future__ import annotations
import json, os, sqlite3
from pathlib import Path
from typing import Protocol


class FeedbackRepository(Protocol):
    def create(self, fb: dict) -> dict: ...
    def get(self, fb_id: str) -> dict | None: ...
    def list_all(self) -> list[dict]: ...
    def update(self, fb_id: str, changes: dict) -> dict | None: ...
    def delete(self, fb_id: str) -> bool: ...
    def find_by_user_event(self, user_id: str, event_id: str) -> dict | None: ...


class MemoryFeedbackRepository:
    def __init__(self): self._s: dict[str, dict] = {}
    def create(self, fb): self._s[fb["id"]] = dict(fb); return dict(fb)
    def get(self, fid): f = self._s.get(fid); return dict(f) if f else None
    def list_all(self): return [dict(f) for f in self._s.values()]
    def update(self, fid, ch):
        if fid not in self._s: return None
        self._s[fid].update(ch); return dict(self._s[fid])
    def delete(self, fid):
        if fid in self._s: del self._s[fid]; return True
        return False
    def find_by_user_event(self, uid, eid):
        for f in self._s.values():
            if f["user_id"] == uid and f["event_id"] == eid: return dict(f)
        return None


class JsonFeedbackRepository:
    def __init__(self, data_dir):
        self._dir = Path(data_dir) / "feedback-service"; self._dir.mkdir(parents=True, exist_ok=True)
        self._f = self._dir / "feedbacks.json"
        if not self._f.exists(): self._write([])
    def _read(self): 
        with self._f.open() as fh: return json.load(fh)
    def _write(self, d):
        t = self._f.with_suffix(".tmp")
        with t.open("w") as fh: json.dump(d, fh)
        os.replace(t, self._f)
    def create(self, fb): lst = self._read(); lst.append(dict(fb)); self._write(lst); return dict(fb)
    def get(self, fid):
        for f in self._read():
            if f["id"] == fid: return dict(f)
        return None
    def list_all(self): return [dict(f) for f in self._read()]
    def update(self, fid, ch):
        lst = self._read()
        for f in lst:
            if f["id"] == fid: f.update(ch); self._write(lst); return dict(f)
        return None
    def delete(self, fid):
        lst = self._read(); nl = [f for f in lst if f["id"] != fid]
        if len(nl) == len(lst): return False
        self._write(nl); return True
    def find_by_user_event(self, uid, eid):
        for f in self._read():
            if f["user_id"] == uid and f["event_id"] == eid: return dict(f)
        return None


_COLS = ["id", "user_id", "event_id", "rating", "comment", "created_at", "updated_at"]
_CREATE = """CREATE TABLE IF NOT EXISTS feedbacks (
    id TEXT PRIMARY KEY, user_id TEXT, event_id TEXT, rating INTEGER,
    comment TEXT, created_at TEXT, updated_at TEXT)"""


class SqliteFeedbackRepository:
    def __init__(self, data_dir):
        db_dir = Path(data_dir) / "feedback-service"; db_dir.mkdir(parents=True, exist_ok=True)
        self._db = str(db_dir / "feedbacks.db")
        with self._conn() as c: c.execute(_CREATE)
    def _conn(self):
        conn = sqlite3.connect(self._db); conn.row_factory = sqlite3.Row; return conn
    def _row(self, r): return dict(zip(_COLS, r)) if r else None
    def create(self, fb):
        with self._conn() as c: c.execute("INSERT INTO feedbacks VALUES(?,?,?,?,?,?,?)", [fb.get(k) for k in _COLS])
        return dict(fb)
    def get(self, fid):
        with self._conn() as c: r = c.execute("SELECT * FROM feedbacks WHERE id=?", (fid,)).fetchone()
        return self._row(r)
    def list_all(self):
        with self._conn() as c: rows = c.execute("SELECT * FROM feedbacks").fetchall()
        return [self._row(r) for r in rows]
    def update(self, fid, ch):
        if not self.get(fid): return None
        cols = [k for k in ch if k in _COLS]; sets = ", ".join(f"{c}=?" for c in cols)
        with self._conn() as c: c.execute(f"UPDATE feedbacks SET {sets} WHERE id=?", [ch[c] for c in cols] + [fid])
        return self.get(fid)
    def delete(self, fid):
        with self._conn() as c: cur = c.execute("DELETE FROM feedbacks WHERE id=?", (fid,))
        return cur.rowcount > 0
    def find_by_user_event(self, uid, eid):
        with self._conn() as c:
            r = c.execute("SELECT * FROM feedbacks WHERE user_id=? AND event_id=?", (uid, eid)).fetchone()
        return self._row(r)


def make_repository(backend, data_dir):
    if backend == "json": return JsonFeedbackRepository(data_dir)
    if backend == "sqlite": return SqliteFeedbackRepository(data_dir)
    return MemoryFeedbackRepository()
