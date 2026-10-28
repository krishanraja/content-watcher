"""The words for a timeline: a platform's captions and local transcription together, not one or the other.

Captions are usually the better text; transcription has the timing of every word. When both exist the timeline keeps
the captions' text, the transcription's word timings, and how far the two agree.
"""

from __future__ import annotations

import re

from ..read import audio


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", (text or "").lower())


def agreement(a: str, b: str) -> float | None:
    """Word overlap of two transcripts (F1 over word counts), 0 to 1."""
    left, right = _tokens(a), _tokens(b)
    if not left or not right:
        return None
    counts: dict[str, int] = {}
    for word in left:
        counts[word] = counts.get(word, 0) + 1
    common = 0
    for word in right:
        if counts.get(word):
            counts[word] -= 1
            common += 1
    if not common:
        return 0.0
    precision, recall = common / len(right), common / len(left)
    return round(2 * precision * recall / (precision + recall), 3)


def words_for(path, heard: audio.Heard, *, captions=None, has_audio: bool = True,
              whisper_model: str | None = None) -> tuple[audio.Heard, dict]:
    """The words the timeline uses, and where they came from."""
    from_captions = audio.parse_captions(captions) if captions and captions.is_file() else None
    if heard.source == "captions" and from_captions is None:
        from_captions = heard
    transcribed = heard if heard.source == "whisper" else None
    if from_captions is not None and from_captions.heard == "words" and transcribed is None and has_audio:
        transcribed = audio.transcribe(path, model_size=whisper_model)
    sources: dict = {"captions": bool(from_captions and from_captions.heard == "words"),
                     "whisper": bool(transcribed and transcribed.heard == "words")}
    if sources["captions"] and sources["whisper"]:
        sources["agreement"] = agreement(from_captions.text, transcribed.text)
        merged = audio.Heard("words", None, "captions+whisper", transcribed.language,
                             from_captions.segments, transcribed.words)
        return merged, sources
    if sources["captions"]:
        return from_captions, sources
    if transcribed is not None:
        return transcribed, sources
    return heard, sources
