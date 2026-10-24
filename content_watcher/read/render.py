"""read.md: the reading as plain text, written for a model or a session to read instead of frames."""

from __future__ import annotations

MAX_CHARS = 40_000


def _clock(seconds: float | None) -> str:
    if seconds is None:
        return "?"
    seconds = max(0.0, float(seconds))
    return f"{int(seconds // 60)}:{seconds % 60:04.1f}"


def _quote(text: str | None, limit: int = 600) -> str:
    text = (text or "").strip().replace("\n", " / ")
    return (text[: limit - 1] + "…") if len(text) > limit else text


def _header(data: dict) -> list[str]:
    post = data.get("post") or {}
    shape = data.get("shape", "?")
    platform = post.get("platform") or "own file"
    who = f" by {post['author']}" if post.get("author") else ""
    when = f" ({post['posted_at'][:10]})" if post.get("posted_at") else ""
    lines = [f"# Reading: {platform} {shape}{who}{when}", ""]
    if post.get("url"):
        lines.append(f"Link: {post['url']}")
    lines.append(f"File: {data['file']['name']} (sha256 {data['sha256'][:16]}…)")
    position = data.get("position")
    if position and position.get("of", 1) > 1:
        lines.append(f"Slide {position['index']} of {position['of']}")
    if post.get("caption"):
        lines += ["", "Caption: " + _quote(post["caption"], 3000)]
    return lines


def _video(data: dict) -> list[str]:
    video = data["video"]
    shots = data["shots"]
    pace = data["pace"]
    hook = data["hook"]
    faces = data.get("faces") or {}
    out = [
        "",
        f"Video: {video['duration_s']} s, {video['width']}x{video['height']} ({video['aspect']}), "
        f"{'with sound' if video['has_audio'] else 'no sound'}.",
        f"Heard: {data['heard']}" + (f" ({data['heard_class']})" if data.get("heard_class") else "")
        + (f", from {data['words']['source']}" if data.get("words", {}).get("source") not in (None, "none") else ""),
        "",
        f"## Hook (first {hook['window_s']:.0f} seconds)",
        f"- Words: \"{_quote(hook['words'], 400)}\"" if hook["words"] else "- Words: none",
        f"- Screen text: {' | '.join(_quote(t, 120) for t in hook['screen_text'])}" if hook["screen_text"] else "- Screen text: none",
        f"- Cuts: {hook['cuts']}",
    ]
    if hook.get("face_on_screen") is not None:
        out.append(f"- Face on screen: {'yes' if hook['face_on_screen'] else 'no'}")
    if hook.get("move"):
        out.append(f"- Camera: {hook['move'].replace('_', ' ')}")
    out += [
        "",
        "## Pace and sound",
        f"- {shots['count']} shots, {shots['cuts_per_min']} cuts a minute, median shot {shots['length_s']['median']} s "
        f"(shortest {shots['length_s']['min']} s, longest {shots['length_s']['max']} s).",
        f"- {pace['words_per_min']} words a minute; speech covers {int(pace['speech_share'] * 100)}% of the time; "
        f"{pace['pauses_over_0_6s']} pauses over 0.6 s, longest {pace['longest_pause_s']} s.",
    ]
    if pace.get("first_word_s") is not None:
        out.append(f"- First word at {pace['first_word_s']} s.")
    sound = data.get("audio") or {}
    if sound.get("integrated_lufs") is not None:
        out.append(f"- Loudness {sound['integrated_lufs']} LUFS, range {sound.get('range_lu')} LU, peak {sound.get('true_peak_dbfs')} dBFS.")
    if faces.get("available"):
        line = f"- Face on screen {int(faces['share_on_face'] * 100)}% of the time"
        if faces.get("framing"):
            line += f", mostly {faces['framing']} (face {int(faces['face_height_median'] * 100)}% of frame height, eyes at {int(faces['eye_line_median'] * 100)}% from the top)"
        out.append(line + ".")
    if data.get("camera_moves"):
        moves = ", ".join(f"{m['kind'].replace('_', ' ')} at {_clock(m['start'])}" for m in data["camera_moves"][:20])
        out.append(f"- Camera moves: {moves}.")
    out += ["", "## Shots"]
    for number, shot in enumerate(shots["list"], start=1):
        bits = [f"{_clock(shot['start'])}–{_clock(shot['end'])}"]
        if "face_share" in shot:
            bits.append(f"face {int(shot['face_share'] * 100)}%")
        if shot.get("move"):
            bits.append(shot["move"].replace("_", " "))
        if shot.get("screen_text"):
            bits.append("text: \"" + _quote(" | ".join(shot["screen_text"]), 200) + "\"")
        out.append(f"{number}. " + ", ".join(bits))
        if number >= 150:
            out.append(f"… {shots['count'] - number} more shots in read.json")
            break
    if data.get("screen_text"):
        out += ["", "## Words on screen"]
        out += [f"[{_clock(item['t'])}] {_quote(item['text'], 300)}" for item in data["screen_text"]]
    return out


