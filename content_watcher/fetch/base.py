"""What every fetcher shares: failure classes, outside tools and downloads."""

from __future__ import annotations

import json
import re
import shutil
import socket
import urllib.error
import urllib.request
from pathlib import Path

from .. import tools
from ..urls import BROWSER_UA

# The status classes Control Center puts into words. Keep to these.
STATUS_CLASSES = ("login_wall", "not_found", "too_big", "blocked", "timeout", "other")

MAX_BYTES = 1_500_000_000  # 1.5 GB: anything bigger is too_big


class FetchFailed(RuntimeError):
    """A fetch method failed. status_class is one of STATUS_CLASSES; detail is a fixed class name."""

    def __init__(self, status_class: str, detail: str):
        assert status_class in STATUS_CLASSES, status_class
        super().__init__(f"{status_class}:{detail}")
        self.status_class = status_class
        self.detail = detail


# Ordered: the first pattern that matches decides.
_PATTERNS: list[tuple[str, str, str]] = [
    (r"File is larger than max-filesize|too large|max-filesize", "too_big", "over_size_cap"),
    (r"Private video|This account is private|login required|log in|logged-in|Sign in to confirm|"
     r"requires authentication|cookies|use --cookies|Restricted Video|age-restricted|"
     r"login page|LoginRequired|authwall", "login_wall", "login_required"),
    (r"empty media response", "login_wall", "empty_media_response"),
    (r"HTTP Error 404|404 Not Found|Video unavailable|Video not available|status code 102(?:04|16)|This video is unavailable|does not exist|"
     r"Post isn't available|post may have been removed|has been removed|no longer available|"
     r"Unsupported URL|NotFoundError|not found", "not_found", "not_found"),
    (r"HTTP Error 429|Too Many Requests|rate.?limit", "blocked", "rate_limited"),
    (r"HTTP Error 403|Forbidden|captcha|challenge|blocked|Unexpected response|PO Token|bot",
     "blocked", "refused"),
    (r"timed out|timeout|Read timed out", "timeout", "network_timeout"),
]


def classify(text: str) -> tuple[str, str]:
    for pattern, status_class, detail in _PATTERNS:
        if re.search(pattern, text, re.I):
            return status_class, detail
    return "other", "unrecognised_error"


def run_tool(name: str, args: list[str | Path], *, timeout: float) -> tools.Ran:
    try:
        binary = tools.need(name)
    except tools.ToolMissing:
        raise FetchFailed("other", f"no_{name.replace('-', '_')}") from None
    ran = tools.run([binary, *args], timeout=timeout)
    if ran.timed_out:
        raise FetchFailed("timeout", f"{name.replace('-', '_')}_timeout")
    if ran.returncode != 0:
        status_class, detail = classify(ran.stderr + "\n" + ran.stdout)
        raise FetchFailed(status_class, detail)
    return ran


def download(url: str, target: Path, *, timeout: float = 120, headers: dict | None = None, opener=None,
             max_bytes: int = MAX_BYTES) -> Path:
    """Download one media URL at once (platform CDN links expire)."""
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, **(headers or {})})
    opener = opener or urllib.request.build_opener()
    partial = target.with_name(target.name + ".part")
    try:
        with opener.open(request, timeout=timeout) as response, partial.open("wb") as handle:
            length = response.headers.get("Content-Length")
            if length and int(length) > max_bytes:
                raise FetchFailed("too_big", "over_size_cap")
            written = 0
            for chunk in iter(lambda: response.read(1024 * 256), b""):
                written += len(chunk)
                if written > max_bytes:
                    raise FetchFailed("too_big", "over_size_cap")
                handle.write(chunk)
    except FetchFailed:
        partial.unlink(missing_ok=True)
        raise
    except urllib.error.HTTPError as exc:
        partial.unlink(missing_ok=True)
        if exc.code == 404 or exc.code == 410:
            raise FetchFailed("not_found", "media_404") from None
        if exc.code in (401, 403):
            raise FetchFailed("blocked", "media_refused") from None
        if exc.code == 429:
            raise FetchFailed("blocked", "rate_limited") from None
        raise FetchFailed("other", f"media_http_{exc.code}") from None
    except (socket.timeout, TimeoutError):
        partial.unlink(missing_ok=True)
        raise FetchFailed("timeout", "media_timeout") from None
    except urllib.error.URLError as exc:
        partial.unlink(missing_ok=True)
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            raise FetchFailed("timeout", "media_timeout") from None
        raise FetchFailed("other", "media_network_error") from None
    if partial.stat().st_size == 0:
        partial.unlink()
        raise FetchFailed("other", "media_empty")
    partial.replace(target)
    return target


def ext_from(url: str, default: str) -> str:
    path = url.split("?", 1)[0]
    match = re.search(r"\.(mp4|mov|webm|jpe?g|png|webp|heic|m4a|mp3)$", path, re.I)
    return "." + match.group(1).lower().replace("jpeg", "jpg") if match else default


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_folder(folder: Path) -> None:
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
