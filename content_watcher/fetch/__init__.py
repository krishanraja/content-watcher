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
from . import apify, free_sites, gallerydl, instagram_embed, instaloader_fetch, linkedin_page, tiktok_page, youtube_extra, ytdlp
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
    """Each platform's chain, free first: the open tools, then free sites, then Apify under Krish's $5 monthly cap,
    then words alone when no file can be had. Order from docs/FETCH_METHODS.md, plus the free sites Krish asked for
    on 2026-10-24 ("Build all the fallbacks. This needs to be bulletproof.")."""
    url, platform, post_id = link.url, link.platform, link.post_id
    cookies = config.cookies.get(platform)
    chain: list[tuple[str, Callable[[Path], Post]]] = []

    def cobalt_step() -> None:
        if config.cobalt_url:
            chain.append(("cobalt", lambda f: free_sites.cobalt(url, platform, post_id, f, config.cobalt_url)))

    if platform == "instagram":
        # The embed first: one request, logged out, the post's own data (instagram_embed.py, tested live).
        chain.append(("instagram_embed", lambda f: instagram_embed.fetch(url, post_id, f)))
        if link.kind == "reel":
            chain.append(("ytdlp", lambda f: ytdlp.fetch(url, platform, f)))
        else:
            chain.append(("ytdlp_carousel", lambda f: ytdlp.fetch_carousel(url, platform, f)))
        chain.append(("instaloader", lambda f: instaloader_fetch.fetch(url, post_id, f)))
        cobalt_step()
        actor = "instagram_reel" if link.kind == "reel" else "instagram_post"
        chain.append((f"apify_{actor}", lambda f: apify.fetch(url, platform, f, config, actor_key=actor, expected_id=post_id)))
        # Age-restricted posts: every logged-out scraper is refused, this downloader is not (28 October 2026).
        chain.append(("apify_instagram_downloader", lambda f: apify.fetch_instagram_downloader(url, post_id, f, config)))
        if cookies:
            chain.append(("gallerydl_cookies", lambda f: gallerydl.fetch(url, platform, f, cookies_profile=cookies)))
        chain.append(("instagram_cover_only", lambda f: instagram_embed.cover_only(url, post_id, f)))
    elif platform == "tiktok":
        if link.kind != "photo":
            chain.append(("ytdlp", lambda f: ytdlp.fetch(url, platform, f, captions="all", need_audio=True)))
        chain.append(("gallerydl", lambda f: gallerydl.fetch(url, platform, f)))
        chain.append(("tiktok_page", lambda f: tiktok_page.fetch(url, f)))
        chain.append(("tikwm", lambda f: free_sites.tikwm(url, f)))
        if link.kind != "photo":
            chain.append(("tikmate", lambda f: free_sites.tikmate(url, f)))
        cobalt_step()
        chain.append(("apify_tiktok", lambda f: apify.fetch(url, platform, f, config, actor_key="tiktok")))
        if cookies:
            chain.append(("ytdlp_cookies", lambda f: ytdlp.fetch(url, platform, f, captions="all", cookies_profile=cookies)))
    elif platform == "youtube":
        meta: dict = {}

        def check(folder: Path) -> Post:
            # Not a fetch: it stops a dead or private link at once, and keeps the title for the word-only steps.
            meta.update(youtube_extra.oembed(url))
            raise FetchFailed("other", "checked")

        chain.append(("yt_oembed", check))
        chain.append(("ytdlp", lambda f: ytdlp.fetch(url, platform, f, captions="youtube")))
        chain.append(("ytdlp_mweb", lambda f: ytdlp.fetch(url, platform, f, captions="youtube", method="ytdlp_mweb",
                                                          extra=["--extractor-args", "youtube:player_client=mweb"])))
        cobalt_step()
        if cookies:
            chain.append(("ytdlp_cookies", lambda f: ytdlp.fetch(url, platform, f, captions="youtube", cookies_profile=cookies)))
        if link.kind == "short":
            # A Short never fails outright: about two cents on Apify under the cap.
            chain.append(("apify_youtube_short", lambda f: apify.fetch_youtube_short(url, post_id, f, config, meta)))
        chain.append(("yt_transcript_api", lambda f: youtube_extra.transcript_api(url, post_id, f, meta)))
        chain.append(("apify_youtube_transcript", lambda f: youtube_extra.johnvc(url, post_id, f, config, meta)))
    elif platform == "linkedin":
        # yt-dlp is not in LinkedIn's chain: the guest page lists the same video files (FETCH_METHODS.md, step 1).
        chain.append(("linkedin_guest_page", lambda f: linkedin_page.fetch(url, post_id, f)))
        chain.append(("apify_linkedin_harvest", lambda f: apify.fetch_linkedin(url, post_id, f, config, actor_key="linkedin_harvest")))
        chain.append(("apify_linkedin_supreme", lambda f: apify.fetch_linkedin(url, post_id, f, config, actor_key="linkedin_supreme")))
        chain.append(("jina_reader", lambda f: linkedin_page.jina(url, post_id, f)))
    else:
        chain.append(("ytdlp", lambda f: ytdlp.fetch(url, platform, f)))
        cobalt_step()
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
            if name == "yt_oembed" and failure.detail == "checked":
                continue  # the link is live; go on to the fetchers
            result.attempts.append(Attempt(name, f"{failure.status_class}:{failure.detail}"))
            if name == "yt_oembed" and failure.status_class in ("not_found", "login_wall"):
                break  # a removed or private video: no fetcher will get it
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
    # Every method failed: the request reports the last step's class (FETCH_METHODS.md, every chain), passing over
    # steps that could only say "other". On 28 October an Instagram post behind a login wall reported "other", from
    # the cover-only last resort, while Apify had said login_wall.
    if result.attempts:
        named = [a for a in result.attempts if not a.outcome.startswith("other:")]
        result.status_class, result.detail = (named or result.attempts)[-1].outcome.split(":", 1)
    else:
        result.status_class, result.detail = "other", "no_method"
    return result


__all__ = ["fetch", "FetchResult", "FetchFailed", "STATUS_CLASSES"]
