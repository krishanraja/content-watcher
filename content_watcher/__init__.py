"""Content Watcher: any post or file Krish points at becomes a text reading on his own machine."""

from . import windowless

# Before anything else here starts a process: on a home computer no program the watcher runs may open a window.
windowless.install()

ENGINE_REV = "cw-2026.10.29"
READ_FORMAT = "content-watcher.read/1"
TIMELINE_FORMAT = "content-watcher.timeline/1"

__all__ = ["ENGINE_REV", "READ_FORMAT", "TIMELINE_FORMAT"]
