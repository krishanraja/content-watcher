"""Free "paste a link, press download" services. Krish, 2026-10-24: "There are so many free sites out there that I
just copy a link in, press download, and it lets me select the quality and whatnot." Each one sees the link sent to
it, and none has a contract, so they sit after the open tools and before any spend.

- TikWM (TikTok): a JSON API, tested live on 2026-10-24 (video, caption, author, counts, a working download).
- Tikmate (TikTok): a JSON lookup, tested live on 2026-10-24; its download host was not reachable from the test
  machine, so the download is unverified until the first run at home.
- cobalt (every platform): the open-source downloader many such sites run on. Run it on the home computer
  (scripts/cobalt/README.md) so no third party sees the links; a hosted instance needs its key.
"""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ..post import Post
from ..urls import BROWSER_UA
from .base import FetchFailed, download, ext_from

TIKWM = "https://www.tikwm.com"
TIKMATE = "https://api.tikmate.app/api/lookup"


def _json(request: urllib.request.Request, *, timeout: float, opener=None, label: str) -> dict:
    opener = opener or urllib.request.build_opener()
    try:
        with opener.open(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        exc.close()
        if exc.code == 404:
            raise FetchFailed("not_found", f"{label}_404") from None
        if exc.code in (401, 403, 429):
            raise FetchFailed("blocked", f"{label}_refused") from None
        raise FetchFailed("other", f"{label}_http_{exc.code}") from None
    except (socket.timeout, TimeoutError):
        raise FetchFailed("timeout", f"{label}_timeout") from None
    except urllib.error.URLError:
        raise FetchFailed("other", f"{label}_unreachable") from None
    except ValueError:
        raise FetchFailed("other", f"{label}_bad_response") from None


def _absolute(url: str | None, base: str) -> str | None:
    if not url:
        return None
    return base + url if url.startswith("/") else url


def tikwm_parts(data: dict) -> tuple[dict, list[tuple[str, str]], str | None]:
    """The post's details, its media in order, and a photo post's sound."""
    if data.get("code") != 0 or not isinstance(data.get("data"), dict):
        message = str(data.get("msg") or "").lower()
        if "not exist" in message or "removed" in message or "private" in message:
            raise FetchFailed("not_found", "tikwm_not_found")
        raise FetchFailed("other", "tikwm_error")
    item = data["data"]
    images = [_absolute(url, TIKWM) for url in item.get("images") or [] if url]
    media = [(url, ".jpg") for url in images if url]
    if not media:
        video = _absolute(item.get("play") or item.get("hdplay") or item.get("wmplay"), TIKWM)
        if video:
            media.append((video, ".mp4"))
    created = item.get("create_time")
    meta = {
        "post_id": str(item.get("id") or "") or None,
        "author": (item.get("author") or {}).get("unique_id"),
        "posted_at": datetime.fromtimestamp(int(created), tz=timezone.utc).isoformat() if created else None,
        "caption": item.get("title"),
        "counts": {name: int(item[key]) for name, key in (("views", "play_count"), ("likes", "digg_count"),
                                                         ("comments", "comment_count"), ("shares", "share_count"))
                   if isinstance(item.get(key), (int, float))},
    }
    music = _absolute(item.get("music"), TIKWM) if images else None
    return meta, media, music


def _save(post: Post, folder: Path, media: list[tuple[str, str]], opener=None) -> Post:
    ident = post.post_id or "post"
    for index, (url, ext) in enumerate(media, start=1):
        suffix = f"_{index:02d}" if len(media) > 1 else ""
        post.media.append(download(url, folder / f"{post.platform}_{ident}{suffix}{ext_from(url, ext)}", opener=opener,
                                   headers={"Referer": "https://www.tiktok.com/"} if post.platform == "tiktok" else None))
    return post


def tikwm(url: str, folder: Path, *, timeout: float = 30, opener=None) -> Post:
    query = urllib.parse.urlencode({"url": url, "hd": 0})
    data = _json(urllib.request.Request(f"{TIKWM}/api/?{query}", headers={"User-Agent": BROWSER_UA}),
                 timeout=timeout, opener=opener, label="tikwm")
    meta, media, music = tikwm_parts(data)
    if not media:
        raise FetchFailed("other", "tikwm_no_media")
    post = Post("tiktok", url, meta["post_id"], meta["author"], meta["posted_at"], meta["caption"], meta["counts"],
                method="tikwm")
    _save(post, folder, media, opener)
    if music:
        try:
            post.audio = download(music, folder / f"tiktok_{post.post_id}_sound.mp3", opener=opener)
        except FetchFailed:
            post.audio = None
    return post


def tikmate_parts(data: dict) -> tuple[dict, str]:
    if not data.get("success") or not data.get("token") or not data.get("id"):
        raise FetchFailed("other", "tikmate_error")
    counts = {}
    for name, key in (("likes", "like_count"), ("comments", "comment_count"), ("shares", "share_count")):
        try:
            counts[name] = int(str(data.get(key)).replace(",", ""))
        except (TypeError, ValueError):
            pass
    posted = None
    try:
        posted = datetime.strptime(str(data.get("create_time")), "%b %d, %Y").date().isoformat()
    except ValueError:
        posted = None
    meta = {"post_id": str(data["id"]), "author": data.get("author_id"), "posted_at": posted,
            "caption": data.get("desc"), "counts": counts}
    return meta, f"https://tikmate.app/download/{data['token']}/{data['id']}.mp4"


def tikmate(url: str, folder: Path, *, timeout: float = 30, opener=None) -> Post:
    request = urllib.request.Request(TIKMATE, data=urllib.parse.urlencode({"url": url}).encode(),
                                     headers={"User-Agent": BROWSER_UA,
                                              "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    meta, video = tikmate_parts(_json(request, timeout=timeout, opener=opener, label="tikmate"))
    post = Post("tiktok", url, meta["post_id"], meta["author"], meta["posted_at"], meta["caption"], meta["counts"],
                method="tikmate")
    return _save(post, folder, [(video, ".mp4")], opener)


COBALT_ERRORS = [
    ("private", "login_wall"), ("age", "login_wall"), ("login", "login_wall"),
    ("unavailable", "not_found"), ("not_found", "not_found"), ("empty", "not_found"),
    ("too_long", "too_big"), ("too_big", "too_big"),
    ("rate", "blocked"), ("auth", "blocked"), ("blocked", "blocked"), ("captcha", "blocked"),
    ("timeout", "timeout"),
]


def cobalt_parts(data: dict) -> list[tuple[str, str]]:
    status = data.get("status")
    if status == "error":
        code = str((data.get("error") or {}).get("code") or "")
        for word, status_class in COBALT_ERRORS:
            if word in code:
                raise FetchFailed(status_class, "cobalt_" + word)
        raise FetchFailed("other", "cobalt_error")
    if status in ("tunnel", "redirect", "stream"):
        filename = str(data.get("filename") or "")
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ".mp4"
        return [(data["url"], ext)]
    if status == "picker":
        items = []
        for item in data.get("picker") or []:
            if item.get("url"):
                items.append((item["url"], ".mp4" if item.get("type") in ("video", "gif") else ".jpg"))
        if items:
            return items
    raise FetchFailed("other", "cobalt_no_media")


def cobalt(url: str, platform: str, post_id: str | None, folder: Path, base_url: str, *, timeout: float = 60,
           opener=None) -> Post:
    headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": BROWSER_UA}
    key = os.environ.get("COBALT_API_KEY")
    if key:
        headers["Authorization"] = f"Api-Key {key}"
    body = {"url": url, "videoQuality": "720", "downloadMode": "auto", "filenameStyle": "basic"}
    request = urllib.request.Request(base_url.rstrip("/") + "/", data=json.dumps(body).encode(), headers=headers,
                                     method="POST")
    media = cobalt_parts(_json(request, timeout=timeout, opener=opener, label="cobalt"))
    post = Post(platform, url, post_id, method="cobalt")
    return _save(post, folder, media, opener)
