"""What is heard: the words with timings, loudness and pauses."""

from __future__ import annotations

import array
import html
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .. import tools

SAMPLE_RATE = 16_000


@dataclass
class Heard:
    heard: str  # words, silent, failed
    heard_class: str | None = None
    source: str = "none"  # captions, whisper, none
    language: str | None = None
    segments: list[dict] = field(default_factory=list)  # {start, end, text}
    words: list[dict] = field(default_factory=list)  # {start, end, word}

    @property
    def text(self) -> str:
        return " ".join(segment["text"].strip() for segment in self.segments if segment["text"].strip())


def has_audio_stream(path: Path, timeout: float = 30) -> bool:
    ffprobe = tools.need("ffprobe")
    ran = tools.run(
        [ffprobe, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", path],
        timeout=timeout,
    )
    return ran.returncode == 0 and bool(ran.stdout.strip())


def decode_samples(path: Path, timeout: float = 600) -> array.array:
    """Decode audio with ffmpeg into 16 kHz mono float32 (the lesson from inspirationhouse)."""
    ffmpeg = tools.need("ffmpeg")
    raw = tools.run_bytes(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", path, "-vn", "-ac", "1",
         "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"],
        timeout=timeout,
    )
    samples = array.array("f")
    samples.frombytes(raw[: len(raw) - len(raw) % 4])
    return samples


def transcribe(path: Path, *, model_size: str | None = None, timeout: float = 1800) -> Heard:
    if not has_audio_stream(path):
        return Heard("silent", "no_audio_stream")
    try:
        from faster_whisper import WhisperModel  # type: ignore
        import numpy  # type: ignore
    except Exception:  # noqa: BLE001 - any import failure means the measure is unavailable
        return Heard("failed", "no_whisper")
    try:
        samples = decode_samples(path, timeout=timeout)
    except Exception:  # noqa: BLE001
        return Heard("failed", "decode_error")
    if not samples:
        return Heard("silent", "empty_audio")
    audio = numpy.frombuffer(samples.tobytes(), dtype=numpy.float32)
    if float(numpy.abs(audio).max()) < 1e-4:
        return Heard("silent", "digital_silence")
    size = model_size or os.environ.get("CONTENT_WATCH_WHISPER", "small")
    try:
        model = WhisperModel(size, device="cpu", compute_type="int8")
        pieces, info = model.transcribe(audio, word_timestamps=True, vad_filter=True, beam_size=5)
        segments, words = [], []
        for piece in pieces:
            segments.append({"start": round(piece.start, 2), "end": round(piece.end, 2), "text": piece.text.strip()})
            for word in piece.words or []:
                words.append({"start": round(word.start, 2), "end": round(word.end, 2), "word": word.word.strip()})
    except Exception:  # noqa: BLE001
        return Heard("failed", "whisper_error")
    if not any(segment["text"] for segment in segments):
        return Heard("silent", "no_speech", source="whisper", language=getattr(info, "language", None))
    return Heard("words", None, "whisper", getattr(info, "language", None), segments, words)


_TIME = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{1,3})")


def _seconds(stamp: str) -> float:
    match = _TIME.search(stamp)
    if not match:
        raise ValueError(stamp)
    hours, minutes, seconds, fraction = match.groups()
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds) + int(fraction.ljust(3, "0")) / 1000


def parse_captions(path: Path) -> Heard:
    """Read a WebVTT or SRT subtitle file a platform supplied."""
    text = path.read_text(encoding="utf-8", errors="replace")
    segments: list[dict] = []
    for block in re.split(r"\r?\n\r?\n", text):
        lines = [line for line in block.splitlines() if line.strip()]
        timing = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if timing is None:
            continue
        start_text, _, end_text = lines[timing].partition("-->")
        try:
            start, end = _seconds(start_text), _seconds(end_text.split()[0] if end_text.split() else end_text)
        except ValueError:
            continue
        body = " ".join(lines[timing + 1:])
        body = html.unescape(re.sub(r"<[^>]+>", "", body)).strip()
        if not body:
            continue
        # Auto captions repeat the previous line as the next cue starts; keep only what is new.
        if segments and body.startswith(segments[-1]["text"]):
            body = body[len(segments[-1]["text"]):].strip()
            if not body:
                segments[-1]["end"] = round(end, 2)
                continue
        if segments and segments[-1]["text"] == body:
            segments[-1]["end"] = round(end, 2)
            continue
        segments.append({"start": round(start, 2), "end": round(end, 2), "text": body})
    if not segments:
        return Heard("silent", "empty_captions", source="captions")
    return Heard("words", None, "captions", None, segments, [])


