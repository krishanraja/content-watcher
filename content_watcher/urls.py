"""Normalising pasted links: platform, canonical post URL and the url_key."""

from __future__ import annotations

import re
import urllib.request
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

PLATFORMS = ("instagram", "tiktok", "youtube", "linkedin", "x", "threads", "facebook", "web")

TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMS = {
    "igsh", "igshid", "si", "feature", "fbclid", "gclid", "ref", "ref_src", "is_from_webapp",
    "sender_device", "sender_web_id", "_r", "_t", "trackingId", "lipi", "rcm", "share_app_id",
    "pp", "img_index",
}
SHORT_HOSTS = {"vm.tiktok.com", "vt.tiktok.com", "youtu.be", "lnkd.in", "t.co"}
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class PostLink:
    platform: str
    url: str
    post_id: str | None
    kind: str | None  # reel, post, video, photo, short, activity
    needs_resolve: bool = False


def platform_of(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    host = host[4:] if host.startswith("www.") else host
    if host.endswith("instagram.com") or host == "instagr.am":
        return "instagram"
    if host.endswith("tiktok.com"):
        return "tiktok"
    if host.endswith("youtube.com") or host == "youtu.be" or host.endswith("youtube-nocookie.com"):
        return "youtube"
    if host.endswith("linkedin.com") or host == "lnkd.in":
        return "linkedin"
    if host in ("x.com", "twitter.com", "mobile.twitter.com"):
        return "x"
    if host.endswith("threads.net") or host.endswith("threads.com"):
        return "threads"
    if host.endswith("facebook.com") or host == "fb.watch":
        return "facebook"
    return "web"


def _strip_tracking(query: str, keep: set[str] | None = None) -> str:
    pairs = []
    for key, values in parse_qs(query, keep_blank_values=False).items():
        if keep is not None and key not in keep:
            continue
        if key in TRACKING_PARAMS or key.startswith(TRACKING_PREFIXES):
            continue
        for value in values:
            pairs.append((key, value))
    return urlencode(sorted(pairs))


def parse(url: str) -> PostLink:
    """Recognise a post link without any network call."""
    raw = url.strip()
    if not re.match(r"^[a-z]+://", raw, re.I):
        raw = "https://" + raw
    parts = urlsplit(raw)
    host = (parts.hostname or "").lower()
    path = re.sub(r"/{2,}", "/", parts.path)
    platform = platform_of(raw)

    if host in SHORT_HOSTS or (platform == "tiktok" and path.startswith("/t/")):
        if host == "youtu.be":
            video_id = path.strip("/").split("/")[0]
            if video_id:
                return PostLink("youtube", f"https://www.youtube.com/watch?v={video_id}", video_id, "video")
        return PostLink(platform, urlunsplit(("https", host, path, parts.query, "")), None, None, True)

    if platform == "instagram":
        if path.startswith("/share/"):
            return PostLink(platform, urlunsplit(("https", "www.instagram.com", path, "", "")), None, None, True)
        match = re.match(r"^(?:/[A-Za-z0-9._]+)?/(p|reel|reels|tv)/([A-Za-z0-9_-]+)", path)
        if match:
            kind = "post" if match.group(1) == "p" else "reel"
            segment = "p" if kind == "post" else "reel"
            code = match.group(2)
            return PostLink(platform, f"https://www.instagram.com/{segment}/{code}/", code, kind)
    elif platform == "tiktok":
        match = re.match(r"^/@([^/]+)/(video|photo)/(\d+)", path)
        if match:
            user, kind, post_id = match.groups()
            return PostLink(platform, f"https://www.tiktok.com/@{user}/{kind}/{post_id}", post_id, kind)
        match = re.match(r"^/(?:embed(?:/v2)?|v)/(\d+)", path)
        if match:
            return PostLink(platform, f"https://www.tiktok.com/@/video/{match.group(1)}", match.group(1), "video")
    elif platform == "youtube":
        query = parse_qs(parts.query)
        if path == "/watch" and query.get("v"):
            video_id = query["v"][0]
            return PostLink(platform, f"https://www.youtube.com/watch?v={video_id}", video_id, "video")
        match = re.match(r"^/(shorts|live|embed)/([A-Za-z0-9_-]{6,})", path)
        if match:
            kind = "short" if match.group(1) == "shorts" else "video"
            video_id = match.group(2)
            canonical = (
                f"https://www.youtube.com/shorts/{video_id}" if kind == "short"
                else f"https://www.youtube.com/watch?v={video_id}"
            )
            return PostLink(platform, canonical, video_id, kind)
    elif platform == "linkedin":
        match = re.search(r"activity[-:](\d{10,})", path)
        if match:
            activity = match.group(1)
            if path.startswith("/posts/"):
                canonical = urlunsplit(("https", "www.linkedin.com", path.rstrip("/") + "/", "", ""))
            else:
                canonical = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity}/"
            return PostLink(platform, canonical, activity, "activity")
        match = re.search(r"urn:li:(?:share|ugcPost):(\d{10,})", path)
        if match:
            return PostLink(
                platform, urlunsplit(("https", "www.linkedin.com", path.rstrip("/") + "/", "", "")),
                match.group(1), "activity",
            )

    query = _strip_tracking(parts.query)
    canonical = urlunsplit(("https", host[4:] if host.startswith("www.") else host, path.rstrip("/") or "/", query, ""))
    return PostLink(platform, canonical, None, None)


def resolve(url: str, *, timeout: float = 15.0, opener=None) -> str:
    """Follow a share or short link to where it lands. Returns the final URL."""
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA}, method="GET")
    opener = opener or urllib.request.build_opener()
    with opener.open(request, timeout=timeout) as response:
        return response.geturl()


def normalise(url: str, *, timeout: float = 15.0, opener=None) -> PostLink:
    link = parse(url)
    if link.needs_resolve:
        landed = resolve(link.url, timeout=timeout, opener=opener)
        resolved = parse(landed)
        if resolved.needs_resolve:
            return PostLink(resolved.platform, resolved.url, None, None, False)
        return resolved
    return link


def url_key(url: str) -> str:
    """The offline canonical form. Short links stay as pasted (minus tracking) until resolved."""
    return parse(url).url
