"""gallery-dl: every slide of a carousel or TikTok photo post, in order."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..post import AUDIO_EXT, IMAGE_EXT, VIDEO_EXT, Post
from .base import FetchFailed, load_json, run_tool


def _first(meta: dict, *keys):
    for key in keys:
        value = meta
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if value not in (None, ""):
            return value
    return None


def post_from_metadata(meta: dict, platform: str, url: str) -> Post:
    posted = _first(meta, "post_date", "date", "createTime")
    if isinstance(posted, (int, float)):
        posted = datetime.fromtimestamp(int(posted), tz=timezone.utc).isoformat()
    elif isinstance(posted, str) and len(posted) >= 19 and posted[10] == " ":
        posted = posted.replace(" ", "T") + ("" if "+" in posted else "+00:00")
    counts = {}
    for name, keys in (("likes", ("likes", "stats.diggCount")), ("comments", ("comments", "stats.commentCount")),
                       ("views", ("video_view_count", "stats.playCount")), ("shares", ("stats.shareCount",))):
        value = _first(meta, *keys)
        if isinstance(value, (int, float)):
            counts[name] = int(value)
    return Post(
        platform=platform, url=url,
        post_id=str(_first(meta, "post_shortcode", "shortcode", "id") or "") or None,
        author=_first(meta, "username", "owner_id", "author.uniqueId", "user"),
        posted_at=posted, caption=_first(meta, "description", "desc", "caption", "title"), counts=counts,
    )


def fetch(url: str, platform: str, folder: Path, *, cookies_profile: str | None = None, timeout: float = 600) -> Post:
    args: list[str | Path] = ["--write-metadata", "--http-timeout", "30", "-D", folder, "-f", "{num:>03}.{extension}"]
    if platform == "tiktok":
        args += ["-o", "audio=true", "-o", "videos=true"]
    method = "gallerydl"
    if cookies_profile:
        args += ["--cookies-from-browser", f"firefox:{cookies_profile}"]
        method = "gallerydl_cookies"
    args.append(url)
    run_tool("gallery-dl", args, timeout=timeout)
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXT | VIDEO_EXT | AUDIO_EXT)
    if not files:
        raise FetchFailed("other", "no_media_written")
    metas = sorted(folder.glob("*.json"))
    meta = load_json(metas[0]) if metas else {}
    post = post_from_metadata(meta, platform, url)
    post.method = method
    slides = [p for p in files if p.suffix.lower() not in AUDIO_EXT]
    sounds = [p for p in files if p.suffix.lower() in AUDIO_EXT]
    post.media = slides
    post.audio = sounds[0] if sounds else None
    for item in metas:
        item.unlink()
    return post
