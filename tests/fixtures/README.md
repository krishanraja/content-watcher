# Fixtures

Recorded response shapes for the fetchers. They are built from the documented fields of each source as of 2026-10-24
(yt-dlp info.json, gallery-dl metadata, TikTok's rehydration JSON, the Apify actors' dataset items, LinkedIn's
JSON-LD). Identifiers, names and text are invented. When a live run on the home computer shows a field moved, record
the real (redacted) response here and the test follows it.

`ytdlp_youtube_dubbed.info.json` is a YouTube Short with auto-dubbed audio tracks: one original English track and four
dubs, in the shape yt-dlp 2026.10.21 gives them (`language`, `language_preference` 10 for the original, the track's
display name in `format_note`). Its `requested_formats` names the Arabic dub, the case the watcher must refuse
(31 October 2026, wh3D5Zx6Prg).
