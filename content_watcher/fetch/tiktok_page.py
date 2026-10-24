"""The free TikTok fallback: the post page's own JSON, fetched like a browser."""

from __future__ import annotations

import http.cookiejar
import json
import re
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ..post import Post
from ..urls import BROWSER_UA
from .base import FetchFailed, download

SCRIPT = re.compile(r'<script[^>]+id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', re.S)


def item_struct(page: str) -> dict:
    match = SCRIPT.search(page)
    if not match:
        if "captcha" in page.lower() or "verify" in page.lower():
            raise FetchFailed("blocked", "challenge_page")
        raise FetchFailed("other", "no_page_data")
    data = json.loads(match.group(1))
    detail = (data.get("__DEFAULT_SCOPE__") or {}).get("webapp.video-detail") or {}
    status = detail.get("statusCode")
    if status in (10204, 10216):
        raise FetchFailed("not_found", "post_removed")
    if status in (10222,):
        raise FetchFailed("login_wall", "private_post")
    item = (detail.get("itemInfo") or {}).get("itemStruct")
    if not item:
        raise FetchFailed("not_found" if status else "other", "no_item")
    return item


def parts(item: dict) -> tuple[dict, list[tuple[str, str]], str | None]:
    images = (item.get("imagePost") or {}).get("images") or []
    media: list[tuple[str, str]] = []
    for image in images:
        urls = (image.get("imageURL") or {}).get("urlList") or []
        if urls:
            media.append((urls[0], ".jpg"))
    if not media:
        video = item.get("video") or {}
        address = video.get("playAddr") or video.get("downloadAddr")
        if address:
            media.append((address, ".mp4"))
    music = (item.get("music") or {}).get("playUrl") if images else None
    stats = item.get("stats") or item.get("statsV2") or {}
    counts = {}
    for name, key in (("likes", "diggCount"), ("comments", "commentCount"), ("views", "playCount"), ("shares", "shareCount")):
        try:
            counts[name] = int(stats[key])
        except (KeyError, TypeError, ValueError):
            pass
    created = item.get("createTime")
    meta = {
        "post_id": item.get("id"),
        "author": (item.get("author") or {}).get("uniqueId"),
        "posted_at": datetime.fromtimestamp(int(created), tz=timezone.utc).isoformat() if created else None,
        "caption": item.get("desc"),
        "counts": counts,
    }
    return meta, media, music


def fetch(url: str, folder: Path, *, timeout: float = 30) -> Post:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Accept-Language": "en-US,en;q=0.9"})
    try:
        with opener.open(request, timeout=timeout) as response:
            page = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise FetchFailed("not_found" if exc.code == 404 else "blocked", f"page_http_{exc.code}") from None
    except (socket.timeout, TimeoutError):
        raise FetchFailed("timeout", "page_timeout") from None
    except urllib.error.URLError:
        raise FetchFailed("other", "page_network_error") from None
    meta, media, music = parts(item_struct(page))
    if not media:
        raise FetchFailed("other", "no_media_in_page")
    post_id = str(meta["post_id"] or "post")
    post = Post(platform="tiktok", url=url, post_id=post_id, author=meta["author"], posted_at=meta["posted_at"],
                caption=meta["caption"], counts=meta["counts"], method="tiktok_page")
    headers = {"Referer": "https://www.tiktok.com/"}
    for index, (media_url, ext) in enumerate(media, start=1):
        suffix = f"_{index:02d}" if len(media) > 1 else ""
        post.media.append(download(media_url, folder / f"tiktok_{post_id}{suffix}{ext}", headers=headers, opener=opener))
    if music:
        try:
            post.audio = download(music, folder / f"tiktok_{post_id}_sound.mp3", headers=headers, opener=opener)
        except FetchFailed:
            post.audio = None
    return post
