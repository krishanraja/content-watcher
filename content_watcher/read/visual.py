"""What is seen: shots, camera moves, words on screen, faces and colours."""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .. import tools

SCENE_THRESHOLD = 0.3
FRAME_WIDTH = 320


def _numpy():
    try:
        import numpy  # type: ignore
    except Exception:  # noqa: BLE001
        return None
    return numpy


def _cv2():
    try:
        import cv2  # type: ignore
    except Exception:  # noqa: BLE001
        return None
    return cv2


def cuts(path: Path, *, threshold: float = SCENE_THRESHOLD, timeout: float = 900) -> list[float]:
    """Times where the picture changes shot, from ffmpeg's scene score."""
    ffmpeg = tools.need("ffmpeg")
    ran = tools.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-i", path, "-an", "-vf",
         f"scale=320:-2,select='gt(scene\\,{threshold})',showinfo", "-f", "null", "-"],
        timeout=timeout,
    )
    times = []
    for line in ran.stderr.splitlines():
        if "showinfo" in line and "pts_time:" in line:
            match = re.search(r"pts_time:\s*([\d.]+)", line)
            if match:
                times.append(round(float(match.group(1)), 2))
    deduped: list[float] = []
    for time in times:
        if not deduped or time - deduped[-1] > 0.2:
            deduped.append(time)
    return deduped


@dataclass
class Frames:
    fps: float
    width: int
    height: int
    data: object  # numpy array, frames x height x width, uint8 grey

    def time(self, index: int) -> float:
        return index / self.fps


def sample_frames(path: Path, duration: float, width: int, height: int, timeout: float = 900) -> Frames | None:
    numpy = _numpy()
    if numpy is None or width <= 0 or height <= 0:
        return None
    fps = 4.0 if duration <= 300 else max(0.5, 1200 / max(duration, 1))
    out_w = FRAME_WIDTH
    out_h = max(2, int(round(height * out_w / width / 2)) * 2)
    ffmpeg = tools.need("ffmpeg")
    raw = tools.run_bytes(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", path, "-an", "-vf",
         f"fps={fps},scale={out_w}:{out_h},format=gray", "-f", "rawvideo", "-"],
        timeout=timeout,
    )
    size = out_w * out_h
    count = len(raw) // size
    if count == 0:
        return None
    data = numpy.frombuffer(raw[: count * size], dtype=numpy.uint8).reshape(count, out_h, out_w)
    return Frames(fps, out_w, out_h, data)


def _pair_motion(numpy, a, b):
    """Best zoom and shift taking frame a to frame b, on small grey frames."""
    h, w = a.shape
    my, mx = int(h * 0.18), int(w * 0.18)
    target = b[my:h - my, mx:w - mx].astype(numpy.float32)
    ys, xs = numpy.mgrid[0:h, 0:w]
    cy, cx = (h - 1) / 2, (w - 1) / 2
    best = (float("inf"), 1.0, 0, 0)
    identity_error = None
    for scale in numpy.linspace(0.94, 1.06, 13):
        sy = numpy.clip(numpy.rint(cy + (ys - cy) / scale), 0, h - 1).astype(int)
        sx = numpy.clip(numpy.rint(cx + (xs - cx) / scale), 0, w - 1).astype(int)
        warped = a[sy, sx].astype(numpy.float32)
        for dy in range(-4, 5):
            for dx in range(-8, 9):
                window = warped[my - dy:h - my - dy, mx - dx:w - mx - dx]
                error = float(numpy.abs(window - target).mean())
                if abs(scale - 1.0) < 1e-6 and dx == 0 and dy == 0:
                    identity_error = error
                if error < best[0]:
                    best = (error, float(scale), dx, dy)
    return best, identity_error


