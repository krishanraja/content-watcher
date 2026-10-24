"""Readings of generated media with known content: each test fails when a measure is wrong."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from content_watcher.post import Post
from content_watcher.read import read_path, read_post
from content_watcher.read import audio
from tests.cw_helpers import FFMPEG, FIXTURES, ffmpeg, make_image, make_video

HAS_TESSERACT = bool(shutil.which("tesseract"))
HAS_ESPEAK = bool(shutil.which("espeak-ng") or shutil.which("espeak"))


def whisper_ready() -> bool:
    try:
        from faster_whisper import WhisperModel  # noqa: F401
        WhisperModel("tiny", device="cpu", compute_type="int8")
    except Exception:  # noqa: BLE001
        return False
    return True


WHISPER = whisper_ready() if HAS_ESPEAK else False


@unittest.skipUnless(FFMPEG, "FFmpeg is required")
class VideoReadingTests(unittest.TestCase):
    """Shot 1: a title card with screen text and speech. Cut at 2 s. Shot 2: a push-in. Cut at 4 s. Shot 3: a pan."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="cw-read-test-")
        root = Path(cls.temp.name)
        cls.root = root
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=720x1280", "-frames:v", "1", str(root / "still.png"))
        ffmpeg("-f", "lavfi", "-i", "mandelbrot=s=1440x1280", "-frames:v", "1", str(root / "wide.png"))
        speech = root / "speech.wav"
        if HAS_ESPEAK:
            espeak = shutil.which("espeak-ng") or shutil.which("espeak")
            import subprocess
            subprocess.run([espeak, "-w", str(speech), "Here is the hook. Three ways to make your videos better."], check=True)
        else:
            ffmpeg("-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono", "-t", "6", str(speech))
        cls.video = root / "known.mp4"
        ffmpeg(
            "-f", "lavfi", "-i", "color=c=navy:s=720x1280:d=2:r=25,drawtext=text='BIG IDEA':fontsize=130:fontcolor=white:x=(w-tw)/2:y=(h-th)/2",
            "-loop", "1", "-i", str(root / "still.png"),
            "-loop", "1", "-i", str(root / "wide.png"),
            "-i", str(speech),
            "-filter_complex",
            "[1:v]zoompan=z='1+0.006*on':d=50:s=720x1280:fps=25,trim=duration=2,setpts=PTS-STARTPTS[z];"
            "[2:v]fps=25,crop=720:1280:'min(t*120,720)':0,trim=duration=2,setpts=PTS-STARTPTS[p];"
            "[0:v][z][p]concat=n=3:v=1:a=0,format=yuv420p[v];[3:a]apad=whole_dur=6[a]",
            "-map", "[v]", "-map", "[a]", "-t", "6", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(cls.video),
        )
        cls.readings = read_path(cls.video, out=root / "readings", whisper_model="tiny")
        cls.reading = cls.readings[0]
        cls.data = cls.reading.read

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_files_written_and_contract_fields_present(self):
        folder = self.reading.folder
        self.assertTrue((folder / "read.json").is_file())
        self.assertTrue((folder / "read.md").is_file())
        saved = json.loads((folder / "read.json").read_text())
        for key in ("format", "engine_rev", "sha256", "shape", "post", "heard", "words_text"):
            self.assertIn(key, saved)
        self.assertEqual(saved["shape"], "video")
        self.assertEqual(len(saved["sha256"]), 64)
        row = self.reading.contract_row()
        self.assertEqual(set(row), {"sha256", "source_url", "platform", "shape", "engine_rev", "read", "read_md"})
        self.assertEqual(row["platform"], "own")

    def test_known_cuts(self):
        cuts = self.data["shots"]["cuts"]
        self.assertEqual(len(cuts), 2, cuts)
        self.assertAlmostEqual(cuts[0], 2.0, delta=0.15)
        self.assertAlmostEqual(cuts[1], 4.0, delta=0.15)
        self.assertEqual(self.data["shots"]["count"], 3)
        self.assertAlmostEqual(self.data["shots"]["cuts_per_min"], 20.0, delta=1.0)

    def test_known_push_in_and_pan(self):
        moves = {round(m["start"]): m["kind"] for m in self.data["camera_moves"]}
        self.assertEqual(moves.get(2), "push_in", self.data["camera_moves"])
        self.assertTrue(str(moves.get(4, "")).startswith("pan_"), self.data["camera_moves"])
        self.assertNotIn(0, moves)  # the static title card does not move

    @unittest.skipUnless(HAS_TESSERACT, "tesseract is required")
    def test_known_screen_text(self):
        texts = " ".join(item["text"] for item in self.data["screen_text"])
        self.assertIn("BIG IDEA", texts)
        self.assertIn("BIG IDEA", " ".join(self.data["hook"]["screen_text"]))
        self.assertIn("BIG IDEA", self.reading.read_md)
        self.assertEqual(self.data["shots"]["list"][0]["screen_text"][0], "BIG IDEA")

    @unittest.skipUnless(WHISPER, "faster-whisper with the tiny model and espeak are required")
    def test_known_words(self):
        self.assertEqual(self.data["heard"], "words")
        self.assertIn("hook", self.data["words_text"].lower())
        self.assertIn("hook", self.data["hook"]["words"].lower())
        self.assertIn("hook", self.reading.read_md.lower())
        self.assertGreater(self.data["pace"]["words_per_min"], 0)

    def test_hook_and_chosen_frames(self):
        self.assertEqual(self.data["hook"]["cuts"], 1)  # the cut at 2 s is inside the first 3 s
        roles = [frame["role"] for frame in self.data["frames"]]
        self.assertIn("hook", roles)
        self.assertLessEqual(len(roles), 2)
        for frame in self.data["frames"]:
            self.assertTrue((self.reading.folder / frame["file"]).is_file())

    def test_loudness_measured(self):
        self.assertIsNotNone(self.data["audio"]["integrated_lufs"])


