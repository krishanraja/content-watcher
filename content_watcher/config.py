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
    # drops go (D1, Krish 2026-10-24: "Yes to Drive filing"). "local" keeps it on this machine only. "engine" is the
    # cloud backup's (Krish, 2026-10-28: "yes build the cloud backup"): no synced folder, so each file goes to the
    # same two Drive folders through the engine's upload route (content-engine api/watch/upload.ts).
    filing: str = "drive"
    # The two folders in Ventures > Inspiration (Krish, 2026-10-24: "one for the content I like ... and one for
    # production quality I like"). The keys stay as the contract's folder values.
    video_inspiration: str | None = None  # synced path of Production Inspo (Drive 1QxrzxISYFXq0er0DG0XSapm7qhvuRmh-)
    cold_ideas: str | None = None  # synced path of Content Inspo (Drive 1FNztJOU82M8zb6IIbUAbvuI6Kr0pF5Hu)
    # The Inspiration root (W3.2): the synced parent folder he linked, with Content Inspo and Production Inspo below
    # it. Either folder set on its own above still wins; unset ones are found below this one by name.
    inspiration_root: str | None = None
    # Where the curated stills of each reading go (at most 8, tagged machine, never counted as his): a machine-owned
    # folder outside his Inspiration tree. Unset: the synced Machine stills Drive folder below, when this machine has
    # it, else the layout's runtime folder (config/studio.json local_roots), content-watcher/stills below it. A folder inside his tree is refused (inspiration.py).
    machine_stills: str | None = None
    # The machine-owned Drive folder the curated stills sync to (Krish's default, 2026-10-29): My Drive > Ventures >
    # Active Ventures > makeyourmindup > 4 Growth > Machine stills, outside his Inspiration tree. inspirationhouse finds
    # it by this id (it rides in each row's machine_stills); no permission was changed for it.
    machine_stills_drive_id: str = "1ryqrwjUloZwlKjn8UroVb6buwKIAPvwf"
    # The synced My Drive itself, where a feedback video he links in Control Center is read from (feedback.py).
    # Unset: three folders up from Production Inspo (My Drive > Ventures > Inspiration > Production Inspo).
    drive_root: str | None = None
    # How Instagram and LinkedIn are fetched (D2): Firefox profile names allowed for cookies, per platform.
    cookies: dict[str, str] = field(default_factory=dict)
    # Platforms where his own signed-in Firefox session, found on this machine, may fetch what only a signed-in account
    # sees (session.py). Ruling (Krish, 2026-10-28): "Yes to both on the two decisions" (Instagram).
    browser_sessions: list[str] = field(default_factory=lambda: ["instagram"])
    # Paid fallback (D2, Krish 2026-10-24: "Apify with $5 cap"): only after the free methods fail, never above the cap.
    apify_enabled: bool = True
    apify_monthly_cap_usd: float = 5.0
    # A cobalt instance (the open-source "paste a link, pick a quality" downloader), best run on this machine:
    # scripts/cobalt/README.md. Empty skips the step. A hosted instance's key goes in COBALT_API_KEY.
    cobalt_url: str = ""
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

    def machine_stills_synced(self) -> Path | None:
        """Where the Machine stills Drive folder syncs on this machine, when it is there."""
        root = self.my_drive_root()
        if root is None:
            return None
        found = root / "Ventures" / "Active Ventures" / "makeyourmindup" / "4 Growth" / "Machine stills"
        return found if found.is_dir() else None

    def local_library(self) -> Path:
        return state_dir() / "library"

    def my_drive_root(self) -> Path | None:
        """The synced My Drive on this machine, or None when neither it nor Production Inspo is set."""
        if self.drive_root:
            return Path(self.drive_root)
        if self.inspiration_root:
            parents = Path(self.inspiration_root).parents
            return parents[1] if len(parents) > 1 else None
        if self.video_inspiration:
            parents = Path(self.video_inspiration).parents
            return parents[2] if len(parents) > 2 else None
        return None

    def folder_path(self, folder: str) -> Path | None:
        """The directory a contract folder name (video_inspiration, cold_ideas) files into."""
        if self.filing == "drive":
            value = self.inspo_folder(folder)
            return Path(value) if value else None
        return self.local_library() / folder

    def inspo_folder(self, folder: str) -> str | None:
        """The synced path of Production Inspo (video_inspiration) or Content Inspo (cold_ideas): set on its own,
        else the folder of that name below the Inspiration root when it is there."""
        own = self.video_inspiration if folder == "video_inspiration" else self.cold_ideas
        if own or not self.inspiration_root:
            return own
        name = "Production Inspo" if folder == "video_inspiration" else "Content Inspo"
        below = Path(self.inspiration_root) / name
        return str(below) if below.is_dir() else None
