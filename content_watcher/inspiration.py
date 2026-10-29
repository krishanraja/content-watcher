"""The Inspiration root and the stills that travel (W3.2, Krish's saved Wave 3 brief).

The watcher reads his Inspiration root: the parent folder he linked, with Content Inspo and Production Inspo below
it (`Config.inspo_folder`). From each video reading it then curates at most 8 stills and copies them to a
machine-owned folder outside his tree, tagged `machine`, and the reading's row says so (`machine_stills`). That row
goes to content_reads, where inspirationhouse reads it, so the stills reach inspirationhouse as machine signals and
never as his inputs: nothing here writes into his tree, and a machine folder inside it is refused.

The ux-feedback path never comes here: `content-watch timeline` and `feedback.py` keep their stills in their own
folders (`.agents/skills/ux-feedback/SKILL.md`).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import layout, tools
from .config import Config

FORMAT = "content-watcher.machine-stills/1"
MAX_STILLS = 8
TAG = "machine"
# Why a still was taken, weighted: a cut or a new screen says more about how a video is made than a spoken line.
WEIGHTS = {"start": 4, "cut": 3, "screen_change": 2, "caption_change": 2, "speech": 1}


class MachineFolderError(RuntimeError):
    """The machine stills folder would sit inside his Inspiration tree."""


def his_tree(config: Config) -> list[Path]:
    """The folders that are his: the Inspiration root and the two folders below it, wherever each is set."""
    out = []
    for value in (config.inspiration_root, config.inspo_folder("video_inspiration"), config.inspo_folder("cold_ideas")):
        if value:
            out.append(Path(value).resolve())
    return out


def _inside(path: Path, folder: Path) -> bool:
    try:
        path.relative_to(folder)
        return True
    except ValueError:
        return False


def machine_dir(config: Config) -> Path:
    """The machine-owned stills folder: config.machine_stills, else the synced Machine stills Drive folder, else the
    layout's runtime folder. Never in his tree."""
    if config.machine_stills:
        chosen = Path(config.machine_stills)
    else:
        chosen = config.machine_stills_synced() or layout.load().runtime_dir("content-watcher", "stills")
    resolved = chosen.resolve()
    for folder in his_tree(config):
        if _inside(resolved, folder) or _inside(folder, resolved):
            raise MachineFolderError(f"refused: {chosen} overlaps his Inspiration tree ({folder.name})")
    return chosen


def _score(entry: dict) -> float:
    triggers = entry.get("triggers") or []
    score = sum(WEIGHTS.get(trigger, 0) for trigger in triggers)
    score += float(entry.get("change_score") or 0)
    if entry.get("screen_text"):
        score += 1
    if "hook" in (entry.get("tags") or []):
        score += 1
    return score


def curate(timeline: dict | None, limit: int = MAX_STILLS) -> list[dict]:
    """At most `limit` stills worth keeping, in time order: one picture each (a still that repeats an earlier
    picture is skipped), the best of each equal stretch of the video first, so they cover it end to end, then the
    best of the rest."""
    entries = [e for e in (timeline or {}).get("entries") or [] if e.get("file") and not e.get("same_as")]
    if not entries or limit <= 0:
        return []
    if len(entries) <= limit:
        return sorted(entries, key=lambda e: e.get("t", 0))
    first, last = entries[0].get("t", 0), entries[-1].get("t", 0)
    span = (last - first) or 1
    chosen: dict[int, dict] = {}
    for bucket in range(limit):
        lo, hi = first + span * bucket / limit, first + span * (bucket + 1) / limit
        inside = [e for e in entries if lo <= e.get("t", 0) < hi or (bucket == limit - 1 and e.get("t", 0) == hi)]
        if inside:
            best = max(inside, key=_score)
            chosen[best["index"]] = best
    for entry in sorted(entries, key=_score, reverse=True):
        if len(chosen) >= limit:
            break
        chosen.setdefault(entry["index"], entry)
    return sorted(chosen.values(), key=lambda e: e.get("t", 0))


def hand_over(reading, config: Config, limit: int = MAX_STILLS) -> dict | None:
    """Copy a reading's curated stills to the machine folder and mark its row. Returns the block added to the row,
    or None when the reading has no timeline stills. A still already there (same bytes) is not copied again."""
    picked = [e for e in curate(reading.read.get("timeline"), limit)
              if reading.folder and (reading.folder / e["file"]).is_file()]
    if not picked:
        return None
    root = machine_dir(config)
    key = reading.sha256[:16]
    target = root / key
    target.mkdir(parents=True, exist_ok=True)
    items = []
    for entry in picked:
        source = reading.folder / entry["file"]
        sha = tools.sha256_file(source)
        name = f"{entry['index']:02d}_{sha[:12]}{source.suffix or '.jpg'}"
        destination = target / name
        if not (destination.is_file() and tools.sha256_file(destination) == sha):
            partial = target / f".{name}.cw-partial"
            shutil.copyfile(source, partial)
            partial.replace(destination)
        items.append({
            "index": entry["index"], "t": entry.get("t"), "name": name, "still_sha256": sha,
            "tags": [TAG] + [tag for tag in entry.get("tags") or [] if tag != TAG],
        })
    block = {
        "format": FORMAT, "owner": TAG, "tags": [TAG], "counts_as_his": False, "source_sha256": reading.sha256,
        "folder_key": key, "drive_folder_id": config.machine_stills_drive_id,
        "synced": config.machine_stills_synced() is not None and root == config.machine_stills_synced(), "limit": limit, "count": len(items), "items": items,
    }
    (target / "stills.json").write_text(json.dumps(block, indent=2), encoding="utf-8")
    reading.read["machine_stills"] = block
    return block


def hand_over_all(readings, config: Config, counts) -> None:
    """hand_over for each reading; it can never fail a reading or hold up its row."""
    for reading in readings:
        try:
            if hand_over(reading, config) is not None:
                counts["stills.machine"] += 1
        except MachineFolderError:
            counts["stills.machine_refused"] += 1
        except Exception:  # noqa: BLE001 - stills are extra; the reading goes out as before without them
            counts["stills.machine_error"] += 1
