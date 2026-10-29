"""content-watch audio: a video's audio track on its own, with ffmpeg alone."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from content_watcher.cli import main
from content_watcher.read import audio
from tests.cw_helpers import FFMPEG, make_video


@unittest.skipUnless(FFMPEG, "FFmpeg is required")
class AudioExtractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.video = make_video(cls.root / "talk.mp4", seconds=2.0)
        cls.silent = make_video(cls.root / "mute.mp4", seconds=1.0, audio=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_copy_keeps_the_codec_and_length(self):
        out = audio.extract(self.video, self.root / "copy")
        self.assertEqual(out.name, "talk.m4a")
        codec, seconds = audio._probe_audio(out)
        self.assertEqual(codec, "aac")
        self.assertAlmostEqual(seconds, 2.0, delta=0.5)

    def test_wav_for_speech_is_16k_mono_pcm(self):
        out = audio.extract(self.video, self.root / "wav", fmt="wav", speech=True)
        self.assertEqual(out.suffix, ".wav")
        self.assertEqual(audio._probe_audio(out)[0], "pcm_s16le")
        self.assertGreater(len(audio.decode_samples(out)), audio.SAMPLE_RATE)

    def test_never_overwrites(self):
        folder = self.root / "twice"
        first = audio.extract(self.video, folder)
        size = first.stat().st_size
        with self.assertRaises(FileExistsError):
            audio.extract(self.video, folder)
        self.assertEqual(first.stat().st_size, size)

    def test_a_video_without_audio_fails_cleanly(self):
        with self.assertRaises(ValueError):
            audio.extract(self.silent, self.root / "none")
        self.assertFalse((self.root / "none").exists())

    def test_cli_prints_the_path(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["audio", str(self.video), "--out", str(self.root / "cli")])
        self.assertEqual(code, 0)
        self.assertIn(str(self.root / "cli" / "talk.m4a"), buffer.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["audio", str(self.silent), "--out", str(self.root / "cli")]), 2)


if __name__ == "__main__":
    unittest.main()
