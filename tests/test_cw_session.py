"""His own signed-in Firefox session for Instagram, found on the machine. Ruling (Krish, 2026-10-28): "Yes to both on
the two decisions". Fake Firefox profiles only: no browser, no network."""

import inspect
import json
import os
import sqlite3
import tempfile
import time
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

from content_watcher import session, watch
from content_watcher.config import Config
from content_watcher.fetch import _methods
from content_watcher.urls import parse


def make_profile(root: Path, name: str, cookies: list[tuple[str, str, int]], mtime: float | None = None) -> Path:
    profile = root / name
    profile.mkdir(parents=True)
    db = sqlite3.connect(profile / "cookies.sqlite")
    db.execute("create table moz_cookies (id integer primary key, host text, name text, value text, expiry integer)")
    db.executemany("insert into moz_cookies (host, name, value, expiry) values (?, ?, 'secret-value', ?)", cookies)
    db.commit()
    db.close()
    if mtime is not None:
        os.utime(profile / "cookies.sqlite", (mtime, mtime))
    return profile


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "Profiles"
        self.root.mkdir()
        self.env = mock.patch.dict(os.environ, {"CONTENT_WATCH_FIREFOX_PROFILES": str(self.root),
                                                "CONTENT_WATCH_HOME": str(Path(self.temp.name) / "home")})
        self.env.start()
        self.later = int(time.time()) + 86400

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_a_live_instagram_sign_in_is_found_and_an_expired_or_other_one_is_not(self):
        live = make_profile(self.root, "a.default-release", [(".instagram.com", "sessionid", self.later)])
        expired = make_profile(self.root, "b.old", [(".instagram.com", "sessionid", int(time.time()) - 60)])
        other = make_profile(self.root, "c.work", [(".example.com", "sessionid", self.later),
                                                   (".instagram.com", "csrftoken", self.later)])
        millis = make_profile(self.root, "d.new", [("instagram.com", "sessionid", self.later * 1000)])
        self.assertTrue(session.has_session(live, "instagram"))
        self.assertFalse(session.has_session(expired, "instagram"))
        self.assertFalse(session.has_session(other, "instagram"))
        self.assertTrue(session.has_session(millis, "instagram"))

    def test_the_most_recently_used_signed_in_profile_wins(self):
        make_profile(self.root, "old.default", [(".instagram.com", "sessionid", self.later)], mtime=time.time() - 3600)
        recent = make_profile(self.root, "new.default-release", [(".instagram.com", "sessionid", self.later)])
        make_profile(self.root, "newest.empty", [], mtime=time.time() + 60)
        self.assertEqual(session.signed_in_profile("instagram"), str(recent))

    def test_no_firefox_means_no_session(self):
        self.assertIsNone(session.signed_in_profile("instagram", root=self.root / "missing"))
        self.assertIsNone(session.signed_in_profile("tiktok"))

    def test_it_never_reads_a_cookie_value(self):
        source = inspect.getsource(session.has_session)
        self.assertIn("select expiry from moz_cookies", source)
        self.assertNotIn("value", source.split("select", 1)[1].split("from", 1)[0])

    def test_his_session_comes_before_anything_paid_and_only_when_found(self):
        link = parse("https://www.instagram.com/p/DfAY9PWFuEX/")
        names = [name for name, _ in _methods(link, Config())]
        self.assertNotIn("gallerydl_cookies", names)
        make_profile(self.root, "a.default-release", [(".instagram.com", "sessionid", self.later)])
        names = [name for name, _ in _methods(link, Config())]
        self.assertLess(names.index("gallerydl_cookies"), names.index("apify_instagram_post"))
        self.assertLess(names.index("instaloader"), names.index("gallerydl_cookies"))
        self.assertNotIn("gallerydl_cookies", [n for n, _ in _methods(link, Config(browser_sessions=[]))])

    def test_the_machine_says_once_an_hour_whether_it_holds_his_session(self):
        counts = Counter()
        watch.note_sessions(Config(), counts, now=1000.0)
        self.assertEqual(counts, Counter({"session.instagram.none": 1}))
        make_profile(self.root, "a.default-release", [(".instagram.com", "sessionid", self.later)])
        watch.note_sessions(Config(), counts, now=1000.0 + 600)
        self.assertEqual(counts, Counter({"session.instagram.none": 1}))  # not again within the hour
        watch.note_sessions(Config(), counts, now=1000.0 + 3700)
        self.assertEqual(counts["session.instagram.firefox"], 1)
        self.assertNotIn("default-release", json.dumps(counts))


if __name__ == "__main__":
    unittest.main()
