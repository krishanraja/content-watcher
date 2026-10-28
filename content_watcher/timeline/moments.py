"""When a still is taken: as words are spoken, as the picture changes and as captions change; then merged and bounded."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from . import tags

# floor: the smallest mean grey difference (0-255, on 320 px frames) that counts as the picture changing (edited video).
# min_share: in a screen recording, the share of pixels that must differ from the last change (0.1%: a word typed).
# reaction: how long after a narrator names something the screen is looked at (a UI responds after it is spoken of).
PROFILES = {
    "social": {"floor": 4.0, "max": 40, "spacing": 1.5, "reaction": 0.0, "width": 1080},
    "ux": {"floor": 0.6, "min_share": 0.001, "max": 120, "spacing": 1.5, "reaction": 0.6, "width": 1920},
}
PIXEL_CHANGE = 25
SETTLE_MAX_S = 8.0  # a picture that keeps changing (a video playing on screen) still gets a still this often
PRIORITY = {"start": 3, "cut": 3, "screen_change": 3, "caption_change": 2, "speech": 1}
LONG_SEGMENT_S = 6.0
SEGMENT_STEP_S = 4.0


@dataclass
class Moment:
    t: float
    triggers: list[str] = field(default_factory=list)
    change_score: float | None = None
    motion: str | None = None

    @property
    def priority(self) -> int:
        return max(PRIORITY.get(trigger, 0) for trigger in self.triggers)


def _numpy():
    try:
        import numpy  # type: ignore
    except Exception:  # noqa: BLE001
        return None
    return numpy


def _clamp(t: float, duration: float) -> float:
    return round(min(max(0.0, t), max(0.0, duration - 0.05)), 2)


def frame_at(frames, t: float):
    index = min(len(frames.data) - 1, max(0, int(round(t * frames.fps))))
    return frames.data[index]


def dhash(grey) -> int | None:
    """A 64-bit difference hash: near-identical pictures have hashes a few bits apart."""
    numpy = _numpy()
    if numpy is None or grey is None:
        return None
    h, w = grey.shape
    ys = numpy.linspace(0, h, 9).astype(int)
    xs = numpy.linspace(0, w, 10).astype(int)
    blocks = numpy.array([[float(grey[ys[i]:max(ys[i + 1], ys[i] + 1), xs[j]:max(xs[j + 1], xs[j] + 1)].mean())
                           for j in range(9)] for i in range(8)])
    value = 0
    for bit in (blocks[:, 1:] > blocks[:, :-1]).flatten():
        value = (value << 1) | int(bit)
    return value


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def sentences(heard) -> list[dict]:
    """Spoken sentences with their times. Transcription can return a whole narration as one segment, so with word
    timings a sentence ends at . ? or ! or a pause over 0.8 s; without them the segments are the sentences."""
    if not heard.words:
        return [{"start": s["start"], "end": s["end"], "text": s["text"].strip()} for s in heard.segments
                if s.get("text", "").strip()]
    found, current = [], []
    for index, word in enumerate(heard.words):
        current.append(word)
        following = heard.words[index + 1] if index + 1 < len(heard.words) else None
        if (word["word"].rstrip().endswith((".", "?", "!")) or following is None
                or following["start"] - word["end"] > 0.8):
            found.append({"start": current[0]["start"], "end": current[-1]["end"],
                          "text": " ".join(w["word"].strip() for w in current).strip()})
            current = []
    return [sentence for sentence in found if sentence["text"]]


def speech_anchors(heard, duration: float, *, reaction: float = 0.0, point_at_terms: bool = False) -> list[Moment]:
    """One moment per spoken sentence (a long one every few seconds). For a narrated recording the moment sits on the
    words that name a problem or a wish, plus the reaction time; otherwise in the middle of what was said."""
    found = []
    for segment in sentences(heard):
        start, end = float(segment["start"]), float(segment["end"])
        if not segment.get("text", "").strip() or end <= start:
            continue
        pieces, at = [], start
        while at < end:
            stop = end if end - start <= LONG_SEGMENT_S else min(end, at + SEGMENT_STEP_S)
            pieces.append((at, stop))
            at = stop
        for piece_start, piece_end in pieces:
            t = (piece_start + piece_end) / 2
            if point_at_terms:
                inside = [w for w in heard.words if piece_start <= w["start"] < piece_end + 0.01]
                hit = tags.first_hit_time(inside)
                if hit is not None:
                    t = hit
            found.append(Moment(_clamp(t + reaction, duration), ["speech"]))
    return found


def cut_moments(cuts: list[float], spans: list[tuple[float, float]], duration: float) -> list[Moment]:
    """Just after each cut, clear of the transition frame."""
    found = []
    for start, end in spans:
        if start <= 0:
            continue
        found.append(Moment(_clamp(min(start + 0.3, (start + end) / 2), duration), ["cut"]))
    return found


def changed_share(a, b, numpy=None) -> float:
    """Share of pixels that differ clearly (more than 25 grey levels) between two frames."""
    numpy = numpy or _numpy()
    return float((numpy.abs(a.astype(numpy.int16) - b.astype(numpy.int16)) > PIXEL_CHANGE).mean())


def screen_changes(frames, duration: float, *, floor: float, scroll: bool = False,
                   min_share: float | None = None) -> list[Moment]:
    """Where the picture changes, from the grey frames the reader already sampled; the still is taken just after the
    change settles, and `change_score` is the share of the picture that changed.

    Edited video (no `min_share`): frame against frame, above the clip's own noise (median plus six median
    deviations) and never below the floor. A screen recording (`min_share`): each frame against the picture at the
    last change, counting changed pixels, so a few typed letters or a menu opening add up to a change while a
    blinking caret or a moving pointer does not."""
    numpy = _numpy()
    if numpy is None or frames is None or len(frames.data) < 2:
        return []
    data = frames.data
    events: list[tuple[int, int, int]] = []  # (frame before the change, settled frame, frame of the sharpest change)
    if min_share is None:
        diffs = numpy.array([float(numpy.abs(data[i].astype(numpy.int16) - data[i - 1].astype(numpy.int16)).mean())
                             for i in range(1, len(data))])
        median = float(numpy.median(diffs))
        mad = float(numpy.median(numpy.abs(diffs - median)))
        threshold = max(floor, median + 6 * mad)
        groups: list[list[int]] = []
        for index in (i + 1 for i, value in enumerate(diffs) if value > threshold):
            if groups and index - groups[-1][-1] <= 2:
                groups[-1].append(index)
            else:
                groups.append([index])
        events = [(g[0] - 1, g[-1], max(g, key=lambda i: diffs[i - 1])) for g in groups]
    else:
        longest = max(1, int(SETTLE_MAX_S * frames.fps))
        reference, index = 0, 1
        while index < len(data):
            if changed_share(data[index], data[reference], numpy) < min_share:
                index += 1
                continue
            settled, peak, peak_share = index, index, changed_share(data[index], data[index - 1], numpy)
            while (settled + 1 < len(data) and settled - index < longest
                   and changed_share(data[settled + 1], data[settled], numpy) >= min_share / 2):
                settled += 1
                share = changed_share(data[settled], data[settled - 1], numpy)
                if share > peak_share:
                    peak, peak_share = settled, share
            events.append((reference, settled, peak))
            reference, index = settled, settled + 1
    found = []
    for before, settled, peak in events:
        moment = Moment(_clamp(frames.time(settled) + 0.25, duration), ["screen_change"],
                        change_score=round(changed_share(data[settled], data[before], numpy), 4))
        if scroll and _is_scroll(numpy, data[peak - 1], data[peak]):
            moment.motion = "scroll"
        found.append(moment)
    return found


def _is_scroll(numpy, a, b) -> bool:
    """The change is the same picture moved up or down."""
    h = a.shape[0]
    a, b = a.astype(numpy.int16), b.astype(numpy.int16)
    still = float(numpy.abs(a - b).mean())
    best = (still, 0)
    for dy in range(-(h // 4), h // 4 + 1):
        if dy == 0:
            continue
        if dy > 0:
            error = float(numpy.abs(a[dy:] - b[:-dy]).mean())
        else:
            error = float(numpy.abs(a[:dy] - b[-dy:]).mean())
        if error < best[0]:
            best = (error, dy)
    # A scroll moves most of the picture, so it changes a lot standing still and almost nothing once shifted.
    return still >= 2.0 and abs(best[1]) >= 2 and best[0] < 0.35 * still


def _words_of(text: str) -> set[str]:
    """Words of three letters or more: OCR of a busy picture yields scraps ("il", "240)") that are not captions."""
    return set(re.findall(r"[a-z][a-z']{2,}", (text or "").lower()))


def _shared(words: set[str], previous: set[str]) -> float:
    """Share of words two captions have in common, counting a word OCR misread by a letter as the same word."""
    if not words or not previous:
        return 0.0
    matched = sum(1 for word in words if difflib.get_close_matches(word, previous, n=1, cutoff=0.8))
    return matched / max(len(words), len(previous))


def caption_changes(samples: list[dict]) -> list[Moment]:
    """A moment each time the words on screen change (fewer than half the words shared with the last caption)."""
    found, previous = [], set()
    for sample in samples:
        words = _words_of(sample["text"])
        if not words:
            continue
        if _shared(words, previous) < 0.5:
            found.append(Moment(round(sample["t"] + 0.1, 2), ["caption_change"]))
        previous = words
    return found


def choose(found: list[Moment], *, spacing: float, limit: int) -> list[Moment]:
    """Merge moments closer than the spacing (keeping every trigger, at the time of the strongest), then keep the
    strongest up to the limit, always keeping the opening."""
    merged: list[Moment] = []
    for moment in sorted(found, key=lambda m: (m.t, -m.priority)):
        if merged and moment.t - merged[-1].t < spacing:
            kept = merged[-1]
            if moment.priority > kept.priority:
                kept.t = moment.t
            for trigger in moment.triggers:
                if trigger not in kept.triggers:
                    kept.triggers.append(trigger)
            kept.triggers.sort(key=lambda trigger: -PRIORITY.get(trigger, 0))
            if moment.change_score is not None:
                kept.change_score = max(kept.change_score or 0.0, moment.change_score)
            kept.motion = kept.motion or moment.motion
            continue
        merged.append(Moment(moment.t, list(moment.triggers), moment.change_score, moment.motion))
    if len(merged) <= limit:
        return merged
    ranked = sorted(merged, key=lambda m: ("start" in m.triggers, m.priority, len(m.triggers), m.change_score or 0.0),
                    reverse=True)
    return sorted(ranked[:limit], key=lambda m: m.t)
