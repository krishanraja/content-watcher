"""content-watch: fetch, read, watch and doctor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Config


def _fetch(args: argparse.Namespace) -> int:
    from .fetch import fetch

    result = fetch(args.url, Path(args.out).expanduser().resolve(), Config.load())
    for attempt in result.attempts:
        print(f"  {attempt.method}: {attempt.outcome}")
    if result.post is None:
        print(f"Failed: {result.status_class} ({result.detail})")
        return 2
    post = result.post
    print(f"Got a {post.platform} {post.infer_shape()} by {post.author or 'unknown'} with {len(post.media)} file(s):")
    for path in post.media:
        print(f"  {path}")
    return 0


def _read(args: argparse.Namespace) -> int:
    from .read import read_path

    readings = read_path(Path(args.path).expanduser().resolve(), out=Path(args.out).expanduser().resolve(),
                         whisper_model=args.whisper or Config.load().whisper_model)
    for reading in readings:
        print(f"{reading.shape} {reading.sha256[:12]}: heard {reading.read.get('heard')}, "
              f"{len(reading.read_md)} characters")
        print(f"  {reading.folder / 'read.md'}")
    return 0


def _watch(args: argparse.Namespace) -> int:
    from .watch import watch_once

    counts = watch_once()
    print(json.dumps(dict(sorted(counts.items()))))
    return 0


def _doctor(args: argparse.Namespace) -> int:
    from .doctor import checks, render

    rows = checks(Config.load())
    print(json.dumps(rows, indent=2) if args.json else render(rows))
    return 0 if all(row["ok"] for row in rows if row["required"]) else 1


def _config(args: argparse.Namespace) -> int:
    config = Config.load()
    for field in ("filing", "video_inspiration", "cold_ideas", "engine_url", "machine", "whisper_model", "cobalt_url"):
        value = getattr(args, field)
        if value is not None:
            setattr(config, field, value)
    if args.cookies:
        platform, _, profile = args.cookies.partition("=")
        if profile:
            config.cookies[platform] = profile
        else:
            config.cookies.pop(platform, None)
    if args.apify_cap is not None:
        config.apify_monthly_cap_usd = args.apify_cap
        config.apify_enabled = args.apify_cap > 0
    path = config.save()
    print(f"Saved {path}")
    print(json.dumps(config.__dict__, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="content-watch", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="fetch one post into a local folder")
    fetch.add_argument("url")
    fetch.add_argument("--out", default="fetched")
    fetch.set_defaults(func=_fetch)

    read = sub.add_parser("read", help="read a file, a folder or a fetched post into read.json and read.md")
    read.add_argument("path")
    read.add_argument("--out", default="readings")
    read.add_argument("--whisper", help="faster-whisper model size (default from config, small)")
    read.set_defaults(func=_read)

    watch = sub.add_parser("watch", help="one run of the queue and the drop folders")
    watch.add_argument("--once", action="store_true", required=True)
    watch.set_defaults(func=_watch)

    doctor = sub.add_parser("doctor", help="what this machine can and cannot do")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=_doctor)

    config = sub.add_parser("config", help="set this machine's settings")
    config.add_argument("--filing", choices=("local", "drive"))
    config.add_argument("--video-inspiration", dest="video_inspiration")
    config.add_argument("--cold-ideas", dest="cold_ideas")
    config.add_argument("--engine-url", dest="engine_url")
    config.add_argument("--machine")
    config.add_argument("--whisper-model", dest="whisper_model")
    config.add_argument("--cobalt-url", dest="cobalt_url", help="a cobalt instance, e.g. http://localhost:9000")
    config.add_argument("--cookies", help="platform=FirefoxProfile, or platform= to clear")
    config.add_argument("--apify-cap", dest="apify_cap", type=float, help="standing monthly cap in USD; 0 turns Apify off")
    config.set_defaults(func=_config)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


def entrypoint() -> None:
    sys.exit(main())
