"""Which language a piece of text is in, cheaply: the script its letters are written in, and for Latin script the
commonest small words. No model and no download. It only has to tell a transcript that does not match the words on
screen (31 October 2026: an Arabic transcript of an English Short, from YouTube's auto-dub), so it answers None
whenever it is not sure rather than guess."""

from __future__ import annotations

import re
import unicodedata

# Script by Unicode letter name prefix: the language a script almost always means, or the script itself.
_SCRIPTS = (
    ("ARABIC", "ar"), ("HEBREW", "he"), ("CYRILLIC", "cyrillic"), ("GREEK", "el"), ("DEVANAGARI", "hi"),
    ("BENGALI", "bn"), ("TAMIL", "ta"), ("THAI", "th"), ("HANGUL", "ko"), ("HIRAGANA", "ja"), ("KATAKANA", "ja"),
    ("CJK", "zh"), ("LATIN", "latin"),
)

_STOPWORDS = {
    "en": "the and you that this is of to in it for was with what are on be your have not they we but",
    "es": "el la que de los las y en un una por con para es del se no lo como pero más",
    "fr": "le la les et des est que une un pour dans pas qui sur avec du ce vous il nous",
    "de": "der die das und ist nicht ein eine zu den mit sie ich es auf für von dem wir",
    "pt": "o a os as que de não um uma para com é do da em se no na você",
    "it": "il la che di e non un una per con sono del della gli le è questo ma",
    "nl": "de het een en van is dat niet je ik op te zijn met voor maar",
    "id": "yang dan ini itu di dengan untuk tidak ada saya kamu dari akan",
    "tr": "ve bir bu da de için ile çok ne ama gibi daha var",
}
_WORDS = {lang: set(words.split()) for lang, words in _STOPWORDS.items()}
_TOKEN = re.compile(r"[^\W\d_]+", re.UNICODE)

MIN_LETTERS = 12  # fewer letters than this is not enough to say anything
MIN_HITS = 3  # small words a Latin-script language needs before it is named


def script_of(text: str) -> str | None:
    counts: dict[str, int] = {}
    for char in text:
        if not char.isalpha():
            continue
        name = unicodedata.name(char, "")
        for prefix, script in _SCRIPTS:
            if name.startswith(prefix):
                counts[script] = counts.get(script, 0) + 1
                break
    total = sum(counts.values())
    if total < MIN_LETTERS:
        return None
    script, count = max(counts.items(), key=lambda item: item[1])
    if count / total < 0.6:
        return None
    if script == "zh" and counts.get("ja"):
        return "ja"
    return script


def detect(text: str | None) -> str | None:
    """An ISO 639-1 code, a script name for a script shared by many languages (`latin`, `cyrillic`), or None."""
    if not text:
        return None
    script = script_of(text)
    if script != "latin":
        return script
    words = [word.lower() for word in _TOKEN.findall(text)]
    scores = sorted(((sum(1 for word in words if word in vocab), lang) for lang, vocab in _WORDS.items()), reverse=True)
    best, runner_up = scores[0], scores[1]
    if best[0] >= MIN_HITS and best[0] >= 1.5 * max(runner_up[0], 1):
        return best[1]
    return "latin"


def _script_family(code: str | None) -> str | None:
    if code in _WORDS or code == "latin":
        return "latin"
    return code


def compare(words_text: str | None, screen_text: str | None) -> dict:
    """The transcript's language against the screen text's. `match` is None when either side cannot be told."""
    heard, shown = detect(words_text), detect(screen_text)
    if heard is None or shown is None:
        match = None
    elif _script_family(heard) != _script_family(shown):
        match = False
    elif "latin" in (heard, shown) and heard != shown:
        match = None  # one side is Latin script in a language this cannot name
    else:
        match = heard == shown
    return {"words": heard, "screen": shown, "match": match}
