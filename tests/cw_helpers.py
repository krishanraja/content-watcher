"""Shared test helpers: a fake network, fake outside tools and generated media."""

from __future__ import annotations

import io
import json
import os
import shutil
import stat
import subprocess
import sys
import urllib.error
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
FFMPEG = shutil.which("ffmpeg")


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, url: str, headers: dict | None = None):
        super().__init__(body)
        self._url = url
        self.headers = headers or {}

    def geturl(self) -> str:
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class FakeOpener:
    """Answers requests from a dict of URL prefix -> bytes, or an int HTTP status."""

    def __init__(self, routes: dict):
        self.routes = routes
        self.calls: list[tuple[str, bytes | None]] = []

    def open(self, request, timeout=None):
        url = request.full_url if hasattr(request, "full_url") else request
        self.calls.append((url, getattr(request, "data", None)))
        for prefix, answer in self.routes.items():
            if url.startswith(prefix):
                if callable(answer):
                    answer = answer(request)
                if isinstance(answer, int):
                    raise urllib.error.HTTPError(url, answer, "status", {}, None)
                return FakeResponse(answer, url)
        raise urllib.error.HTTPError(url, 404, "no route", {}, None)


def fake_tool(directory: Path, name: str, body: str) -> Path:
    """A stand-in outside tool on PATH: a Python script that gets the real command line."""
    directory.mkdir(parents=True, exist_ok=True)
    script = directory / name
    script.write_text(f"#!{sys.executable}\nimport sys, json, pathlib, shutil\nargs = sys.argv[1:]\n{body}\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def with_path(directory: Path) -> dict:
    env = dict(os.environ)
    env["PATH"] = f"{directory}{os.pathsep}{env.get('PATH', '')}"
    return env


def ffmpeg(*args: str) -> None:
    subprocess.run([FFMPEG or "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def make_image(path: Path, text: str | None, *, colour: str = "white", size: str = "1080x1350", font_colour: str = "black",
               fontsize: int = 110) -> Path:
    draw = f",drawtext=text='{text}':expansion=none:fontsize={fontsize}:fontcolor={font_colour}:x=(w-tw)/2:y=(h-th)/2" if text else ""
    ffmpeg("-f", "lavfi", "-i", f"color=c={colour}:s={size}:d=1{draw}", "-frames:v", "1", str(path))
    return path


def make_video(path: Path, *, seconds: float = 2.0, colour: str = "navy", text: str | None = None,
               audio: bool = True) -> Path:
    draw = f",drawtext=text='{text}':fontsize=110:fontcolor=white:x=(w-tw)/2:y=(h-th)/2" if text else ""
    args = ["-f", "lavfi", "-i", f"color=c={colour}:s=720x1280:d={seconds}:r=25{draw}"]
    if audio:
        args += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={seconds}", "-c:a", "aac"]
    args += ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-shortest", str(path)]
    ffmpeg(*args)
    return path


def load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))
