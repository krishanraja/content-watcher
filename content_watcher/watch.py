"""One watch run: claim pasted links, fetch, file, read, report; then read new hand-dropped files."""

from __future__ import annotations

import json
import shutil
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import ENGINE_REV
from .config import Config, state_dir
from .engine import Engine, EngineError
from .fetch import fetch
from .filing import FOLDERS, FilingError, file_post
from .post import Post, kind_of
from .read.reader import read_path, read_post
from .state import State, run_lock

DROP_LIMIT = 3  # hand-dropped files read per run, so a run stays short


def log_line(counts: Counter) -> Path:
    """The local log: counts and class names only, never a link, a caption or a file name."""
    target = state_dir() / "watch.log"
    target.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with target.open("a", encoding="utf-8") as handle:
        handle.write(stamp + " " + json.dumps(dict(sorted(counts.items())), separators=(",", ":")) + "\n")
    return target


def handle_request(request: dict, config: Config, engine: Engine, state: State, counts: Counter) -> None:
    request_id = str(request["id"])
    work = state_dir() / "fetch" / request_id
    work.mkdir(parents=True, exist_ok=True)
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
    try:
        media = file_post(post, config, request.get("lane"))
    except FilingError as failure:
        engine.report(request_id, config.machine, "failed", status_class="other", shape=shape)
        counts[f"failed.filing.{failure.status_class}"] += 1
        return
    engine.report(request_id, config.machine, "filed", shape=shape, media=media)
    counts["filed"] += 1
    readings = read_post(post.media[0].parent, out=state_dir() / "readings" / request_id,
                         whisper_model=config.whisper_model)
    rows = [reading.contract_row() for reading in readings]
    engine.report(request_id, config.machine, "read", shape=shape, media=media, reads=rows)
    for reading in readings:
        state.mark_sent(reading.sha256, ENGINE_REV)
        counts[f"heard.{reading.read.get('heard')}"] += 1
    counts["read"] += 1
    shutil.rmtree(work, ignore_errors=True)


def drop_candidates(config: Config, state: State) -> list[tuple[Path, str, str]]:
    found = []
    for folder in FOLDERS:
        value = config.video_inspiration if folder == "video_inspiration" else config.cold_ideas
        if not value or not Path(value).is_dir():
            continue
        for path in sorted(Path(value).iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not path.is_file() or path.name.startswith(".") or kind_of(path) not in ("video", "image", "text"):
                continue
            sha = state.sha_of(path)
            if not state.read_sent(sha, ENGINE_REV):
                found.append((path, sha, folder))
    return found


def read_drops(config: Config, engine: Engine, state: State, counts: Counter, limit: int = DROP_LIMIT) -> None:
    for path, sha, _folder in drop_candidates(config, state)[:limit]:
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


def watch_once(config: Config | None = None, engine: Engine | None = None) -> Counter:
    config = config or Config.load()
    counts: Counter = Counter()
    started = time.monotonic()
    with run_lock() as got:
        if not got:
            counts["skipped.already_running"] += 1
            log_line(counts)
            return counts
        engine = engine or Engine(config.engine_url)
        state = State()
        try:
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
            if "engine.no_engine_key" not in counts:
                try:
                    read_drops(config, engine, state, counts)
                except EngineError as failure:
                    counts[f"engine.{failure.status_class}"] += 1
        finally:
            state.close()
    counts["seconds"] = int(time.monotonic() - started)
    log_line(counts)
    return counts
