"""The cloud backup's filing: through the engine's upload route into Drive, never a synced folder. Krish, 2026-10-28:
"yes build the cloud backup". A stub engine on localhost plays both the engine and Google's upload session."""

import hashlib
import json
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
from content_watcher.fetch import Attempt, FetchResult
from content_watcher.filing import FilingError, file_post
from content_watcher.post import Post
from tests.cw_helpers import make_image


class CloudStub:
    """The engine's claim, upload and report routes, and a Drive session that answers the sha256 of what it got."""

    def __init__(self, queue, *, exists=False, corrupt=False):
        self.queue = list(queue)
        self.calls = []
        self.drive = {}
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, answer, code=200):
                payload = json.dumps(answer).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_PUT(self):
                data = self.rfile.read(int(self.headers["Content-Length"]))
                name = self.path.rsplit("=", 1)[-1]
                stub.calls.append(("PUT", name, self.headers.get("Authorization")))
                stub.drive[name] = data
                digest = hashlib.sha256(b"x" if corrupt else data).hexdigest()
                self.reply({"id": "F1", "name": name, "size": str(len(data)), "sha256Checksum": digest})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                stub.calls.append((self.path, body, self.headers.get("Authorization")))
                if self.path == "/api/watch/claim":
                    answer = {"requests": stub.queue[: body["limit"]]}
                    stub.queue = stub.queue[body["limit"]:]
                elif self.path == "/api/watch/upload":
                    answer = {"ok": True, "exists": True, "name": body["name"]} if exists else {
                        "ok": True, "exists": False, "name": body["name"],
                        "upload_url": f"{stub.url}/upload/drive/v3/files?uploadType=resumable&upload_id={body['name']}"}
                else:
                    answer = {"ok": True}
                self.reply(answer)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def paths(self):
        return [call[0] for call in self.calls]

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class CloudFilingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = mock.patch.dict(os.environ, {"CONTENT_WATCH_HOME": str(self.root / "home"),
                                                "MINDMAKE_ENGINE_TOKEN": "test-key"})
        self.env.start()
        self.config = Config(filing="engine", machine="cloud-gh", whisper_model="tiny")
        self.slide = make_image(self.root / "slide.jpg", text="THE POINT")

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def fake_fetch(self, url, dest, config):
        folder = dest / "instagram_PxY"
        folder.mkdir(parents=True)
        shutil.copy(self.slide, folder / "instagram_PxY_1.jpg")
        post = Post("instagram", url, "PxY", "writer.example", caption="one idea",
                    media=[folder / "instagram_PxY_1.jpg"], method="apify", shape="image")
        post.save(folder)
        return FetchResult(post, [Attempt("apify", "ok")])

    def run_once(self, stub):
        with mock.patch.object(watch, "fetch", side_effect=self.fake_fetch):
            return watch.watch_once(self.config, Engine(stub.url))

    def test_a_link_is_filed_through_the_engine_into_the_folder_its_tag_names(self):
        stub = CloudStub([{"id": "req-9", "url": "https://www.instagram.com/p/PxY/", "lane": "strategy"}])
        try:
            counts = self.run_once(stub)
        finally:
            stub.close()
        self.assertEqual(counts["filed"], 1)
        self.assertEqual(counts["read"], 1)
        self.assertEqual(stub.paths(), ["/api/watch/claim", "/api/watch/upload", "PUT", "/api/watch/report",
                                        "/api/watch/report"])
        upload = stub.calls[1][1]
        self.assertEqual((upload["id"], upload["machine"], upload["folder"]), ("req-9", "cloud-gh", "cold_ideas"))
        self.assertEqual(upload["sha256"], tools.sha256_file(self.slide))
        self.assertIsNone(stub.calls[2][2], "no key travels with the Drive session")
        self.assertEqual(stub.drive["instagram_PxY_1.jpg"], self.slide.read_bytes())
        filed = stub.calls[3][1]
        self.assertEqual(filed["status"], "filed")
        self.assertEqual(filed["media"][0]["name"], "instagram_PxY_1.jpg")
        self.assertEqual(filed["media"][0]["folder"], "cold_ideas")
        self.assertEqual(stub.calls[4][1]["status"], "read")

    def test_the_same_bytes_already_in_drive_are_not_sent_again(self):
        stub = CloudStub([{"id": "req-9", "url": "https://www.instagram.com/p/PxY/", "lane": "strategy"}], exists=True)
        try:
            counts = self.run_once(stub)
        finally:
            stub.close()
        self.assertNotIn("PUT", stub.paths())
        self.assertEqual(counts["filed"], 1)

    def test_a_copy_google_hashes_differently_fails_the_request_and_is_never_reported_filed(self):
        stub = CloudStub([{"id": "req-9", "url": "https://www.instagram.com/p/PxY/", "lane": "production"}],
                         corrupt=True)
        try:
            counts = self.run_once(stub)
        finally:
            stub.close()
        self.assertEqual(counts["failed.filing.copy_mismatch"], 1)
        statuses = [call[1]["status"] for call in stub.calls if call[0] == "/api/watch/report"]
        self.assertEqual(statuses, ["failed"])

    def test_engine_filing_needs_an_uploader_and_a_refused_upload_is_a_class(self):
        post = Post("instagram", "u", "PxY", "a", media=[self.slide], shape="image")
        with self.assertRaises(FilingError) as missing:
            file_post(post, self.config, "strategy")
        self.assertEqual(missing.exception.status_class, "no_uploader")

        class Refusing:
            def upload(self, *args, **kwargs):
                raise EngineError("engine_http_503")

        upload = watch.engine_uploader(Refusing(), "req-9", "cloud-gh")
        with self.assertRaises(FilingError) as refused:
            file_post(post, self.config, "strategy", upload)
        self.assertEqual(refused.exception.status_class, "engine_http_503")


if __name__ == "__main__":
    unittest.main()