def loudness(path: Path, timeout: float = 600) -> dict:
    ffmpeg = tools.need("ffmpeg")
    ran = tools.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
        timeout=timeout,
    )
    summary = ran.stderr[ran.stderr.rfind("Summary:"):] if "Summary:" in ran.stderr else ""
    integrated = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", summary)
    lra = re.search(r"LRA:\s+(-?[\d.]+) LU", summary)
    peak = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)

    def number(match):
        if not match or match.group(1) == "-inf":
            return None
        return round(float(match.group(1)), 1)

    return {"integrated_lufs": number(integrated), "range_lu": number(lra), "true_peak_dbfs": number(peak)}


def silences(path: Path, *, noise_db: int = -35, minimum: float = 0.5, timeout: float = 600) -> list[dict]:
    ffmpeg = tools.need("ffmpeg")
    ran = tools.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-i", path, "-vn", "-af",
         f"silencedetect=noise={noise_db}dB:d={minimum}", "-f", "null", "-"],
        timeout=timeout,
    )
    spans, start = [], None
    for line in ran.stderr.splitlines():
        began = re.search(r"silence_start: (-?[\d.]+)", line)
        ended = re.search(r"silence_end: (-?[\d.]+)", line)
        if began:
            start = max(0.0, float(began.group(1)))
        elif ended and start is not None:
            spans.append({"start": round(start, 2), "end": round(float(ended.group(1)), 2)})
            start = None
    return spans


_CONTAINER = {"aac": ".m4a", "alac": ".m4a", "opus": ".opus", "mp3": ".mp3", "vorbis": ".ogg", "flac": ".flac"}


def _probe_audio(path: Path, timeout: float = 30) -> tuple[str | None, float | None]:
    """The first audio stream's codec and duration in seconds."""
    ffprobe = tools.need("ffprobe")
    ran = tools.run(
        [ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name,duration:format=duration",
         "-of", "json", path],
        timeout=timeout,
    )
    if ran.returncode != 0:
        return None, None
    data = json.loads(ran.stdout or "{}")
    stream = (data.get("streams") or [{}])[0]
    duration = stream.get("duration") or (data.get("format") or {}).get("duration")
    try:
        seconds = float(duration) if duration not in (None, "N/A") else None
    except ValueError:
        seconds = None
    return stream.get("codec_name"), seconds


def extract(path: Path, out_dir: Path, *, fmt: str = "copy", speech: bool = False, timeout: float = 600) -> Path:
    """Write a video's audio track to its own file with ffmpeg alone: no model, no tokens.

    copy keeps the original audio bit for bit and is the fastest; wav and mp3 re-encode. speech makes the
    wav 16 kHz mono, the shape Whisper reads. An existing output is never overwritten and the source is never touched.
    """
    if fmt not in ("copy", "wav", "mp3"):
        raise ValueError(f"unknown format {fmt}")
    if not has_audio_stream(path):
        raise ValueError(f"{path} has no audio stream")
    codec, source_seconds = _probe_audio(path)
    if fmt == "copy":
        suffix, codec_args = _CONTAINER.get(codec or "", ".mka"), ["-c:a", "copy"]
    elif fmt == "wav":
        suffix, codec_args = ".wav", ["-c:a", "pcm_s16le"] + (["-ar", str(SAMPLE_RATE), "-ac", "1"] if speech else [])
    else:
        suffix, codec_args = ".mp3", ["-c:a", "libmp3lame", "-q:a", "2"]
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"{path.stem}{suffix}"
    if output.exists():
        raise FileExistsError(f"{output} already exists")
    ffmpeg = tools.need("ffmpeg")
    ran = tools.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-i", path, "-vn", "-sn", "-dn",
         "-map", "0:a:0", *codec_args, output],
        timeout=timeout,
    )
    if ran.returncode != 0 or not output.exists() or output.stat().st_size == 0:
        output.unlink(missing_ok=True)
        reason = "timed out" if ran.timed_out else " ".join(ran.stderr.strip().splitlines()[-3:])
        raise RuntimeError(f"ffmpeg could not extract the audio: {reason}")
    _, out_seconds = _probe_audio(output)
    if source_seconds and (out_seconds is None or abs(out_seconds - source_seconds) > 0.5):
        output.unlink(missing_ok=True)
        raise RuntimeError(f"extracted audio lasts {out_seconds}s, the source's {source_seconds}s")
    return output
