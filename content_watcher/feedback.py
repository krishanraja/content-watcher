"""Feedback videos Krish links in Control Center: one claimed a run, read from his synced Drive, its timeline made here,
its stills and feedback file put in its folder in Ventures > Bugs & Issues > <venture>, and a report that has the engine
write the Claude Code prompt there and email it to him.

Krish, 2026-10-28: "somewhere in my control centre where I can specifically add a feedback video that's not
inspiration ... It would trigger only this one part of the system", and the input: "videos I'll take on my phone as
MP4 and upload them to Google Drive ... I probably want to send the link to the MP4 or the video file, which is stored
in my Google Drive." So the video is read where his Drive has synced it to this computer, checked by size and MD5, and
never copied, moved or deleted. Nothing here touches the Inspiration queue, content_reads, the Inspiration folders or
the drop reader: it only uses `content_watcher.timeline` and the engine's api/ux-feedback routes (docs/WATCH_API.md).
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path

from .config import Config, state_dir
from .engine import Engine, EngineError, put_upload

# A recording is transcribed on the machine's CPU: start one only when the run has this long left before its deadline.
FEEDBACK_MIN_TIME_S = 12 * 60
MAX_SIGNALS = 100


class FeedbackError(Exception):
    def __init__(self, status_class: str):
        super().__init__(status_class)
        self.status_class = status_class


def is_cloud(machine: str) -> bool:
    return machine.lower().startswith("cloud")


def md5_file(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - Drive's own checksum, compared, never trusted for security
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def synced_copy(config: Config, drive_path: str, size: int, md5: str | None) -> Path:
    """The recording where his Drive has synced it to this computer, or a class saying why not: not there yet (or
    still arriving) goes back to the queue; different bytes under that name is a different file."""
    root = config.my_drive_root()
    if root is None or not (root / "Ventures").is_dir():
        raise FeedbackError("no_drive_root")
    parts = [part for part in drive_path.split("/") if part]
    if not parts or any(part in (".", "..") for part in parts):
        raise FeedbackError("bad_drive_path")
    path = root.joinpath(*parts)
    if not path.is_file() or path.stat().st_size != size:
        raise FeedbackError("not_synced_yet")
    if md5 and md5_file(path) != md5.lower():
        raise FeedbackError("not_the_same_file")
    return path


def summary_of(data: dict) -> dict:
    source = data.get("source") or {}
    width, height = source.get("width") or None, source.get("height") or None
    return {
        "duration_s": data["duration_s"],
        "stills": data["counts"]["stills"],
        "images": data["counts"]["images"],
        "width": width,
        "height": height,
        "portrait": (height > width) if width and height else None,
        "signals": [
            {"t": hit["t"], "signal": hit["signal"], "term": hit["term"][:60], "said": (hit["said"] or "")[:400],
             "still": hit["index"]}
            for hit in data.get("ux_signals", [])[:MAX_SIGNALS]
        ],
    }


def handle_feedback(job: dict, config: Config, engine: Engine, counts: Counter, *, put=put_upload) -> None:
    from .timeline import build_standalone
    from .timeline.render import render_timeline_md

    recording_id = str(job["id"])
    source = synced_copy(config, str(job["drive_path"]), int(job["bytes"]), job.get("md5"))
    try:
        folder, built = build_standalone(source, state_dir() / "feedback" / recording_id, profile="ux",
                                         whisper_model=config.whisper_model)
    except Exception:  # noqa: BLE001 - by class, never the message
        raise FeedbackError("timeline_failed") from None
    links: dict[str, str] = {}
    stills = sorted({Path(path) for path in built.stills})
    if stills:
        plan = engine.feedback_drive(recording_id, config.machine, [
            {"name": still.name, "mime": "image/jpeg", "bytes": still.stat().st_size, "place": "stills"}
            for still in stills])
        sessions = {item["name"]: item["upload_url"] for item in plan.get("uploads") or []}
        for still in stills:
            if still.name not in sessions:
                raise FeedbackError("drive_session_missing")
            answer = put(sessions[still.name], still, "image/jpeg")
            if not answer.get("id"):
                raise FeedbackError("drive_upload_no_id")
            links[f"stills/{still.name}"] = f"https://drive.google.com/file/d/{answer['id']}/view"
        counts["feedback.stills_uploaded"] += len(stills)
    intro = [f"Feedback on {job.get('venture_label') or 'one of your products'}, from "
             f"[{job['name']}](https://drive.google.com/file/d/{job['drive_file_id']}/view)."]
    if job.get("note"):
        intro.append(f"What it is about, in your words: {job['note']}")
    feedback_file = folder / "feedback.md"
    feedback_file.write_text(render_timeline_md(built.data, links=links, intro=intro), encoding="utf-8")
    plan = engine.feedback_drive(recording_id, config.machine, [
        {"name": "feedback.md", "mime": "text/markdown", "bytes": feedback_file.stat().st_size, "place": "folder"}])
    session = next((item["upload_url"] for item in plan.get("uploads") or [] if item["name"] == "feedback.md"), None)
    if not session:
        raise FeedbackError("drive_session_missing")
    answer = put(session, feedback_file, "text/markdown")
    if not answer.get("id"):
        raise FeedbackError("drive_upload_no_id")
    engine.feedback_report(recording_id, config.machine, "done", feedback_file_id=str(answer["id"]),
                           summary=summary_of(built.data))
    counts["feedback.done"] += 1


def feedback_once(config: Config, engine: Engine, counts: Counter, time_left_s: float, **handlers) -> None:
    """At most one feedback video a run, on a home computer, when the run has time for it. Engine trouble is counted
    under feedback., so it never stops the drop reader the way the Inspiration queue's does."""
    if is_cloud(config.machine):
        return
    if time_left_s < FEEDBACK_MIN_TIME_S:
        counts["feedback.deferred"] += 1
        return
    try:
        job = engine.feedback_claim(config.machine)
    except EngineError as failure:
        counts[f"feedback.{failure.status_class}"] += 1
        return
    if not job:
        return
    counts["feedback.claimed"] += 1
    try:
        handle_feedback(job, config, engine, counts, **handlers)
        return
    except FeedbackError as failure:
        status_class = failure.status_class
    except EngineError as failure:
        status_class = failure.status_class
    except Exception:  # noqa: BLE001 - by class, never the message
        status_class = "other"
    status_class = re.sub(r"[^a-z_]+", "", status_class.lower()).strip("_")[:40] or "other"  # the engine's class shape
    counts[f"feedback.failed.{status_class}"] += 1
    try:
        engine.feedback_report(str(job["id"]), config.machine, "failed", status_class=status_class)
    except EngineError as failure:
        counts[f"feedback.{failure.status_class}"] += 1
