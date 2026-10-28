"""Filing, the engine client and one watch run end to end, against a stub engine on localhost."""

import json
from collections import Counter
import os
import shutil
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

from content_watcher import tools, watch
from content_watcher.config import Config
from content_watcher.engine import Engine, EngineError
from content_watcher.fetch import FetchResult
from content_watcher.fetch import Attempt
from content_watcher.filing import FilingError, file_one, file_post, folder_for
from content_watcher.post import Post
from tests.cw_helpers import FFMPEG, make_image, make_video


class StubEngine:
    def __init__(self, queue, held=None):
        self.queue = list(queue)
        self.held = dict(held or {})  # sha -> engine_rev of a reading the engine already holds
        self.calls = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                stub.calls.append((self.path, body, self.headers.get("Authorization")))
                if self.headers.get("Authorization") != "Bearer test-key":
                    self.send_response(401)
                    self.end_headers()
                    return
                answer = {}
                if self.path == "/api/watch/claim":
                    answer = {"requests": stub.queue[: body["limit"]]}
                    stub.queue = stub.queue[body["limit"]:]
                if self.path == "/api/watch/read" and "check" in body:
                    # The engine's rule (heldReads): the same or a newer revision; a test's revisions share one shape.
                    answer = {"held": {sha: stub.held[sha] for sha in body["check"]
                                       if sha in stub.held and stub.held[sha] >= body["engine_rev"]}}
                payload = json.dumps(answer).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()

    def paths(self):
        return [path for path, _, _ in self.calls]


class FilingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_same_bytes_is_a_no_op_and_different_bytes_never_overwrite(self):
        source = self.root / "instagram_A.mp4"
        source.write_bytes(b"first")
        target_dir = self.root / "drive"
        first, sha = file_one(source, target_dir)
        again, sha_again = file_one(source, target_dir)
        self.assertEqual((first, sha), (again, sha_again))
        self.assertEqual(sha, tools.sha256_file(source))
        source.write_bytes(b"second, different")
        other, _ = file_one(source, target_dir)
        self.assertEqual(other.name, "instagram_A_v2.mp4")
        self.assertEqual(first.read_bytes(), b"first")
        self.assertEqual(sorted(p.name for p in target_dir.iterdir()), ["instagram_A.mp4", "instagram_A_v2.mp4"])

    def test_folders_by_shape_and_lane(self):
        self.assertEqual(folder_for("video", None), "video_inspiration")
        self.assertEqual(folder_for("carousel", None), "cold_ideas")
        self.assertEqual(folder_for("text", None), "cold_ideas")
        self.assertEqual(folder_for("carousel", "production"), "video_inspiration")
        self.assertEqual(folder_for("video", "strategy"), "cold_ideas")

    def test_drive_is_the_default_and_needs_its_folders_set(self):
        clip = self.root / "tiktok_1.mp4"
        clip.write_bytes(b"x")
        self.assertEqual(Config().filing, "drive")
        with self.assertRaises(FilingError) as failure:
            file_post(Post("tiktok", "u", "1", media=[clip]), Config())
        self.assertEqual(failure.exception.status_class, "folder_not_set")

    def test_drive_filing_needs_the_folder_to_exist(self):
        clip = self.root / "tiktok_1.mp4"
        clip.write_bytes(b"x")
        post = Post("tiktok", "u", "1", media=[clip])
        config = Config(filing="drive", video_inspiration=str(self.root / "missing"))
        with self.assertRaises(FilingError) as failure:
            file_post(post, config)
        self.assertEqual(failure.exception.status_class, "drive_folder_missing")
        (self.root / "missing").mkdir()
        media = file_post(post, config)
        self.assertEqual(media[0]["folder"], "video_inspiration")
        self.assertEqual(media[0]["mime"], "video/mp4")
        self.assertEqual(media[0]["bytes"], 1)


class EngineClientTests(unittest.TestCase):
    def test_wrong_key_and_no_key_are_classes(self):
        stub = StubEngine([])
        try:
            with self.assertRaises(EngineError) as refused:
                Engine(stub.url, "wrong").claim("pc", 1)
            self.assertEqual(refused.exception.status_class, "engine_refused_key")
            with self.assertRaises(EngineError) as none:
                Engine(stub.url, "").claim("pc", 1)
            self.assertEqual(none.exception.status_class, "no_engine_key")
        finally:
            stub.close()


