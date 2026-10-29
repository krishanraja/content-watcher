"""W3.2: the Inspiration root is read, and at most 8 curated stills go to a machine-owned folder, tagged machine.

Synthetic fixtures only: folders made in a temporary directory, stills as made-up bytes, timelines written here.
"""

import json
import os
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

from content_watcher import inspiration, tools, watch
from content_watcher.config import Config
from content_watcher.read.reader import Reading
from content_watcher.state import State
from tests.cw_helpers import make_video

ROOT = Path(__file__).resolve().parents[1]


def timeline(n: int, seconds: float = 60.0) -> dict:
    entries = []
    for i in range(1, n + 1):
        t = round(seconds * (i - 1) / max(n - 1, 1), 2)
        entries.append({
            "index": i, "t": t, "file": f"stills/{i:02d}.jpg",
            "triggers": ["start"] if i == 1 else (["cut"] if i % 5 == 0 else ["speech"]),
            "change_score": 0.5 if i % 5 == 0 else 0.05, "screen_text": "SALE" if i % 7 == 0 else "",
            "same_as": 2 if i == 3 else None, "tags": ["hook"] if t < 3 else ["speech:yes"],
        })
    return {"format": "content-watcher.timeline/1", "profile": "social", "entries": entries}


def tree(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.stat().st_size for p in sorted(root.rglob("*"))}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.root = self.base / "My Drive" / "Ventures" / "Inspiration"
        (self.root / "Content Inspo").mkdir(parents=True)
        (self.root / "Production Inspo").mkdir(parents=True)
        studio = self.base / "studio.json"
        studio.write_text(json.dumps({"local_roots": {"runtime": str(self.base / "runtime")}}), encoding="utf-8")
        self.env = mock.patch.dict(os.environ, {"CONTENT_WATCH_STUDIO": str(studio),
                                                "CONTENT_WATCH_HOME": str(self.base / "home")})
        self.env.start()
        self.config = Config(inspiration_root=str(self.root))

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def reading(self, n: int = 40) -> Reading:
        folder = self.base / "readings" / f"r{n}"
        (folder / "stills").mkdir(parents=True)
        for i in range(1, n + 1):
            (folder / "stills" / f"{i:02d}.jpg").write_bytes(b"\xff\xd8synthetic still " + bytes([i]))
        data = {"format": "content-watcher.read/1", "post": None, "heard": "words", "words_text": "hi",
                "timeline": timeline(n)}
        return Reading("ab" * 32, "video", "own", None, data, "# reading", folder=folder)


class InspirationRootTests(Base):
    def test_both_folders_are_found_below_the_root(self):
        self.assertEqual(self.config.inspo_folder("cold_ideas"), str(self.root / "Content Inspo"))
        self.assertEqual(self.config.inspo_folder("video_inspiration"), str(self.root / "Production Inspo"))
        self.assertEqual(self.config.folder_path("cold_ideas"), self.root / "Content Inspo")
        self.assertEqual(self.config.my_drive_root(), self.base / "My Drive")

    def test_a_folder_set_on_its_own_still_wins(self):
        elsewhere = self.base / "Elsewhere"
        elsewhere.mkdir()
        config = Config(inspiration_root=str(self.root), cold_ideas=str(elsewhere))
        self.assertEqual(config.inspo_folder("cold_ideas"), str(elsewhere))
        self.assertEqual(config.inspo_folder("video_inspiration"), str(self.root / "Production Inspo"))

    def test_a_missing_folder_below_the_root_is_unset(self):
        (self.root / "Production Inspo").rmdir()
        self.assertIsNone(self.config.inspo_folder("video_inspiration"))

    def test_hand_dropped_files_below_the_root_are_read(self):
        (self.root / "Content Inspo" / "idea.txt").write_text("a thought", encoding="utf-8")
        (self.root / "Production Inspo" / "reel.mp4").write_bytes(b"not really a video")
        found = watch.drop_candidates(self.config, State())
        self.assertEqual(sorted((p.name, f) for p, _sha, f in found),
                         [("idea.txt", "cold_ideas"), ("reel.mp4", "video_inspiration")])


class CurateTests(unittest.TestCase):
    def test_at_most_eight_in_time_order_one_picture_each(self):
        picked = inspiration.curate(timeline(40))
        self.assertEqual(len(picked), 8)
        times = [e["t"] for e in picked]
        self.assertEqual(times, sorted(times))
        self.assertNotIn(3, [e["index"] for e in picked])  # repeats still 2's picture
        self.assertEqual(picked[0]["index"], 1)  # the opening
        self.assertGreaterEqual(picked[-1]["t"], 50)  # and the end of the video

    def test_a_short_timeline_keeps_what_it_has(self):
        self.assertEqual([e["index"] for e in inspiration.curate(timeline(4))], [1, 2, 4])
        self.assertEqual(inspiration.curate(None), [])
        self.assertEqual(inspiration.curate({"entries": []}), [])