def camera_moves(frames: Frames | None, shot_spans: list[tuple[float, float]]) -> list[dict]:
    """Push-ins, pull-outs and pans per shot."""
    numpy = _numpy()
    if frames is None or numpy is None:
        return []
    small = frames.data[:, ::2, ::2]
    width = small.shape[2]
    moves = []
    for start, end in shot_spans:
        first = int(numpy.ceil(start * frames.fps))
        last = min(int(numpy.floor(end * frames.fps)), len(small) - 1)
        zoom, shift_x, shift_y, pairs = 1.0, 0.0, 0.0, 0
        for index in range(first, last):
            a, b = small[index], small[index + 1]
            if float(a.std()) < 4.0:
                continue
            (error, scale, dx, dy), identity = _pair_motion(numpy, a, b)
            if identity is not None and identity - error < 0.5:
                continue  # no real improvement over standing still
            zoom *= scale
            shift_x += dx
            shift_y += dy
            pairs += 1
        if not pairs:
            continue
        kind = None
        if zoom >= 1.06:
            kind = "push_in"
        elif zoom <= 1 / 1.06:
            kind = "pull_out"
        elif abs(shift_x) / width >= 0.08:
            kind = "pan_left" if shift_x > 0 else "pan_right"
        elif abs(shift_y) / small.shape[1] >= 0.08:
            kind = "tilt_up" if shift_y > 0 else "tilt_down"
        if kind:
            moves.append({
                "start": round(start, 2), "end": round(end, 2), "kind": kind,
                "zoom": round(zoom, 3), "shift_x_share": round(shift_x / width, 3),
            })
    return moves


def faces(frames: Frames | None) -> dict:
    cv2 = _cv2()
    numpy = _numpy()
    if frames is None or cv2 is None or numpy is None or not hasattr(cv2, "CascadeClassifier"):
        return {"available": False}
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(str(cascade_path))
    if detector.empty():
        return {"available": False}
    step = max(1, int(round(frames.fps / 2)))  # about two a second
    samples = []
    for index in range(0, len(frames.data), step):
        found = detector.detectMultiScale(frames.data[index], scaleFactor=1.1, minNeighbors=5,
                                          minSize=(int(frames.height * 0.08),) * 2)
        if len(found):
            x, y, w, h = max(found, key=lambda box: box[2] * box[3])
            samples.append({
                "t": round(frames.time(index), 2),
                "height_share": round(h / frames.height, 3),
                "centre_x": round((x + w / 2) / frames.width, 3),
                "eye_line": round((y + 0.4 * h) / frames.height, 3),
            })
        else:
            samples.append({"t": round(frames.time(index), 2)})
    with_face = [sample for sample in samples if "height_share" in sample]
    total = len(samples) or 1
    result = {
        "available": True,
        "method": "opencv_haar_frontal",
        "frames_checked": len(samples),
        "share_on_face": round(len(with_face) / total, 3),
        "samples": samples,
    }
    if with_face:
        heights = sorted(sample["height_share"] for sample in with_face)
        eyes = sorted(sample["eye_line"] for sample in with_face)
        result["face_height_median"] = heights[len(heights) // 2]
        result["eye_line_median"] = eyes[len(eyes) // 2]
        result["framing"] = (
            "close" if result["face_height_median"] >= 0.35
            else "medium" if result["face_height_median"] >= 0.18 else "wide"
        )
    return result


def grab_frame(path: Path, time: float, target: Path, *, width: int = 1280, timeout: float = 60) -> Path | None:
    ffmpeg = tools.need("ffmpeg")
    ran = tools.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(0.0, time):.2f}",
         "-i", path, "-frames:v", "1", "-vf", f"scale='min({width},iw)':-2", target],
        timeout=timeout,
    )
    return target if ran.returncode == 0 and target.is_file() else None


