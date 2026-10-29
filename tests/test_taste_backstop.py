"""W3.3 the filtered chat backstop: only Krish's flagged lines are kept, scrubbed, locally; a planted secret is removed.

Synthetic transcript only: every line and every secret below is made up for the test.
"""

import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("taste_backstop", ROOT / "scripts" / "taste_backstop.py")
backstop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backstop)

# Planted secrets, assembled so no scanner reads this file as holding a real one.
KEY = "sk-" + "test" + "A1b2C3d4E5f6G7h8J9k0"
GH = "ghp_" + "Z" * 24
EMAIL = "someone" + "@" + "example.com"


def record(role, content, **extra):
    return json.dumps({"type": role, "message": {"role": role, "content": content}, **extra})


def transcript(folder: Path) -> Path:
    lines = [
        record("user", "Add the stills folder please."),
        record("user", f"No, that's wrong. The key is {KEY} and never put it in a test."),
        record("user", [{"type": "text", "text": f"Don't email {EMAIL} about it. Use token {GH} instead."}]),
        record("assistant", "No, I will not do that."),  # the assistant's words are never his
        record("user", [{"type": "tool_result", "content": "no such file, wrong path"}]),  # tool output
        record("user", "<system-reminder>Never do this.</system-reminder>Fine as it is."),
        record("user", "<pasted_content id=1>stop, wrong, never</pasted_content>Looks good."),
        record("user", "Never a carousel.", isMeta=True),
        record("user", "Never a carousel.", isSidechain=True),
        record("user", f"No, that's wrong. The key is {KEY} and never put it in a test."),  # a repeat
        "not json",
    ]
    path = folder / "session.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


class TasteBackstopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.path = transcript(self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_tagged_for_this_repository(self):
        self.assertEqual(backstop.VENTURE, "publication")
        self.assertEqual(backstop.REPO, "krishanraja/content-watcher")

    def test_dry_run_keeps_only_his_flagged_lines(self):
        printed = []
        self.assertEqual(backstop.main(["--dry-run", str(self.path)], out=printed.append), 0)
        self.assertEqual(printed, [
            "No, that's wrong.",
            "The key is [key] and never put it in a test.",
            "Don't email [email] about it.",
            "Use token [key] instead.",
        ])

    def test_a_planted_secret_is_removed(self):
        kept = " ".join(backstop.flagged(self.path))
        for secret in (KEY, GH, EMAIL, "A1b2C3d4"):
            self.assertNotIn(secret, kept)
        self.assertIn("[key]", kept)
        self.assertIn("[email]", kept)

    def test_the_hook_appends_locally_once_and_sends_nothing(self):
        hook = json.dumps({"transcript_path": str(self.path), "session_id": "s1"})
        printed = []
        self.assertEqual(backstop.main([], stdin=io.StringIO(hook), root=self.dir, out=printed.append), 0)
        self.assertEqual(backstop.main([], stdin=io.StringIO(hook), root=self.dir, out=printed.append), 0)
        rows = [json.loads(line) for line in (self.dir / ".scratch" / "taste" / "backstop.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r["repository"] == "krishanraja/content-watcher" and r["posted"] is False for r in rows))
        self.assertEqual(printed[1], "taste backstop: 0 flagged lines kept locally; nothing sent")
        source = (ROOT / "scripts" / "taste_backstop.py").read_text(encoding="utf-8")
        for module in ("urllib", "http.client", "requests", "socket"):
            self.assertNotIn("import " + module, source)

    def test_a_broken_hook_input_never_breaks_the_session(self):
        for raw in ("", "{", json.dumps({"transcript_path": 5}), json.dumps({"transcript_path": "/no/such/file"})):
            with self.subTest(raw=raw):
                self.assertEqual(backstop.main([], stdin=io.StringIO(raw), root=self.dir, out=lambda _l: None), 0)

    def test_settings_run_it_at_session_end(self):
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        command = settings["hooks"]["SessionEnd"][0]["hooks"][0]["command"]
        self.assertIn("$CLAUDE_PROJECT_DIR/scripts/taste_backstop.py", command)

    def test_outbox_is_ignored_by_git(self):
        self.assertIn(".scratch/", (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())


if __name__ == "__main__":
    unittest.main()