@unittest.skipUnless(FFMPEG, "FFmpeg is required")
class CaptionTests(unittest.TestCase):
    def test_auto_captions_are_deduplicated(self):
        heard = audio.parse_captions(FIXTURES / "youtube_auto.en.vtt")
        self.assertEqual(heard.source, "captions")
        self.assertEqual([s["text"] for s in heard.segments],
                         ["the hook is", "everything you say first", "then you earn the next ten seconds"])

    def test_platform_captions_win_over_transcription(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = make_video(root / "tiktok_1.mp4", seconds=6)
            shutil.copy(FIXTURES / "youtube_auto.en.vtt", root / "tiktok_1.en.vtt")
            post = Post("tiktok", "https://www.tiktok.com/@a/video/1", "1", "a", media=[video],
                        captions_file=root / "tiktok_1.en.vtt", method="ytdlp")
            post.save(root)
            reading = read_post(root, out=root / "r", whisper_model="tiny")[0]
        self.assertEqual(reading.read["words"]["source"], "captions")
        self.assertIn("everything you say first", reading.read["words_text"])
        self.assertEqual(reading.read["post"]["platform"], "tiktok")
        self.assertEqual(reading.platform, "tiktok")

    def test_silent_video_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = make_video(root / "silent.mp4", seconds=2, audio=False)
            reading = read_path(video, out=root / "r")[0]
        self.assertEqual(reading.read["heard"], "silent")
        self.assertEqual(reading.read["heard_class"], "no_audio_stream")


@unittest.skipUnless(FFMPEG, "FFmpeg is required")
class CarouselTests(unittest.TestCase):
    def test_one_reading_per_slide_and_the_first_covers_the_post(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slides = [
                make_image(root / "instagram_Cx_01.jpg", "ONE IDEA"),
                make_image(root / "instagram_Cx_02.jpg", "SECOND POINT", colour="black", font_colour="white"),
                make_image(root / "instagram_Cx_03.png", "42%", fontsize=400),
            ]
            post = Post("instagram", "https://www.instagram.com/p/Cx/", "Cx", "carousel.example",
                        caption="Five ways to open a talk", media=slides, method="apify_instagram_post")
            post.save(root)
            readings = read_post(root, out=root / "r")
            shas = {r.sha256 for r in readings}
            first_md = readings[0].read_md
            folder_files = sorted(p.name for p in (root / "r").iterdir())
        self.assertEqual(len(readings), 3)
        self.assertEqual(len(shas), 3)
        self.assertTrue(all(r.shape == "carousel" for r in readings))
        self.assertEqual([r.read["position"]["index"] for r in readings], [1, 2, 3])
        self.assertEqual(len(readings[0].read["post_slides"]), 3)
        self.assertIn("Five ways to open a talk", first_md)
        self.assertEqual(len(folder_files), 3)
        self.assertEqual(readings[1].read["slide"]["colours"][0]["hex"][:3], "#00")
        if HAS_TESSERACT:
            order = [first_md.find("ONE IDEA"), first_md.find("SECOND POINT"), first_md.find("42%")]
            self.assertTrue(all(i >= 0 for i in order), first_md)
            self.assertEqual(order, sorted(order))
            self.assertIn("one_number", readings[2].read["slide"]["layout"])


class TextPostTests(unittest.TestCase):
    def test_filed_linkedin_markdown_reads_back_its_author_and_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "linkedin_7250000000000000000.md"
            path.write_text(
                "# LinkedIn post by Pat Example\n\nAuthor: Pat Example\nPosted: 2026-10-19\n"
                "Link: https://www.linkedin.com/feed/update/urn:li:activity:7250000000000000000/\nPlatform: linkedin\n\n"
                "Most decks fail on slide one.\n\n1. One idea a slide\n2. A number\n3. The ask #decks\n",
                encoding="utf-8",
            )
            reading = read_path(path, out=Path(tmp) / "r")[0]
        self.assertEqual(reading.shape, "text")
        self.assertEqual(reading.read["post"]["author"], "Pat Example")
        self.assertEqual(reading.platform, "linkedin")
        self.assertEqual(reading.read["text"]["list_lines"], 3)
        self.assertEqual(reading.read["text"]["first_line"], "Most decks fail on slide one.")
        self.assertIn("Most decks fail on slide one.", reading.read_md)
        self.assertEqual(reading.read["heard"], "silent")


if __name__ == "__main__":
    unittest.main()
