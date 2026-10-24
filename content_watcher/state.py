"""What this machine has already done: hashed files and sent readings. SQLite, on this machine only."""

from __future__ import annotations

import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from . import tools
from .config import state_dir


class State:
    def __init__(self, path: Path | None = None):
        self.path = path or state_dir() / "state.sqlite"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.executescript(
            """
            create table if not exists files (path text primary key, size integer, mtime real, sha256 text);
            create table if not exists reads (sha256 text primary key, engine_rev text, sent_at real);
            """
        )

    def sha_of(self, path: Path) -> str:
        stat = path.stat()
        row = self.db.execute("select size, mtime, sha256 from files where path = ?", (str(path),)).fetchone()
        if row and row[0] == stat.st_size and abs(row[1] - stat.st_mtime) < 1e-6:
            return row[2]
        sha = tools.sha256_file(path)
        self.db.execute("insert or replace into files values (?, ?, ?, ?)", (str(path), stat.st_size, stat.st_mtime, sha))
        self.db.commit()
        return sha

    def read_sent(self, sha: str, engine_rev: str) -> bool:
        row = self.db.execute("select engine_rev from reads where sha256 = ?", (sha,)).fetchone()
        return bool(row and row[0] == engine_rev)

    def mark_sent(self, sha: str, engine_rev: str) -> None:
        self.db.execute("insert or replace into reads values (?, ?, ?)", (sha, engine_rev, time.time()))
        self.db.commit()

    def close(self) -> None:
        self.db.close()


@contextmanager
def run_lock(stale_after: float = 7200):
    """One watch run at a time on this machine; a lock older than two hours is taken over."""
    target = state_dir() / "watch.lock"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and time.time() - target.stat().st_mtime > stale_after:
        target.unlink(missing_ok=True)
    try:
        handle = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        yield False
        return
    try:
        os.write(handle, str(os.getpid()).encode())
        os.close(handle)
        yield True
    finally:
        target.unlink(missing_ok=True)
