# 2026-10-29: `content-watch audio`

Status: added `content-watch audio <video>` (`content_watcher/read/audio.py` `extract`). It writes a video's audio track to its own file with ffmpeg alone, so it needs no model and no tokens. The default, `--format copy`, copies the audio stream untouched into the matching container (.m4a, .opus, .mp3, .ogg, .flac, else .mka). `--format wav` and `--format mp3` re-encode it, and `--format wav --speech` gives 16 kHz mono for Whisper. It never overwrites an existing output and never touches the source, and it checks the output's duration against the source's. Tests: `tests/test_cw_audio.py`.

Next step: when the compression engine's clip cutting needs an audio-only input, use `extract` rather than decoding again.

North Star check: does not move the compression share directly. It gives the clip and transcription steps a fast, lossless audio input.