def _words(data: dict) -> list[str]:
    segments = (data.get("words") or {}).get("segments") or []
    if not segments:
        return []
    out = ["", f"## Words ({data['words']['source']}{', ' + data['words']['language'] if data['words'].get('language') else ''})"]
    out += [f"[{_clock(seg['start'])}] {seg['text']}" for seg in segments]
    return out


def _slide(data: dict) -> list[str]:
    slide = data["slide"]
    out = [
        "",
        f"Image: {slide['width']}x{slide['height']} ({slide['aspect']}), layout: {', '.join(slide['layout'])}.",
    ]
    if slide.get("word_count") is not None:
        out.append(f"Text on it: {slide['word_count']} words, {int((slide['text_area_share'] or 0) * 100)}% of the area.")
    if slide.get("colours"):
        out.append("Colours: " + ", ".join(f"{c['hex']} {int(c['share'] * 100)}%" for c in slide["colours"]))
    if slide.get("text"):
        out += ["", "Text:", slide["text"]]
    return out


def _post_slides(data: dict) -> list[str]:
    slides = data.get("post_slides")
    if not slides:
        return []
    out = ["", f"## The whole post, {len(slides)} slides in order"]
    for slide in slides:
        layout = f" ({', '.join(slide['layout'])})" if slide.get("layout") else ""
        out.append(f"### Slide {slide['index']}: {slide['kind']}{layout}")
        if slide.get("text"):
            out.append(slide["text"])
        if slide.get("words_text"):
            out.append(f"Said: \"{_quote(slide['words_text'], 1500)}\"")
    if data.get("post_audio"):
        out.append("")
        out.append(f"Post sound: heard {data['heard']}" + (f": \"{_quote(data['words_text'], 2000)}\"" if data["words_text"] else ""))
    return out


def _text(data: dict) -> list[str]:
    text = data["text"]
    return [
        "",
        f"Text post: {text['word_count']} words, {text['paragraphs']} paragraphs, {text['list_lines']} list lines.",
        f"First line: \"{_quote(text['first_line'], 300)}\"",
        "",
        text["body"],
    ]


def render_md(data: dict) -> str:
    lines = _header(data)
    lines += _post_slides(data)
    if "video" in data:
        lines += _video(data)
    if "slide" in data:
        lines += _slide(data)
    if "text" in data:
        lines += _text(data)
    lines += _words(data)
    if data.get("frames"):
        lines += ["", "## Frames kept beside this reading"]
        lines += [f"- {f['role']} at {_clock(f['t'])}: {f['file']}" for f in data["frames"]]
    if data.get("unmeasured"):
        lines += ["", "Not measured on this machine: " + ", ".join(sorted(set(data["unmeasured"]))) + "."]
    text = "\n".join(lines).strip() + "\n"
    if len(text) > MAX_CHARS:
        text = text[: MAX_CHARS - 60].rsplit("\n", 1)[0] + "\n\n[Cut at 40,000 characters; the rest is in read.json.]\n"
    return text
