"""LinkedIn without a login: one guest GET of the public post page (FETCH_METHODS.md, LinkedIn step 1)."""

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
COMMENTARY = re.compile(r'<p[^>]*data-test-id="main-feed-activity-card__commentary"[^>]*>(.*?)</p>', re.S)
VIDEO_SOURCES = re.compile(r'<video[^>]*data-sources="([^"]*)"', re.S)
CAPTIONS = re.compile(r'data-captions-url="([^"]+)"')
DOCUMENT = re.compile(r'data-native-document-config="([^"]*)"')
FEEDSHARE = re.compile(r'https://media\.licdn\.com/dms/image/[^"\s]*feedshare[^"\s]*')


def _text_of(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment)
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def _first(value):
    if isinstance(value, list):
        return value[0] if value else {}
    return value or {}


def _count(node: dict, kinds: tuple[str, ...]) -> int | None:
    for stat in node.get("interactionStatistic") or []:
        kind = str(_first(stat.get("interactionType")) if isinstance(stat.get("interactionType"), list) else stat.get("interactionType") or "")
        if any(k in kind for k in kinds):
            try:
                return int(stat.get("userInteractionCount"))
            except (TypeError, ValueError):
                return None
    return None


def parse_page(page: str, final_url: str = "") -> dict:
    if "/authwall" in final_url or "/login" in final_url or "/signup" in final_url:
        raise FetchFailed("login_wall", "signin_page")
    node: dict = {}
    for block in LD_JSON.findall(page):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        for candidate in data if isinstance(data, list) else data.get("@graph", [data]):
            if isinstance(candidate, dict) and candidate.get("@type") in ("SocialMediaPosting", "VideoObject",
                                                                           "DiscussionForumPosting", "Article"):
                node = candidate
                break
        if node:
            break
    commentary = COMMENTARY.search(page)
    text = _text_of(commentary.group(1)) if commentary else (node.get("articleBody") or node.get("text") or "")
    if not node and not commentary:
        if 'class="authwall' in page or "sign in" in page.lower()[:20000]:
            raise FetchFailed("login_wall", "signin_page")
        raise FetchFailed("other", "no_post_body")
    person = _first(node.get("creator") if node.get("@type") == "VideoObject" else node.get("author")) or _first(node.get("author"))
    video = None
    sources = VIDEO_SOURCES.search(page)
    if sources:
        try:
            listed = json.loads(html.unescape(sources.group(1)))
            best = max(listed, key=lambda s: int(s.get("data-bitrate") or s.get("bitrate") or 0) or len(str(s.get("src"))))
            video = best.get("src")
        except (ValueError, TypeError, AttributeError):
            video = None
    captions = CAPTIONS.search(page)
    caption_url = html.unescape(captions.group(1)) if captions else (_first(node.get("caption")).get("contentUrl") if isinstance(_first(node.get("caption")), dict) else None)
    # The largest size of each picture; never rewrite a size in a signed URL (it returns 403).
    by_picture: dict[str, tuple[int, str]] = {}
    for url in FEEDSHARE.findall(html.unescape(page)):
        key = url.split("/feedshare")[0]
        size_match = re.search(r"shrink_(\d+)", url)
        size = int(size_match.group(1)) if size_match else 0
        if key not in by_picture or size > by_picture[key][0]:
            by_picture[key] = (size, url)
    shape = "video" if video else "document" if DOCUMENT.search(page) else "image" if by_picture else "text"
    counts = {name: value for name, value in (("likes", _count(node, ("Like",))), ("comments", _count(node, ("Comment",))))
              if value is not None}
    return {
        "text": text,
        "author": person.get("name") if isinstance(person, dict) else None,
        "posted_at": node.get("uploadDate") if node.get("@type") == "VideoObject" else node.get("datePublished"),
        "images": [url for _, url in by_picture.values()],
        "video": video,
        "caption_url": caption_url,
        "transcript": node.get("transcript") if isinstance(node.get("transcript"), str) else None,
        "shape": shape,
        "counts": counts,
    }


def as_markdown(post: Post) -> str:
    lines = [f"# LinkedIn post by {post.author or 'unknown'}", ""]
    lines.append(f"Author: {post.author or ''}")
    lines.append(f"Posted: {post.posted_at or ''}")
    lines.append(f"Link: {post.url}")
    lines.append("Platform: linkedin")
    lines += ["", post.caption or ""]
    return "\n".join(lines).strip() + "\n"


def _get(url: str, timeout: float) -> tuple[str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.geturl(), response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 999:
            raise FetchFailed("blocked", "http_999") from None
        if exc.code in (401, 403):
            raise FetchFailed("login_wall", f"page_http_{exc.code}") from None
        raise FetchFailed("not_found" if exc.code in (404, 410) else "other", f"page_http_{exc.code}") from None
    except (socket.timeout, TimeoutError):
        raise FetchFailed("timeout", "page_timeout") from None
    except urllib.error.URLError:
        raise FetchFailed("other", "page_network_error") from None


def fetch(url: str, post_id: str | None, folder: Path, *, timeout: float = 20) -> Post:
    try:
        final_url, page = _get(url, timeout)
        found = parse_page(page, final_url)
    except FetchFailed as failure:
        # One GET of the /embed/ form on a sign-in page, no body or a timeout, never after a 999 (spec, step 1).
        if failure.detail == "http_999" or not post_id:
            raise
        final_url, page = _get(f"https://www.linkedin.com/embed/feed/update/urn:li:activity:{post_id}", timeout)
        found = parse_page(page, final_url)
    ident = post_id or "post"
    post = Post(platform="linkedin", url=url, post_id=ident, author=found["author"], posted_at=found["posted_at"],
                caption=found["text"], counts=found["counts"], method="linkedin_guest_page")
    text_file = folder / f"linkedin_{ident}.md"
    text_file.write_text(as_markdown(post), encoding="utf-8")
    post.media = [text_file]
    # A step works only when it returns the text and every media file the post shows.
    for index, image_url in enumerate(found["images"][:20], start=1):
        post.media.append(download(image_url, folder / f"linkedin_{ident}_{index:02d}.jpg", timeout=60))
    if found["video"]:
        post.media.append(download(found["video"], folder / f"linkedin_{ident}.mp4", timeout=300))
    if found["caption_url"]:
        try:
            post.captions_file = download(found["caption_url"], folder / f"linkedin_{ident}.vtt", timeout=60)
        except FetchFailed:
            post.captions_file = None
    post.shape = "text"
    return post
