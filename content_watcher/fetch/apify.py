"""The paid fallback on Apify: only with a standing monthly cap Krish set, and a local spend ledger."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .. import secrets
from ..config import Config, state_dir
from ..post import Post
from .base import FetchFailed, download, ext_from

API = "https://api.apify.com/v2"

# Estimated cost of one run at Krish's tier (brief section 6), with headroom for the run's start fee.
ACTORS = {
    "instagram_reel": ("apify~instagram-reel-scraper", 0.01),
    "instagram_post": ("apify~instagram-scraper", 0.01),
    "tiktok": ("clockworks~tiktok-video-scraper", 0.01),
}


def ledger_path() -> Path:
    return state_dir() / "apify-spend.json"


def month_spend(now: datetime | None = None) -> float:
    month = (now or datetime.now(timezone.utc)).strftime("%Y-%m")
    try:
        return float(json.loads(ledger_path().read_text(encoding="utf-8")).get(month, 0.0))
    except (OSError, ValueError):
        return 0.0


def record_spend(amount: float, now: datetime | None = None) -> None:
    month = (now or datetime.now(timezone.utc)).strftime("%Y-%m")
    target = ledger_path()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data[month] = round(float(data.get(month, 0.0)) + amount, 4)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")


def allowed(config: Config, estimate: float) -> None:
    """Raise unless a paid run of this estimate fits Krish's standing cap."""
    if not config.apify_enabled or config.apify_monthly_cap_usd <= 0:
        raise FetchFailed("blocked", "spend_not_approved")
    if month_spend() + estimate > config.apify_monthly_cap_usd:
        raise FetchFailed("blocked", "spend_cap_reached")
    if not secrets.apify_token():
        raise FetchFailed("blocked", "no_apify_token")


