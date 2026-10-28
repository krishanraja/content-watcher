"""The paid fallback on Apify: only with a standing monthly cap Krish set, and a local spend ledger."""

from __future__ import annotations

import contextlib
import contextvars
import json
import os
import socket
import time
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
    "youtube_transcript": ("johnvc~YoutubeTranscripts", 0.01),
    # $0.02 a minute at 720p; a Short is under three minutes (FETCH_METHODS.md, YouTube step 9).
    "youtube_short_video": ("marielise.dev~youtube-video-downloader", 0.06),
    "linkedin_harvest": ("harvestapi~linkedin-profile-posts", 0.005),
    "linkedin_supreme": ("supreme_coder~linkedin-post", 0.005),
    # A downloader service that reaches what every logged-out scraper is refused. 28 October 2026: Krish's carousel
    # (/p/DfAY9PWFuEX) answered Apify's scraper "Restricted access ... The post is age-restricted", and this actor
    # returned all 16 slides. About $0.0004 a request.
    "instagram_downloader": ("snapinsta~instagram-downloader-api", 0.002),
}

# The engine holds the one Apify key and runs an actor for the request a machine holds (content-engine
# api/watch/apify.ts). The cloud backup always goes through it (CONTENT_WATCH_APIFY_VIA_ENGINE=1); a home computer does
# whenever it has no key of its own or its key is refused, so a key missing from or expired on a machine never stops a
# fetch (Krish, 2026-10-28: "Keys from sessions are fragile, you should by now have a more robust way of not failing at
# that step!"). The request is known only inside watch.handle_request, which sets it here; the spend cap and ledger
# still apply on this machine.
_ENGINE_RUN: contextvars.ContextVar = contextvars.ContextVar("content_watch_engine_run", default=None)


def via_engine() -> bool:
    if _ENGINE_RUN.get() is None:
        return False
    return os.environ.get("CONTENT_WATCH_APIFY_VIA_ENGINE") == "1" or not secrets.apify_token()


def _refused_here(failure: FetchFailed) -> bool:
    """This machine's own key was refused and the engine can run the actor instead."""
    return failure.detail == "apify_refused" and _ENGINE_RUN.get() is not None


@contextlib.contextmanager
def engine_runs(engine, request_id: str, machine: str):
    token = _ENGINE_RUN.set((engine, request_id, machine))
    try:
        yield
    finally:
        _ENGINE_RUN.reset(token)


def _run_via_engine(actor: str, payload: dict) -> list[dict]:
    from ..engine import EngineError  # imported here: engine.py does not import this module

    engine, request_id, machine = _ENGINE_RUN.get()
    try:
        return engine.apify(request_id, machine, actor, payload)
    except EngineError as failure:
        raise FetchFailed("blocked", f"apify_via_{failure.status_class}"[:60]) from None


MIME_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "video/mp4": ".mp4",
            "video/quicktime": ".mov"}


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
    if not secrets.apify_token() and not via_engine():
        raise FetchFailed("blocked", "no_apify_token")


def run_actor(actor: str, payload: dict, *, timeout: float = 300, opener=None) -> list[dict]:
    if via_engine():
        return _run_via_engine(actor, payload)
    try:
        return _run_actor_here(actor, payload, timeout=timeout, opener=opener)
    except FetchFailed as failure:
        if _refused_here(failure):
            return _run_via_engine(actor, payload)
        raise


def _run_actor_here(actor: str, payload: dict, *, timeout: float, opener) -> list[dict]:
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


