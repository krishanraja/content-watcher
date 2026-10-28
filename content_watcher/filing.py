"""Filing fetched media into the folder where Krish's own drops go. Never overwrites, never deletes."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import tools
from .config import Config
from .post import Post, kind_of, mime_of

FOLDERS = ("video_inspiration", "cold_ideas")


class FilingError(RuntimeError):
    def __init__(self, status_class: str):
        super().__init__(status_class)
        self.status_class = status_class


def folder_for(shape: str, lane: str | None) -> str:
    """video_inspiration is Production Inspo, cold_ideas is Content Inspo (Ventures > Inspiration, since 2026-10-24).
    The lane Krish chose wins; with none, a video goes to Production Inspo and anything else to Content Inspo."""
    if lane == "production":
        return "video_inspiration"
    if lane == "strategy":
        return "cold_ideas"
    return "video_inspiration" if shape == "video" else "cold_ideas"


def file_one(source: Path, directory: Path) -> tuple[Path, str]:
    """Copy source into directory. The same bytes already there is a no-op; a different file keeps its name free."""
    sha = tools.sha256_file(source)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / source.name
    counter = 2
    while target.exists():
        if target.is_file() and tools.sha256_file(target) == sha:
            return target, sha
        target = directory / f"{source.stem}_v{counter}{source.suffix}"
        counter += 1
    partial = directory / f".{target.name}.cw-partial"
    shutil.copyfile(source, partial)
    if tools.sha256_file(partial) != sha:
        partial.unlink(missing_ok=True)
        raise FilingError("copy_mismatch")
    partial.replace(target)
    return target, sha


def reuse_filed(source: Path, sha: str, folder: str, prior: dict | None, remap: dict | None) -> dict | None:
    """An earlier try of this request already filed a file of this name in this folder: use it, and read this
    fetch's bytes as that file. A platform's CDN can hand a second fetch different bytes for the same slide
    (28 October 2026: 194,030 bytes, then 167,614), so filing them again would add a _v2 copy and a second card."""
    known = (prior or {}).get(source.name)
    if not known or known.get("folder") != folder or not known.get("sha256"):
        return None
    if remap is not None and sha != known["sha256"]:
        remap[sha] = known["sha256"]
    return {key: known[key] for key in ("name", "sha256", "mime", "bytes", "folder") if key in known}


def file_post(post: Post, config: Config, lane: str | None = None, upload=None, prior: dict | None = None,
              remap: dict | None = None) -> list[dict]:
    """File every media file of the post, in post order. Returns the contract's media entries.

    With filing "engine" (the cloud backup, which has no synced Drive folder) each file goes through
    upload(folder, source, sha256), which answers the name it was filed under in Drive. `prior` is what an earlier
    try of the same request filed, by name; a file found there is reused (reuse_filed) and `remap` records which of
    this fetch's hashes stands for which filed one."""
    shape = post.infer_shape()
    folder = folder_for(shape, lane)
    if config.filing == "engine":
        if upload is None:
            raise FilingError("no_uploader")
        entries = []
        for source in post.media:
            if kind_of(source) is None:
                continue
            sha = tools.sha256_file(source)
            reused = reuse_filed(source, sha, folder, prior, remap)
            entries.append(reused or {
                "name": upload(folder, source, sha), "sha256": sha, "mime": mime_of(source),
                "bytes": source.stat().st_size, "folder": folder,
            })
        return entries
    directory = config.folder_path(folder)
    if directory is None:
        raise FilingError("folder_not_set")
    if config.filing == "drive" and not directory.is_dir():
        raise FilingError("drive_folder_missing")
    entries = []
    for source in post.media:
        if kind_of(source) is None:
            continue
        reused = reuse_filed(source, tools.sha256_file(source), folder, prior, remap)
        if reused:
            entries.append(reused)
            continue
        target, sha = file_one(source, directory)
        entries.append({
            "name": target.name, "sha256": sha, "mime": mime_of(target),
            "bytes": target.stat().st_size, "folder": folder,
        })
    return entries
