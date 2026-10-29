"""W2.11 one local layout: every reader resolves from config/studio.json, and the path guard refuses a planted path."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from content_watcher import layout

ROOT = Path(__file__).resolve().parents[1]
# Built from pieces so this file never trips the guard it tests.
DEV = "C:" + "\\Users\\" + "krish" + "\\dev\\"
NOW_CAP = 12_000


def studio(path: Path, roots: dict | None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema": "studio/1"}
    if roots is not None:
        data["local_roots"] = roots
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.here = self.base / "content-watcher"
        self.env = mock.patch.dict(os.environ, {"LOCALAPPDATA": str(self.base / "local")}, clear=False)
        self.env.start()
        os.environ.pop("CONTENT_WATCH_STUDIO", None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_own_copy_matches_the_reference_shape(self):
        data = json.loads((ROOT / "config" / "studio.json").read_text(encoding="utf-8"))
        self.assertEqual(data["local_roots"], {
            "repos": DEV + "makeyourmindup\\{repo}",
            "worktrees": DEV + "makeyourmindup\\.worktrees\\{repo}\\{branch}",
            "runtime": "%LOCALAPPDATA%\\makeyourmindup\\",
        })

    def test_content_engine_beside_this_clone_wins(self):
        studio(self.here / "config" / "studio.json", {"runtime": "%LOCALAPPDATA%\\own\\"})
        engine = studio(self.base / "content-engine" / "config" / "studio.json", {"runtime": "%LOCALAPPDATA%\\engine\\"})
        found = layout.load(self.here)
        self.assertEqual(found.source, engine)
        self.assertEqual(found.runtime_dir("stills"), self.base / "local" / "engine" / "stills")

    def test_content_engine_without_local_roots_falls_back_to_own_copy(self):
        own = studio(self.here / "config" / "studio.json", {"runtime": "%LOCALAPPDATA%\\makeyourmindup\\"})
        studio(self.base / "content-engine" / "config" / "studio.json", None)  # today's content-engine main
        found = layout.load(self.here)
        self.assertEqual(found.source, own)
        self.assertEqual(found.runtime_dir(), self.base / "local" / "makeyourmindup")

    def test_a_worktree_finds_content_engine_in_the_repos_root(self):
        tree = self.base / ".worktrees" / "content-watcher" / "claude-x"
        engine = studio(self.base / "content-engine" / "config" / "studio.json", {"runtime": "%LOCALAPPDATA%\\e\\"})
        self.assertEqual(layout.load(tree).source, engine)

    def test_repo_and_worktree_patterns_fill_in(self):
        own = studio(self.here / "config" / "studio.json", {
            "repos": str(self.base / "dev" / "{repo}"), "worktrees": str(self.base / "dev" / ".worktrees" / "{repo}" / "{branch}"),
        })
        found = layout.load(self.here, override=str(own))
        self.assertEqual(found.repo_dir("content-engine"), self.base / "dev" / "content-engine")
        self.assertEqual(found.worktree_dir("content-engine", "main"), self.base / "dev" / ".worktrees" / "content-engine" / "main")

    def test_unset_runtime_variable_falls_back_home(self):
        os.environ.pop("LOCALAPPDATA")
        studio(self.here / "config" / "studio.json", {"runtime": "%LOCALAPPDATA%\\makeyourmindup\\"})
        self.assertEqual(layout.load(self.here).runtime_dir("x"), Path.home() / ".makeyourmindup" / "x")

    def test_no_studio_file_still_has_a_runtime(self):
        found = layout.load(self.here)
        self.assertIsNone(found.source)
        self.assertIsNone(found.repo_dir("content-engine"))
        self.assertEqual(found.runtime_dir(), Path.home() / ".makeyourmindup")

    def test_this_repository_resolves_from_its_own_config(self):
        found = layout.load()
        self.assertIsNotNone(found.source)
        self.assertEqual(found.source.name, "studio.json")


class PathGuardTests(unittest.TestCase):
    def guard(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "check_paths.py"), *args],
                              capture_output=True, text=True)

    def test_this_repository_is_clean(self):
        result = self.guard()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_a_planted_path_fails(self):
        for planted in (DEV + "makeyourmindup\\content-engine", "C:" + "/Users/krish/dev/x", "c:" + "\\\\users\\\\Krish\\\\dev\\\\y"):
            with self.subTest(planted=planted), tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / "reader.py").write_text(f"ROOT = r'{planted}'\n", encoding="utf-8")
                result = self.guard(tmp)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("reader.py:1", result.stdout)

    def test_only_config_studio_json_may_hold_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            studio(Path(tmp) / "config" / "studio.json", {"repos": DEV + "{repo}"})
            self.assertEqual(self.guard(tmp).returncode, 0)
            studio(Path(tmp) / "other" / "studio.json", {"repos": DEV + "{repo}"})
            self.assertEqual(self.guard(tmp).returncode, 1)

    def test_other_users_and_folders_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.md").write_text("C:\\Users\\krish\\AppData and %LOCALAPPDATA%\\makeyourmindup\\", encoding="utf-8")
            self.assertEqual(self.guard(tmp).returncode, 0)


class NowCapTests(unittest.TestCase):
    def test_now_md_stays_under_its_byte_cap(self):
        size = len((ROOT / "NOW.md").read_bytes())
        self.assertLessEqual(size, NOW_CAP, "move the oldest of NOW.md to docs/history/NOW-changes.md")

    def test_history_lives_in_docs_history(self):
        history = (ROOT / "docs" / "history" / "NOW-changes.md").read_text(encoding="utf-8")
        self.assertIn("- 2026-10-24 **Content Watcher, first build**", history)
        self.assertIn("docs/history/NOW-changes.md", (ROOT / "NOW.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
