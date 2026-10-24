"""YouTube beyond yt-dlp (FETCH_METHODS.md, YouTube): oEmbed to check the link and give the title and channel, and
two routes to the words when the video itself will not come: youtube-transcript-api (free) and Apify's
johnvc/YoutubeTranscripts (paid, under the standing cap). Words without the file are filed as a text card."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ..config import Config
from ..post import Post
from ..urls import BROWSER_UA
from . import apify
from .base import FetchFailed, text_post


def oembed(url: str, *, timeout: float = 20, opener=None) -> dict:
    """The video exists and is public: its title and channel. Anything else is a class, so the chain stops early."""
    query = urllib.parse.urlencode({"url": url, "format": "json"})
    request = urllib.request.Request(f"https://www.youtube.com/oembed?{query}", headers={"User-Agent": BROWSER_UA})
    opener = opener or urllib.request.build_opener()
    try:
        with opener.open(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        exc.close()
        if exc.code in (401, 403):
            raise FetchFailed("login_wall", "yt_private") from None
        if exc.code in (400, 404):
            raise FetchFailed("not_found", "yt_not_found") from None
        raise FetchFailed("other", f"yt_oembed_http_{exc.code}") from None
    except (socket.timeout, TimeoutError):
        raise FetchFailed("timeout", "yt_oembed_timeout") from None
    except (urllib.error.URLError, ValueError):
        raise FetchFailed("other", "yt_oembed_unreachable") from None


def _transcript_body(snippets: list[dict]) -> str:
    lines = []
    for snippet in snippets:
        start = float(snippet.get("start") or 0)
        lines.append(f"[{int(start // 60)}:{start % 60:04.1f}] {str(snippet.get('text') or '').strip()}")
    return "\n".join(line for line in lines if not line.endswith("] "))


def transcript_api(url: str, video_id: str, folder: Path, meta: dict) -> Post:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except Exception:  # noqa: BLE001
        raise FetchFailed("other", "no_youtube_transcript_api") from None
    try:
        api = YouTubeTranscriptApi()
        tracks = list(api.list(video_id))
        if not tracks:
            raise FetchFailed("other", "no_captions")
        manual = [t for t in tracks if not getattr(t, "is_generated", False)]
        track = (manual or tracks)[0]
        fetched = track.fetch()
        snippets = [{"start": s.start, "text": s.text} for s in fetched]
    except FetchFailed:
        raise
    except Exception as exc:  # noqa: BLE001 - the library's own errors, by name only
        name = type(exc).__name__
        if "Blocked" in name:
            raise FetchFailed("blocked", "yt_transcript_blocked") from None
        if "Unavailable" in name or "NotFound" in name or "Disabled" in name:
            raise FetchFailed("other", "no_captions") from None
        raise FetchFailed("other", "yt_transcript_error") from None
    if not snippets:
        raise FetchFailed("other", "no_captions")
    post = Post("youtube", url, video_id, meta.get("author_name"), None, meta.get("title"), method="yt_transcript_api")
    text_post(post, folder, title=meta.get("title") or f"YouTube video {video_id}", body=_transcript_body(snippets),
              note="Words only: the video could not be downloaded.")
    return post


def johnvc(url: str, video_id: str, folder: Path, config: Config, meta: dict, *, opener=None) -> Post:
    actor, estimate = apify.ACTORS["youtube_transcript"]
    apify.allowed(config, estimate)
    apify.record_spend(estimate)
    items = apify.run_actor(actor, {"youtube_url": url, "languages": ["en"], "include_metadata": True,
                                    "include_extended_metadata": True}, opener=opener)
    if not items:
        raise FetchFailed("other", "apify_item_error")
    item = items[0]
    apify._item_error(item)
    raw = item.get("transcript") or item.get("captions") or item.get("data") or []
    if isinstance(raw, str):
        snippets = [{"start": 0, "text": raw}]
    else:
        snippets = [{"start": s.get("start") or s.get("offset") or 0, "text": s.get("text") or ""} for s in raw if isinstance(s, dict)]
    if not any(s["text"] for s in snippets):
        raise FetchFailed("other", "apify_item_error")
    post = Post("youtube", url, video_id, item.get("channel") or item.get("author") or meta.get("author_name"),
                item.get("upload_date"), item.get("title") or meta.get("title"), method="apify_youtube_transcript")
    text_post(post, folder, title=post.caption or f"YouTube video {video_id}", body=_transcript_body(snippets),
              note="Words only: the video could not be downloaded.")
    return post
