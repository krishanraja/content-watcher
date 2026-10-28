"""Feedback videos from Control Center: claimed, timelined here, stills and feedback file to Drive, one report; never the
Inspiration queue, content_reads or the drop folders."""

import json
import os
import tempfile
import threading
import unittest
from collections import Counter
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

from content_watcher import feedback, watch
from content_watcher.config import Config
from content_watcher.engine import Engine
from tests.cw_helpers import FFMPEG, ffmpeg

try:
    import numpy  # noqa: F401
    HAS_NUMPY = True
except Exception:  # noqa: BLE001
    HAS_NUMPY = False


class FeedbackEngine:
    """The engine's api/ux-feedback routes, recording every call; a 404 for any route in `missing`."""

    def __init__(self, recording: dict | None, missing: tuple = ()):
        self.recording = recording
        self.calls: list[tuple[str, dict]] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                stub.calls.append((self.path, body))
                if self.path in missing:
                    self.send_response(404)
                    self.end_headers()
                    return
                answer: dict = {}
                if self.path == "/api/ux-feedback/claim":
                    answer = {"ok": True, "recording": stub.recording, "expired": 0}
                    stub.recording = None
                elif self.path == "/api/ux-feedback/drive":
                    answer = {"ok": True, "folder_id": "folder_ABCDEFGHIJ", "folder_url": "https://drive/f",
                              "uploads": [{"name": f["name"], "upload_url": f"https://upload/{f['name']}"} for f in body["files"]]}
                elif self.path.startswith("/api/watch/claim"):
                    answer = {"requests": []}
                payload = json.dumps(answer).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def paths(self) -> list[str]:
        return [path for path, _ in self.calls]

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def fake_put(uploaded: list):
    def put(url, path, mime):
        uploaded.append((url.rsplit("/", 1)[-1], mime, Path(path).read_bytes()))
        return {"id": "drive_" + Path(path).stem.replace(".", "_")}
    return put


@unittest.skipUnless(FFMPEG and HAS_NUMPY, "FFmpeg and numpy are required")
class FeedbackLaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="cw-feedback-test-")
        cls.root = Path(cls.temp.name)
        cls.video = cls.root / "uploaded.mp4"
        ffmpeg("-f", "lavfi", "-i", "color=c=white:s=1280x720:d=3:r=25",
               "-f", "lavfi", "-i", "color=c=navy:s=1280x720:d=3:r=25",
               "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p[v]", "-map", "[v]",
               "-c:v", "libx264", "-preset", "ultrafast", str(cls.video))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.state = Path(tempfile.mkdtemp(prefix="state-", dir=self.root))
        self.patch = mock.patch.dict(os.environ, {"CONTENT_WATCH_HOME": str(self.state)})
        self.patch.start()
        self.config = Config(machine="Surface", engine_url="http://unused", whisper_model="tiny")

    def tearDown(self):
        self.patch.stop()

    def job(self, **over):
        return {"id": "00000000-0000-4000-8000-000000000001", "name": "Checkout run.mp4", "note": None,
                "mime": "video/mp4", "bytes": self.video.stat().st_size, "attempts": 1,
                "download_url": self.video.resolve().as_uri(), **over}

    def test_a_feedback_video_goes_to_drive_and_is_reported_done(self):
        stub = FeedbackEngine(self.job())
        uploaded: list = []
        counts = Counter()
        try:
            feedback.feedback_once(self.config, Engine(stub.url, token="k"), counts, time_left_s=1200, put=fake_put(uploaded))
        finally:
            stub.close()
        self.assertEqual(counts["feedback.done"], 1, dict(counts))
        self.assertEqual(stub.paths(), ["/api/ux-feedback/claim", "/api/ux-feedback/drive", "/api/ux-feedback/drive",
                                        "/api/ux-feedback/report"])
        stills = [name for name, mime, _ in uploaded if mime == "image/jpeg"]
        self.assertGreaterEqual(len(stills), 2)
        self.assertEqual(uploaded[-1][:2], ("feedback.md", "text/markdown"))
        text = uploaded[-1][2].decode()
        self.assertIn("Each line links the still of that moment in Drive.", text)
        self.assertIn("https://drive.google.com/file/d/drive_still_001", text)
        report = stub.calls[-1][1]
        self.assertEqual((report["status"], report["feedback_file_id"]), ("done", "drive_feedback"))
        self.assertEqual(set(report["summary"]), {"duration_s", "stills", "images", "signals"})
        work = self.state / "feedback" / self.job()["id"]
        self.assertFalse((work / "Checkout run.mp4").exists())  # this machine's copy of the recording is gone
        self.assertTrue(any(work.glob("*/feedback.md")))

    def test_a_cloud_machine_and_a_short_run_never_claim(self):
        stub = FeedbackEngine(self.job())
        counts = Counter()
        try:
            cloud = Config(machine="cloud-gh", engine_url="http://unused")
            feedback.feedback_once(cloud, Engine(stub.url, token="k"), counts, time_left_s=1200)
            feedback.feedback_once(self.config, Engine(stub.url, token="k"), counts, time_left_s=60)
        finally:
            stub.close()
        self.assertEqual(stub.paths(), [])
        self.assertEqual(counts["feedback.deferred"], 1)

    def test_a_short_download_is_reported_failed_by_class(self):
        stub = FeedbackEngine(self.job(bytes=10))
        counts = Counter()
        try:
            feedback.feedback_once(self.config, Engine(stub.url, token="k"), counts, time_left_s=1200, put=fake_put([]))
        finally:
            stub.close()
        self.assertEqual(stub.paths(), ["/api/ux-feedback/claim", "/api/ux-feedback/report"])
        self.assertEqual(stub.calls[-1][1], {"id": self.job()["id"], "machine": "Surface", "status": "failed",
                                             "status_class": "download_incomplete"})

    def test_an_engine_without_the_routes_does_not_stop_the_drop_reader(self):
        stub = FeedbackEngine(None, missing=("/api/ux-feedback/claim",))
        try:
            with mock.patch.object(watch, "read_drops") as drops:
                counts = watch.watch_once(self.config, Engine(stub.url, token="k"))
        finally:
            stub.close()
        self.assertEqual(counts["feedback.engine_route_missing"], 1)
        drops.assert_called_once()
        self.assertNotIn("/api/watch/read", stub.paths())

    def test_the_lane_never_reaches_the_inspiration_routes(self):
        stub = FeedbackEngine(self.job())
        try:
            feedback.feedback_once(self.config, Engine(stub.url, token="k"), Counter(), time_left_s=1200, put=fake_put([]))
        finally:
            stub.close()
        self.assertFalse([path for path in stub.paths() if path.startswith("/api/watch/")])

    def test_failure_classes_take_the_engine_shape(self):
        stub = FeedbackEngine(self.job(download_url="http://127.0.0.1:9/nothing"))
        try:
            feedback.feedback_once(self.config, Engine(stub.url, token="k"), Counter(), time_left_s=1200)
        finally:
            stub.close()
        self.assertRegex(stub.calls[-1][1]["status_class"], r"^[a-z_]{1,40}$")


if __name__ == "__main__":
    unittest.main()