@unittest.skipUnless(FFMPEG, "FFmpeg is required")
class WatchOnceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = mock.patch.dict(os.environ, {"CONTENT_WATCH_HOME": str(self.root / "home"),
                                                "MINDMAKE_ENGINE_TOKEN": "test-key"})
        self.env.start()
        self.videos = self.root / "Production Inspo"
        self.cold = self.root / "Content Inspo"
        self.videos.mkdir()
        self.cold.mkdir()
        self.config = Config(filing="drive", video_inspiration=str(self.videos), cold_ideas=str(self.cold),
                             machine="test-pc", whisper_model="tiny")
        self.clip = make_video(self.root / "source.mp4", seconds=2, text="HOOK")

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def fake_fetch(self, url, dest, config):
        folder = dest / "instagram_DAbC"
        folder.mkdir(parents=True)
        shutil.copy(self.clip, folder / "instagram_DAbC.mp4")
        post = Post("instagram", url, "DAbC", "studio.example", caption="three edits",
                    media=[folder / "instagram_DAbC.mp4"], method="ytdlp", shape="video")
        post.save(folder)
        return FetchResult(post, [Attempt("ytdlp", "ok")])

    def test_a_pasted_link_is_filed_read_and_reported(self):
        stub = StubEngine([{"id": "req-1", "url": "https://www.instagram.com/reel/DAbC/", "lane": None,
                            "platform": "instagram", "attempts": 1}])
        try:
            with mock.patch.object(watch, "fetch", side_effect=self.fake_fetch):
                counts = watch.watch_once(self.config, Engine(stub.url))
        finally:
            stub.close()
        self.assertEqual(counts["claimed"], 1)
        self.assertEqual(counts["read"], 1)
        self.assertEqual(stub.paths(), ["/api/watch/claim", "/api/watch/report", "/api/watch/report"])
        filed = stub.calls[1][1]
        read = stub.calls[2][1]
        self.assertEqual((filed["status"], filed["shape"]), ("filed", "video"))
        self.assertEqual(read["status"], "read")
        media = filed["media"][0]
        on_drive = self.videos / media["name"]
        self.assertTrue(on_drive.is_file())
        self.assertEqual(media["sha256"], tools.sha256_file(on_drive))  # the hash of the bytes as filed
        self.assertEqual(media["folder"], "video_inspiration")
        row = read["reads"][0]
        self.assertEqual(row["sha256"], media["sha256"])
        self.assertEqual(row["read"]["post"]["author"], "studio.example")
        self.assertIn(row["read"]["heard"], ("words", "silent", "failed"))
        self.assertIn("words_text", row["read"])
        self.assertLessEqual(len(row["read_md"]), 40_000)
        # The filed clip is now known, so the drop scan does not read it a second time.
        self.assertNotIn("drop.read", counts)

    def test_a_second_try_reuses_the_file_the_first_filed(self):
        filed = {"name": "instagram_DAbC.mp4", "sha256": "e" * 64, "mime": "video/mp4", "bytes": 9,
                 "folder": "video_inspiration"}
        stub = StubEngine([{"id": "req-3", "url": "https://www.instagram.com/reel/DAbC/", "lane": None,
                            "media": [filed]}])
        try:
            with mock.patch.object(watch, "fetch", side_effect=self.fake_fetch):
                counts = watch.watch_once(self.config, Engine(stub.url))
        finally:
            stub.close()
        self.assertEqual(counts["read"], 1)
        self.assertEqual(list(self.videos.iterdir()), [])  # nothing copied a second time
        self.assertEqual(stub.calls[1][1]["media"], [filed])
        self.assertEqual(stub.calls[2][1]["reads"][0]["sha256"], "e" * 64)

    def test_a_failed_fetch_reports_its_class(self):
        stub = StubEngine([{"id": "req-2", "url": "https://www.instagram.com/reel/gone/", "lane": None}])
        failed = FetchResult(None, [Attempt("ytdlp", "not_found:not_found")], "not_found", "not_found")
        try:
            with mock.patch.object(watch, "fetch", return_value=failed):
                counts = watch.watch_once(self.config, Engine(stub.url))
        finally:
            stub.close()
        report = stub.calls[1][1]
        self.assertEqual((report["status"], report["status_class"]), ("failed", "not_found"))
        self.assertEqual(counts["failed.not_found"], 1)

    def test_hand_dropped_files_are_read_once(self):
        shutil.copy(self.clip, self.videos / "dropped.mp4")
        make_image(self.cold / "slide.png", "COLD IDEA")
        stub = StubEngine([])
        try:
            first = watch.watch_once(self.config, Engine(stub.url))
            second = watch.watch_once(self.config, Engine(stub.url))
        finally:
            stub.close()
        self.assertEqual(first["drop.read"], 2)
        self.assertNotIn("drop.read", second)
        reads = [body for path, body, _ in stub.calls if path == "/api/watch/read" and "reads" in body]
        self.assertEqual(len(reads), 2)
        shas = {body["reads"][0]["sha256"] for body in reads}
        self.assertIn(tools.sha256_file(self.videos / "dropped.mp4"), shas)

    def test_a_file_the_engine_already_holds_is_never_read_again(self):
        # What the other machine filed from a link and read: the engine says so, and this machine does no work on it.
        shutil.copy(self.clip, self.videos / "instagram_DAbC.mp4")
        make_image(self.cold / "slide.png", "COLD IDEA")
        held = {tools.sha256_file(self.videos / "instagram_DAbC.mp4"): watch.ENGINE_REV}
        stub = StubEngine([], held=held)
        try:
            with mock.patch.object(watch, "read_path", wraps=watch.read_path) as reader:
                first = watch.watch_once(self.config, Engine(stub.url))
                second = watch.watch_once(self.config, Engine(stub.url))
        finally:
            stub.close()
        self.assertEqual((first["drop.held"], first["drop.read"]), (1, 1))
        self.assertEqual([call.args[0].name for call in reader.call_args_list], ["slide.png"])
        self.assertNotIn("drop.read", second)
        self.assertNotIn("drop.held", second)  # marked read here, so not even asked again

    def test_an_older_reading_or_a_silent_engine_still_reads(self):
        shutil.copy(self.clip, self.videos / "dropped.mp4")
        stub = StubEngine([], held={tools.sha256_file(self.videos / "dropped.mp4"): "cw-2026.01.01"})
        try:
            counts = watch.watch_once(self.config, Engine(stub.url))
        finally:
            stub.close()
        self.assertEqual(counts["drop.read"], 1)

        make_image(self.cold / "slide.png", "COLD IDEA")

        class Silent(Engine):
            def held(self, machine, shas, engine_rev):
                raise EngineError("engine_http_400")  # an engine from before the check

        stub = StubEngine([])
        try:
            counts = watch.watch_once(self.config, Silent(stub.url))
        finally:
            stub.close()
        self.assertEqual((counts["drop.held_unknown"], counts["drop.read"]), (1, 1))
        self.assertFalse(any(key.startswith("engine.") for key in counts))

    def test_log_carries_counts_and_classes_only(self):
        stub = StubEngine([{"id": "req-3", "url": "https://www.instagram.com/reel/secret-link/", "lane": None}])
        failed = FetchResult(None, [Attempt("ytdlp", "login_wall:empty_media_response")], "login_wall", "x")
        try:
            with mock.patch.object(watch, "fetch", return_value=failed):
                watch.watch_once(self.config, Engine(stub.url))
        finally:
            stub.close()
        log = (self.root / "home" / "watch.log").read_text()
        self.assertNotIn("secret-link", log)
        self.assertNotIn("instagram.com", log)
        self.assertIn("failed.login_wall", log)

    def test_a_second_run_waits_for_the_first(self):
        lock = self.root / "home" / "watch.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("1")
        counts = watch.watch_once(self.config, Engine("http://127.0.0.1:9"))
        self.assertEqual(counts["skipped.already_running"], 1)


