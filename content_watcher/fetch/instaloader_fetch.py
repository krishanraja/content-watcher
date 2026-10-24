"""Instaloader, anonymous, for one Instagram post: the video, or every image of a carousel, with its caption
(FETCH_METHODS.md, Instagram step 4). Never logged in."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..post import IMAGE_EXT, Post, VIDEO_EXT
from .base import FetchFailed, run_tool


def post_from_json(data: dict, url: str) -> Post:
    node = data.get("node") or data
    owner = node.get("owner") or {}
    edges = ((node.get("edge_media_to_caption") or {}).get("edges") or [])
    caption = edges[0].get("node", {}).get("text") if edges else node.get("caption")
    taken = node.get("taken_at_timestamp") or node.get("taken_at")
    counts = {}
    for name, keys in (("likes", ("edge_media_preview_like", "edge_liked_by")), ("comments", ("edge_media_to_comment",))):
        for key in keys:
            value = (node.get(key) or {}).get("count")
            if isinstance(value, int):
                counts[name] = value
                break
    if isinstance(node.get("video_view_count"), int):
        counts["views"] = node["video_view_count"]
    return Post(
        "instagram", url, node.get("shortcode"), owner.get("username"),
        datetime.fromtimestamp(int(taken), tz=timezone.utc).isoformat() if taken else None, caption, counts,
    )


def fetch(url: str, shortcode: str, folder: Path, *, timeout: float = 300) -> Post:
    run_tool("instaloader", [
        "--dirname-pattern", folder, "--filename-pattern", "{shortcode}", "--no-compress-json",
        "--no-profile-pic", "--no-video-thumbnails", "--quiet", "--", f"-{shortcode}",
    ], timeout=timeout)
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in VIDEO_EXT | IMAGE_EXT)
    # A video slide also saves its cover picture under the same name: the video is the slide.
    slides: dict[str, Path] = {}
    for path in files:
        if path.stem in slides and slides[path.stem].suffix.lower() in VIDEO_EXT:
            continue
        slides[path.stem] = path
    media = [slides[key] for key in sorted(slides, key=lambda stem: (len(stem), stem))]
    if not media:
        raise FetchFailed("other", "no_media_written")
    meta = next((p for p in folder.glob("*.json")), None)
    post = post_from_json(json.loads(meta.read_text(encoding="utf-8")), url) if meta else Post("instagram", url, shortcode)
    post.post_id = post.post_id or shortcode
    if not post.caption:
        text = next((p for p in folder.glob("*.txt")), None)
        post.caption = text.read_text(encoding="utf-8").strip() if text else None
    post.media = media
    post.method = "instaloader"
    for extra in [*folder.glob("*.json"), *folder.glob("*.txt")]:
        extra.unlink()
    return post
