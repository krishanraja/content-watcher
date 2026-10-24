import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from content_watcher import tools


class WindowsInstallsTest(unittest.TestCase):
    def test_finds_tesseract_and_poppler_off_path(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            tess = root / "pf" / "Tesseract-OCR" / "tesseract.exe"
            pdf = root / "local" / "Microsoft" / "WinGet" / "Packages" / "oschwartz10612.Poppler_x" / "poppler-25.07.0" / "Library" / "bin" / "pdftotext.exe"
            for f in (tess, pdf):
                f.parent.mkdir(parents=True)
                f.write_text("")
            env = {"ProgramFiles": str(root / "pf"), "LOCALAPPDATA": str(root / "local")}
            with mock.patch.dict(os.environ, env, clear=False), \
                 mock.patch.object(tools.sys, "platform", "win32"), \
                 mock.patch.object(tools.sys, "executable", str(root / "py" / "python.exe")), \
                 mock.patch.object(tools.shutil, "which", return_value=None):
                self.assertEqual(tools.which("tesseract"), str(tess))
                self.assertEqual(tools.which("pdftotext"), str(pdf))
                self.assertIsNone(tools.which("nothing-here"))

    def test_not_windows_skips_the_search(self):
        with mock.patch.object(tools.sys, "platform", "linux"), \
             mock.patch.object(tools.shutil, "which", return_value=None):
            self.assertIsNone(tools.which("tesseract-not-installed-xyz"))


if __name__ == "__main__":
    unittest.main()
