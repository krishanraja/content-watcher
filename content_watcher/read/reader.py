"""Turning one file, or one fetched post, into readings: read.json and read.md."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from video_compression.ffmpeg import probe_media

from .. import ENGINE_REV, READ_FORMAT, tools
from ..post import Post, kind_of, mime_of
from . import audio, visual
from .render import render_md

HOOK_SECONDS = 3.0


@dataclass
class Reading:
    sha256: str
    shape: str
    platform: str
    source_url: str | None
    read: dict
    read_md: str
    frames: list[Path] = field(default_factory=list)
    folder: Path | None = None
    stills: list[Path] = field(default_factory=list)

    def contract_row(self) -> dict:
        """What content_reads stores."""
        return {
            "sha256": self.sha256,
            "source_url": self.source_url,
            "platform": self.platform,
            "shape": self.shape,
            "engine_rev": ENGINE_REV,
            "read": self.read,
            "read_md": self.read_md,
        }

    def save(self, folder: Path) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "read.json").write_text(json.dumps(self.read, indent=2, ensure_ascii=False), encoding="utf-8")
        (folder / "read.md").write_text(self.read_md, encoding="utf-8")
        moved = []
        for frame in self.frames:
            target = folder / frame.name
            if frame.resolve() != target.resolve():
                shutil.copy2(frame, target)
            moved.append(target)
        self.frames = moved
        if self.stills:
            (folder / "stills").mkdir(exist_ok=True)
            kept = []
            for still in self.stills:
                target = folder / "stills" / still.name
                if still.resolve() != target.resolve():
                    shutil.copy2(still, target)
                kept.append(target)
            self.stills = kept
        self.folder = folder
        return folder


def _base(path: Path, shape: str, post: Post | None, sha: str) -> dict:
    return {
        "format": READ_FORMAT,
        "engine_rev": ENGINE_REV,
        "sha256": sha,
        "shape": shape,
        "file": {"name": path.name, "bytes": path.stat().st_size, "mime": mime_of(path)},
        "post": post.summary() if post else None,
        "heard": "silent",
        "heard_class": "not_applicable",
        "words_text": "",
        "unmeasured": [],
    }


def _heard_into(data: dict, heard: audio.Heard) -> None:
    data["heard"] = heard.heard
    data["heard_class"] = heard.heard_class
    data["words_text"] = heard.text
    data["words"] = {
        "source": heard.source,
        "language": heard.language,
        "segments": heard.segments,
        "word_count": len(heard.text.split()),
    }


def read_video(path: Path, *, post: Post | None = None, captions: Path | None = None,
               workdir: Path | None = None, whisper_model: str | None = None) -> Reading:
    sha = tools.sha256_file(path)
    work = Path(workdir or tempfile.mkdtemp(prefix="cw-read-"))
    work.mkdir(parents=True, exist_ok=True)
    data = _base(path, "video", post, sha)
    info = probe_media(path)
    duration = info.duration_seconds
    data["video"] = {
        "duration_s": round(duration, 2), "width": info.width, "height": info.height,
        "fps": round(info.fps, 2), "aspect": _aspect(info.width, info.height), "has_audio": info.has_audio,
    }

    # Words: a platform's own captions first (free and usually better), then local transcription.
    heard = audio.parse_captions(captions) if captions and captions.is_file() else None
    if heard is None or heard.heard != "words":
        heard = audio.transcribe(path, model_size=whisper_model) if info.has_audio else audio.Heard("silent", "no_audio_stream")
    _heard_into(data, heard)
    if heard.heard_class == "no_whisper":
        data["unmeasured"].append("words")

    # Shots.
    cut_times = [time for time in visual.cuts(path) if 0.1 < time < duration - 0.1]
    edges = [0.0, *cut_times, duration]
    spans = [(edges[i], edges[i + 1]) for i in range(len(edges) - 1) if edges[i + 1] - edges[i] > 0.05]
    lengths = sorted(end - start for start, end in spans)
    minutes = duration / 60 if duration else 0
    data["shots"] = {
        "count": len(spans),
        "cuts": cut_times,
        "cuts_per_min": round(len(cut_times) / minutes, 1) if minutes else 0.0,
        "length_s": {
            "median": round(lengths[len(lengths) // 2], 2) if lengths else 0.0,
            "mean": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
            "min": round(lengths[0], 2) if lengths else 0.0,
            "max": round(lengths[-1], 2) if lengths else 0.0,
        },
        "list": [{"start": round(s, 2), "end": round(e, 2)} for s, e in spans],
    }

    frames = visual.sample_frames(path, duration, info.width, info.height)
    if frames is None:
        data["unmeasured"].extend(["camera_moves", "faces"])
    data["camera_moves"] = visual.camera_moves(frames, spans)
    data["faces"] = visual.faces(frames)
    if not data["faces"].get("available"):
        if "faces" not in data["unmeasured"]:
            data["unmeasured"].append("faces")
    else:
        samples = data["faces"].pop("samples")
        for shot in data["shots"]["list"]:
            inside = [s for s in samples if shot["start"] <= s["t"] < shot["end"]]
            if inside:
                hits = [s for s in inside if "height_share" in s]
                shot["face_share"] = round(len(hits) / len(inside), 2)
                if hits:
                    shot["face_height"] = round(sum(s["height_share"] for s in hits) / len(hits), 3)

    text = visual.screen_text(path, spans, work)
    if not text["available"]:
        data["unmeasured"].append("screen_text")
    data["screen_text"] = text["items"]
    for item in text["items"]:
        shot = data["shots"]["list"][item["shot"]]
        shot.setdefault("screen_text", []).append(item["text"])
    for shot in data["shots"]["list"]:
        for move in data["camera_moves"]:
            if move["start"] == shot["start"]:
                shot["move"] = move["kind"]

    # Sound.
    if info.has_audio:
        data["audio"] = audio.loudness(path)
        quiet = audio.silences(path)
        data["audio"]["silences"] = len(quiet)
        data["audio"]["longest_silence_s"] = round(max((q["end"] - q["start"] for q in quiet), default=0.0), 2)
    else:
        data["audio"] = {"integrated_lufs": None, "silences": None}

    # Pace.
    word_count = data["words"]["word_count"]
    speech_time = sum(seg["end"] - seg["start"] for seg in heard.segments)
    gaps = [b["start"] - a["end"] for a, b in zip(heard.words, heard.words[1:])] if heard.words else [
        b["start"] - a["end"] for a, b in zip(heard.segments, heard.segments[1:])
    ]
    data["pace"] = {
        "words_per_min": round(word_count / minutes, 1) if minutes and word_count else 0.0,
        "speech_share": round(min(1.0, speech_time / duration), 2) if duration else 0.0,
        "pauses_over_0_6s": sum(1 for gap in gaps if gap > 0.6),
        "longest_pause_s": round(max(gaps, default=0.0), 2),
        "first_word_s": heard.segments[0]["start"] if heard.segments else None,
    }
    data["pace"]["sound_without_words_share"] = (
        round(max(0.0, 1.0 - data["pace"]["speech_share"]), 2) if info.has_audio else None
    )

    # The hook: the first three seconds.
    hook_words = [seg["text"] for seg in heard.segments if seg["start"] < HOOK_SECONDS]
    if heard.words:
        hook_words = [" ".join(w["word"] for w in heard.words if w["start"] < HOOK_SECONDS)]
    data["hook"] = {
        "window_s": HOOK_SECONDS,
        "words": " ".join(hook_words).strip(),
        "screen_text": [item["text"] for item in text["items"] if item["t"] < HOOK_SECONDS],
        "cuts": sum(1 for time in cut_times if time < HOOK_SECONDS),
        "face_on_screen": _face_in(data["faces"], samples if data["faces"].get("available") else [], 0, HOOK_SECONDS),
        "move": next((m["kind"] for m in data["camera_moves"] if m["start"] < HOOK_SECONDS), None),
    }

    # Two chosen frames for the rare reader that needs to see.
    chosen = []
    hook_time = min(1.0, duration / 2)
    hook_frame = visual.grab_frame(path, hook_time, work / f"{sha[:12]}_hook.jpg", width=512)
    if hook_frame:
        chosen.append({"role": "hook", "t": round(hook_time, 2), "file": hook_frame.name})
    if text.get("most_text_time") is not None and abs(text["most_text_time"] - hook_time) > 0.5:
        most = visual.grab_frame(path, text["most_text_time"], work / f"{sha[:12]}_most_text.jpg", width=512)
        if most:
            chosen.append({"role": "most_text", "t": round(text["most_text_time"], 2), "file": most.name})
    data["frames"] = chosen
    frame_paths = [work / item["file"] for item in chosen]

    # The timeline: stills at each moment with what was said and shown. It can never fail or hold up the reading.
    stills: list[Path] = []
    try:
        from ..timeline import timeline

        built = timeline(
            path, profile="social", duration=duration, heard=heard, cuts=cut_times, spans=spans, frames=frames,
            workdir=work / f"{sha[:12]}_stills", face_samples=samples if data["faces"].get("available") else None,
            camera_moves=data["camera_moves"], post=data["post"], captions=captions, has_audio=info.has_audio,
            whisper_model=whisper_model, profile_reason="every video reading carries a social timeline",
        )
        data["timeline"], stills = built.data, built.stills
    except Exception:  # noqa: BLE001 - a timeline is extra; the reading goes out as before without it
        data["unmeasured"].append("timeline")
    return Reading(sha, "video", post.platform if post else "own", post.url if post else None,
                   data, render_md(data), frame_paths, stills=stills)


def _face_in(face_data: dict, samples: list, start: float, end: float):
    if not face_data.get("available"):
        return None
    inside = [s for s in samples if start <= s["t"] < end]
    return any("height_share" in s for s in inside) if inside else None


def _aspect(width: int, height: int) -> str:
    if not width or not height:
        return "unknown"
    ratio = width / height
    for name, value in (("9:16", 9 / 16), ("4:5", 4 / 5), ("1:1", 1.0), ("16:9", 16 / 9), ("4:3", 4 / 3)):
        if abs(ratio - value) < 0.03:
            return name
    return f"{ratio:.2f}:1"


def _image_dims(path: Path) -> tuple[int, int]:
    ffprobe = tools.need("ffprobe")
    ran = tools.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                     "-of", "csv=p=0", path], timeout=30)
    try:
        width, height = (int(x) for x in ran.stdout.strip().split(",")[:2])
    except ValueError:
        return 0, 0
    return width, height


def _layout(ocr: dict | None, face: bool | None) -> list[str]:
    labels = []
    if ocr:
        lines = ocr["lines"]
        numeric = [line for line in lines if re.fullmatch(r"[\s$£€]*[\d.,]+\s*[%xkKmMbB+]*\s*", line)]
        bullets = [line for line in lines if re.match(r"^\s*([-•*→✓]|\d+[.)])\s+", line)]
        if numeric and ocr["biggest_line_share"] >= 0.08:
            labels.append("one_number")
        if len(bullets) >= 3:
            labels.append("list")
        if ocr["text_area_share"] >= 0.12 or len(lines) >= 8:
            labels.append("text_heavy")
        elif not lines:
            labels.append("no_text")
    if face:
        labels.append("face")
    if not labels:
        labels.append("image_led")
    return labels


def _single_face(path: Path) -> bool | None:
    cv2 = visual._cv2()
    if cv2 is None or not hasattr(cv2, "CascadeClassifier"):
        return None
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None
    detector = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
    found = detector.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5,
                                      minSize=(int(image.shape[0] * 0.08),) * 2)
    return bool(len(found))


def read_image(path: Path, *, post: Post | None = None, index: int = 1, workdir: Path | None = None) -> Reading:
    sha = tools.sha256_file(path)
    data = _base(path, "image", post, sha)
    work = Path(workdir or tempfile.mkdtemp(prefix="cw-read-"))
    work.mkdir(parents=True, exist_ok=True)
    source = path
    if path.suffix.lower() in (".webp", ".heic", ".gif"):
        converted = visual.grab_frame(path, 0, work / f"{sha[:12]}.png", width=2000)
        source = converted or path
    width, height = _image_dims(source)
    ocr = visual.ocr_image(source)
    face = _single_face(source)
    data["slide"] = {
        "index": index,
        "width": width,
        "height": height,
        "aspect": _aspect(width, height),
        "text": ocr["text"] if ocr else None,
        "text_area_share": ocr["text_area_share"] if ocr else None,
        "line_count": len(ocr["lines"]) if ocr else None,
        "word_count": len(ocr["text"].split()) if ocr else None,
        "face": face,
        "layout": _layout(ocr, face),
        "colours": visual.colours(source),
    }
    if ocr is None:
        data["unmeasured"].append("screen_text")
    if face is None:
        data["unmeasured"].append("faces")
    data["words_text"] = ""
    return Reading(sha, "image", post.platform if post else "own", post.url if post else None,
                   data, render_md(data))


def parse_text_post(text: str) -> tuple[dict, str]:
    """A filed text post starts with Author:, Posted: and Link: lines; the rest is the post."""
    meta, body_lines, in_header = {}, [], True
    for line in text.splitlines():
        match = re.match(r"^(Author|Posted|Link|Platform):\s*(.*)$", line) if in_header else None
        if match:
            meta[match.group(1).lower()] = match.group(2).strip()
            continue
        if in_header and line.startswith("# "):
            meta.setdefault("title", line[2:].strip())
            continue
        if in_header and not line.strip():
            continue
        in_header = False
        body_lines.append(line)
    return meta, "\n".join(body_lines).strip()


def read_text(path: Path, *, post: Post | None = None) -> Reading:
    raw = path.read_text(encoding="utf-8", errors="replace")
    sha = tools.sha256_file(path)
    data = _base(path, "text", post, sha)
    meta, body = parse_text_post(raw)
    if post is None and meta:
        data["post"] = {
            "author": meta.get("author"), "posted_at": meta.get("posted"), "caption": body,
            "url": meta.get("link"), "platform": meta.get("platform"),
        }
    paragraphs = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    lines = [line for line in body.splitlines() if line.strip()]
    data["text"] = {
        "body": body,
        "word_count": len(body.split()),
        "paragraphs": len(paragraphs),
        "first_line": lines[0].strip() if lines else "",
        "list_lines": sum(1 for line in lines if re.match(r"^\s*([-•*→✓]|\d+[.)])\s+", line)),
        "hashtags": re.findall(r"#\w+", body),
    }
    platform = post.platform if post else (meta.get("platform") or "own")
    return Reading(sha, "text", platform, post.url if post else meta.get("link"), data, render_md(data))


def read_document(path: Path, *, post: Post | None = None, workdir: Path | None = None, max_pages: int = 30) -> Reading:
    """A PDF (a LinkedIn document post): its text, and each page read as a slide (layout, words, colours)."""
    sha = tools.sha256_file(path)
    data = _base(path, "document", post, sha)
    work = Path(workdir or tempfile.mkdtemp(prefix="cw-read-"))
    work.mkdir(parents=True, exist_ok=True)
    pdftotext, pdftoppm = tools.which("pdftotext"), tools.which("pdftoppm")
    body = ""
    if pdftotext:
        ran = tools.run([pdftotext, "-layout", path, "-"], timeout=120)
        body = ran.stdout.strip() if ran.returncode == 0 else ""
    else:
        data["unmeasured"].append("document_text")
    pages = []
    if pdftoppm:
        prefix = work / f"{sha[:12]}_page"
        tools.run([pdftoppm, "-png", "-r", "80", "-l", str(max_pages), path, prefix], timeout=300)
        for index, image in enumerate(sorted(work.glob(f"{sha[:12]}_page*.png")), start=1):
            slide = read_image(image, index=index, workdir=work).read["slide"]
            pages.append(slide)
    else:
        data["unmeasured"].append("document_pages")
    data["document"] = {"page_count": len(pages) or None, "text": body, "pages": pages,
                        "word_count": len(body.split())}
    data["words_text"] = ""
    return Reading(sha, "document", post.platform if post else "own", post.url if post else None, data, render_md(data))


def read_post(folder: Path, *, out: Path | None = None, whisper_model: str | None = None) -> list[Reading]:
    """One reading per file in a fetched post; the first file's reading covers the whole post."""
    post = Post.load(folder)
    shape = post.infer_shape()
    out = out or folder / "readings"
    readings: list[Reading] = []
    with tempfile.TemporaryDirectory(prefix="cw-post-") as tmp:
        work = Path(tmp)
        for index, media in enumerate(post.media, start=1):
            kind = kind_of(media)
            if kind == "video":
                reading = read_video(media, post=post, captions=post.captions_file, workdir=work,
                                     whisper_model=whisper_model)
            elif kind == "image":
                reading = read_image(media, post=post, index=index, workdir=work)
            elif kind == "text":
                reading = read_text(media, post=post)
            elif kind == "document":
                reading = read_document(media, post=post, workdir=work)
            else:
                continue
            reading.shape = shape if shape in ("carousel",) else reading.shape
            reading.read["shape"] = reading.shape
            reading.read["position"] = {"index": index, "of": len(post.media)}
            readings.append(reading)
        if shape == "carousel" and readings:
            heard = None
            if post.audio and post.audio.is_file():
                heard = audio.transcribe(post.audio, model_size=whisper_model)
            first = readings[0]
            first.read["post_slides"] = [
                {
                    "index": r.read["position"]["index"],
                    "sha256": r.sha256,
                    "kind": "video" if "video" in r.read else "image",
                    "text": (r.read.get("slide") or {}).get("text")
                    or "\n".join(i["text"] for i in r.read.get("screen_text", [])),
                    "layout": (r.read.get("slide") or {}).get("layout"),
                    "words_text": r.read.get("words_text", ""),
                }
                for r in readings
            ]
            if heard is not None:
                _heard_into(first.read, heard)
                first.read["post_audio"] = True
            first.read_md = render_md(first.read)
            for other in readings[1:]:
                other.read_md = render_md(other.read)
        for reading in readings:
            reading.save(out / f"{reading.read['position']['index']:02d}_{reading.sha256[:12]}")
    return readings


