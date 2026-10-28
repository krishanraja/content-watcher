"""What this machine can and cannot do, naming each missing piece."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

from . import ENGINE_REV, secrets, session, tools
from .config import Config, state_dir
from .fetch import apify
from .urls import BROWSER_UA


def _module_version(name: str) -> str | None:
    if importlib.util.find_spec(name) is None:
        return None
    try:
        module = __import__(name)
    except Exception:  # noqa: BLE001
        return "broken"
    return str(getattr(module, "__version__", "installed"))


def at_least(found: str | None, wanted: str) -> bool:
    """Compare dotted versions as numbers: 1.32.17 is newer than 1.4.0."""
    def parts(text: str) -> tuple[int, ...]:
        return tuple(int(piece) for piece in re.findall(r"\d+", text)[:4])
    return bool(found) and parts(found) >= parts(wanted)


def checks(config: Config) -> list[dict]:
    rows: list[dict] = []

    def add(name: str, ok: bool, detail: str, needed_for: str, required: bool = False) -> None:
        rows.append({"check": name, "ok": ok, "detail": detail, "needed_for": needed_for, "required": required})

    add("python", sys.version_info >= (3, 10), sys.version.split()[0], "everything", True)
    for binary in ("ffmpeg", "ffprobe"):
        found = tools.which(binary)
        add(binary, bool(found), found or "missing: install FFmpeg and put it on PATH", "reading video", True)
    whisper = _module_version("faster_whisper")
    add("faster-whisper", whisper == "1.2.1", whisper or "missing: pip install faster-whisper==1.2.1",
        "the words in a video")
    numpy = _module_version("numpy")
    add("numpy", bool(numpy), numpy or "missing: pip install numpy", "camera moves, faces, colours")
    cv2 = _module_version("cv2")
    has_cascade = False
    if cv2 and cv2 != "broken":
        import cv2 as _cv2  # type: ignore
        has_cascade = hasattr(_cv2, "CascadeClassifier")
    add("opencv", has_cascade, (cv2 or "missing") + ("" if has_cascade else ": pip install \"opencv-python-headless<5\""),
        "faces")
    tesseract = tools.tool_version("tesseract")
    add("tesseract", bool(tesseract), tesseract or "missing: install Tesseract OCR and put it on PATH",
        "words on screen and on slides")
    ytdlp = tools.tool_version("yt-dlp")
    add("yt-dlp", at_least(ytdlp, "2026.10.21"), ytdlp or "missing: install yt-dlp 2026.10.21 by hand (its changelog warns against the -U self-updater)",
        "Instagram reels, TikTok and YouTube videos")
    gallery = tools.tool_version("gallery-dl")
    add("gallery-dl", at_least(gallery, "1.32.17"),
        (gallery + " (TikTok's 403 fix is only on gallery-dl master, not in 1.32.17)") if gallery else "missing: pip install -U gallery-dl",
        "TikTok photo posts and carousels")
    curl_cffi = _module_version("curl_cffi")
    add("curl_cffi", curl_cffi == "0.16.0", (curl_cffi + (" (pin 0.16.0: newer is blocked on TikTok)" if curl_cffi != "0.16.0" else "")) if curl_cffi else "missing: pip install curl_cffi==0.16.0",
        "yt-dlp browser impersonation (Instagram, TikTok)")
    try:
        from importlib.metadata import version as _dist_version
        bgutil = _dist_version("bgutil-ytdlp-pot-provider")
    except Exception:  # noqa: BLE001
        bgutil = None
    import socket as _socket
    try:
        with _socket.create_connection(("127.0.0.1", 4416), timeout=2):
            server = True
    except OSError:
        server = False
    add("bgutil PO token", bool(bgutil) and server,
        (bgutil or "plugin missing: pip install bgutil-ytdlp-pot-provider==2.0.2")
        + ("" if server else "; its server is not running on 127.0.0.1:4416 (the installer starts it with Docker)"),
        "YouTube and Shorts from the home connection")
    instaloader = _module_version("instaloader")
    add("instaloader", bool(instaloader), instaloader or "missing: pip install instaloader==4.15.4", "an Instagram fallback")
    transcripts = _module_version("youtube_transcript_api")
    add("youtube-transcript-api", bool(transcripts), transcripts or "missing: pip install youtube-transcript-api==1.2.4",
        "YouTube words when the video will not download")
    poppler = tools.which("pdftoppm")
    add("poppler", bool(poppler), poppler or "missing: install Poppler (winget install oschwartz10612.Poppler)",
        "LinkedIn document posts (PDF pages)")
    if config.cobalt_url:
        import urllib.request
        try:
            with urllib.request.urlopen(config.cobalt_url, timeout=5) as response:
                cobalt_ok = response.status < 500
        except Exception:  # noqa: BLE001
            cobalt_ok = False
        add("cobalt", cobalt_ok, config.cobalt_url + ("" if cobalt_ok else " (not answering: is Docker running?)"),
            "a free downloader for every platform")
    else:
        add("cobalt", False, "not set up (optional): scripts/cobalt/README.md", "a free downloader for every platform")
    deno = tools.tool_version("deno")
    add("deno", bool(deno), deno or "missing: install deno (winget install DenoLand.Deno)", "YouTube's player challenge")
    add("engine key", bool(secrets.engine_token()), "present" if secrets.engine_token() else
        f"missing: Windows Credential Manager {secrets.ENGINE_TARGET} or MINDMAKE_ENGINE_TOKEN", "the queue", True)
    if config.apify_enabled:
        add("apify", bool(secrets.apify_token()),
            f"cap ${config.apify_monthly_cap_usd:.2f} a month, ${apify.month_spend():.2f} spent this month"
            if secrets.apify_token() else f"missing token: {secrets.APIFY_TARGET} or APIFY_TOKEN", "paid fallback")
    else:
        add("apify", False, "off: no standing monthly cap set (decision D2)", "paid fallback")
    for platform in ("instagram", "linkedin", "tiktok", "youtube"):
        profile = config.cookies.get(platform)
        found = None if profile or platform not in config.browser_sessions else session.signed_in_profile(platform)
        detail = (f"Firefox profile '{profile}'" if profile else
                  f"his signed-in Firefox session ({Path(found).name})" if found else
                  "no signed-in Firefox session on this machine (logged out only)" if platform in config.browser_sessions
                  else "none (logged out only)")
        add(f"cookies {platform}", bool(profile or found), detail, f"{platform} posts behind a login")
    add("filing", True, config.filing + (" (on this machine only)" if config.filing == "local" else " (the two Drive folders)"),
        "where fetched media goes")
    for label, flag, value in (("Production Inspo", "--production-inspo", config.video_inspiration),
                               ("Content Inspo", "--content-inspo", config.cold_ideas)):
        exists = bool(value) and Path(value).is_dir()
        add(f"folder {label}", exists, value or f"not set: content-watch config {flag} <synced path>",
            "filing and reading hand-dropped files", config.filing == "drive")
    add("state", True, str(state_dir()), "local log, readings and state")
    add("browser user agent", True, BROWSER_UA, "TikTok and LinkedIn page reads")
    timeline_missing = [name for name, ok in (("faster-whisper", bool(whisper)), ("numpy", bool(numpy)),
                                              ("tesseract", bool(tesseract)), ("opencv", has_cascade)) if not ok]
    add("timeline", not timeline_missing, "full" if not timeline_missing else "without " + ", ".join(timeline_missing),
        "stills with what was said and shown at each (content-watch timeline, and every video reading)")
    add("engine_rev", True, ENGINE_REV, "the reading format")
    return rows


def render(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        mark = "ok  " if row["ok"] else ("MISSING" if row["required"] else "no  ")
        lines.append(f"{mark:8} {row['check']:24} {row['detail']}  ({row['needed_for']})")
    missing = [row["check"] for row in rows if row["required"] and not row["ok"]]
    lines.append("")
    lines.append("Ready to run the watcher." if not missing else "Not ready. Missing: " + ", ".join(missing) + ".")
    return "\n".join(lines)
