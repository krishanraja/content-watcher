"""A timeline as plain text: one line a still, written for a model or a session to read instead of frames."""

from __future__ import annotations

from ..read.render import _clock, _quote


def timeline_lines(data: dict, heading: str = "##", links: dict[str, str] | None = None) -> list[str]:
    counts = data["counts"]
    out = ["", f"{heading} Timeline: {counts['stills']} stills ({counts['images']} pictures), {data['profile']} profile"]
    out.append("Each line: time, still, why it was taken, what was said around it, words on screen, tags. "
               "Tags are rules over what was measured, not a picture model.")
    words = data.get("words") or {}
    if words.get("agreement") is not None:
        out.append(f"Captions and transcription agree on {int(words['agreement'] * 100)}% of words.")
    if data.get("ux_signals"):
        out.append("UX signals: " + "; ".join(
            f"{_clock(hit['t'])} {hit['signal']} (\"{hit['term']}\", still {hit['index']:02d})" for hit in data["ux_signals"][:40]
        ) + ".")
    if data.get("post_tags"):
        out.append("Post: " + " ".join(data["post_tags"][:30]))
    for entry in data["entries"]:
        bits = [f"[{_clock(entry['t'])}] still {entry['index']:02d}"
                + (f" (same picture as {entry['same_as']:02d})" if entry.get("same_as") else ""),
                ", ".join(entry["triggers"])]
        if entry.get("said"):
            bits.append(f"said: \"{_quote(entry['said'], 240)}\"")
        if entry.get("screen_text"):
            bits.append(f"screen: \"{_quote(entry['screen_text'], 160)}\"")
        if links and links.get(entry.get("file") or ""):
            bits.append(f"still: {links[entry['file']]}")
        rest = [tag for tag in entry["tags"] if not tag.startswith("trigger:")]
        if rest:
            bits.append("tags: " + " ".join(rest))
        out.append(" | ".join(bits))
    if data.get("unmeasured"):
        out.append("Not measured for this timeline: " + ", ".join(data["unmeasured"]) + ".")
    return out


def render_timeline_md(data: dict, links: dict[str, str] | None = None) -> str:
    """The timeline as a file; with `links` (a still's file to its Drive link) each line links its picture."""
    source = data.get("source") or {}
    lines = [f"# Timeline: {source.get('file', 'video')}", ""]
    lines.append(f"{data['duration_s']} s, profile {data['profile']} ({data.get('profile_reason') or 'asked for'}).")
    words = data.get("words") or {}
    heard = data.get("heard")
    lines.append(f"Words from {words.get('source', 'none')}" + (f" ({heard['heard_class']})" if heard else "") + ".")
    lines.append("Each line links the still of that moment in Drive." if links else
                 "Stills are in the stills folder beside this file; nothing here was uploaded.")
    lines += timeline_lines(data, links=links)
    if data.get("sentences"):
        lines += ["", "## Everything that was said"]
        lines += [f"[{_clock(s['start'])}] {s['text']}" for s in data["sentences"]]
    return "\n".join(lines).strip() + "\n"
