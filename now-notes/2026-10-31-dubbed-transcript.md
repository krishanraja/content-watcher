# 2026-10-31: wrong-language transcript from a YouTube auto-dub

Status:
- Cause: Hannah Fry's Short wh3D5Zx6Prg (content_reads d16a3279) was read from captions, not Whisper. YouTube auto-dubs the video and machine-captions each dub; yt-dlp labels every machine caption `<lang>-orig`, so `--sub-langs ".*-orig"` brought back `ar-orig` beside `en-orig`, and the picker took the first by name: Arabic.
- Fixed on branch `claude/original-language-transcript` (not merged): the format string asks for the audio track yt-dlp marks `original` and fetches once more with its format id if a dub was still chosen (`dubbed_audio_only` when no original exists); captions are chosen by the original track's language, never by name; every video reading compares its words' language with its screen text's (`content_watcher/read/language.py`, no model), transcribes the file's own audio when captions do not match, and withholds words that still do not match as `transcript_language_mismatch`. 193 tests pass.
- Not done: the re-read of wh3D5Zx6Prg. YouTube refuses the cloud container (bot check on yt-dlp, IpBlocked on youtube-transcript-api), so it has to run on a home computer after this branch is merged and installed there. `inspiration_items` aae54ef9 still holds the Arabic transcript. ENGINE_REV is unchanged on purpose: a bump makes every drop read again.

Next step: Krish merges the branch and updates the install on both home computers, then the link is re-queued through the engine so `watch --once` reads it again; check `content_reads.read->'words'->'language_check'` reads `match: true` and the transcript starts "All the neurons".

North Star check: does not move the compression share. It protects the content engine's study of Hannah Fry's scripts (the simplicity standard), a reading-quality fix outside the number.
