"""The transcript's language against the screen text's (31 October 2026: an Arabic transcript of an English Short)."""

import unittest
from pathlib import Path
from unittest import mock

from content_watcher.read import audio, language, reader

ARABIC = ("كل الخلايا العصبية الموجودة في دماغك كانت هناك منذ يوم ولادتك، ونحن نعرف هذا بسبب القنابل النووية. "
          "اسمحوا لي أن أشرح.")
ENGLISH = ("All the neurons in your brain have been there since the day you were born, and we know this because of "
           "nuclear bombs. Let me explain.")
SCREEN = [{"t": 0.5, "text": "All the neurons"}, {"t": 3.5, "text": "since the day you were born,"},
          {"t": 6.5, "text": "because of nuclear bombs."}, {"t": 18.5, "text": "leaving you with carbon 14,"},
          {"t": 21.5, "text": "fat unwieldy version of carbon"}, {"t": 88.4, "text": "that you have recently eaten"}]


def heard(text: str, source: str) -> audio.Heard:
    return audio.Heard("words", None, source, None, [{"start": 0.0, "end": 3.0, "text": text}], [])


class DetectTests(unittest.TestCase):
    def test_scripts_and_latin_languages(self):
        self.assertEqual(language.detect(ARABIC), "ar")
        self.assertEqual(language.detect(ENGLISH), "en")
        self.assertEqual(language.detect("Todas las neuronas de tu cerebro están ahí desde el día que naciste, por las bombas"), "es")
        self.assertEqual(language.detect("Все нейроны в вашем мозге были там с самого рождения"), "cyrillic")
        self.assertIsNone(language.detect("90 10 150"))
        self.assertIsNone(language.detect(""))

    def test_compare(self):
        screen = "\n".join(item["text"] for item in SCREEN)
        self.assertEqual(language.compare(ARABIC, screen), {"words": "ar", "screen": "en", "match": False})
        self.assertTrue(language.compare(ENGLISH, screen)["match"])
        self.assertIsNone(language.compare(ENGLISH, "rotor cloud")["match"])  # too little on screen to say


class ReaderCheckTests(unittest.TestCase):
    def test_dub_captions_are_replaced_by_the_audio(self):
        data: dict = {}
        with mock.patch.object(audio, "transcribe", return_value=heard(ENGLISH, "whisper")) as transcribe:
            got, captions = reader._check_language(data, heard(ARABIC, "captions"), Path("x.ar-orig.vtt"), Path("x.mp4"),
                                                  SCREEN, True, None)
        transcribe.assert_called_once()
        self.assertEqual((got.source, captions), ("whisper", None))
        self.assertTrue(data["words_text"].startswith("All the neurons"))
        self.assertEqual(data["words"]["language_check"]["replaced"], "captions")

    def test_a_mismatch_that_stays_is_withheld_and_named(self):
        data: dict = {}
        with mock.patch.object(audio, "transcribe", return_value=heard(ARABIC, "whisper")):
            got, _ = reader._check_language(data, heard(ARABIC, "captions"), None, Path("x.mp4"), SCREEN, True, None)
        self.assertEqual((data["heard"], data["heard_class"], data["words_text"]),
                         ("failed", "transcript_language_mismatch", ""))
        check = data["words"]["language_check"]
        self.assertEqual(check["status"], "transcript_language_mismatch")
        self.assertTrue(check["withheld"]["text"].startswith("كل"))
        self.assertEqual(got.heard, "failed")

    def test_matching_words_are_left_alone(self):
        data: dict = {}
        with mock.patch.object(audio, "transcribe") as transcribe:
            got, _ = reader._check_language(data, heard(ENGLISH, "captions"), None, Path("x.mp4"), SCREEN, True, None)
        transcribe.assert_not_called()
        self.assertEqual((data["heard"], data["words"]["language_check"]["match"]), ("words", True))


if __name__ == "__main__":
    unittest.main()