def run_actor(actor: str, payload: dict, *, timeout: float = 300, opener=None) -> list[dict]:
    token = secrets.apify_token()
    request = urllib.request.Request(
        f"{API}/acts/{actor}/run-sync-get-dataset-items?timeout={int(timeout - 20)}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    opener = opener or urllib.request.build_opener()
    try:
        with opener.open(request, timeout=timeout) as response:
            items = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 402:
            raise FetchFailed("blocked", "apify_out_of_credit") from None
        if exc.code in (401, 403):
            raise FetchFailed("blocked", "apify_refused") from None
        if exc.code == 408:
            raise FetchFailed("timeout", "apify_timeout") from None
        raise FetchFailed("other", f"apify_http_{exc.code}") from None
    except (socket.timeout, TimeoutError):
        raise FetchFailed("timeout", "apify_timeout") from None
    except urllib.error.URLError:
        raise FetchFailed("other", "apify_network_error") from None
    if not isinstance(items, list):
        raise FetchFailed("other", "apify_bad_response")
    return items


def _item_error(item: dict) -> None:
    error = str(item.get("error") or item.get("errorDescription") or "")
    if not error:
        return
    lowered = error.lower()
    if "not_found" in lowered or "not found" in lowered or "does not exist" in lowered:
        raise FetchFailed("not_found", "apify_not_found")
    if "private" in lowered or "restricted" in lowered or "login" in lowered:
        raise FetchFailed("login_wall", "apify_restricted")
    raise FetchFailed("other", "apify_item_error")


def instagram_parts(item: dict) -> tuple[dict, list[tuple[str, str]]]:
    """The post's details and its media URLs in post order, as (url, default extension)."""
    _item_error(item)
    media: list[tuple[str, str]] = []
    children = item.get("childPosts") or []
    if children:
        for child in children:
            if (child.get("type") == "Video" or child.get("videoUrl")) and child.get("videoUrl"):
                media.append((child["videoUrl"], ".mp4"))
            elif child.get("displayUrl"):
                media.append((child["displayUrl"], ".jpg"))
    elif item.get("type") == "Sidecar" and item.get("images"):
        media = [(url, ".jpg") for url in item["images"]]
    elif item.get("downloadedVideo") or item.get("videoUrl"):
        media.append((item.get("downloadedVideo") or item["videoUrl"], ".mp4"))
    elif item.get("displayUrl"):
        media.append((item["displayUrl"], ".jpg"))
    counts = {
        name: int(item[key]) for name, key in (("likes", "likesCount"), ("comments", "commentsCount"),
                                               ("views", "videoPlayCount"), ("views", "videoViewCount"))
        if isinstance(item.get(key), (int, float)) and int(item[key]) >= 0
    }
    meta = {
        "post_id": item.get("shortCode") or item.get("id"),
        "author": item.get("ownerUsername"),
        "posted_at": item.get("timestamp"),
        "caption": item.get("caption"),
        "counts": counts,
    }
    return meta, media


def tiktok_parts(item: dict) -> tuple[dict, list[tuple[str, str]], str | None, str | None]:
    _item_error(item)
    media: list[tuple[str, str]] = []
    slides = item.get("slideshowImageLinks") or []
    if slides:
        media = [((s.get("downloadLink") or s.get("tiktokLink")), ".jpg") for s in slides if s.get("downloadLink") or s.get("tiktokLink")]
    else:
        video = (item.get("mediaUrls") or [None])[0] or (item.get("videoMeta") or {}).get("downloadAddr")
        if video:
            media.append((video, ".mp4"))
    subtitle = None
    for link in (item.get("videoMeta") or {}).get("subtitleLinks") or []:
        if str(link.get("language", "")).lower().startswith("en") and link.get("downloadLink"):
            subtitle = link["downloadLink"]
            break
    music = (item.get("musicMeta") or {}).get("playUrl") if slides else None
    counts = {
        name: int(item[key]) for name, key in (("likes", "diggCount"), ("comments", "commentCount"),
                                               ("views", "playCount"), ("shares", "shareCount"))
        if isinstance(item.get(key), (int, float))
    }
    meta = {
        "post_id": item.get("id"),
        "author": (item.get("authorMeta") or {}).get("name"),
        "posted_at": item.get("createTimeISO"),
        "caption": item.get("text"),
        "counts": counts,
    }
    return meta, media, subtitle, music


def fetch(url: str, platform: str, folder: Path, config: Config, *, actor_key: str, opener=None) -> Post:
    actor, estimate = ACTORS[actor_key]
    allowed(config, estimate)
    if actor_key == "instagram_reel":
        payload = {"username": [url], "includeDownloadedVideo": True, "includeTranscript": False}
    elif actor_key == "instagram_post":
        payload = {"directUrls": [url], "resultsType": "posts", "resultsLimit": 1, "addParentData": False}
    else:
        payload = {
            "postURLs": [url], "shouldDownloadVideos": True, "shouldDownloadSlideshowImages": True,
            "shouldDownloadCovers": False, "downloadSubtitlesOptions": "DOWNLOAD_SUBTITLES",
            "videoKvStoreIdOrName": "content-watcher",
        }
    items = run_actor(actor, payload, opener=opener)
    record_spend(estimate)
    if not items:
        raise FetchFailed("not_found", "apify_empty")
    subtitle = music = None
    if platform == "tiktok":
        meta, media, subtitle, music = tiktok_parts(items[0])
    else:
        meta, media = instagram_parts(items[0])
    if not media:
        raise FetchFailed("other", "apify_no_media")
    post_id = str(meta.get("post_id") or "post")
    post = Post(platform=platform, url=url, post_id=post_id, author=meta.get("author"),
                posted_at=meta.get("posted_at"), caption=meta.get("caption"), counts=meta.get("counts") or {},
                method=f"apify_{actor_key}")
    for index, (media_url, default_ext) in enumerate(media, start=1):
        suffix = f"_{index:02d}" if len(media) > 1 else ""
        target = folder / f"{platform}_{post_id}{suffix}{ext_from(media_url, default_ext)}"
        post.media.append(download(media_url, target, opener=opener))
    if subtitle:
        try:
            post.captions_file = download(subtitle, folder / f"{platform}_{post_id}.en.vtt", opener=opener)
        except FetchFailed:
            post.captions_file = None
    if music:
        try:
            post.audio = download(music, folder / f"{platform}_{post_id}_sound{ext_from(music, '.mp3')}", opener=opener)
        except FetchFailed:
            post.audio = None
    return post
