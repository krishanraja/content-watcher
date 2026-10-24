# Content Watcher

Anything Krish points at, a link to a post or a file he drops, becomes a full text reading on his own machine, with no
model watching it. The same repository still holds the video compression engine below; his own recordings need both.

## Content Watcher in one minute

```sh
pip install -e ".[watch]"          # faster-whisper, OpenCV, yt-dlp, gallery-dl
content-watch doctor                # what this machine can and cannot do, naming each missing piece
content-watch read path/to/video.mp4 --out readings      # read.json + read.md, measured locally
content-watch fetch "https://www.tiktok.com/@a/video/1" --out fetched
content-watch watch --once          # claim pasted links, fetch, file, read, report; then read new drops
```

- What a reading holds: [`docs/READ_FORMAT.md`](docs/READ_FORMAT.md).
- How the home computers reach the system: [`docs/WATCH_API.md`](docs/WATCH_API.md).
- The build brief and the decisions only Krish makes: [`docs/BRIEF.md`](docs/BRIEF.md), [`docs/DECISIONS.md`](docs/DECISIONS.md).
- Install on a Windows home computer (checks first, installs nothing if a piece is missing):
  `powershell -ExecutionPolicy Bypass -File scripts\install-content-watch.ps1 -CheckOnly`, then without `-CheckOnly`.

Settings live in `%LOCALAPPDATA%\content-watcher\config.json` (`content-watch config --help`); keys are read from
Windows Credential Manager (`Mindmake/engine-operator-token`, `Mindmake/apify-token`) and never printed. The log there
carries counts and class names only.

---

# Video Compression Engine

Compress large videos locally, estimate the result before a long encode, and optionally let ChatGPT Work review the content and extract useful clips.

No video is uploaded by this engine. The source is preserved. FFmpeg does the media work on the user's machine, while ChatGPT Work can guide the conversation and make purpose-aware cut suggestions from a local review pack.

## Fastest start in ChatGPT Work

There are two supported ways to start.

### With the repository attached

1. Clone this repository.
2. Create a local project in the ChatGPT desktop app with this repository as the primary folder.
3. Add the folder containing the source video as another project folder when it is outside the repository.
4. Start ChatGPT Work and say:

> Need to compress a video

The repository's `AGENTS.md` and `.agents/skills/video-compression` skill are discovered automatically from the primary folder. The agent asks where the video is stored, what it is for, and whether you want suggested cuts. It then probes the file, estimates output size from representative samples, creates an optional review pack, compresses locally, and fully verifies the output.

### With a copy-paste opening prompt

Paste the complete [ChatGPT Work opening prompt](COPY-PASTE-PROMPT.md) into a new task. It contains the setup check, guided interview, autonomous compression workflow, honest media-review rules, output verification, and sanitized session-feedback loop in one reusable prompt.

The source can be supplied as either a cloud-drive share URL or a local file path. A cloud URL requires valid link, signed-in account, or connector permissions. A local path requires a local project or another local execution environment with the containing folder attached or permitted. ChatGPT Work controls the actual file-access approval.

## Simple terminal command

Requirements:

- Python 3.10 or newer
- FFmpeg and ffprobe on `PATH`

Run directly from the cloned repository:

```sh
python -m video_compression
```

The interactive command asks the same three questions and saves the compressed video beside the source in a new folder.

Every ChatGPT Work session can also produce a sanitized local review of problems, workarounds, and outcomes. With the user's opt-in and an authenticated GitHub CLI, the agent can submit that review directly as a labelled issue. Without GitHub access, the same Markdown report is ready to copy and paste. See [the session learning loop](docs/LEARNING.md).

Install the reusable command with pipx:

```sh
pipx install git+https://github.com/krishanraja/video-compression.git
video-compress
```

### Install FFmpeg

Windows:

```powershell
winget install Gyan.FFmpeg
```

macOS:

```sh
brew install ffmpeg
```

Ubuntu or Debian:

