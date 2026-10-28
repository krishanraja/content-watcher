"""Timelines: stills at the right moments, honest tags, and no reach beyond the folder they are written to."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from content_watcher import cli, tools
from content_watcher.read import audio, read_path
from content_watcher.read.visual import Frames
from content_watcher.timeline import TimelineBudget, build_standalone, moments, tags
from content_watcher.timeline import captions as timeline_words
from tests.cw_helpers import FFMPEG, ffmpeg, make_video

try:
    import numpy
except Exception:  # noqa: BLE001
    numpy = None


def _words(*items):
    """(start, end, word) triples as transcription word timings."""
    return [{"start": s, "end": e, "word": w} for s, e, w in items]


def _screen_recording(path: Path, *, audio_track: bool = False) -> Path:
    """Three screens, 3 seconds each: a page, the same page with a button added (a small change), a new page."""
    page = "drawtext=text='Settings':fontsize=60:fontcolor=black:x=80:y=60"
    args = [
        "-f", "lavfi", "-i", f"color=c=white:s=1280x720:d=3:r=25,{page}",
        "-f", "lavfi", "-i", f"color=c=white:s=1280x720:d=3:r=25,{page},drawbox=x=900:y=600:w=220:h=70:color=blue:t=fill",
        "-f", "lavfi", "-i", "color=c=0xf0f0ff:s=1280x720:d=3:r=25,drawtext=text='Saved':fontsize=60:fontcolor=green:x=80:y=300",
    ]
    if audio_track:
        args += ["-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000:duration=9"]
    args += ["-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]", "-map", "[v]"]
    if audio_track:
        args += ["-map", "3:a", "-c:a", "aac"]
    args += ["-t", "9", "-c:v", "libx264", "-preset", "ultrafast", str(path)]
    ffmpeg(*args)
    return path


class SentenceAndAnchorTests(unittest.TestCase):
    def test_one_long_segment_splits_into_sentences_on_word_timings(self):
        heard = audio.Heard("words", None, "whisper", "en",
                            [{"start": 0.0, "end": 5.0, "text": "This is the page. Where is save? Nice."}],
                            _words((0.0, 0.3, "This"), (0.3, 0.5, "is"), (0.5, 0.7, "the"), (0.7, 1.0, "page."),
                                   (2.0, 2.3, "Where"), (2.3, 2.5, "is"), (2.5, 2.9, "save?"), (4.5, 5.0, "Nice.")))
        found = moments.sentences(heard)
        self.assertEqual([s["text"] for s in found], ["This is the page.", "Where is save?", "Nice."])
        self.assertEqual((found[1]["start"], found[1]["end"]), (2.0, 2.9))

    def test_a_narrated_problem_is_pointed_at_plus_the_reaction_time(self):
        heard = audio.Heard("words", None, "whisper", "en", [],
                            _words((1.0, 1.2, "I"), (1.2, 1.5, "can't"), (1.5, 1.8, "find"), (1.8, 2.2, "it.")))
        anchors = moments.speech_anchors(heard, 10.0, reaction=0.6, point_at_terms=True)
        self.assertEqual([m.t for m in anchors], [1.8])  # "can't find" starts at 1.2, plus 0.6
        plain = moments.speech_anchors(heard, 10.0)
        self.assertEqual([m.t for m in plain], [1.6])  # the middle of the sentence

    def test_choose_merges_close_moments_keeps_triggers_and_bounds_the_count(self):
        found = [moments.Moment(0.5, ["start"]), moments.Moment(1.0, ["speech"]),
                 moments.Moment(4.0, ["speech"]), moments.Moment(4.4, ["screen_change"], change_score=0.2)]
        chosen = moments.choose(found, spacing=1.5, limit=10)
        self.assertEqual([m.t for m in chosen], [0.5, 4.4])
        self.assertEqual(chosen[0].triggers, ["start", "speech"])
        self.assertEqual(chosen[1].triggers, ["screen_change", "speech"])
        many = [moments.Moment(0.5, ["start"])] + [moments.Moment(2.0 * i, ["speech"]) for i in range(1, 30)]
        bounded = moments.choose(many, spacing=1.5, limit=5)
        self.assertEqual(len(bounded), 5)
        self.assertEqual(bounded[0].triggers, ["start"])

    def test_caption_changes_ignore_ocr_scraps(self):
        samples = [{"t": 0.0, "text": "STOP SCROLLING"}, {"t": 0.5, "text": "STOP SCROLLlNG"},
                   {"t": 1.0, "text": "THREE HOOKS"}, {"t": 1.5, "text": "240) / il / AS"}, {"t": 2.0, "text": "THREE HOOKS"}]
        self.assertEqual([m.t for m in moments.caption_changes(samples)], [0.1, 1.1])


class TagTests(unittest.TestCase):
    def test_the_ux_lexicon_tags_a_known_transcript(self):
        hits = tags.ux_signals("I can’t find the save button. I expected it at the top. Oh nice.")
        self.assertEqual([(h["signal"], h["term"]) for h in hits],
                         [("friction", "can't find"), ("expectation", "i expected"), ("delight", "nice")])
        self.assertEqual(tags.ux_signals("The page loaded."), [])

    def test_tags_for_a_still(self):
        entry = {"t": 1.0, "triggers": ["screen_change", "speech"], "layout": ["text_heavy"], "change_score": 0.3,
                 "motion": "scroll", "said": "where is it", "ux_signals": [{"signal": "friction", "term": "where is"}],
                 "face": {"on": True, "framing": "close"}}
        self.assertEqual(tags.tags_for(entry, "ux"), [
            "trigger:screen_change", "trigger:speech", "hook", "layout:text_heavy", "face:yes", "framing:close",
            "change:large", "motion:scroll", "speech:yes", "ux_signal:friction",
        ])

    def test_post_tags(self):
        self.assertEqual(tags.post_tags({"platform": "instagram", "author": "a", "caption": "Try it #Hooks #hooks #ux"}),
                         ["platform:instagram", "author:a", "hashtag:hooks", "hashtag:ux"])


class CaptionMergeTests(unittest.TestCase):
    def test_captions_give_the_text_and_transcription_the_timings(self):
        captions = audio.Heard("words", None, "captions", None, [{"start": 0.0, "end": 2.0, "text": "Three ways to hook"}])
        whisper = audio.Heard("words", None, "whisper", "en", [{"start": 0.0, "end": 2.0, "text": "Three ways to hug"}],
                              _words((0.0, 0.4, "Three"), (0.4, 0.8, "ways"), (0.8, 1.0, "to"), (1.0, 1.5, "hug")))
        with mock.patch.object(audio, "transcribe", return_value=whisper) as transcribe:
            merged, sources = timeline_words.words_for(Path("x.mp4"), captions)
        transcribe.assert_called_once()
        self.assertEqual(merged.source, "captions+whisper")
        self.assertEqual(merged.text, "Three ways to hook")
        self.assertEqual(len(merged.words), 4)
        self.assertEqual(sources, {"captions": True, "whisper": True, "agreement": 0.75})

    def test_without_transcription_the_captions_stand_alone(self):
        captions = audio.Heard("words", None, "captions", None, [{"start": 0.0, "end": 2.0, "text": "Hello"}])
        with mock.patch.object(audio, "transcribe", return_value=audio.Heard("failed", "no_whisper")):
            merged, sources = timeline_words.words_for(Path("x.mp4"), captions)
        self.assertEqual(merged.source, "captions")
        self.assertEqual(sources, {"captions": True, "whisper": False})


@unittest.skipUnless(numpy is not None, "numpy is required")
class ScreenChangeTests(unittest.TestCase):
    def test_small_and_large_changes_and_a_scroll(self):
        rng = numpy.random.default_rng(1)
        page = rng.integers(0, 255, size=(180, 320)).astype(numpy.uint8)
        frames = [page.copy() for _ in range(40)]
        for index in range(10, 20):  # a button appears at frame 10
            frames[index][150:170, 250:300] = 0
        for index in range(20, 40):  # the page scrolls by 12 rows at frame 20
            frames[index] = numpy.roll(frames[19], -12, axis=0)
        found = moments.screen_changes(Frames(4.0, 320, 180, numpy.stack(frames)), 10.0, floor=0.6, scroll=True)
        self.assertEqual([m.t for m in found], [2.75, 5.25])
        self.assertIsNone(found[0].motion)
        self.assertEqual(found[1].motion, "scroll")
        self.assertLess(found[0].change_score, found[1].change_score)

    def test_typing_adds_up_to_a_change_and_a_blinking_caret_does_not(self):
        frames = numpy.full((40, 180, 320), 255, dtype=numpy.uint8)
        for index in range(40):
            if index % 2:
                frames[index][100:103, 50] = 0  # the caret blinks every frame
        for letter in range(8):  # from frame 20, one letter a frame (3x4 dark pixels each)
            for index in range(20 + letter, 40):
                frames[index][100:104, 60 + letter * 5:63 + letter * 5] = 0
        found = moments.screen_changes(Frames(4.0, 320, 180, frames), 10.0, floor=0.6, min_share=0.001)
        self.assertEqual(len(found), 1)
        self.assertGreaterEqual(found[0].t, 5.0)  # once enough letters are there, not on the caret

    def test_a_still_picture_has_no_changes(self):
        page = numpy.full((40, 180, 320), 200, dtype=numpy.uint8)
        self.assertEqual(moments.screen_changes(Frames(4.0, 320, 180, page), 10.0, floor=0.6), [])


@unittest.skipUnless(FFMPEG and numpy is not None, "FFmpeg and numpy are required")
class StandaloneTimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="cw-timeline-test-")
        cls.root = Path(cls.temp.name)
        cls.video = _screen_recording(cls.root / "feedback.mp4")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_a_screen_recording_gets_a_still_at_each_change(self):
        folder, built = build_standalone(self.video, self.root / "out", profile="auto")
        data = built.data
        self.assertEqual(data["format"], "content-watcher.timeline/1")
        self.assertEqual(data["profile"], "ux")
        changes = [e["t"] for e in data["entries"] if "screen_change" in e["triggers"]]
        for scripted in (3.0, 6.0):
            self.assertTrue(any(scripted <= t <= scripted + 1.0 for t in changes), (scripted, changes))
        self.assertTrue((folder / "timeline.json").is_file())
        self.assertIn("## Timeline:", (folder / "timeline.md").read_text())
        for entry in data["entries"]:
            self.assertTrue((folder / entry["file"]).is_file())
            self.assertEqual(tools.sha256_file(folder / entry["file"]), entry["still_sha256"])
        self.assertFalse((folder / "stills" / "captions").exists())

    def test_never_over_an_earlier_folder(self):
        first, _ = build_standalone(self.video, self.root / "again", profile="ux", max_stills=2)
        second, built = build_standalone(self.video, self.root / "again", profile="ux", max_stills=2)
        self.assertNotEqual(first, second)
        self.assertTrue(second.name.endswith("_2"))
        self.assertLessEqual(built.data["counts"]["stills"], 2)

    def test_a_missing_ocr_is_named_not_zeroed(self):
        real = tools.which
        with mock.patch.object(tools, "which", side_effect=lambda name: None if name == "tesseract" else real(name)):
            _, built = build_standalone(self.video, self.root / "no-ocr", profile="ux")
        self.assertIn("screen_text", built.data["unmeasured"])

    def test_the_command_touches_no_engine_filing_watch_or_state(self):
        """The UX skill's command writes only to --out: anything reaching inspirationhouse or Drive fails the test."""
        def refuse(*args, **kwargs):
            raise AssertionError("the timeline command reached outside its folder")

        import content_watcher.engine as engine
        import content_watcher.filing as filing
        import content_watcher.state as state
        import content_watcher.watch as watch
        out = self.root / "isolated"
        with mock.patch.object(engine.Engine, "__init__", refuse), mock.patch.object(engine.Engine, "_post", refuse), \
                mock.patch.object(filing, "file_post", refuse), mock.patch.object(watch, "watch_once", refuse), \
                mock.patch.object(state.State, "__init__", refuse), mock.patch.object(engine, "put_upload", refuse):
            code = cli.main(["timeline", str(self.video), "--out", str(out), "--profile", "ux"])
        self.assertEqual(code, 0)
        written = sorted(p.relative_to(out).parts[0] for p in out.iterdir())
        self.assertEqual(len(written), 1)


