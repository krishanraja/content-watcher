"""One local layout for the Make Your Mind Up chain (W2.11): where repositories, worktrees and runtime live.

Every reader resolves these folders from `config/studio.json` `local_roots`, never from a path written in code; the
CI path guard (`scripts/check_paths.py`) refuses a hard-coded one. content-engine owns the layout: its
`config/studio.json` is read first when that clone sits beside this one (the layout's own `{repo}` pattern puts them
side by side) and carries `local_roots`; this repository's copy of the same shape is read otherwise.

Nothing here moves, creates or deletes a folder. Moving an existing clone waits on Krish's consent row for that
exact folder (W3.4).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
OWN = HERE / "config" / "studio.json"
OWNER_REPO = "content-engine"
_VAR = re.compile(r"%([^%]+)%")


@dataclass(frozen=True)
class Layout:
    repos: str | None
    worktrees: str | None
    runtime: str | None
    source: Path | None  # the studio.json the roots came from; None when no file was found

    def repo_dir(self, repo: str) -> Path | None:
        return _path(self.repos, repo=repo)

    def worktree_dir(self, repo: str, branch: str) -> Path | None:
        return _path(self.worktrees, repo=repo, branch=branch.replace("/", os.sep))

    def runtime_dir(self, *parts: str) -> Path:
        """The engine-made runtime folder (`%LOCALAPPDATA%\\makeyourmindup\\` on Windows), with parts below it.
        Off Windows, or with the variable unset, it falls back to ~/.makeyourmindup so a test or a container still
        has one."""
        root = _path(self.runtime)
        if root is None:
            root = Path.home() / ".makeyourmindup"
        return root.joinpath(*parts)


def _expand(value: str) -> str | None:
    """%VAR% and $VAR expanded from the environment; None when a %VAR% is unset."""
    missing = []

    def sub(match: re.Match) -> str:
        found = os.environ.get(match.group(1))
        if found is None:
            missing.append(match.group(1))
            return ""
        return found

    out = _VAR.sub(sub, value)
    return None if missing else os.path.expandvars(out)


def _path(pattern: str | None, **fields: str) -> Path | None:
    if not pattern:
        return None
    expanded = _expand(pattern)
    if expanded is None:
        return None
    try:
        filled = expanded.format(**fields)
    except (KeyError, IndexError):
        return None
    if os.sep == "/":
        filled = filled.replace("\\", "/")
    return Path(filled.rstrip("/\\") or filled)


def _roots(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    roots = data.get("local_roots") if isinstance(data, dict) else None
    if not isinstance(roots, dict) or not any(isinstance(roots.get(k), str) for k in ("repos", "worktrees", "runtime")):
        return None
    return roots


def candidates(here: Path = HERE) -> list[Path]:
    """content-engine's studio.json beside this clone (a worktree's parent too), then this repository's own copy."""
    out = [here.parent / OWNER_REPO / "config" / "studio.json"]
    if here.parent.parent.name == ".worktrees" or here.parent.parent.parent.name == ".worktrees":
        out.append(here.parents[2] / OWNER_REPO / "config" / "studio.json")
    out.append(here / "config" / "studio.json")
    return out


def load(here: Path = HERE, override: str | None = None) -> Layout:
    """The layout from the first studio.json that carries local_roots. CONTENT_WATCH_STUDIO names a file to use
    instead (a test, or a machine whose clones have not moved yet)."""
    chosen = override or os.environ.get("CONTENT_WATCH_STUDIO")
    paths = [Path(chosen)] if chosen else candidates(here)
    for path in paths:
        roots = _roots(path)
        if roots is not None:
            return Layout(roots.get("repos"), roots.get("worktrees"), roots.get("runtime"), path)
    return Layout(None, None, None, None)
