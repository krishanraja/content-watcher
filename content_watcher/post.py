"""The one normalised post every fetcher returns."""

from __future__ import annotations

import json
import mimetypes
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif"}
AUDIO_EXT = {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".opus"}
TEXT_EXT = {".md", ".txt"}
DOC_EXT = {".pdf"}


def kind_of(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in VIDEO_EXT:
        return "video"
    if suffix in IMAGE_EXT:
        return "image"
    if suffix in AUDIO_EXT:
        return "audio"
    if suffix in TEXT_EXT:
        return "text"
    if suffix in DOC_EXT:
        return "document"
    return None


def mime_of(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed:
        return guessed
    return {".webp": "image/webp", ".heic": "image/heic", ".md": "text/markdown"}.get(
        path.suffix.lower(), "application/octet-stream"
    )


@dataclass
class Post:
    platform: str
    url: str
    post_id: str | None = None
    author: str | None = None
    posted_at: str | None = None  # ISO 8601
    caption: str | None = None
    counts: dict[str, int] = field(default_factory=dict)
    media: list[Path] = field(default_factory=list)  # in post order
    audio: Path | None = None  # a photo post's sound, kept beside the slides
    captions_file: Path | None = None  # platform subtitles, when offered
    method: str | None = None  # which fetch method worked, as a class
    shape: str | None = None  # video, carousel, image, text, document

    def infer_shape(self) -> str:
        if self.shape:
            return self.shape
        kinds = [kind_of(path) for path in self.media]
        if not kinds:
            return "text"
        if len(kinds) == 1:
            return {"video": "video", "image": "image", "text": "text", "document": "document"}.get(
                kinds[0] or "", "video"
            )
        return "carousel"

    def summary(self) -> dict[str, Any]:
        return {
            "author": self.author,
            "posted_at": self.posted_at,
            "caption": self.caption,
            "url": self.url,
            "platform": self.platform,
        }

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["media"] = [path.name for path in self.media]
        data["audio"] = self.audio.name if self.audio else None
        data["captions_file"] = self.captions_file.name if self.captions_file else None
        data["shape"] = self.infer_shape()
        return data

    def save(self, folder: Path) -> Path:
        target = folder / "post.json"
        target.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return target

    @classmethod
    def load(cls, folder: Path) -> "Post":
        data = json.loads((folder / "post.json").read_text(encoding="utf-8"))
        return cls(
            platform=data["platform"],
            url=data["url"],
            post_id=data.get("post_id"),
            author=data.get("author"),
            posted_at=data.get("posted_at"),
            caption=data.get("caption"),
            counts=data.get("counts") or {},
            media=[folder / name for name in data.get("media") or []],
            audio=folder / data["audio"] if data.get("audio") else None,
            captions_file=folder / data["captions_file"] if data.get("captions_file") else None,
            method=data.get("method"),
            shape=data.get("shape"),
        )
