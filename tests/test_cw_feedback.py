"""Feedback videos linked in Control Center: read from his synced Drive (never copied, moved or deleted), timelined here,
stills to Stills and the feedback file to the recording's folder, one report; never the Inspiration queue,
content_reads or the drop folders."""

import hashlib
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

ID = "00000000-0000-4000-8000-000000000001"


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
        # His synced Drive: My Drive > Ventures > Bugs & Issues > run.mp4, and Production Inspo beside it.
        cls.drive = cls.root / "My Drive"
        cls.bugs = cls.drive / "Ventures" / "Bugs & Issues"
        cls.bugs.mkdir(parents=True)
        (cls.drive / "Ventures" / "Inspiration" / "Production Inspo").mkdir(parents=True)
        cls.video = cls.bugs / "run.mp4"
        ffmpeg("-f", "lavfi", "-i", "color=c=white:s=720x1280:d=3:r=25",
               "-f", "lavfi", "-i", "color=c=navy:s=720x1280:d=3:r=25",
               "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p[v]", "-map", "[v]",
               "-c:v", "libx264", "-preset", "ultrafast", str(cls.video))
        cls.md5 = hashlib.md5(cls.video.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.state = Path(tempfile.mkdtemp(prefix="state-", dir=self.root))
        self.patch = mock.patch.dict(os.environ, {"CONTENT_WATCH_HOME": str(self.state)})
        self.patch.start()
        inspo = self.drive / "Ventures" / "Inspiration" / "Production Inspo"
        self.config = Config(machine="Surface", engine_url="http://unused", whisper_model="tiny",
                             video_inspiration=str(inspo))

    def tearDown(self):
        self.patch.stop()

    def job(self, **over):
        return {"id": ID, "name": "run.mp4", "note": "the invented checkout", "mime": "video/mp4",
                "bytes": self.video.stat().st_size, "md5": self.md5, "drive_file_id": "src_ABCDEFGHIJ",
                "drive_path": "Ventures/Bugs & Issues/run.mp4", "venture": "heartside", "venture_label": "Heartside",
                "attempts": 1, **over}

    def run_once(self, job, **kw):
        stub = FeedbackEngine(job)
        counts = Counter()
        try:
            feedback.feedback_once(kw.pop("config", self.config), Engine(stub.url, token="k"), counts,
                                   time_left_s=kw.pop("time_left_s", 1200), **kw)
        finally:
            stub.close()
        return stub, counts

    def test_the_synced_recording_is_read_in_place_and_its_outputs_go_to_drive(self):
        before = self.video.read_bytes()
        uploaded: list = []
        stub, counts = self.run_once(self.job(), put=fake_put(uploaded))
        self.assertEqual(counts["feedback.done"], 1, dict(counts))
        self.assertEqual(stub.paths(), ["/api/ux-feedback/claim", "/api/ux-feedback/drive", "/api/ux-feedback/drive",
                                        "/api/ux-feedback/report"])
        stills_ask, feedback_ask = stub.calls[1][1]["files"], stub.calls[2][1]["files"]
        self.assertEqual({f["place"] for f in stills_ask}, {"stills"})
        self.assertEqual([(f["name"], f["place"]) for f in feedback_ask], [("feedback.md", "folder")])
        self.assertGreaterEqual(len(stills_ask), 2)
        text = uploaded[-1][2].decode()
        self.assertIn("Feedback on Heartside, from [run.mp4](https://drive.google.com/file/d/src_ABCDEFGHIJ/view).", text)
        self.assertIn("What it is about, in your words: the invented checkout", text)
        self.assertIn("https://drive.google.com/file/d/drive_still_001", text)
        report = stub.calls[-1][1]
        self.assertEqual((report["status"], report["feedback_file_id"]), ("done", "drive_feedback"))
        self.assertEqual((report["summary"]["width"], report["summary"]["height"], report["summary"]["portrait"]),
                         (720, 1280, True))
        # His recording is exactly where he left it, byte for byte.
        self.assertEqual(self.video.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.bugs.iterdir()), ["run.mp4"])

    def test_a_recording_not_synced_yet_goes_back_to_the_queue(self):
        stub, counts = self.run_once(self.job(drive_path="Ventures/Bugs & Issues/later.mp4"))
        self.assertEqual(stub.paths(), ["/api/ux-feedback/claim", "/api/ux-feedback/report"])
        self.assertEqual(stub.calls[-1][1]["status_class"], "not_synced_yet")
        stub, _ = self.run_once(self.job(bytes=10))  # still arriving: the size is not the size yet
        self.assertEqual(stub.calls[-1][1]["status_class"], "not_synced_yet")

    def test_different_bytes_under_that_name_are_refused(self):
        stub, _ = self.run_once(self.job(md5="0" * 32))
        self.assertEqual(stub.calls[-1][1]["status_class"], "not_the_same_file")

    def test_no_synced_drive_and_a_path_that_climbs_out_are_refused(self):
        stub, _ = self.run_once(self.job(), config=Config(machine="Surface", engine_url="http://unused"))
        self.assertEqual(stub.calls[-1][1]["status_class"], "no_drive_root")
        stub, _ = self.run_once(self.job(drive_path="Ventures/../../secret.mp4"))
        self.assertEqual(stub.calls[-1][1]["status_class"], "bad_drive_path")

    def test_a_cloud_machine_and_a_short_run_never_claim(self):
        cloud = Config(machine="cloud-gh", engine_url="http://unused")
        stub, _ = self.run_once(self.job(), config=cloud)
        self.assertEqual(stub.paths(), [])
        stub, counts = self.run_once(self.job(), time_left_s=60)
        self.assertEqual(stub.paths(), [])
        self.assertEqual(counts["feedback.deferred"], 1)

    def test_an_engine_without_the_routes_does_not_stop_the_drop_reader(self):
        stub = FeedbackEngine(None, missing=("/api/ux-feedback/claim",))
        try:
            with mock.patch.object(watch, "read_drops") as drops:
                counts = watch.watch_once(self.config, Engine(stub.url, token="k"))
        finally:
            stub.close()
        self.assertEqual(counts["feedback.engine_route_missing"], 1)
        drops.assert_called_once()

    def test_the_lane_never_reaches_the_inspiration_routes(self):
        stub, _ = self.run_once(self.job(), put=fake_put([]))
        self.assertFalse([path for path in stub.paths() if path.startswith("/api/watch/")])

    def test_the_drive_root_is_three_up_from_production_inspo_or_set(self):
        self.assertEqual(self.config.my_drive_root(), self.drive)
        self.assertEqual(Config(drive_root="/x/My Drive").my_drive_root(), Path("/x/My Drive"))
        self.assertIsNone(Config().my_drive_root())


if __name__ == "__main__":
    unittest.main()