```sh
sudo apt-get update
sudo apt-get install ffmpeg
```

## Composable commands

```sh
# Check the machine and test real encoders
python -m video_compression doctor

# Read metadata without changing the file
python -m video_compression probe "/path/to/input.mp4"

# Select a profile and working encoder
python -m video_compression plan "/path/to/input.mp4" --purpose "Drive sharing"

# Encode three representative samples and estimate the final size
python -m video_compression estimate "/path/to/input.mp4" --purpose "Drive sharing"

# Create a proxy, audio copy, contact sheet, and black/silence timeline
python -m video_compression analyze "/path/to/input.mp4" \
  --purpose "Find complete educational clips" \
  --output-dir "/path/to/output/review-pack"

# Compress atomically, then probe and fully decode the result
python -m video_compression compress "/path/to/input.mp4" \
  --purpose "Drive sharing" \
  --output "/path/to/output/compressed.mp4"

# Render purpose-aware segments selected in ChatGPT Work
python -m video_compression cut "/path/to/input.mp4" \
  --segments "/path/to/segments.json" \
  --purpose "Short social clips" \
  --output-dir "/path/to/output/segments"

# Record a problem that the user noticed
python -m video_compression --session-dir "/path/to/session" feedback note \
  --kind problem --message "The estimated size was too optimistic"

# Draft the sanitized end-of-session review
python -m video_compression --session-dir "/path/to/session" feedback draft \
  --output "/path/to/session/session-review.md" \
  --title "Estimate missed on screen recording" \
  --purpose "Email attachment" \
  --outcome "Compressed after lowering the target"
```

On PowerShell, put the command on one line or use PowerShell's backtick continuation instead of the shell backslashes shown above.

## Profiles and encoders

The purpose selects a sensible default profile:

| Purpose | Default | Typical use |
| --- | --- | --- |
| share | HEVC | Drive, messaging, family sharing |
| email | H.264 at 720p | Small, broadly playable attachment |
| universal | H.264 | Maximum playback compatibility |
| social | H.264 at 1080p | Social platform upload |
| web | H.264 fast-start | Website delivery |
| archive | HEVC | Smaller high-quality master |
| editing | High-quality H.264 | Later editing |

The engine tests encoders instead of trusting that a listed hardware encoder works. It prefers NVIDIA NVENC, Intel Quick Sync, or Apple VideoToolbox when available, then falls back to libx264, libx265, SVT-AV1, or libaom.

Use `--codec h264`, `--codec hevc`, or `--codec av1` to override the profile. AV1 is usually slow without recent hardware and is not the safest compatibility default.

Use `--quality high`, `--quality balanced`, or `--quality small`. A hard size cap can be requested with `--target-size-mb`, though content complexity means a small margin should be allowed.

## What "watching" means

The engine does not pretend motion statistics understand meaning. `analyze` creates evidence that a capable host can actually review:

- `review-proxy.mp4` for visual and audio review
- `review-audio.mp3` for audio-first material such as podcasts
- `contact-sheet.jpg` for quick navigation
- `timeline.json` for black and silent ranges
- `metadata.json` for technical facts

The ChatGPT Work skill requires the agent to say what it actually inspected. Suggested clips must be based on spoken or visual content and the user's purpose, not merely scene changes or silence. Accepted suggestions use [the segment schema](docs/segments.schema.json).

## Safety and output guarantees

- The source is never deleted by the engine.
- Output cannot equal the source path.
- Existing outputs are not replaced unless `--overwrite` is explicit.
- FFmpeg writes to a temporary file and the engine moves it into place only after a successful encode.
- Full verification checks streams, duration, size, and a complete decode.
- A JSON verification report is saved beside each compressed full video.

## Development

```sh
python -m unittest discover -s tests -v
```

The test suite includes a real synthetic-video flow when FFmpeg is installed.

Optional GitHub Actions templates for CI and feedback acknowledgement live in `examples/github-workflows`. They can be enabled by a repository owner whose GitHub token has workflow scope.
