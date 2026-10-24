"""yt-dlp: the first free method for Instagram reels, TikTok videos, YouTube and post videos."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..post import Post, VIDEO_EXT
from .base import FetchFailed, load_json, run_tool

AUTHOR_KEYS = {
    "instagram": ("channel", "uploader_id", "uploader"),
    "tiktok": ("uploader", "channel", "creator"),
    "youtube": ("channel", "uploader"),
}


def post_from_info(info: dict, platform: str, url: str) -> Post:
    author = next((info[key] for key in AUTHOR_KEYS.get(platform, ("uploader", "channel")) if info.get(key)), None)
    posted = None
    if info.get("timestamp"):
        posted = datetime.fromtimestamp(int(info["timestamp"]), tz=timezone.utc).isoformat()
    elif info.get("upload_date"):
        day = str(info["upload_date"])
        posted = f"{day[:4]}-{day[4:6]}-{day[6:8]}"
    counts = {
        name: int(info[key])
        for name, key in (("views", "view_count"), ("likes", "like_count"),
                          ("comments", "comment_count"), ("shares", "repost_count"))
        if isinstance(info.get(key), (int, float))
    }
    caption = info.get("description") or info.get("title")
    return Post(platform=platform, url=url, post_id=str(info.get("id") or "") or None, author=author,
                posted_at=posted, caption=caption, counts=counts)


def fetch(url: str, platform: str, folder: Path, *, captions: str | None = None, cookies_profile: str | None = None,
          timeout: float = 600, method: str = "ytdlp") -> Post:
    template = str(folder / f"{platform}_%(id)s.%(ext)s")
    args: list[str | Path] = [
        "--no-progress", "--no-playlist", "--no-warnings", "--socket-timeout", "30", "--retries", "3",
        "--max-filesize", "1500M", "--merge-output-format", "mp4", "--write-info-json", "-o", template,
    ]
    if captions == "all":
        args += ["--write-subs", "--sub-langs", "all,-live_chat", "--sub-format", "vtt/srt/best"]
    elif captions == "youtube":
        args += ["--write-subs", "--write-auto-subs", "--sub-langs", "en.*,en", "--sub-format", "vtt/best"]
    if cookies_profile:
        args += ["--cookies-from-browser", f"firefox:{cookies_profile}"]
        method += "_cookies"
    args.append(url)
    ran = run_tool("yt-dlp", args, timeout=timeout)
    infos = sorted(folder.glob("*.info.json"))
    videos = [p for p in sorted(folder.iterdir()) if p.suffix.lower() in VIDEO_EXT and ".part" not in p.name]
    if not videos:
        raise FetchFailed("other", "no_video_in_post" if "no video" in ran.stderr.lower() else "no_media_written")
    info = load_json(infos[0]) if infos else {}
    post = post_from_info(info, platform, url)
    post.media = [videos[0]]
    subtitles = sorted(p for p in folder.iterdir() if p.suffix.lower() in (".vtt", ".srt"))
    english = [p for p in subtitles if ".en" in p.name.lower()]
    post.captions_file = (english or subtitles or [None])[0]
    post.method = method
    post.shape = "video"
    for item in infos:
        item.unlink()
    return post
