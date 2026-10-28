"""Building a timeline: choosing the moments, taking the stills, and saying what was said and shown at each."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from video_compression.ffmpeg import probe_media

from .. import TIMELINE_FORMAT, tools
from ..read import audio, visual
from . import captions as captions_words
from . import moments, tags
from .moments import Moment

DEFAULT_BUDGET_S = {"social": 240.0, "ux": 900.0}
WINDOW_S = 2.0
SAME_PICTURE_SHARE = 0.0005  # fewer pixels than a typed letter or two: the same picture


class TimelineBudget(Exception):
    """The timeline ran past its time budget; the reading goes out without it."""


@dataclass
class Built:
    data: dict
    stills: list[Path] = field(default_factory=list)
    words: audio.Heard | None = None


def budget_for(profile: str) -> float:
    try:
        return float(os.environ["CONTENT_WATCH_TIMELINE_BUDGET"])
    except (KeyError, ValueError):
        return DEFAULT_BUDGET_S[profile]


def _caption_samples(path: Path, duration: float, workdir: Path, deadline: float) -> list[dict] | None:
    """Words on screen about twice a second (fewer in a long video), skipping frames that repeat the one before,
    so each caption a reel burns in is read once. None when the frame times cannot be trusted."""
    fps = 2.0 if duration <= 90 else max(0.2, 180 / max(duration, 1))
    folder = workdir / "captions"
    folder.mkdir(parents=True, exist_ok=True)
    ffmpeg = tools.need("ffmpeg")
    ran = tools.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-i", path, "-an", "-vf",
         f"fps={fps},scale='min(720,iw)':-2,mpdecimate,showinfo", "-fps_mode", "vfr", folder / "c_%05d.png"],
        timeout=600,
    )
    times = [round(float(m.group(1)), 2) for m in re.finditer(r"showinfo.*?pts_time:\s*([\d.]+)", ran.stderr)]
    images = sorted(folder.glob("c_*.png"))
    if ran.returncode != 0 or len(times) != len(images):
        return None
    samples = []
    for t, image in zip(times, images):
        if time.monotonic() > deadline:
            raise TimelineBudget("captions")
        found = visual.ocr_image(image)
        samples.append({"t": t, "text": (found or {}).get("text", ""), "ocr": found})
        image.unlink(missing_ok=True)
    return samples


def _shot_of(spans: list[tuple[float, float]], t: float) -> int | None:
    for index, (start, end) in enumerate(spans):
        if start <= t < end:
            return index
    return len(spans) - 1 if spans else None


def _signals_near(words: audio.Heard, t: float) -> list[dict]:
    """UX signals in every sentence spoken within two seconds either side, each with its sentence."""
    hits = []
    for sentence in moments.sentences(words):
        if sentence["end"] > t - WINDOW_S and sentence["start"] < t + WINDOW_S:
            hits += [{**hit, "sentence": sentence["text"]} for hit in tags.ux_signals(sentence["text"])]
    return hits


def _said(words: audio.Heard, t: float) -> tuple[str, list[dict], str]:
    """The words spoken within two seconds either side, with their times, and the sentence being spoken."""
    low, high = t - WINDOW_S, t + WINDOW_S
    if words.words:
        near = [w for w in words.words if w["end"] > low and w["start"] < high]
        said = " ".join(w["word"] for w in near).strip()
    else:
        near = [{"start": s["start"], "end": s["end"], "text": s["text"]}
                for s in words.segments if s["end"] > low and s["start"] < high]
        said = " ".join(s["text"] for s in near).strip()
    spoken = moments.sentences(words)
    sentence = next((s["text"] for s in spoken if s["start"] <= t <= s["end"]), None)
    if sentence is None:
        before = [s for s in spoken if 0 <= t - s["end"] <= 1.0]
        sentence = before[-1]["text"] if before else ""
    return said[:600], near, sentence.strip()


def _face_at(samples: list[dict] | None, t: float) -> dict | None:
    if samples is None:
        return None
    near = [s for s in samples if abs(s["t"] - t) <= 0.6]
    if not near:
        return None
    sample = min(near, key=lambda s: abs(s["t"] - t))
    height = sample.get("height_share")
    return {"on": height is not None, "framing": tags.framing(height)}


def timeline(path: Path, *, profile: str, duration: float, heard: audio.Heard, cuts: list[float],
             spans: list[tuple[float, float]], frames, workdir: Path, face_samples: list[dict] | None = None,
             camera_moves: list[dict] | None = None, post: dict | None = None, captions: Path | None = None,
             has_audio: bool = True, whisper_model: str | None = None, profile_reason: str = "",
             budget_s: float | None = None, max_stills: int | None = None) -> Built:
    from ..read.reader import _layout

    config = moments.PROFILES[profile]
    deadline = time.monotonic() + (budget_s if budget_s is not None else budget_for(profile))

    def check(stage: str) -> None:
        if time.monotonic() > deadline:
            raise TimelineBudget(stage)

    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    unmeasured: list[str] = []
    words, sources = captions_words.words_for(path, heard, captions=captions, has_audio=has_audio,
                                              whisper_model=whisper_model)
    if words.heard_class == "no_whisper":
        unmeasured.append("words")
    check("words")

    found = [Moment(round(min(0.5, duration / 2), 2), ["start"])]
    found += moments.speech_anchors(words, duration, reaction=config["reaction"], point_at_terms=profile == "ux")
    if profile == "social":
        found += moments.cut_moments(cuts, spans, duration)
    if frames is not None:
        found += moments.screen_changes(frames, duration, floor=config["floor"], scroll=profile == "ux",
                                        min_share=config.get("min_share"))
    else:
        unmeasured.append("screen_changes")
    samples: list[dict] = []
    if profile == "social":
        if tools.which("tesseract"):
            samples = _caption_samples(path, duration, workdir, deadline) or []
            found += moments.caption_changes(samples)
        else:
            unmeasured.append("screen_text")
    check("moments")

    chosen = moments.choose(found, spacing=config["spacing"], limit=max_stills or config["max"])
    can_ocr = bool(tools.which("tesseract"))
    if profile == "ux" and not can_ocr:
        unmeasured.append("screen_text")
    entries: list[dict] = []
    stills: list[Path] = []
    last_image: tuple | None = None  # (grey frame, entry) of the last picture taken
    for number, moment in enumerate(chosen, start=1):
        check("stills")
        entry: dict = {"index": number, "t": moment.t, "triggers": moment.triggers, "shot": _shot_of(spans, moment.t)}
        grey = moments.frame_at(frames, moment.t) if frames is not None else None
        grey_hash = moments.dhash(grey)
        if grey_hash is not None:
            entry["dhash"] = f"{grey_hash:016x}"
        repeat = (last_image is not None and grey is not None and last_image[0] is not None
                  and set(moment.triggers) <= {"speech"}
                  and moments.changed_share(grey, last_image[0]) < SAME_PICTURE_SHARE)
        if repeat:
            # The narrator talks over a screen that has not changed: the same picture, not another copy of it.
            image = last_image[1]
            entry["same_as"] = image["index"]
            for key in ("file", "still_sha256", "screen_text", "colours", "layout_ocr"):
                if key in image:
                    entry[key] = image[key]
        else:
            target = workdir / f"still_{number:03d}_{int(round(moment.t * 1000)):07d}ms.jpg"
            grabbed = visual.grab_frame(path, moment.t, target, width=config["width"])
            entry["file"] = f"stills/{grabbed.name}" if grabbed else None
            if grabbed:
                stills.append(grabbed)
                entry["still_sha256"] = tools.sha256_file(grabbed)
                entry["colours"] = visual.colours(grabbed)
                if profile == "ux" and can_ocr:
                    found_text = visual.ocr_image(grabbed)
                    entry["layout_ocr"] = found_text
                    entry["screen_text"] = (found_text or {}).get("text", "")
            last_image = (grey, entry)
        if profile == "social" and samples:
            shown = [s for s in samples if s["t"] <= moment.t + 0.25]
            if shown:
                entry["screen_text"] = shown[-1]["text"]
                entry["layout_ocr"] = shown[-1]["ocr"]
        said, near, sentence = _said(words, moment.t)
        entry["said"] = said
        entry["words"] = near
        entry["sentence"] = sentence
        entry["ux_signals"] = _signals_near(words, moment.t)
        entry["face"] = _face_at(face_samples, moment.t) if profile == "social" else None
        if entry["face"] is None:
            entry.pop("face")
        ocr = entry.pop("layout_ocr", None)
        if ocr is not None or entry.get("face") is not None:
            entry["layout"] = _layout(ocr, (entry.get("face") or {}).get("on"))
        entry["change_score"] = moment.change_score
        motion = moment.motion
        if motion is None and profile == "social" and camera_moves and entry["shot"] is not None:
            start = spans[entry["shot"]][0]
            motion = next((m["kind"] for m in camera_moves if abs(m["start"] - start) < 0.01), None)
        entry["motion"] = motion
        entry["tags"] = tags.tags_for(entry, profile)
        entries.append(entry)

    by_trigger: dict[str, int] = {}
    for entry in entries:
        for trigger in entry["triggers"]:
            by_trigger[trigger] = by_trigger.get(trigger, 0) + 1
    data = {
        "format": TIMELINE_FORMAT,
        "profile": profile,
        "profile_reason": profile_reason,
        "duration_s": round(duration, 2),
        "words": {"source": words.source, "language": words.language, **sources},
        "lexicon": tags.LEXICON_VERSION,
        "counts": {"stills": len(entries), "images": len(stills), "by_trigger": by_trigger},
        "post_tags": tags.post_tags(post),
        "ux_signals": _signal_summary(entries),
        "unmeasured": sorted(set(unmeasured)),
        "entries": entries,
    }
    return Built(data, stills, words)


def _signal_summary(entries: list[dict]) -> list[dict]:
    """Each UX signal once, at the first still near the sentence that carries it."""
    seen, out = set(), []
    for entry in entries:
        for hit in entry["ux_signals"]:
            key = (hit["sentence"], hit["signal"], hit["term"])
            if key in seen:
                continue
            seen.add(key)
            out.append({"t": entry["t"], "index": entry["index"], "signal": hit["signal"], "term": hit["term"],
                        "said": hit["sentence"]})
    return out


def resolve_profile(requested: str, *, has_post: bool, face_share: float | None, changes_per_min: float,
                    cuts_per_min: float) -> tuple[str, str]:
    """`auto` reads a screen recording as `ux`: no post, almost no faces, and more small changes than hard cuts."""
    if requested in moments.PROFILES:
        return requested, "asked for"
    faces_low = face_share is None or face_share < 0.1
    if not has_post and faces_low and changes_per_min >= 1.5 * max(cuts_per_min, 1.0):
        return "ux", (f"no post, faces on {int((face_share or 0) * 100)}% of frames, {changes_per_min:.1f} screen changes "
                      f"a minute against {cuts_per_min:.1f} cuts")
    return "social", (f"faces on {int((face_share or 0) * 100)}% of frames, {changes_per_min:.1f} screen changes a minute "
                      f"against {cuts_per_min:.1f} cuts" + (", from a post" if has_post else ""))


def _free_folder(base: Path) -> Path:
    if not base.exists():
        return base
    for number in range(2, 1000):
        candidate = base.with_name(f"{base.name}_{number}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(base)


def build_standalone(path: Path, out: Path, *, profile: str = "auto", whisper_model: str | None = None,
                     captions: Path | None = None, max_stills: int | None = None,
                     budget_s: float | None = None) -> tuple[Path, Built]:
    """A timeline of one file into its own new folder under `out`: timeline.json, timeline.md and stills/.
    It writes nowhere else: no engine, no filing, no watch state, and never over an earlier folder."""
    from .render import render_timeline_md

    path = Path(path)
    info = probe_media(path)
    duration = info.duration_seconds
    sha = tools.sha256_file(path)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-")[:60] or "video"
    folder = _free_folder(Path(out) / f"{stem}_{sha[:12]}")
    folder.mkdir(parents=True)
    heard = audio.transcribe(path, model_size=whisper_model) if info.has_audio else audio.Heard("silent", "no_audio_stream")
    cut_times = [t for t in visual.cuts(path) if 0.1 < t < duration - 0.1]
    edges = [0.0, *cut_times, duration]
    spans = [(edges[i], edges[i + 1]) for i in range(len(edges) - 1) if edges[i + 1] - edges[i] > 0.05]
    frames = visual.sample_frames(path, duration, info.width, info.height)
    face_data = visual.faces(frames)
    face_samples = face_data.get("samples") if face_data.get("available") else None
    minutes = duration / 60 if duration else 0
    ux = moments.PROFILES["ux"]
    changes = moments.screen_changes(frames, duration, floor=ux["floor"], min_share=ux["min_share"]) if frames is not None else []
    chosen, reason = resolve_profile(
        profile, has_post=False, face_share=face_data.get("share_on_face"),
        changes_per_min=len(changes) / minutes if minutes else 0.0,
        cuts_per_min=len(cut_times) / minutes if minutes else 0.0,
    )
    work = folder / "stills"
    built = timeline(
        path, profile=chosen, duration=duration, heard=heard, cuts=cut_times, spans=spans, frames=frames,
        workdir=work, face_samples=face_samples,
        camera_moves=visual.camera_moves(frames, spans) if chosen == "social" else None,
        captions=captions, has_audio=info.has_audio, whisper_model=whisper_model, profile_reason=reason,
        budget_s=budget_s, max_stills=max_stills,
    )
    leftovers = work / "captions"
    if leftovers.is_dir() and not any(leftovers.iterdir()):
        leftovers.rmdir()
    built.data["source"] = {"file": path.name, "sha256": sha, "bytes": path.stat().st_size,
                            "width": info.width, "height": info.height, "has_audio": info.has_audio}
    if heard.heard != "words":
        built.data["heard"] = {"heard": heard.heard, "heard_class": heard.heard_class}
    # On its own the timeline is the whole record of a feedback session, so it keeps everything that was said.
    built.data["sentences"] = moments.sentences(built.words) if built.words else []
    (folder / "timeline.json").write_text(json.dumps(built.data, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "timeline.md").write_text(render_timeline_md(built.data), encoding="utf-8")
    return folder, built
