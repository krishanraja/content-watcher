"""The path guard (W2.11): refuse a hard-coded path into Krish's dev folder anywhere but config/studio.json.

Every reader resolves its folders from `config/studio.json` `local_roots` (`content_watcher/layout.py`), so a dev path
written anywhere else is a second source of truth that goes stale the day a clone moves. Either slash, any case,
JSON-escaped backslashes included. CI runs it on every pull request (`.github/workflows/checks.yml`).

    python scripts/check_paths.py          # the tracked files of this repository
    python scripts/check_paths.py DIR      # every file under DIR (the test plants a path there)

Exit 0 when clean, 1 with each offending file and line otherwise.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"config/studio.json"}
# Written as a pattern so this file never matches itself: C, colon, then Users, krish and dev with any slashes.
DEV_PATH = re.compile(r"c:[\\/]+users[\\/]+krish[\\/]+dev(?:[\\/]|$)", re.I | re.M)
MAX_BYTES = 5 * 1024 * 1024


def tracked(root: Path) -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return [path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts]
    return [root / name for name in out.decode("utf-8", "replace").split("\0") if name]


def offences(root: Path, files: list[Path]) -> list[str]:
    found = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel in ALLOWED or not path.is_file() or path.stat().st_size > MAX_BYTES:
            continue
        try:
            text = path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # binary
        for number, line in enumerate(text.splitlines(), 1):
            if DEV_PATH.search(line):
                found.append(f"{rel}:{number}: hard-coded dev path; read it from config/studio.json local_roots")
    return found


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        root = Path(args[0]).resolve()
        files = [path for path in root.rglob("*") if path.is_file()]
    else:
        root = ROOT
        files = tracked(root)
    found = offences(root, files)
    for line in found:
        print(line)
    if found:
        print(f"path guard: {len(found)} hard-coded dev path{'' if len(found) == 1 else 's'}")
        return 1
    print(f"path guard: clean ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
