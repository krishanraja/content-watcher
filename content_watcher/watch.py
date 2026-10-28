"""One watch run: claim pasted links, fetch, file, read, report; then read new hand-dropped files."""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import ENGINE_REV
from .config import Config, state_dir
from .engine import Engine, EngineError, put_upload
from .fetch import apify as paid
from .fetch import fetch
from .filing import FOLDERS, FilingError, file_post
from .post import Post, kind_of, mime_of
from .read.reader import read_path, read_post
from .state import State, run_lock

DROP_LIMIT = 3  # hand-dropped files read per run, so a run stays short
# The longest a run may live. From 25 and 26 October 2026 both home computers stopped logging at 08:00 and a press of
# Run did nothing: a run that never ends holds the scheduled task, which ignores new starts while one is running. A
# run past this logs where it was (stage.<name>), frees the lock and ends, so the next minute's run starts clean.
RUN_DEADLINE_S = 20 * 60
_STAGE = ["start"]


def heartbeat(stage: str) -> None:
    """Where this run is, for the health report the recordings pass sends the engine (content-engine
    scripts/recordings-upload.ps1). A stage name and a time only, never a link or a file name."""
    _STAGE[0] = stage
    try:
        target = state_dir() / "watch.heartbeat"
        target.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        target.write_text(json.dumps({"at": stamp, "stage": stage, "pid": os.getpid()}), encoding="utf-8")
    except OSError:
        pass


def _over_time(counts: Counter, exit_process=os._exit) -> None:
    """The deadline: log the stage the run was stuck in, free the lock, end the process."""
    counts["killed.over_time"] += 1
    counts[f"stage.{_STAGE[0]}"] += 1
    try:
        log_line(counts)
        (state_dir() / "watch.lock").unlink(missing_ok=True)
    finally:
        exit_process(3)


def log_line(counts: Counter) -> Path:
    """The local log: counts and class names only, never a link, a caption or a file name."""
    target = state_dir() / "watch.log"
    target.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with target.open("a", encoding="utf-8") as handle:
        handle.write(stamp + " " + json.dumps(dict(sorted(counts.items())), separators=(",", ":")) + "\n")
    return target


def engine_uploader(engine: Engine, request_id: str, machine: str, put=put_upload):
    """Filing for the cloud backup: the engine opens a Drive session in the lane's folder and the bytes go straight to
    Google, which answers the file's sha256. A different sha256 is a failed copy; nothing is ever deleted."""
    def upload(folder: str, source: Path, sha: str) -> str:
        mime = mime_of(source)
        try:
            answer = engine.upload(request_id, machine, folder=folder, name=source.name, sha256=sha,
                                   size=source.stat().st_size, mime=mime)
            if answer.get("exists"):
                return str(answer["name"])
            filed = put(answer["upload_url"], source, mime)
        except EngineError as failure:
            raise FilingError(failure.status_class) from None
        got = str(filed.get("sha256Checksum") or "").lower()
        if got and got != sha:
            raise FilingError("copy_mismatch")
        return str(filed.get("name") or answer["name"])
    return upload


def handle_request(request: dict, config: Config, engine: Engine, state: State, counts: Counter) -> None:
    request_id = str(request["id"])
    heartbeat("fetch")
    work = state_dir() / "fetch" / request_id
    work.mkdir(parents=True, exist_ok=True)
    with paid.engine_runs(engine, request_id, config.machine):
        result = fetch(request["url"], work, config)
    for attempt in result.attempts:
        counts[f"method.{attempt.method}.{attempt.outcome.split(':')[0]}"] += 1
    if result.post is None:
        engine.report(request_id, config.machine, "failed", status_class=result.status_class)
        counts[f"failed.{result.status_class}"] += 1
        shutil.rmtree(work, ignore_errors=True)
        return
    post: Post = result.post
    shape = post.infer_shape()
    heartbeat("file")
    try:
        upload = engine_uploader(engine, request_id, config.machine) if config.filing == "engine" else None
        media = file_post(post, config, request.get("lane"), upload)
    except FilingError as failure:
        engine.report(request_id, config.machine, "failed", status_class="other", shape=shape)
        counts[f"failed.filing.{failure.status_class}"] += 1
        return
    engine.report(request_id, config.machine, "filed", shape=shape, media=media)
    counts["filed"] += 1
    heartbeat("read")
    readings = read_post(post.media[0].parent, out=state_dir() / "readings" / request_id,
                         whisper_model=config.whisper_model)
    rows = [reading.contract_row() for reading in readings]
    engine.report(request_id, config.machine, "read", shape=shape, media=media, reads=rows)
    for reading in readings:
        state.mark_sent(reading.sha256, ENGINE_REV)
        counts[f"heard.{reading.read.get('heard')}"] += 1
    counts["read"] += 1
    shutil.rmtree(work, ignore_errors=True)


