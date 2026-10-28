"""Feedback videos Krish adds in Control Center: one claimed a run, its timeline made here, its stills and feedback
file put in a Drive folder of their own, and a report that has the engine email him a Claude Code prompt.

Krish, 2026-10-28: "somewhere in my control centre where I can specifically add a feedback video that's not
inspiration ... It would trigger only this one part of the system." So nothing here touches the Inspiration queue,
content_reads, the Inspiration folders or the drop reader: it only uses `content_watcher.timeline` and the engine's
api/ux-feedback routes (docs/WATCH_API.md).
"""

from __future__ import annotations

import re
import shutil
import socket
import ssl
import urllib.error
import urllib.request
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


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 ._()-]+", "-", name).strip(" .-")[:120]
    return cleaned or "recording.mp4"


def download(url: str, target: Path, size: int, *, timeout: float = 600, opener=None) -> Path:
    """The recording from its signed URL, checked against the size Control Center recorded."""
    opener = opener or urllib.request.build_opener()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with opener.open(urllib.request.Request(url), timeout=timeout) as response, open(target, "wb") as handle:
            shutil.copyfileobj(response, handle, length=1024 * 1024)
    except urllib.error.HTTPError as exc:
        exc.close()
        raise FeedbackError("download_failed") from None
    except (urllib.error.URLError, socket.timeout, TimeoutError, ssl.SSLError, ConnectionError):
        raise FeedbackError("download_failed") from None
    if target.stat().st_size != size:
        raise FeedbackError("download_incomplete")
    return target


def summary_of(data: dict) -> dict:
    return {
        "duration_s": data["duration_s"],
        "stills": data["counts"]["stills"],
        "images": data["counts"]["images"],
        "signals": [
            {"t": hit["t"], "signal": hit["signal"], "term": hit["term"][:60], "said": (hit["said"] or "")[:400],
             "still": hit["index"]}
            for hit in data.get("ux_signals", [])[:MAX_SIGNALS]
        ],
    }


def handle_feedback(job: dict, config: Config, engine: Engine, counts: Counter, *, opener=None, put=put_upload) -> None:
    from .timeline import build_standalone
    from .timeline.render import render_timeline_md

    recording_id = str(job["id"])
    work = state_dir() / "feedback" / recording_id
    source = download(str(job["download_url"]), work / safe_name(str(job["name"])), int(job["bytes"]), opener=opener)
    try:
        folder, built = build_standalone(source, work, profile="ux", whisper_model=config.whisper_model)
    except Exception:  # noqa: BLE001 - by class, never the message
        raise FeedbackError("timeline_failed") from None
    finally:
        source.unlink(missing_ok=True)  # this machine's copy; the recording stays in his private storage
    links: dict[str, str] = {}
    stills = sorted({Path(path) for path in built.stills})
    if stills:
        plan = engine.feedback_drive(recording_id, config.machine, [
            {"name": still.name, "mime": "image/jpeg", "bytes": still.stat().st_size} for still in stills])
        sessions = {item["name"]: item["upload_url"] for item in plan.get("uploads") or []}
        for still in stills:
            if still.name not in sessions:
                raise FeedbackError("drive_session_missing")
            answer = put(sessions[still.name], still, "image/jpeg")
            if not answer.get("id"):
                raise FeedbackError("drive_upload_no_id")
            links[f"stills/{still.name}"] = f"https://drive.google.com/file/d/{answer['id']}/view"
        counts["feedback.stills_uploaded"] += len(stills)
    feedback_file = folder / "feedback.md"
    feedback_file.write_text(render_timeline_md(built.data, links=links), encoding="utf-8")
    plan = engine.feedback_drive(recording_id, config.machine, [
        {"name": "feedback.md", "mime": "text/markdown", "bytes": feedback_file.stat().st_size}])
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