class MachineFolderTests(Base):
    def test_default_is_the_layout_runtime_folder(self):
        self.assertEqual(inspiration.machine_dir(self.config), self.base / "runtime" / "content-watcher" / "stills")

    def test_the_synced_machine_stills_drive_folder_wins_when_present(self):
        synced = self.base / "My Drive" / "Ventures" / "Active Ventures" / "makeyourmindup" / "4 Growth" / "Machine stills"
        synced.mkdir(parents=True)
        self.assertEqual(inspiration.machine_dir(self.config), synced)

    def test_a_folder_in_his_tree_is_refused(self):
        for inside in (self.root, self.root / "Content Inspo" / "stills", self.root.parent):
            with self.subTest(inside=inside):
                config = Config(inspiration_root=str(self.root), machine_stills=str(inside))
                with self.assertRaises(inspiration.MachineFolderError):
                    inspiration.machine_dir(config)


class HandOverTests(Base):
    def test_eight_stills_go_to_the_machine_folder_tagged_machine(self):
        before = tree(self.root)
        reading = self.reading(40)
        block = inspiration.hand_over(reading, self.config)
        self.assertEqual(tree(self.root), before)  # nothing in his tree
        self.assertEqual(block["count"], 8)
        self.assertEqual(block["owner"], "machine")
        self.assertEqual(block["tags"], ["machine"])
        self.assertIs(block["counts_as_his"], False)
        self.assertEqual(block["drive_folder_id"], "1ryqrwjUloZwlKjn8UroVb6buwKIAPvwf")
        self.assertIs(block["synced"], False)
        folder = self.base / "runtime" / "content-watcher" / "stills" / ("ab" * 8)
        names = sorted(p.name for p in folder.iterdir() if p.suffix == ".jpg")
        self.assertEqual(names, sorted(item["name"] for item in block["items"]))
        self.assertTrue(all(item["tags"][0] == "machine" for item in block["items"]))
        self.assertEqual(json.loads((folder / "stills.json").read_text())["counts_as_his"], False)
        self.assertEqual(reading.contract_row()["read"]["machine_stills"], block)

    def test_a_second_hand_over_adds_nothing(self):
        reading = self.reading(12)
        inspiration.hand_over(reading, self.config)
        folder = self.base / "runtime" / "content-watcher" / "stills" / ("ab" * 8)
        first = tree(folder)
        inspiration.hand_over(reading, self.config)
        self.assertEqual(tree(folder), first)

    def test_no_timeline_no_stills(self):
        reading = self.reading(3)
        reading.read.pop("timeline")
        self.assertIsNone(inspiration.hand_over(reading, self.config))
        self.assertNotIn("machine_stills", reading.read)

    def test_a_refused_folder_never_fails_the_reading(self):
        config = Config(inspiration_root=str(self.root), machine_stills=str(self.root / "Content Inspo"))
        reading, counts = self.reading(5), Counter()
        before = tree(self.root)
        inspiration.hand_over_all([reading], config, counts)
        self.assertEqual(counts["stills.machine_refused"], 1)
        self.assertNotIn("machine_stills", reading.read)
        self.assertEqual(tree(self.root), before)

    def test_a_dropped_file_reading_carries_its_stills_to_the_engine(self):
        (self.root / "Production Inspo" / "reel.mp4").write_bytes(b"synthetic")
        reading = self.reading(20)
        engine = mock.Mock()
        engine.held.return_value = set()
        with mock.patch.object(watch, "read_path", return_value=[reading]):
            watch.read_drops(self.config, engine, State(), Counter())
        rows = engine.read.call_args[0][1]
        self.assertEqual(rows[0]["read"]["machine_stills"]["count"], 8)


@unittest.skipUnless(tools.which("ffmpeg"), "FFmpeg is required")
class RealReadingTests(Base):
    def test_a_generated_video_hands_over_its_stills(self):
        from content_watcher.read.reader import read_path

        video = make_video(self.base / "reel.mp4", seconds=3.0, text="HELLO")
        reading = read_path(video, out=self.base / "out", whisper_model="tiny")[0]
        block = inspiration.hand_over(reading, self.config)
        self.assertIsNotNone(block)
        self.assertLessEqual(block["count"], 8)
        folder = inspiration.machine_dir(self.config) / block["folder_key"]
        for item in block["items"]:
            self.assertTrue((folder / item["name"]).is_file())


class UxPathStaysSeparateTests(unittest.TestCase):
    def test_the_ux_feedback_path_never_reaches_the_machine_stills(self):
        for path in [ROOT / "content_watcher" / "feedback.py", *(ROOT / "content_watcher" / "timeline").glob("*.py")]:
            with self.subTest(path=path.name):
                self.assertNotIn("inspiration", path.read_text(encoding="utf-8").split('"""', 2)[-1])
        source = (ROOT / "content_watcher" / "cli.py").read_text(encoding="utf-8")
        timeline_command = source[source.index("def _timeline"):source.index("def ", source.index("def _timeline") + 5)]
        self.assertNotIn("inspiration", timeline_command)


if __name__ == "__main__":
    unittest.main()
