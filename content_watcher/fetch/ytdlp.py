"""yt-dlp: the first free method for Instagram reels, TikTok videos, YouTube and post videos."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..post import IMAGE_EXT, Post, VIDEO_EXT
from .base import FetchFailed, has_audio, load_json, run_tool

# The audio track the speaker recorded, never a dub. yt-dlp marks YouTube's original track "original" in its format
# note and ranks it first; the explicit filter keeps that true if the ranking ever changes. On 31 October 2026 a Hannah
# Fry Short came back with an Arabic transcript, from the captions of YouTube's Arabic auto-dub (see pick_captions).
QUALITY = ("bv*[height<=720]+ba[format_note*=original]/bv*[height<=720]+ba[format_note!*=?dubbed]"
           "/b[height<=720]/bv*+ba[format_note*=original]/bv*+ba/b")

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


def _audio_formats(info: dict) -> list[dict]:
    return [f for f in info.get("formats") or [] if f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none")]


def _is_original(fmt: dict) -> bool:
    return (fmt.get("language_preference") or 0) >= 10 or "original" in str(fmt.get("format_note") or "").lower()


def original_language(info: dict) -> str | None:
    """The language the video was spoken in: the original audio track's, else the one yt-dlp names for the video."""
    for fmt in _audio_formats(info):
        if _is_original(fmt) and fmt.get("language"):
            return str(fmt["language"]).split("-")[0].lower()
    language = info.get("language")
    return str(language).split("-")[0].lower() if language else None


def original_audio_id(info: dict) -> str | None:
    """The best original-language audio-only format, when the video has more than one audio language."""
    audio = _audio_formats(info)
    if len({f.get("language") for f in audio if f.get("language")}) < 2:
        return None
    originals = [f for f in audio if _is_original(f) and "drc" not in str(f.get("format_id"))]
    if not originals:
        return None
    return str(max(originals, key=lambda f: (f.get("abr") or f.get("tbr") or 0))["format_id"])


def chose_dub(info: dict) -> bool:
    """yt-dlp picked an audio track in another language than the original one."""
    original = original_language(info)
    chosen = [f for f in info.get("requested_formats") or [info] if f.get("acodec") not in (None, "none")]
    if not original or not chosen:
        return False
    language = chosen[-1].get("language")
    return bool(language) and str(language).split("-")[0].lower() != original and not _is_original(chosen[-1])


def pick_captions(files: list[Path], original: str | None) -> Path | None:
    """The captions in the language spoken. YouTube auto-dubs a video into other languages and machine-captions each
    dub, and yt-dlp names every machine caption "<lang>-orig", so `.*-orig` brings back ar-orig beside en-orig. The
    old rule took the first by name: Arabic. Now the original language decides; with several and no way to tell,
    none, so the reading transcribes the original audio itself."""
    def lang(path: Path) -> str:
        parts = path.name.lower().split(".")
        return parts[-2] if len(parts) >= 3 else ""

    if original:
        for wanted in (f"{original}-orig", original):
            exact = [p for p in files if lang(p) == wanted]
            if exact:
                return exact[0]
        regional = [p for p in files if lang(p).startswith(f"{original}-") and not lang(p).endswith("-orig")]
        # Captions only in other languages are a translation or a dub's: the reading transcribes the audio instead.
        return regional[0] if regional else None
    orig = [p for p in files if lang(p).endswith("-orig")]
    if len(orig) == 1:
        return orig[0]
    if len(orig) > 1:
        return None
    english = [p for p in files if lang(p) == "en" or lang(p).startswith("en-")]
    return (english or files or [None])[0]


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
    ran = run_tool("yt-dlp", [*args, url], timeout=timeout)
    infos = sorted(folder.glob("*.info.json"))
    videos = [p for p in sorted(folder.iterdir()) if p.suffix.lower() in VIDEO_EXT and ".part" not in p.name]
    if not videos:
        raise FetchFailed("other", "no_video_in_post" if "no video" in ran.stderr.lower() else "no_media_written")
    info = load_json(infos[0]) if infos else {}
    audio_id = original_audio_id(info)
    if chose_dub(info) and audio_id:
        # A dub slipped through: fetch once more with the original track named outright.
        for path in videos:
            path.unlink()
        index = args.index("-f")
        again = [*args[:index + 1], f"bv*[height<=720]+{audio_id}/bv*+{audio_id}", *args[index + 2:], "--no-write-subs",
                 "--no-write-auto-subs", url]
        run_tool("yt-dlp", again, timeout=timeout)
        videos = [p for p in sorted(folder.iterdir()) if p.suffix.lower() in VIDEO_EXT and ".part" not in p.name]
        if not videos:
            raise FetchFailed("other", "no_original_audio")
        info = load_json(infos[0]) if infos and infos[0].is_file() else info
        if chose_dub(info):
            raise FetchFailed("other", "dubbed_audio_only")
    if need_audio and has_audio(videos[0]) is False:
        raise FetchFailed("other", "no_audio")
    post = post_from_info(info, platform, url)
    post.media = [videos[0]]
    subtitles = sorted(p for p in folder.iterdir() if p.suffix.lower() in (".vtt", ".srt"))
    post.captions_file = pick_captions(subtitles, original_language(info))
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
