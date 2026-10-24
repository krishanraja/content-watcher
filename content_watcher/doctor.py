"""What this machine can and cannot do, naming each missing piece."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

from . import ENGINE_REV, secrets, tools
from .config import Config, state_dir
from .fetch import apify


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
    add("yt-dlp", at_least(ytdlp, "2026.10.21"), ytdlp or "missing: pip install -U \"yt-dlp[default,curl-cffi]\"",
        "Instagram reels, TikTok and YouTube videos")
    gallery = tools.tool_version("gallery-dl")
    add("gallery-dl", at_least(gallery, "1.32.17"), gallery or "missing: pip install -U gallery-dl",
        "TikTok photo posts and carousels")
    curl_cffi = _module_version("curl_cffi")
    add("curl_cffi", bool(curl_cffi), curl_cffi or "missing: pip install curl_cffi==0.16.0",
        "yt-dlp browser impersonation (Instagram, TikTok)")
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
        add(f"cookies {platform}", bool(profile), f"Firefox profile '{profile}'" if profile else "none (logged out only)",
            f"{platform} posts behind a login")
    add("filing", True, config.filing + (" (on this machine only)" if config.filing == "local" else " (the two Drive folders)"),
        "where fetched media goes")
    for folder, value in (("video_inspiration", config.video_inspiration), ("cold_ideas", config.cold_ideas)):
        exists = bool(value) and Path(value).is_dir()
        add(f"folder {folder}", exists, value or "not set: content-watch config --" + folder.replace("_", "-") + " <path>",
            "filing and reading hand-dropped files", config.filing == "drive")
    add("state", True, str(state_dir()), "local log, readings and state")
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