def read_path(path: Path, *, out: Path, whisper_model: str | None = None) -> list[Reading]:
    path = Path(path)
    if path.is_dir():
        if (path / "post.json").is_file():
            return read_post(path, out=out, whisper_model=whisper_model)
        readings = []
        for child in sorted(path.iterdir()):
            if child.is_file() and kind_of(child) in ("video", "image", "text", "document"):
                readings.extend(read_path(child, out=out, whisper_model=whisper_model))
        return readings
    kind = kind_of(path)
    with tempfile.TemporaryDirectory(prefix="cw-file-") as tmp:
        if kind == "video":
            reading = read_video(path, workdir=Path(tmp), whisper_model=whisper_model)
        elif kind == "image":
            reading = read_image(path, workdir=Path(tmp))
        elif kind == "text":
            reading = read_text(path)
        elif kind == "document":
            reading = read_document(path, workdir=Path(tmp))
        elif kind == "audio":
            heard = audio.transcribe(path, model_size=whisper_model)
            sha = tools.sha256_file(path)
            data = _base(path, "video", None, sha)
            _heard_into(data, heard)
            reading = Reading(sha, "video", "own", None, data, render_md(data))
        else:
            raise ValueError(f"Not a file this reads: {path.name}")
        reading.save(out / reading.sha256[:12])
    return [reading]
