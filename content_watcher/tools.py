"""Finding and running outside tools, always with a timeout."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from video_compression.ffmpeg import VideoCompressionError, find_binary


class ToolMissing(RuntimeError):
    """An optional outside tool is not installed."""


@dataclass
class Ran:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def _windows_installs(name: str) -> list[Path]:
    """Where the Windows installers put tools that do not always reach PATH: Tesseract's
    installer leaves PATH alone, and winget's Poppler changes PATH only for shells opened later."""
    found: list[Path] = []
    for root in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if root:
            found.append(Path(root) / "Tesseract-OCR" / f"{name}.exe")
    local = os.environ.get("LOCALAPPDATA")
    if local:
        packages = Path(local) / "Microsoft" / "WinGet" / "Packages"
        if packages.is_dir():
            found.extend(sorted(packages.glob(f"oschwartz10612.Poppler_*/poppler-*/Library/bin/{name}.exe"), reverse=True))
    return found


def which(name: str) -> str | None:
    if name in ("ffmpeg", "ffprobe"):
        try:
            return str(find_binary(name))
        except VideoCompressionError:
            return None
    found = shutil.which(name)
    if found:
        return found
    # Tools installed with pip into this interpreter, for example yt-dlp and gallery-dl.
    scripts = Path(sys.executable).parent
    for candidate in (scripts / name, scripts / f"{name}.exe", scripts / "Scripts" / f"{name}.exe"):
        if candidate.is_file():
            return str(candidate)
    if sys.platform == "win32":
        for candidate in _windows_installs(name):
            if candidate.is_file():
                return str(candidate)
    return None


def need(name: str) -> str:
    found = which(name)
    if not found:
        raise ToolMissing(name)
    return found


def run(args: list[str | Path], *, timeout: float, input_bytes: bytes | None = None) -> Ran:
    command = [str(item) for item in args]
    try:
        result = subprocess.run(
            command,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return Ran(-1, _text(exc.stdout), _text(exc.stderr), timed_out=True)
    return Ran(result.returncode, _text(result.stdout), _text(result.stderr))


def run_bytes(args: list[str | Path], *, timeout: float) -> bytes:
    """Run a command and return its raw stdout, raising on failure."""
    command = [str(item) for item in args]
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False
    )
    if result.returncode != 0:
        tail = _text(result.stderr).strip().splitlines()[-5:]
        raise RuntimeError(f"{Path(command[0]).name} failed: {' '.join(tail)}")
    return result.stdout


def _text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.decode("utf-8", errors="replace")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tool_version(name: str, flag: str = "--version") -> str | None:
    found = which(name)
    if not found:
        return None
    ran = run([found, flag], timeout=20)
    if ran.returncode != 0:
        return None
    line = (ran.stdout or ran.stderr).strip().splitlines()
    return line[0].strip() if line else None
