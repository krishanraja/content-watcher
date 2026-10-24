"""Fetching one post from a pasted link: each platform's methods in order, first success wins."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .. import urls
from ..config import Config
from ..post import Post
from . import apify, gallerydl, linkedin_page, tiktok_page, ytdlp
from .base import STATUS_CLASSES, FetchFailed

@dataclass
class Attempt:
    method: str
    outcome: str  # ok, or status_class:detail


@dataclass
class FetchResult:
    post: Post | None
    attempts: list[Attempt] = field(default_factory=list)
    status_class: str | None = None
    detail: str | None = None


def _methods(link: urls.PostLink, config: Config) -> list[tuple[str, Callable[[Path], Post]]]:
    """Each platform's chain for Krish's D2 answer (Apify after the free methods, $5 a month, none of his
    accounts), in the order docs/FETCH_METHODS.md gives."""
    url, platform = link.url, link.platform
    cookies = config.cookies.get(platform)
    chain: list[tuple[str, Callable[[Path], Post]]] = []
    if platform == "instagram":
        if link.kind == "reel":
            chain.append(("ytdlp", lambda f: ytdlp.fetch(url, platform, f)))
            chain.append(("apify_instagram_reel", lambda f: apify.fetch(
                url, platform, f, config, actor_key="instagram_reel", expected_id=link.post_id)))
        else:
            chain.append(("ytdlp_carousel", lambda f: ytdlp.fetch_carousel(url, platform, f)))
            chain.append(("apify_instagram_post", lambda f: apify.fetch(
                url, platform, f, config, actor_key="instagram_post", expected_id=link.post_id)))
        if cookies:
            chain.append(("gallerydl_cookies", lambda f: gallerydl.fetch(url, platform, f, cookies_profile=cookies)))
    elif platform == "tiktok":
        if link.kind != "photo":
            chain.append(("ytdlp", lambda f: ytdlp.fetch(url, platform, f, captions="all", need_audio=True)))
        chain.append(("gallerydl", lambda f: gallerydl.fetch(url, platform, f)))
        chain.append(("tiktok_page", lambda f: tiktok_page.fetch(url, f)))
        chain.append(("apify_tiktok", lambda f: apify.fetch(url, platform, f, config, actor_key="tiktok")))
        if cookies:
            chain.append(("ytdlp_cookies", lambda f: ytdlp.fetch(url, platform, f, captions="all", cookies_profile=cookies)))
    elif platform == "youtube":
        chain.append(("ytdlp", lambda f: ytdlp.fetch(url, platform, f, captions="youtube")))
        # On a refusal, once more as the mobile web client with the PO token provider (FETCH_METHODS.md, YouTube).
        chain.append(("ytdlp_mweb", lambda f: ytdlp.fetch(url, platform, f, captions="youtube", method="ytdlp_mweb",
                                                          extra=["--extractor-args", "youtube:player_client=mweb"])))
        if cookies:
            chain.append(("ytdlp_cookies", lambda f: ytdlp.fetch(url, platform, f, captions="youtube", cookies_profile=cookies)))
    elif platform == "linkedin":
        # yt-dlp is not in LinkedIn's chain: the guest page lists the same video files (FETCH_METHODS.md, step 1).
        chain.append(("linkedin_guest_page", lambda f: linkedin_page.fetch(url, link.post_id, f)))
    else:
        chain.append(("ytdlp", lambda f: ytdlp.fetch(url, platform, f)))
    return chain


def _standardise(post: Post, folder: Path) -> None:
    """Name files <platform>_<post id>[_NN].<ext>, in post order, so the tagger reads hints from names."""
    ident = re.sub(r"[^A-Za-z0-9_-]", "", post.post_id or "") or "post"
    post.post_id = post.post_id or ident
    renamed = []
    many = len(post.media) > 1
    for index, path in enumerate(post.media, start=1):
        name = f"{post.platform}_{ident}{f'_{index:02d}' if many else ''}{path.suffix.lower()}"
        target = folder / name
        if path.resolve() != target.resolve():
            path.replace(target)
        renamed.append(target)
    post.media = renamed
    if post.audio:
        target = folder / f"{post.platform}_{ident}_sound{post.audio.suffix.lower()}"
        if post.audio.resolve() != target.resolve():
            post.audio.replace(target)
        post.audio = target


def fetch(url: str, dest: Path, config: Config | None = None, *, resolve: bool = True) -> FetchResult:
    """Fetch one post into dest/<platform>_<id>/ with post.json beside the media."""
    config = config or Config.load()
    try:
        link = urls.normalise(url) if resolve else urls.parse(url)
    except Exception:  # noqa: BLE001 - a share link that will not resolve
        link = urls.parse(url)
        if link.needs_resolve:
            return FetchResult(None, [Attempt("resolve", "not_found:short_link_dead")], "not_found", "short_link_dead")
    if link.platform in ("instagram", "tiktok", "youtube", "linkedin") and not link.post_id:
        return FetchResult(None, [Attempt("normalise", "not_found:unsupported_url")], "not_found", "unsupported_url")
    result = FetchResult(None)
    work = dest / f".fetching_{link.platform}_{link.post_id or 'post'}"
    for name, method in _methods(link, config):
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        try:
            post = method(work)
        except FetchFailed as failure:
            result.attempts.append(Attempt(name, f"{failure.status_class}:{failure.detail}"))
            continue
        post.url = link.url
        post.post_id = post.post_id or link.post_id
        _standardise(post, work)
        final = dest / f"{post.platform}_{post.post_id}"
        if final.exists():
            shutil.rmtree(final)
        work.replace(final)
        post.media = [final / p.name for p in post.media]
        post.audio = final / post.audio.name if post.audio else None
        post.captions_file = final / post.captions_file.name if post.captions_file else None
        post.save(final)
        result.post = post
        result.attempts.append(Attempt(name, "ok"))
        return result
    if work.exists():
        shutil.rmtree(work)
    # Every method failed: the request reports the last step's class (FETCH_METHODS.md, every chain).
    if result.attempts:
        result.status_class, result.detail = result.attempts[-1].outcome.split(":", 1)
    else:
        result.status_class, result.detail = "other", "no_method"
    return result


__all__ = ["fetch", "FetchResult", "FetchFailed", "STATUS_CLASSES"]