def _call(request: urllib.request.Request, opener, timeout: float):
    try:
        with opener.open(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
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


def run_actor_async(actor: str, payload: dict, *, timeout: float = 900, poll_every: float = 10, opener=None,
                    sleep=time.sleep, clock=time.monotonic) -> list[dict]:
    """Start a run, poll it, then read its dataset: a run with downloads can pass the 300-second limit of the
    synchronous call (FETCH_METHODS.md, TikTok step 4)."""
    if via_engine():
        return _run_via_engine(actor, payload)
    try:
        return _run_actor_async_here(actor, payload, timeout=timeout, poll_every=poll_every, opener=opener,
                                     sleep=sleep, clock=clock)
    except FetchFailed as failure:
        if _refused_here(failure):
            return _run_via_engine(actor, payload)
        raise


def _run_actor_async_here(actor: str, payload: dict, *, timeout: float, poll_every: float, opener, sleep,
                          clock) -> list[dict]:
    token = secrets.apify_token()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    opener = opener or urllib.request.build_opener()
    started = _call(urllib.request.Request(f"{API}/acts/{actor}/runs", data=json.dumps(payload).encode("utf-8"),
                                           headers=headers, method="POST"), opener, 60)
    run = (started or {}).get("data") or {}
    run_id = run.get("id")
    if not run_id:
        raise FetchFailed("other", "apify_bad_response")
    deadline = clock() + timeout
    while run.get("status") in (None, "READY", "RUNNING"):
        if clock() > deadline:
            raise FetchFailed("timeout", "apify_timeout")
        sleep(poll_every)
        run = (_call(urllib.request.Request(f"{API}/actor-runs/{run_id}", headers=headers), opener, 60) or {}).get("data") or {}
    if run.get("status") != "SUCCEEDED":
        raise FetchFailed("timeout" if "TIMED" in str(run.get("status")) else "other", "apify_run_failed")
    dataset = run.get("defaultDatasetId")
    items = _call(urllib.request.Request(f"{API}/datasets/{dataset}/items?clean=true", headers=headers), opener, 60)
    if not isinstance(items, list):
        raise FetchFailed("other", "apify_bad_response")
    return items


def _item_error(item: dict) -> None:
    error = " ".join(str(item.get(key) or "") for key in ("error", "errorDescription", "requestErrorMessages", "errorCode")).strip()
    if not error:
        return
    lowered = error.lower()
    if "blocked" in lowered:
        raise FetchFailed("blocked", "apify_blocked")
    if "not_found" in lowered or "not found" in lowered or "does not exist" in lowered:
        raise FetchFailed("not_found", "apify_not_found")
    if "private" in lowered or "restricted" in lowered or "login" in lowered:
        raise FetchFailed("login_wall", "apify_restricted")
    raise FetchFailed("other", "apify_item_error")


def instagram_parts(item: dict, expected_id: str | None = None) -> tuple[dict, list[tuple[str, str]]]:
    """The post's details and its media URLs in post order, as (url, default extension)."""
    _item_error(item)
    if expected_id and item.get("shortCode") and item["shortCode"] != expected_id:
        raise FetchFailed("other", "apify_wrong_item")
    media: list[tuple[str, str]] = []
    children = item.get("childPosts") or []
    if item.get("type") == "Sidecar" and item.get("images") and len(children) != len(item["images"]):
        raise FetchFailed("other", "ig_missing_slides")
    if children:
        for child in children:
            if (child.get("type") == "Video" or child.get("videoUrl")) and child.get("videoUrl"):
                media.append((child["videoUrl"], ".mp4"))
            elif child.get("displayUrl"):
                media.append((child["displayUrl"], ".jpg"))
    elif item.get("type") == "Sidecar" and item.get("images"):
        media = [(url, ".jpg") for url in item["images"]]
    elif item.get("videoUrl") or item.get("downloadedVideo"):
        media.append((item.get("videoUrl") or item["downloadedVideo"], ".mp4"))
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
        stored = [url for url in item.get("mediaUrls") or [] if url]
        media = [(url, ".mp4") for url in stored]
        if not media and (item.get("videoMeta") or {}).get("downloadAddr"):
            media.append((item["videoMeta"]["downloadAddr"], ".mp4"))
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


def fetch(url: str, platform: str, folder: Path, config: Config, *, actor_key: str, opener=None,
          expected_id: str | None = None) -> Post:
    actor, estimate = ACTORS[actor_key]
    allowed(config, estimate)
    if actor_key == "instagram_reel":
        # No stored copy: it costs $0.015 a started MB on top of the run (FETCH_METHODS.md, Instagram step 2).
        payload = {"username": [url], "includeDownloadedVideo": False, "includeTranscript": False}
    elif actor_key == "instagram_post":
        payload = {"directUrls": [url], "resultsType": "posts", "resultsLimit": 1, "addParentData": False}
    else:
        payload = {
            "postURLs": [url], "shouldDownloadVideos": True, "shouldDownloadSlideshowImages": True,
            "shouldDownloadCovers": False, "downloadSubtitlesOptions": "DOWNLOAD_SUBTITLES",
            # No named store: files stay in the run's own store and expire with it, so nothing on his Apify
            # account needs deleting (FETCH_METHODS.md, TikTok open question 6).
        }
    # Counted before the call: a run that times out may still be charged.
    record_spend(estimate)
    if platform == "tiktok":
        items = run_actor_async(actor, payload, opener=opener)
    else:
        items = run_actor(actor, payload, opener=opener)
    if not items:
        raise FetchFailed("other", "apify_item_error")
    subtitle = music = None
    if platform == "tiktok":
        meta, media, subtitle, music = tiktok_parts(items[0])
    else:
        meta, media = instagram_parts(items[0], expected_id)
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


def _posted(item: dict) -> str | None:
    posted = item.get("postedAtISO") or item.get("postedAt")
    if isinstance(posted, dict):
        posted = posted.get("date") or posted.get("timestamp")
    return str(posted) if posted else None


def linkedin_parts(item: dict) -> dict:
    """A LinkedIn post from harvestapi/linkedin-profile-posts or supreme_coder/linkedin-post (FETCH_METHODS.md,
    LinkedIn step 3). Field names come from each actor's page; the first approved run confirms them."""
    _item_error(item)
    text = item.get("content") or item.get("text") or ""
    if not str(text).strip():
        raise FetchFailed("other", "apify_item_error")
    author = item.get("author") or {}
    if isinstance(author, str):
        author = {"name": author}
    images = [img.get("url") if isinstance(img, dict) else img for img in item.get("postImages") or item.get("images") or []]
    video = None
    streams = (((item.get("linkedinVideo") or {}).get("videoPlayMetadata") or {}).get("progressiveStreams") or [])
    if streams:
        best = max(streams, key=lambda st: (st.get("height") or 0, st.get("bitrate") or 0))
        if (best.get("height") or 0) > 720:
            smaller = [st for st in streams if (st.get("height") or 0) <= 720]
            best = max(smaller, key=lambda st: st.get("height") or 0) if smaller else best
        locations = best.get("streamingLocations") or []
        video = (locations[0].get("url") if locations else None) or best.get("url")
    document = item.get("document") or {}
    engagement = item.get("engagement") or {}
    counts = {}
    for name, value in (("likes", engagement.get("likes", item.get("numLikes"))),
                        ("comments", engagement.get("comments", item.get("numComments"))),
                        ("shares", engagement.get("shares", item.get("numShares")))):
        if isinstance(value, int):
            counts[name] = value
    return {
        "text": str(text).strip(),
        "author": author.get("name"),
        "posted_at": _posted(item),
        "images": [url for url in images if url],
        "video": video,
        "pdf": document.get("transcribedDocumentUrl"),
        "counts": counts,
    }


def instagram_downloader_parts(item: dict) -> list[tuple[str, str]]:
    """The downloader's media URLs in post order, each with the extension its file type names. The URL's own suffix
    can say .heic while the bytes are JPEG (stp=dst-jpg), so the type decides."""
    if item.get("status") is not True:
        _item_error({"error": item.get("error") or item.get("message") or "downloader_failed"})
    out = []
    for media in item.get("media") or []:
        media_url = media.get("url") if isinstance(media, dict) else None
        if not media_url:
            continue
        kind = str(media.get("fileType") or "").lower()
        out.append((media_url, MIME_EXT.get(kind) or (".mp4" if kind.startswith("video") else ".jpg")))
    return out


def fetch_instagram_downloader(url: str, post_id: str | None, folder: Path, config: Config, *, opener=None) -> Post:
    """The last paid step for an Instagram post or reel: a downloader that reaches age-restricted posts. It gives the
    files only, so the reading carries no caption or author."""
    actor, estimate = ACTORS["instagram_downloader"]
    allowed(config, estimate)
    record_spend(estimate)
    items = run_actor(actor, {"url": url}, opener=opener)
    if not items:
        raise FetchFailed("other", "apify_item_error")
    media = instagram_downloader_parts(items[0])
    if not media:
        raise FetchFailed("other", "apify_no_media")
    ident = post_id or "post"
    post = Post(platform="instagram", url=url, post_id=ident, method="apify_instagram_downloader")
    for index, (media_url, ext) in enumerate(media, start=1):
        suffix = f"_{index:02d}" if len(media) > 1 else ""
        post.media.append(download(media_url, folder / f"instagram_{ident}{suffix}{ext}", opener=opener))
    return post


def fetch_linkedin(url: str, post_id: str | None, folder: Path, config: Config, *, actor_key: str, opener=None) -> Post:
    from .linkedin_page import as_markdown

    actor, estimate = ACTORS[actor_key]
    allowed(config, estimate)
    record_spend(estimate)
    if actor_key == "linkedin_harvest":
        payload = {"targetUrls": [url], "maxPosts": 1, "scrapeComments": False, "scrapeReactions": False}
    else:
        payload = {"urls": [url], "deepScrape": True, "fetchDocumentDetails": True, "numComments": 0, "numLikes": 0}
    items = run_actor(actor, payload, opener=opener)
    if not items:
        raise FetchFailed("other", "apify_item_error")
    found = linkedin_parts(items[0])
    ident = post_id or "post"
    post = Post("linkedin", url, ident, found["author"], found["posted_at"], found["text"], found["counts"],
                method=f"apify_{actor_key}")
    text_file = folder / f"linkedin_{ident}.md"
    text_file.write_text(as_markdown(post), encoding="utf-8")
    post.media = [text_file]
    for index, image_url in enumerate(found["images"][:20], start=1):
        post.media.append(download(image_url, folder / f"linkedin_{ident}_{index:02d}.jpg", opener=opener))
    if found["video"]:
        post.media.append(download(found["video"], folder / f"linkedin_{ident}.mp4", opener=opener, timeout=300))
    elif actor_key == "linkedin_harvest" and "video" in str(items[0]).lower() and not found["images"]:
        raise FetchFailed("other", "apify_no_video")  # a video post with no file: the next actor reads video
    if found["pdf"]:
        post.media.append(download(found["pdf"], folder / f"linkedin_{ident}.pdf", opener=opener, timeout=120))
    post.shape = "text"
    return post


def _first_url(item, depth: int = 0) -> str | None:
    """The downloadable file in an actor's item, wherever the actor put it (the field name is read off the first run)."""
    if depth > 3:
        return None
    if isinstance(item, str):
        return item if item.startswith("http") and (".mp4" in item or "download" in item or "video" in item) else None
    if isinstance(item, dict):
        for key in ("downloadUrl", "download_url", "videoUrl", "video_url", "fileUrl", "file_url", "url", "mediaUrl"):
            value = item.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return value
        for value in item.values():
            found = _first_url(value, depth + 1)
            if found:
                return found
    if isinstance(item, list):
        for value in item:
            found = _first_url(value, depth + 1)
            if found:
                return found
    return None


def fetch_youtube_short(url: str, video_id: str, folder: Path, config: Config, meta: dict, *, opener=None) -> Post:
    """The paid backstop for a YouTube Short's file, about two cents, under the standing cap."""
    actor, estimate = ACTORS["youtube_short_video"]
    allowed(config, estimate)
    record_spend(estimate)
    items = run_actor(actor, {"urls": [url], "quality": "720p", "format": "mp4"}, opener=opener)
    if not items:
        raise FetchFailed("other", "apify_item_error")
    _item_error(items[0])
    file_url = _first_url(items[0])
    if not file_url:
        raise FetchFailed("other", "apify_no_media")
    post = Post("youtube", url, video_id, meta.get("author_name") or items[0].get("channel"),
                items[0].get("upload_date"), meta.get("title") or items[0].get("title"), method="apify_youtube_short")
    post.media = [download(file_url, folder / f"youtube_{video_id}.mp4", opener=opener, timeout=300)]
    post.shape = "video"
    return post
