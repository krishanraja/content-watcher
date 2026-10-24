"""yt-dlp: the first free method for Instagram reels, TikTok videos, YouTube and post videos."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..post import IMAGE_EXT, Post, VIDEO_EXT
from .base import FetchFailed, has_audio, load_json, run_tool

QUALITY = "bv*[height<=720]+ba/b[height<=720]/bv*+ba/b"

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
          timeout: float = 600, method: str = "ytdlp", extra: list[str] | None = None,
          need_audio: bool = False) -> Post:
    """One video. `need_audio` makes a file with no sound track a failure, so the chain moves on (TikTok)."""
    template = str(folder / f"{platform}_%(id)s.%(ext)s")
    args: list[str | Path] = [
        "--no-progress", "--no-playlist", "--no-warnings", "--socket-timeout", "30", "--retries", "3",
        "--max-filesize", "1500M", "--merge-output-format", "mp4", "--write-info-json", "-o", template,
        # 720p is plenty for study, smaller and faster (Krish, 2026-10-24: "I never really need to download a
        # high-quality video when I'm doing this job").
        "-f", QUALITY,
    ]
    if captions == "all":
        args += ["--write-subs", "--sub-langs", "all,-live_chat", "--sub-format", "vtt/srt/best"]
    elif captions == "youtube":
        # The language spoken, never YouTube's machine translation (FETCH_METHODS.md, YouTube step 2).
        args += ["--write-subs", "--write-auto-subs", "--sub-langs", ".*-orig", "--sub-format", "vtt/best", "-t", "sleep"]
    if extra:
        args += extra
    if cookies_profile:
        args += ["--cookies-from-browser", f"firefox:{cookies_profile}"]
        method += "_cookies"
    args.append(url)
    ran = run_tool("yt-dlp", args, timeout=timeout)
    infos = sorted(folder.glob("*.info.json"))
    videos = [p for p in sorted(folder.iterdir()) if p.suffix.lower() in VIDEO_EXT and ".part" not in p.name]
    if not videos:
        raise FetchFailed("other", "no_video_in_post" if "no video" in ran.stderr.lower() else "no_media_written")
    if need_audio and has_audio(videos[0]) is False:
        raise FetchFailed("other", "no_audio")
    info = load_json(infos[0]) if infos else {}
    post = post_from_info(info, platform, url)
    post.media = [videos[0]]
    subtitles = sorted(p for p in folder.iterdir() if p.suffix.lower() in (".vtt", ".srt"))
    preferred = [p for p in subtitles if "-orig" in p.name.lower()] or [p for p in subtitles if ".en" in p.name.lower()]
    post.captions_file = (preferred or subtitles or [None])[0]
    post.method = method
    post.shape = "video"
    for item in infos:
        item.unlink()
    return post


def fetch_carousel(url: str, platform: str, folder: Path, *, timeout: float = 600) -> Post:
    """Every slide of an Instagram /p/ post, logged out: video slides as video, image slides as their picture
    (FETCH_METHODS.md, Instagram carousels step 2)."""
    args: list[str | Path] = [
        "--no-progress", "--no-warnings", "--socket-timeout", "30", "--retries", "3", "--max-filesize", "1500M",
        "--ignore-no-formats-error", "--write-thumbnail", "--write-info-json", "--merge-output-format", "mp4",
        "-o", str(folder / "%(id)s_%(playlist_index)02d.%(ext)s"), url,
    ]
    run_tool("yt-dlp", args, timeout=timeout)
    infos = sorted(folder.glob("*.info.json"))
    slides: dict[str, Path] = {}
    for path in sorted(folder.iterdir()):
        if ".part" in path.name or path.name.endswith(".info.json"):
            continue
        kind = path.suffix.lower()
        if kind not in VIDEO_EXT and kind not in IMAGE_EXT:
            continue
        key = path.stem
        # A video slide also writes its thumbnail; the video is the slide.
        if key in slides and slides[key].suffix.lower() in VIDEO_EXT:
            continue
        slides[key] = path
    files = [slides[key] for key in sorted(slides)]
    expected = None
    for item in infos:
        data = load_json(item)
        if data.get("_type") == "playlist" or data.get("playlist_count"):
            expected = data.get("playlist_count") or len(data.get("entries") or []) or None
            break
    if not files:
        raise FetchFailed("other", "no_media_written")
    if expected and len(files) < expected:
        raise FetchFailed("other", "ig_missing_slides")
    first = load_json(infos[0]) if infos else {}
    post = post_from_info(first, platform, url)
    post.post_id = str(first.get("playlist_id") or first.get("id") or "").split("_")[0] or post.post_id
    post.media = files
    post.method = "ytdlp_carousel"
    post.shape = "carousel" if len(files) > 1 else ("video" if files[0].suffix.lower() in VIDEO_EXT else "image")
    for item in infos:
        item.unlink()
    return post