def ocr_image(image: Path, timeout: float = 60) -> dict | None:
    """Words on an image with tesseract. None when tesseract is not installed."""
    tesseract = tools.which("tesseract")
    if not tesseract:
        return None
    ran = tools.run([tesseract, image, "stdout", "--psm", "11", "tsv"], timeout=timeout)
    if ran.returncode != 0:
        return {"text": "", "lines": [], "text_area_share": 0.0, "biggest_line_share": 0.0}
    rows = [line.split("\t") for line in ran.stdout.splitlines()[1:]]
    page_w = page_h = 0
    lines: dict[tuple, list] = {}
    area = 0
    for row in rows:
        if len(row) < 12:
            continue
        level, block, par, line, _word, left, top, width, height, conf, text = (
            row[0], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11]
        )
        if level == "1":
            page_w, page_h = int(width), int(height)
            continue
        if level != "5":
            continue
        word = text.strip()
        try:
            confidence = float(conf)
        except ValueError:
            continue
        if confidence < 50 or not re.search(r"[A-Za-z0-9]", word):
            continue
        lines.setdefault((block, par, line), []).append((int(left), word, int(height)))
        area += int(width) * int(height)
    ordered = []
    for key in sorted(lines, key=lambda k: (int(k[0]), int(k[1]), int(k[2]))):
        words = sorted(lines[key])
        text = " ".join(word for _, word, _ in words)
        if len(re.sub(r"[^A-Za-z0-9]", "", text)) >= 2:
            ordered.append({"text": text, "height": max(h for _, _, h in words)})
    page_area = (page_w * page_h) or 1
    return {
        "text": "\n".join(line["text"] for line in ordered),
        "lines": [line["text"] for line in ordered],
        "text_area_share": round(area / page_area, 3),
        "biggest_line_share": round(max((line["height"] for line in ordered), default=0) / (page_h or 1), 3),
    }


def screen_text(path: Path, shot_spans: list[tuple[float, float]], workdir: Path, *, limit: int = 60) -> dict:
    """Words on screen per shot: the middle of each shot, and every 3 seconds in long ones."""
    if not tools.which("tesseract"):
        return {"available": False, "items": []}
    times: list[tuple[int, float]] = []
    for index, (start, end) in enumerate(shot_spans):
        length = end - start
        picks = [start + length / 2] if length < 3 else [start + 0.5 + step * 3 for step in range(int((length - 0.5) // 3) + 1)]
        times.extend((index, min(pick, end - 0.05)) for pick in picks)
    if len(times) > limit:
        stride = len(times) / limit
        times = [times[int(i * stride)] for i in range(limit)]
    items, previous = [], None
    best = (0.0, None)
    for shot_index, time in times:
        frame = grab_frame(path, time, workdir / f"ocr_{time:08.2f}.png")
        if frame is None:
            continue
        found = ocr_image(frame)
        if not found or not found["text"]:
            continue
        if found["text_area_share"] > best[0]:
            best = (found["text_area_share"], time)
        if found["text"] == previous:
            continue
        previous = found["text"]
        items.append({"t": round(time, 2), "shot": shot_index, "text": found["text"],
                      "text_area_share": found["text_area_share"]})
    return {"available": True, "method": "tesseract", "items": items, "most_text_time": best[1]}


def colours(path: Path, *, count: int = 5, timeout: float = 60) -> list[dict]:
    """The main colours of an image, as hex with their share."""
    numpy = _numpy()
    ffmpeg = tools.which("ffmpeg")
    if numpy is None or not ffmpeg:
        return []
    try:
        raw = tools.run_bytes(
            [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", path, "-frames:v", "1",
             "-vf", "scale=64:64,format=rgb24", "-f", "rawvideo", "-"],
            timeout=timeout,
        )
    except Exception:  # noqa: BLE001
        return []
    pixels = numpy.frombuffer(raw[: 64 * 64 * 3], dtype=numpy.uint8).reshape(-1, 3)
    buckets = (pixels // 51).astype(int)  # six levels a channel
    keys = buckets[:, 0] * 36 + buckets[:, 1] * 6 + buckets[:, 2]
    values, counts = numpy.unique(keys, return_counts=True)
    order = numpy.argsort(-counts)[:count]
    result = []
    for position in order:
        members = pixels[keys == values[position]]
        mean = members.mean(axis=0).astype(int)
        result.append({"hex": "#{:02x}{:02x}{:02x}".format(*mean), "share": round(counts[position] / len(pixels), 3)})
    return result


def tempdir(prefix: str) -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(prefix=prefix)
