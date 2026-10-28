"""Tags on each still: plain rules over what was measured, not a picture model.

The UX signals come from a small lexicon matched against the words spoken around a still. It is versioned so a
reading says which rules tagged it.
"""

from __future__ import annotations

import re

LEXICON_VERSION = "ux-1"

LEXICON: dict[str, tuple[str, ...]] = {
    "friction": (
        "can't find", "cannot find", "couldn't find", "where is", "where's", "hard to", "annoying", "frustrat",
        "too slow", "so slow", "is slow", "broken", "doesn't work", "does not work", "not working", "error",
        "stuck", "bug", "takes too long", "too many", "clunky", "laggy", "fiddly",
    ),
    "confusion": (
        "confus", "not sure", "don't know what", "don't understand", "what does", "what is this", "unclear",
        "why is", "i'm lost", "no idea", "makes no sense", "doesn't make sense",
    ),
    "expectation": (
        "i expected", "i'd expect", "i would expect", "should be", "should have", "i thought", "i assumed",
        "supposed to", "would be nice", "i want", "i wish", "i'd like", "i would like",
    ),
    "delight": (
        "love", "nice", "great", "easy", "perfect", "beautiful", "smooth", "awesome", "really good", "so fast",
        "brilliant", "intuitive",
    ),
}

_PATTERNS = {
    signal: re.compile(r"\b(" + "|".join(re.escape(term) for term in terms) + r")", re.IGNORECASE)
    for signal, terms in LEXICON.items()
}


def normalise(text: str) -> str:
    return (text or "").replace("’", "'").replace("‘", "'").lower()


def ux_signals(text: str) -> list[dict]:
    """Every lexicon hit in the text, in order: `signal`, `term`."""
    text = normalise(text)
    hits = []
    for signal, pattern in _PATTERNS.items():
        for match in pattern.finditer(text):
            hits.append((match.start(), signal, match.group(1)))
    return [{"signal": signal, "term": term} for _pos, signal, term in sorted(hits)]


def first_hit_time(words: list[dict]) -> float | None:
    """When the first lexicon term starts, from word timings: where a narrator points at a problem."""
    for index, word in enumerate(words):
        window = " ".join(w["word"] for w in words[index:index + 4])
        if any(_PATTERNS[s].match(normalise(window)) for s in _PATTERNS):
            return word["start"]
    return None


def framing(height_share: float | None) -> str | None:
    if height_share is None:
        return None
    return "close" if height_share >= 0.35 else "medium" if height_share >= 0.18 else "wide"


def tags_for(entry: dict, profile: str) -> list[str]:
    tags = [f"trigger:{trigger}" for trigger in entry["triggers"]]
    if entry["t"] < 3.0:
        tags.append("hook")
    for label in entry.get("layout") or []:
        tags.append(f"layout:{label}")
    face = entry.get("face")
    if face is not None:
        tags.append("face:yes" if face.get("on") else "face:no")
        if face.get("framing"):
            tags.append(f"framing:{face['framing']}")
    score = entry.get("change_score")
    if score is not None and "screen_change" in entry["triggers"]:
        tags.append("change:large" if score >= 0.15 else "change:small")
    if entry.get("motion"):
        tags.append(f"motion:{entry['motion']}")
    tags.append("speech:yes" if entry.get("said") else "speech:none")
    for signal in sorted({hit["signal"] for hit in entry.get("ux_signals") or []}):
        tags.append(f"ux_signal:{signal}")
    return tags


def post_tags(post: dict | None) -> list[str]:
    if not post:
        return []
    tags = [f"platform:{post['platform']}"] if post.get("platform") else []
    if post.get("author"):
        tags.append(f"author:{post['author']}")
    tags += [f"hashtag:{tag}" for tag in dict.fromkeys(t[1:].lower() for t in re.findall(r"#\w+", post.get("caption") or ""))]
    return tags