if __name__ == "__main__":
    unittest.main()


class SelfReportTest(unittest.TestCase):
    """Krish, 2026-10-28: "i should never really need to copy and paste log files to you like this, ever". A run
    names why the engine could not be reached, says where it was if it ran too long, and never hangs."""

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"CONTENT_WATCH_HOME": self.home})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.home, ignore_errors=True)

    def test_unreachable_is_named_by_its_cause(self):
        import socket
        import ssl
        from content_watcher.engine import unreachable_class

        self.assertEqual(unreachable_class(ssl.SSLCertVerificationError("x")), "engine_tls_untrusted")
        self.assertEqual(unreachable_class(ssl.SSLError("x")), "engine_tls_error")
        self.assertEqual(unreachable_class(socket.gaierror("x")), "engine_dns_failed")
        self.assertEqual(unreachable_class(ConnectionRefusedError()), "engine_connection_refused")
        self.assertEqual(unreachable_class(PermissionError()), "engine_blocked")
        self.assertEqual(unreachable_class(TimeoutError()), "engine_timeout")
        self.assertEqual(unreachable_class("Tunnel connection failed: 407 Proxy Authentication Required"), "engine_proxy")
        self.assertEqual(unreachable_class(OSError("anything else")), "engine_unreachable")

    def test_a_refused_connection_reaches_the_log_by_class(self):
        engine = Engine("http://127.0.0.1:1", token="test-key", timeout=5)
        config = Config(machine="test-machine")
        counts = watch.watch_once(config, engine)
        self.assertEqual(counts["engine.engine_connection_refused"], 1)
        self.assertNotIn("drop.read", counts, "no dropped file is read while the engine cannot be reached")
        line = (Path(self.home) / "watch.log").read_text(encoding="utf-8").strip().splitlines()[-1]
        self.assertIn('"engine.engine_connection_refused":1', line)
        beat = json.loads((Path(self.home) / "watch.heartbeat").read_text(encoding="utf-8"))
        self.assertEqual(beat["stage"], "done")

    def test_a_run_that_cannot_start_still_logs_its_class(self):
        with mock.patch.object(watch.Config, "load", side_effect=ValueError("bad config")):
            counts = watch.watch_once()
        self.assertEqual(counts["run.error.ValueError"], 1)
        self.assertIn('"run.error.ValueError":1', (Path(self.home) / "watch.log").read_text(encoding="utf-8"))

    def test_a_run_past_its_deadline_logs_its_stage_frees_the_lock_and_ends(self):
        lock = Path(self.home) / "watch.lock"
        lock.write_text("123")
        watch.heartbeat("read_drop")
        ended = []
        counts = Counter()
        watch._over_time(counts, exit_process=ended.append)
        self.assertEqual(ended, [3])
        self.assertFalse(lock.exists())
        line = (Path(self.home) / "watch.log").read_text(encoding="utf-8").strip()
        self.assertIn('"killed.over_time":1', line)
        self.assertIn('"stage.read_drop":1', line)
