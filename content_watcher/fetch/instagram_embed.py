"""Instagram's own embed player, logged out (Krish, 2026-10-24: "Instagram and YouTube Shorts are the main ones, you
need to find a reliable way").

The embed is the page Instagram serves to any website that embeds a post, so it answers without a login. Its HTML
carries the post's own data (`contextJSON` > `gql_data` > `shortcode_media`): every slide in order with whether it is a
video, the file addresses, the caption and the account. Tested live on 2026-10-24 from a cloud machine, where the full
reel page sends a logged-out visitor to the login page: one reel, one three-video carousel and one photo, each read
exactly, the files downloaded with sound. A plain request needs a browser's navigation headers to get that data; if it
ever comes back without it, the same page is opened in a headless browser (Playwright), when installed.

A reel with licensed music has no file address in the embed ("Watch on Instagram"): it fails here as
`ig_licensed_audio` and goes on to the next step, which handles it.
"""

from __future__ import annotations

import json
import os
import re
import socket
import urllib.error
import urllib.request
from pathlib import Path

from ..post import Post
from ..urls import BROWSER_UA
from .base import FetchFailed, download

EMBED = "https://www.instagram.com/p/{code}/embed/captioned/"
HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Upgrade-Insecure-Requests": "1",
}
CONTEXT = re.compile(r'"contextJSON":"((?:[^"\\]|\\.)*)"')


def media_data(page: str) -> dict | None:
    """The post's shortcode_media from an embed page, or None when the page does not carry it."""
    found = CONTEXT.search(page)
    if not found:
        return None
    try:
        context = json.loads(json.loads('"' + found.group(1) + '"'))
    except ValueError:
        return None
    return ((context.get("gql_data") or {}).get("shortcode_media")) or None


def parts(media: dict) -> tuple[dict, list[tuple[str, str]]]:
    """The post's details and its files in order, as (url, extension)."""
    children = [edge.get("node") or {} for edge in (media.get("edge_sidecar_to_children") or {}).get("edges") or []]
    nodes = children or [media]
    files: list[tuple[str, str]] = []
    for node in nodes:
        if node.get("is_video"):
            if not node.get("video_url"):
                raise FetchFailed("other", "ig_licensed_audio")
            files.append((node["video_url"], ".mp4"))
        elif node.get("display_url"):
            files.append((node["display_url"], ".jpg"))
    if not files:
        raise FetchFailed("other", "ig_embed_no_media")
    edges = (media.get("edge_media_to_caption") or {}).get("edges") or []
    counts = {}
    for name, keys in (("likes", ("edge_liked_by", "edge_media_preview_like")), ("comments", ("edge_media_to_comment",))):
        for key in keys:
            value = (media.get(key) or {}).get("count")
            if isinstance(value, int):
                counts[name] = value
                break
    if isinstance(media.get("video_view_count"), int):
        counts["views"] = media["video_view_count"]
    taken = media.get("taken_at_timestamp")
    from datetime import datetime, timezone
    meta = {
        "post_id": media.get("shortcode"),
        "author": (media.get("owner") or {}).get("username"),
        "posted_at": datetime.fromtimestamp(int(taken), tz=timezone.utc).isoformat() if taken else None,
        "caption": (edges[0].get("node") or {}).get("text") if edges else None,
        "counts": counts,
    }
    return meta, files


def _plain(code: str, timeout: float) -> str:
    request = urllib.request.Request(EMBED.format(code=code), headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        exc.close()
        if exc.code == 404:
            raise FetchFailed("not_found", "ig_removed") from None
        if exc.code in (403, 429):
            raise FetchFailed("blocked", f"ig_embed_http_{exc.code}") from None
        raise FetchFailed("other", f"ig_embed_http_{exc.code}") from None
    except (socket.timeout, TimeoutError):
        raise FetchFailed("timeout", "ig_embed_timeout") from None
    except urllib.error.URLError:
        raise FetchFailed("other", "ig_embed_unreachable") from None


def _browser(code: str, timeout: float) -> str:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:  # noqa: BLE001
        return ""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.environ.get("CONTENT_WATCH_CHROMIUM") or None)
            try:
                page = browser.new_context(user_agent=BROWSER_UA, locale="en-US").new_page()
                response = page.goto(EMBED.format(code=code), wait_until="domcontentloaded", timeout=timeout * 1000)
                return response.text() if response else ""
            finally:
                browser.close()
    except Exception:  # noqa: BLE001 - a browser problem is a missed step, never a crash
        return ""


def fetch(url: str, shortcode: str, folder: Path, *, timeout: float = 30) -> Post:
    page = _plain(shortcode, timeout)
    media = media_data(page)
    if media is None:
        page = _browser(shortcode, timeout) or page
        media = media_data(page)
    if media is None:
        if "may have been removed" in page or "link to this photo or video may be broken" in page:
            raise FetchFailed("not_found", "ig_removed")
        raise FetchFailed("other", "ig_embed_no_data")
    meta, files = parts(media)
    code = meta["post_id"] or shortcode
    post = Post("instagram", url, code, meta["author"], meta["posted_at"], meta["caption"], meta["counts"],
                method="instagram_embed")
    for index, (file_url, ext) in enumerate(files, start=1):
        suffix = f"_{index:02d}" if len(files) > 1 else ""
        post.media.append(download(file_url, folder / f"instagram_{code}{suffix}{ext}", timeout=120))
    post.shape = "carousel" if len(files) > 1 else ("video" if files[0][1] == ".mp4" else "image")
    return post


def cover_only(url: str, shortcode: str, folder: Path, *, timeout: float = 30) -> Post:
    """The last resort for a post no step could get the files of (a licensed-music reel that every other step also
    missed): its cover picture and caption from the embed, so the link still becomes a card. The reading says it is a
    picture; the file name and the note say the video was out of reach."""
    page = _plain(shortcode, timeout)
    media = media_data(page) or media_data(_browser(shortcode, timeout) or "")
    if not media or not media.get("display_url"):
        raise FetchFailed("other", "ig_embed_no_data")
    edges = (media.get("edge_media_to_caption") or {}).get("edges") or []
    caption = (edges[0].get("node") or {}).get("text") if edges else None
    code = media.get("shortcode") or shortcode
    note = "Cover picture only: the video could not be downloaded (licensed music keeps it out of reach)."
    post = Post("instagram", url, code, (media.get("owner") or {}).get("username"), None,
                f"{caption}\n\n({note})" if caption else f"({note})", method="instagram_cover_only")
    post.media = [download(media["display_url"], folder / f"instagram_{code}_cover.jpg", timeout=60)]
    post.shape = "image"
    return post