def drop_candidates(config: Config, state: State, limit: int = DROP_LIMIT) -> list[tuple[Path, str, str]]:
    """Newest unread files first, stopping at the limit: hashing a Drive file can mean downloading it."""
    files = []
    for folder in FOLDERS:
        value = config.video_inspiration if folder == "video_inspiration" else config.cold_ideas
        if not value or not Path(value).is_dir():
            continue
        for path in Path(value).iterdir():
            if path.is_file() and not path.name.startswith(".") and kind_of(path) in ("video", "image", "text"):
                files.append((path.stat().st_mtime, path, folder))
    found = []
    for _mtime, path, folder in sorted(files, key=lambda item: item[0], reverse=True):
        sha = state.sha_of(path)
        if not state.read_sent(sha, ENGINE_REV):
            found.append((path, sha, folder))
            if len(found) >= limit:
                break
    return found


def read_drops(config: Config, engine: Engine, state: State, counts: Counter, limit: int = DROP_LIMIT) -> None:
    for path, sha, _folder in drop_candidates(config, state, limit):
        heartbeat("read_drop")
        try:
            readings = read_path(path, out=state_dir() / "readings" / "drops", whisper_model=config.whisper_model)
        except Exception:  # noqa: BLE001 - one bad file must not stop the run
            counts["drop.read_error"] += 1
            state.mark_sent(sha, ENGINE_REV)  # do not retry a file that cannot be read every minute
            continue
        engine.read(config.machine, [reading.contract_row() for reading in readings])
        for reading in readings:
            state.mark_sent(reading.sha256, ENGINE_REV)
        counts["drop.read"] += 1


def watch_once(config: Config | None = None, engine: Engine | None = None, deadline_s: float = RUN_DEADLINE_S) -> Counter:
    counts: Counter = Counter()
    started = time.monotonic()
    heartbeat("start")
    timer = threading.Timer(deadline_s, _over_time, args=(counts,))
    timer.daemon = True
    timer.start()
    try:
        _watch_once(config, engine, counts)
    except Exception as exc:  # noqa: BLE001 - a run that cannot start still logs, by class
        counts[f"run.error.{type(exc).__name__}"] += 1
    finally:
        timer.cancel()
    heartbeat("done")
    counts["seconds"] = int(time.monotonic() - started)
    log_line(counts)
    return counts


def _watch_once(config: Config | None, engine: Engine | None, counts: Counter) -> None:
    config = config or Config.load()
    with run_lock() as got:
        if not got:
            counts["skipped.already_running"] += 1
            return
        engine = engine or Engine(config.engine_url)
        state = State()
        try:
            heartbeat("claim")
            try:
                requests = engine.claim(config.machine, config.claim_limit)
            except EngineError as failure:
                counts[f"engine.{failure.status_class}"] += 1
                requests = []
            counts["claimed"] += len(requests)
            for request in requests:
                try:
                    handle_request(request, config, engine, state, counts)
                except EngineError as failure:
                    counts[f"engine.{failure.status_class}"] += 1
                except Exception:  # noqa: BLE001 - report a class, never the message
                    counts["request.error"] += 1
                    try:
                        engine.report(str(request["id"]), config.machine, "failed", status_class="other")
                    except EngineError:
                        pass
            # Dropped files only when the engine answered: their readings have nowhere to go otherwise.
            if not any(key.startswith("engine.") for key in counts):
                heartbeat("drops")
                try:
                    read_drops(config, engine, state, counts)
                except EngineError as failure:
                    counts[f"engine.{failure.status_class}"] += 1
        finally:
            state.close()
