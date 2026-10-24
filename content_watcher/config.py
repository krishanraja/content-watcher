"""Settings for this machine: one JSON file, never holding a secret."""

from __future__ import annotations

import json
import os
import socket
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


def state_dir() -> Path:
    override = os.environ.get("CONTENT_WATCH_HOME")
    if override:
        return Path(override)
    if sys.platform == "win32" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "content-watcher"
    return Path.home() / ".content-watcher"


@dataclass
class Config:
    # Where fetched media is filed. "drive" files into the two synced Drive folders below, where Krish's own
    # drops go (D1, Krish 2026-10-24: "Yes to Drive filing"). "local" keeps it on this machine only.
    filing: str = "drive"
    video_inspiration: str | None = None  # synced path of makeyourmindup > Video Engine > Inspiration
    cold_ideas: str | None = None  # synced path of Cold Ideas & Inspo
    # How Instagram and LinkedIn are fetched (D2): Firefox profile names allowed for cookies, per platform.
    cookies: dict[str, str] = field(default_factory=dict)
    # Paid fallback (D2). Off until Krish sets a standing monthly cap.
    apify_enabled: bool = False
    apify_monthly_cap_usd: float = 0.0
    engine_url: str = "https://content-engine-flame-nu.vercel.app"
    machine: str = field(default_factory=lambda: os.environ.get("COMPUTERNAME") or socket.gethostname() or "home")
    whisper_model: str = "small"
    claim_limit: int = 3

    @classmethod
    def path(cls) -> Path:
        return state_dir() / "config.json"

    @classmethod
    def load(cls) -> "Config":
        target = cls.path()
        if not target.is_file():
            return cls()
        data = json.loads(target.read_text(encoding="utf-8"))
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)

    def save(self) -> Path:
        target = self.path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return target

    def local_library(self) -> Path:
        return state_dir() / "library"

    def folder_path(self, folder: str) -> Path | None:
        """The directory a contract folder name (video_inspiration, cold_ideas) files into."""
        if self.filing == "drive":
            value = self.video_inspiration if folder == "video_inspiration" else self.cold_ideas
            return Path(value) if value else None
        return self.local_library() / folder
