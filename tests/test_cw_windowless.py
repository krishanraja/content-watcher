"""No window on a home computer, and no step that a missing key or a lapsed sign-in can stop. Krish, 2026-10-28: "HIDE
ALL CONSOLE POP UPS FOREVER FROM EVERY REPO AND LOCAL TASK" and "Keys from sessions are fragile, you should by now have
a more robust way of not failing at that step!"."""

import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from content_watcher import windowless
from content_watcher.config import Config
from content_watcher.fetch import _methods
from content_watcher.urls import parse


class FakePopen:
    def __init__(self, args, bufsize=-1, executable=None, stdin=None, stdout=None, stderr=None, preexec_fn=None,
                 close_fds=True, shell=False, cwd=None, env=None, universal_newlines=None, startupinfo=None,
                 creationflags=0, **rest):
        self.creationflags = creationflags


class WindowlessTests(unittest.TestCase):
    def fake(self):
        class Popen(FakePopen):
            pass

        return Popen

    def test_every_child_on_windows_is_started_without_a_window(self):
        Popen = self.fake()
        self.assertTrue(windowless.install("win32", Popen))
        self.assertEqual(Popen(["ffmpeg"]).creationflags, windowless.CREATE_NO_WINDOW)
        self.assertEqual(Popen(["x"], creationflags=0x200).creationflags, 0x200 | windowless.CREATE_NO_WINDOW)

        class AsyncioStyle(Popen):  # asyncio and Playwright subclass Popen and call its __init__
            def __init__(self, args, **kwargs):
                super().__init__(args, **kwargs)

        self.assertEqual(AsyncioStyle(["node"]).creationflags, windowless.CREATE_NO_WINDOW)

    def test_a_child_that_asks_for_its_own_console_keeps_it(self):
        Popen = self.fake()
        windowless.install("win32", Popen)
        self.assertEqual(Popen(["x"], creationflags=windowless.CREATE_NEW_CONSOLE).creationflags,
                         windowless.CREATE_NEW_CONSOLE)
        self.assertEqual(Popen(["x"], creationflags=windowless.DETACHED_PROCESS).creationflags,
                         windowless.DETACHED_PROCESS)
        positional = Popen(["x"], -1, None, None, None, None, None, True, False, None, None, None, None, 0x4)
        self.assertEqual(positional.creationflags, 0x4)

    def test_installing_twice_wraps_once_and_elsewhere_nothing_changes(self):
        Popen = self.fake()
        windowless.install("win32", Popen)
        first = Popen.__init__
        windowless.install("win32", Popen)
        self.assertIs(Popen.__init__, first)
        Other = self.fake()
        original = Other.__init__
        self.assertFalse(windowless.install("linux", Other))
        self.assertIs(Other.__init__, original)

    def test_tools_run_under_the_console_python_beside_pythonw(self):
        with tempfile.TemporaryDirectory() as temp:
            pythonw = Path(temp) / "pythonw.exe"
            python = Path(temp) / "python.exe"
            pythonw.write_bytes(b"")
            self.assertEqual(windowless.console_python(str(pythonw)), str(pythonw))  # no twin: as it was
            python.write_bytes(b"")
            self.assertEqual(windowless.console_python(str(pythonw)), str(python))
            self.assertEqual(windowless.console_python(str(python)), str(python))
        from content_watcher.fetch import base

        with mock.patch.object(windowless, "console_python", return_value="C:/py/python.exe"), \
                mock.patch.object(base.importlib.util, "find_spec", return_value=object()):
            self.assertEqual(base.tool_command("yt-dlp")[:2], ["C:/py/python.exe", "-m"])