@unittest.skipUnless(FFMPEG, "FFmpeg is required")
class ReadingCarriesTimelineTests(unittest.TestCase):
    """Every video reading carries a timeline, and a timeline that fails leaves the reading exactly as before."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="cw-timeline-read-")
        cls.root = Path(cls.temp.name)
        cls.video = make_video(cls.root / "reel.mp4", seconds=3.0, text="HELLO")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_the_reading_has_a_timeline_and_its_stills(self):
        reading = read_path(self.video, out=self.root / "with", whisper_model="tiny")[0]
        timeline = reading.read["timeline"]
        self.assertEqual(timeline["profile"], "social")
        self.assertGreaterEqual(timeline["counts"]["stills"], 1)
        for entry in timeline["entries"]:
            self.assertTrue((reading.folder / entry["file"]).is_file())
        saved = json.loads((reading.folder / "read.json").read_text())
        self.assertEqual(saved["timeline"]["counts"], timeline["counts"])
        self.assertIn("## Timeline:", reading.read_md)
        self.assertLess(reading.read_md.index("## Timeline:"), reading.read_md.index("## Frames kept"))

    def _without(self, reading):
        data = dict(reading.read)
        data.pop("timeline", None)
        data["unmeasured"] = [item for item in data["unmeasured"] if item != "timeline"]
        return data

    def test_a_failing_timeline_leaves_the_reading_as_it_was(self):
        good = read_path(self.video, out=self.root / "good", whisper_model="tiny")[0]
        with mock.patch("content_watcher.timeline.timeline", side_effect=RuntimeError("boom")):
            failed = read_path(self.video, out=self.root / "failed", whisper_model="tiny")[0]
        self.assertNotIn("timeline", failed.read)
        self.assertIn("timeline", failed.read["unmeasured"])
        self.assertEqual(self._without(failed), self._without(good))
        self.assertFalse((failed.folder / "stills").exists())
        for key in ("post", "heard", "words_text"):  # the fields inspirationhouse is promised
            self.assertIn(key, failed.read)

    def test_a_timeline_past_its_budget_is_dropped(self):
        with mock.patch.dict(os.environ, {"CONTENT_WATCH_TIMELINE_BUDGET": "0"}):
            reading = read_path(self.video, out=self.root / "late", whisper_model="tiny")[0]
        self.assertNotIn("timeline", reading.read)
        self.assertIn("timeline", reading.read["unmeasured"])

    def test_budget_error_is_its_own_class(self):
        self.assertTrue(issubclass(TimelineBudget, Exception))


if __name__ == "__main__":
    unittest.main()
