"""Krish's own signed-in Instagram session in Firefox on this machine, for posts only a signed-in account can see.

Ruling (Krish, 2026-10-28): "Yes to both on the two decisions", the second being whether a home computer may use his
logged-in Instagram session from Firefox for posts like his age-restricted carousel. So the watcher looks for a Firefox
profile holding a live Instagram sign-in and hands that profile to gallery-dl, which reads the cookies itself.

This module only asks whether such a cookie exists and has not expired: it reads the cookie's host, name and expiry,
never its value, and it writes nothing. Nothing here signs in, posts, likes or follows.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

SESSION_COOKIES = {"instagram": ("instagram.com", "sessionid")}


def firefox_root() -> Path:
    override = os.environ.get("CONTENT_WATCH_FIREFOX_PROFILES")
    if override:
        return Path(override)
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles"
    return Path.home() / ".mozilla" / "firefox"


def _profiles(root: Path) -> list[Path]:
    """Profile folders holding a cookie store, the most recently used first."""
    if not root.is_dir():
        return []
    found = [p for p in root.iterdir() if p.is_dir() and (p / "cookies.sqlite").is_file()]
    return sorted(found, key=lambda p: (p / "cookies.sqlite").stat().st_mtime, reverse=True)


def has_session(profile: Path, platform: str, now: float | None = None) -> bool:
    """Whether this profile holds an unexpired sign-in cookie for the platform. Firefox keeps its store open, so a
    copy is read (with its write-ahead log), and only the host, name and expiry columns."""
    domain, name = SESSION_COOKIES[platform]
    now = time.time() if now is None else now
    with tempfile.TemporaryDirectory(prefix="cw-session-") as tmp:
        copy = Path(tmp) / "cookies.sqlite"
        try:
            shutil.copyfile(profile / "cookies.sqlite", copy)
            wal = profile / "cookies.sqlite-wal"
            if wal.is_file():
                shutil.copyfile(wal, Path(tmp) / "cookies.sqlite-wal")
            connection = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
        except (OSError, sqlite3.Error):
            return False
        try:
            rows = connection.execute(
                "select expiry from moz_cookies where name = ? and (host = ? or host like ?)",
                (name, domain, f"%.{domain}"),
            ).fetchall()
        except sqlite3.Error:
            return False
        finally:
            connection.close()
    # Firefox has stored expiry in seconds and, in newer builds, milliseconds; either way a live one is past now.
    return any(isinstance(expiry, (int, float)) and expiry > now for (expiry,) in rows)


def signed_in_profile(platform: str, root: Path | None = None) -> str | None:
    """The folder of the most recently used Firefox profile signed in to the platform, or None."""
    if platform not in SESSION_COOKIES:
        return None
    for profile in _profiles(root or firefox_root()):
        if has_session(profile, platform):
            return str(profile)
    return None