@unittest.skipUnless(sys.platform == "win32", "a real window can only be looked for on Windows")
class NoWindowOnWindowsTests(unittest.TestCase):
    """The real thing: a windowless parent (pythonw.exe, as the scheduled task runs) starts a console program, and
    every top-level window on the desktop is looked at while it runs. The control, with the patch left out, has to
    show a window, or the probe proves nothing."""

    PROBE = textwrap.dedent("""
        import ctypes, ctypes.wintypes as w, json, sys
        user32 = ctypes.windll.user32
        found = []
        def each(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                name = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, name, 256)
                if name.value in ("ConsoleWindowClass", "CASCADIA_HOSTING_WINDOW_CLASS"):
                    found.append(int(hwnd))
            return True
        user32.EnumWindows(ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)(each), 0)
        print(json.dumps(found))
    """)

    def windows(self) -> set[int]:
        out = subprocess.run([sys.executable, "-c", self.PROBE], capture_output=True, text=True, check=True)
        return set(__import__("json").loads(out.stdout))

    def run_under_pythonw(self, patched: bool) -> set[int]:
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        self.assertTrue(pythonw.is_file(), "pythonw.exe is beside python.exe on Windows")
        child = textwrap.dedent(f"""
            import subprocess, sys
            sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r})
            {"import content_watcher" if patched else "pass"}
            subprocess.run(["cmd.exe", "/c", "ping", "-n", "6", "127.0.0.1"], stdout=subprocess.PIPE)
        """)
        before = self.windows()
        process = subprocess.Popen([str(pythonw), "-c", child])
        seen: set[int] = set()
        deadline = time.monotonic() + 8
        while process.poll() is None and time.monotonic() < deadline:
            seen |= self.windows() - before
            time.sleep(0.3)
        process.wait(timeout=20)
        return seen

    def test_the_probe_sees_the_window_an_unpatched_run_opens(self):
        self.assertTrue(self.run_under_pythonw(patched=False), "the control opened no window the probe could see")

    def test_a_patched_run_opens_no_window(self):
        self.assertEqual(self.run_under_pythonw(patched=True), set())


class NeverBlockedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = mock.patch.dict(os.environ, {"CONTENT_WATCH_HOME": str(self.root / "home")})
        self.env.start()
        os.environ.pop("APIFY_TOKEN", None)
        os.environ.pop("CONTENT_WATCH_APIFY_VIA_ENGINE", None)
        self.config = Config(machine="LORIMER", apify_enabled=True, apify_monthly_cap_usd=5.0)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def engine(self):
        class Engine_:
            calls = []

            def apify(self, request_id, machine, actor, payload):
                self.calls.append((request_id, machine, actor))
                return [{"status": True, "media": [{"url": "https://cdn.example/a.jpg", "fileType": "image/jpeg"}]}]

        return Engine_()

    def test_a_home_computer_with_no_key_borrows_the_engines(self):
        from content_watcher import secrets
        from content_watcher.fetch import apify
        from tests.cw_helpers import FakeOpener

        engine = self.engine()
        with mock.patch.object(secrets, "_windows_credential", return_value=None), \
                apify.engine_runs(engine, "req-1", "LORIMER"):
            post = apify.fetch_instagram_downloader("https://www.instagram.com/p/PxY/", "PxY", self.root, self.config,
                                                    opener=FakeOpener({"https://cdn.example/": b"slide"}))
        self.assertEqual(engine.calls, [("req-1", "LORIMER", "snapinsta~instagram-downloader-api")])
        self.assertEqual(post.media[0].name, "instagram_PxY.jpg")

    def test_a_key_this_machine_holds_that_is_refused_falls_back_to_the_engine(self):
        from content_watcher.fetch import apify
        from tests.cw_helpers import FakeOpener

        engine = self.engine()
        opener = FakeOpener({"https://api.apify.com/": 401, "https://cdn.example/": b"slide"})
        with mock.patch.dict(os.environ, {"APIFY_TOKEN": "expired"}), apify.engine_runs(engine, "req-2", "SURFACE"):
            apify.fetch_instagram_downloader("https://www.instagram.com/p/PxY/", "PxY", self.root, self.config,
                                             opener=opener)
        self.assertEqual(len(engine.calls), 1)
        self.assertTrue(opener.calls[0][0].startswith("https://api.apify.com/"))  # its own key was tried first

    def test_his_signed_in_step_is_capped_so_it_can_never_hold_a_run(self):
        from content_watcher.fetch import gallerydl

        link = parse("https://www.instagram.com/p/DfAY9PWFuEX/")
        config = Config(cookies={"instagram": "C:/Users/k/AppData/Roaming/Mozilla/Firefox/Profiles/a.default"})
        step = dict(_methods(link, config))["gallerydl_cookies"]
        with mock.patch.object(gallerydl, "fetch") as fetch:
            step(self.root)
        self.assertEqual(fetch.call_args.kwargs["timeout"], 180)


if __name__ == "__main__":
    unittest.main()
