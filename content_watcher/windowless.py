"""No window, ever, on a home computer.

The scheduled task runs the watcher under pythonw.exe, which has no console. Windows gives every console program such a
process starts (ffmpeg, ffprobe, tesseract, yt-dlp's python.exe, Playwright's node) a console window of its own, so a
run that reads a few files opened a stream of black windows over Krish's work for minutes at a time. Krish,
2026-10-28: "HIDE ALL CONSOLE POP UPS FOREVER FROM EVERY REPO AND LOCAL TASK".

So on Windows every process this one starts is started with CREATE_NO_WINDOW: it still gets a console, with no window,
and anything it starts in turn shares that hidden console. A caller that asks for a console of its own
(CREATE_NEW_CONSOLE or DETACHED_PROCESS) keeps it. The patch is on subprocess.Popen itself, so asyncio's subprocesses,
Playwright's driver and the compression engine's ffprobe are covered with no change of their own. Every child here
has its output piped, so nothing is lost by its console being hidden.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CREATE_NO_WINDOW = 0x08000000
CREATE_NEW_CONSOLE = 0x00000010
DETACHED_PROCESS = 0x00000008
# Popen's own positional slot for creationflags; a caller that fills it is left exactly as it asked.
_FLAGS_POSITION = 13


def hidden_flags(flags: int | None) -> int:
    flags = int(flags or 0)
    if flags & (CREATE_NEW_CONSOLE | DETACHED_PROCESS):
        return flags
    return flags | CREATE_NO_WINDOW


def install(platform: str = sys.platform, popen: type = subprocess.Popen) -> bool:
    """Make every Popen on Windows windowless. Idempotent; a no-op elsewhere. True when the patch is in place."""
    if platform != "win32":
        return False
    original = popen.__init__
    if getattr(original, "_windowless", False):
        return True

    def __init__(self, *args, **kwargs):
        if len(args) <= _FLAGS_POSITION:
            kwargs["creationflags"] = hidden_flags(kwargs.get("creationflags"))
        original(self, *args, **kwargs)

    __init__._windowless = True  # type: ignore[attr-defined]
    __init__.__wrapped__ = original  # type: ignore[attr-defined]
    __init__.__doc__ = original.__doc__
    popen.__init__ = __init__
    return True


def console_python(executable: str | None = None) -> str:
    """The python.exe beside pythonw.exe. A tool run as its own Python process (yt-dlp, gallery-dl, instaloader) starts
    programs of its own that this process cannot reach; under python.exe, started without a window, those share its
    hidden console. Under pythonw.exe each of them would open a window."""
    executable = executable or sys.executable
    path = Path(executable)
    if path.name.lower() == "pythonw.exe":
        console = path.with_name("python.exe")
        if console.is_file():
            return str(console)
    return executable
