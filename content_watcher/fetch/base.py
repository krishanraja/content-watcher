"""What every fetcher shares: failure classes, outside tools and downloads."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
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
    # These carry yt-dlp's "use --cookies" hint but are refusals, not login walls (FETCH_METHODS.md, Instagram step 2).
    (r"exceeded the rate-limit|HTTP Error 429|Too Many Requests|rate.?limit", "blocked", "rate_limited"),
    (r"empty media response", "blocked", "empty_media_response"),
    (r"Sign in to confirm you.re not a bot|not a bot", "blocked", "bot_check"),
    (r"status code 10204|IP address is blocked", "blocked", "ip_blocked"),
    (r"Private video|This account is private|login required|requires authentication|Restricted Video|"
     r"age-restricted|LoginRequired|authwall|Sign in to confirm your age", "login_wall", "login_required"),
    (r"Unsupported URL", "other", "unsupported_url"),
    (r"HTTP Error 404|404 Not Found|Video unavailable|This video is unavailable|Video not available|does not exist|"
     r"status code 10216|Post isn't available|post may have been removed|has been removed|no longer available|"
     r"NotFoundError|not found", "not_found", "not_found"),
    (r"HTTP Error 403|Forbidden|captcha|challenge|blocked|Unexpected response|PO Token|"
     r"Unable to extract universal data", "blocked", "refused"),
    (r"timed out|timeout|Read timed out", "timeout", "network_timeout"),
]


def classify(text: str) -> tuple[str, str]:
    for pattern, status_class, detail in _PATTERNS:
        if re.search(pattern, text, re.I):
            return status_class, detail
    return "other", "unrecognised_error"


MODULES = {"yt-dlp": "yt_dlp", "gallery-dl": "gallery_dl", "instaloader": "instaloader"}


def tool_command(name: str) -> list[str]:
    """Run yt-dlp and gallery-dl through this interpreter, so a stale copy on PATH is never the one that runs."""
    module = MODULES.get(name)
    if module and importlib.util.find_spec(module) is not None:
        return [sys.executable, "-m", module]
    found = tools.which(name)  # a stand-alone install, or a test's stand-in
    if not found:
        raise FetchFailed("other", f"no_{name.replace('-', '_')}")
    return [found]


def run_tool(name: str, args: list[str | Path], *, timeout: float) -> tools.Ran:
    ran = tools.run([*tool_command(name), *args], timeout=timeout)
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


def has_audio(path: Path) -> bool | None:
    """Whether a downloaded video has a sound track; None when ffprobe is missing."""
    ffprobe = tools.which("ffprobe")
    if not ffprobe:
        return None
    ran = tools.run([ffprobe, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                     "-of", "csv=p=0", path], timeout=30)
    return bool(ran.stdout.strip()) if ran.returncode == 0 else None


def text_post(post, folder: Path, *, title: str, body: str, note: str | None = None) -> Path:
    """File a post whose media could not be had as Markdown of its words, so a pasted link still becomes a card.
    The header lines are the ones read.reader.parse_text_post reads back."""
    lines = [f"# {title}", ""]
    lines.append(f"Author: {post.author or ''}")
    lines.append(f"Posted: {post.posted_at or ''}")
    lines.append(f"Link: {post.url}")
    lines.append(f"Platform: {post.platform}")
    lines += ["", body.strip()]
    if note:
        lines += ["", f"({note})"]
    target = folder / f"{post.platform}_{post.post_id or 'post'}.md"
    target.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    post.media = [target]
    post.shape = "text"
    return target
