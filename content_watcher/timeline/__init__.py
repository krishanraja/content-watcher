"""Timelines: a video as timestamped stills, each carrying what was said, what was on screen and its tags.

Two outlets share this package. The reader adds a `social` timeline to every video reading (so every reel the watcher
reads carries one), and `content-watch timeline` builds one on its own for a file, writing only to the folder it is
given: no engine, no filing, no watch state. Nothing here is uploaded.
"""

from .build import Built, TimelineBudget, build_standalone, timeline

__all__ = ["Built", "TimelineBudget", "build_standalone", "timeline"]
