"""LinkedIn without a login, where the post is public (provisional until the research run lands)."""

from __future__ import annotations

import html
import json
import re
import socket
import urllib.error
import urllib.request
from pathlib import Path

from ..post import Post
from ..urls import BROWSER_UA
from .base import FetchFailed, download

LD_JSON = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.S)


def _meta(page: str, name: str) -> str | None:
    match = re.search(rf'<meta[^>]+(?:property|name)="{re.escape(name)}"[^>]+content="([^"]*)"', page)
    return html.unescape(match.group(1)) if match else None


def parse_page(page: str, final_url: str = "") -> dict:
    if "/authwall" in final_url or "/login" in final_url or 'class="authwall' in page:
        raise FetchFailed("login_wall", "authwall")
    for block in LD_JSON.findall(page):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        for node in data if isinstance(data, list) else data.get("@graph", [data]):
            if not isinstance(node, dict) or node.get("@type") not in ("SocialMediaPosting", "DiscussionForumPosting", "Article", "VideoObject"):
                continue
            author = node.get("author") or {}
            if isinstance(author, list):
                author = author[0] if author else {}
            images = node.get("image") or []
            if isinstance(images, dict):
                images = [images]
            if isinstance(images, str):
                images = [images]
            video = node.get("video") or {}
            if isinstance(video, list):
                video = video[0] if video else {}
            return {
                "text": node.get("articleBody") or node.get("text") or node.get("description") or "",
                "author": author.get("name") if isinstance(author, dict) else None,
                "posted_at": node.get("datePublished"),
                "images": [i.get("url") if isinstance(i, dict) else i for i in images if i],
                "video": video.get("contentUrl") if isinstance(video, dict) else None,
                "counts": {},
            }
    text = _meta(page, "og:description") or _meta(page, "description")
    if not text:
        raise FetchFailed("login_wall", "no_public_text")
    return {"text": text, "author": _meta(page, "og:title"), "posted_at": None, "images": [], "video": None, "counts": {}}


def as_markdown(post: Post) -> str:
    lines = [f"# LinkedIn post by {post.author or 'unknown'}", ""]
    lines.append(f"Author: {post.author or ''}")
    lines.append(f"Posted: {post.posted_at or ''}")
    lines.append(f"Link: {post.url}")
    lines.append("Platform: linkedin")
    lines += ["", post.caption or ""]
    return "\n".join(lines).strip() + "\n"


def fetch(url: str, post_id: str | None, folder: Path, *, timeout: float = 30) -> Post:
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            final_url = response.geturl()
            page = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 999):
            raise FetchFailed("login_wall" if exc.code != 999 else "blocked", f"page_http_{exc.code}") from None
        raise FetchFailed("not_found" if exc.code in (404, 410) else "other", f"page_http_{exc.code}") from None
    except (socket.timeout, TimeoutError):
        raise FetchFailed("timeout", "page_timeout") from None
    except urllib.error.URLError:
        raise FetchFailed("other", "page_network_error") from None
    found = parse_page(page, final_url)
    ident = post_id or "post"
    post = Post(platform="linkedin", url=url, post_id=ident, author=found["author"], posted_at=found["posted_at"],
                caption=found["text"], counts=found["counts"], method="linkedin_public_page")
    text_file = folder / f"linkedin_{ident}.md"
    text_file.write_text(as_markdown(post), encoding="utf-8")
    post.media = [text_file]
    for index, image_url in enumerate(found["images"][:20], start=1):
        try:
            post.media.append(download(image_url, folder / f"linkedin_{ident}_{index:02d}.jpg", timeout=timeout))
        except FetchFailed:
            continue
    if found["video"]:
        try:
            post.media.append(download(found["video"], folder / f"linkedin_{ident}.mp4", timeout=120))
        except FetchFailed:
            pass
    post.shape = "text"
    return post
