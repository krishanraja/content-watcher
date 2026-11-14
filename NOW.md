---
repo: krishanraja/content-watcher
product: Content Watcher
as_of: 2026-11-14
head: ef7b665
lifecycle: beta
production_url: none
state_doc: README.md
history_log: docs/history/LOG.md
truth_files: [docs/NORTH_STAR.md]
authority_order: [docs/NORTH_STAR.md, README.md]
steward: https://github.com/krishanraja/ai-harness/blob/main/docs/steward/RUNBOOK.md
---

# Content Watcher (with the Video Compression Engine): where it is right now

## What it is

Content Watcher turns a link Krish pastes (a TikTok, Instagram, YouTube or LinkedIn post) or a file he drops into a full text reading on his own machine, with no model watching it. This repository, `krishanraja/content-watcher` (renamed from `video-compression` on 2026-10-24), holds two things: Content Watcher itself (package `content_watcher`, command `content-watch` with `read`, `fetch`, `timeline`, `audio`, `watch --once`, `doctor` and `config`, plus a Windows installer), and the Video Compression Engine it grew from (package `video_compression`, command `video-compress`), which compresses large videos locally and cuts the useful clips with nothing uploaded.

## Who it is for and why it matters for Mindmake

Krish, and the systems that learn his taste. Posts he saves all day reach the content engine, the taste ledger and Control Center's Inspiration board as text measured on his own machine, so no Claude session spends his subscription watching frames (`docs/BRIEF.md` section 1). His own raw recordings get the same reading and have their best clips cut, ready for the content engine.

Its readings feed the content engine, which is a makeyourmindup product, not a Mindmake one (Ruling, Krish, 2026-10-28: "content-engine, which is not a mindmake product, it's a makeyourmindup product"). The heading above is the fleet's own wording, and it changes only through the docs steward.

## Where it is right now (as of 2026-11-14)

<!-- north-star-state {"week_of": "2026-10-26", "week_target": 25.0, "current": null, "current_as_of": null, "current_source": null, "urgency": 4, "urgency_reason": "not measured yet"} --> **North Star number: U4, far behind.** Share of the week's raw recordings compressed with their best clips cut, with no manual step: not measured yet, against 25% this week, on the way to 100% by 16 November 2026. A bold swing every day; work that does not move the number waits.

Lifecycle: beta. Content Watcher is built, merged and installed on both home computers, and pasted links are followed end to end: 18 of 23 requests in `content_watch_requests` reached `read` between 27 October and 12 November (Supabase, read-only count, 2026-11-14). The Video Compression Engine is published and unchanged since 2026-09-15 (`git log -- video_compression`). The detail is in `README.md`.

- D3 is prepared as a yes-or-no question in `docs/DECISIONS.md`, with its number's source (`content_watch_requests` joined to `content_reads` on `read_id`, Mindmaker OS), how Control Center would measure it, and a baseline of 16 of 23 pasted links read within 15 minutes (70%, to 2026-11-14); `docs/FALLBACKS.md` now lists the signed-in yt-dlp step the code runs for TikTok video and YouTube. (2026-11-14)
- `content-watch doctor` proves cobalt fetches a real post (`free_sites.cobalt_probe`: version, one public TikTok, first 64 KB read), every cobalt request sends `localProcessing: disabled`, the installer pins gallery-dl 1.32.18 or later (TikTok 403 fix) and adds cobalt's yt-session-generator for YouTube (merged as #28). ArchiveBox was turned down. The real doctor row has not been seen: the cloud container runs no cobalt. (2026-11-03)
- a YouTube auto-dub no longer gives a wrong-language transcript (merged as #26 and #27): yt-dlp asks for the track marked `original`, captions are chosen by that track's language, and every video reading checks its words' language against its screen text (`content_watcher/read/language.py`), transcribing the file's own audio or withholding the words as `transcript_language_mismatch`. The cause was Short wh3D5Zx6Prg (content_reads d16a3279), read from `ar-orig` captions; its re-read has not run, because YouTube refuses the cloud container. (2026-10-31)
- W2.11 (#20) reads the local layout from `config/studio.json` `local_roots` with a CI path guard and caps NOW.md at 12,000 bytes; W3.3 (#21) keeps a SessionEnd taste backstop in `.scratch/taste/backstop.jsonl` only; W3.2 (#22) files at most 8 curated stills a reading to a machine-owned folder, carried in the row as `machine_stills`. (2026-10-29)
- `content-watch audio <video>` (`content_watcher/read/audio.py` `extract`) writes a video's audio track to its own file with ffmpeg alone, no model and no tokens: `--format copy` by default, `wav` or `mp3` on request, `--format wav --speech` for 16 kHz mono; it never overwrites an output or touches the source, and checks the output's duration (`tests/test_cw_audio.py`). (2026-10-29)
- **Built and on main** (`git log`, `content_watcher/`): the reading engine, the fetch chains for Instagram, TikTok, YouTube and LinkedIn (`docs/FALLBACKS.md`, `content_watcher/fetch/__init__.py`), the watch loop, `doctor`, and `scripts/install-content-watch.ps1`. Merged as #3, #4, #6, #7 and #8; the build branch is gone.
- **Tests** (run 2026-11-14, `python -m unittest discover -s tests`, Linux container): 197 tests, all pass, 4 skipped. They use fixtures, fake responses and generated media; none reaches a platform. On 2026-10-28 the count was 133, and with faster-whisper, OpenCV and tesseract hidden, as on CI, all passed with 5 skipped.
- **Tested live, from a cloud machine on 2026-10-24** (`docs/FALLBACKS.md`): Instagram's embed player on a reel, a three-video carousel and a photo post, with a full fetch and reading of the reel through `content-watch`; TikWM on a TikTok video and photo post. **Not tested live:** the YouTube and LinkedIn chains (built from the research in `docs/FETCH_METHODS.md`, fixture tests only), Tikmate's download, and any Apify run.
- **Installed on both home computers** (2026-10-24, readback pasted by Krish; not checkable from this repository).
- **Engine routes** (`docs/WATCH_API.md`): recorded as merged in content-engine (#161, 2026-10-24). No live call from a home computer has reached them yet. This repository cannot read content-engine, so the merge is taken from the record.

## What changed recently

Each change, newest first, is in `docs/history/NOW-changes.md` (moved there verbatim on 2026-10-29). `NOW.md` stays under its byte cap (12,000 bytes, `tests/test_layout.py`).

## What is next and what is waiting on Krish

- Next (2026-11-14): Krish answers D3 yes or no.
- **D1 answered** (2026-10-24, "Yes to Drive filing"): fetched media files into his two Drive folders. **D2 answered** ("Apify with $5 cap"). Both are in `docs/DECISIONS.md`.
- **Waiting on Krish: D3**, the North Star for the renamed repository. `docs/NORTH_STAR.md` still holds the compression-only wording and number (set 2026-10-18, metric added 2026-10-23, both before the rename); no answer to D3 is in the record. The proposed wording is in `docs/BRIEF.md` section 3. Only Krish changes the North Star.
- **Proved live on 28 October (head `2348567`):** on Surface a pasted Instagram reel, queued again at 08:27:43 UTC, was claimed, fetched, read with its words and reported by 08:29:09, with its one filed copy reused and nothing added to Drive. The YouTube file Krish shared, dropped in Content Inspo at 08:27:29, was read at 08:31:09 (140 s, words heard, 8 shots). Both computers run this head; neither holds a Firefox Instagram session (`session.instagram.none`), so an age-restricted post goes to the paid downloader, through the engine when a machine has no key of its own. content-engine's recordings pass now runs every console task of his with no window (Lorimer 7 of 7; Surface 4, with 3 installed with admin rights waiting on one admin run).
- Checkpoint still open (brief section 10 step 2): read one real saved video from his Inspiration folder and compare its `read.md` token count with the taste ledger's eight 512px frames. Needs the home computer or his go-ahead to read one Drive file.
- **W3.2 stills folder** (Krish's default, 2026-10-29): Drive > Ventures > Active Ventures > makeyourmindup > 4 Growth > Machine stills, id `1ryqrwjUloZwlKjn8UroVb6buwKIAPvwf`. A machine whose synced Drive has it files the stills there; inspirationhouse reads it by that id.
- Measure the North Star number and record it on the first line under "Where it is right now".
- North Star check (2026-11-14): recalibration proposed. The compression share has no source and its deadline is 16 November; the proposed replacement is measurable today (`docs/DECISIONS.md`, D3).

## Read next

- `docs/NORTH_STAR.md`: the North Star, its number and its weekly ladder.
- `README.md`: what this repository is and how it runs, for both Content Watcher and the compression engine.
- `docs/DECISIONS.md`: Krish's rulings in his words, and the open decision D3.
- `docs/FALLBACKS.md`: the chains the code runs, and what was tested live.
- `docs/READ_FORMAT.md`, `docs/WATCH_API.md`: the reading and the routes.
- `docs/FETCH_METHODS.md`: the 2026-10-24 research behind the chains, with prices and open questions.
- `docs/BRIEF.md`: the original build brief, with a status note at its top.
- `docs/STATE.md`: the compression engine's own state record.

## Do not trust

- `docs/BRIEF.md` section 6 (the per-platform methods) and sections 7 to 10 (what to build and in what order): written 2026-10-24 before the build and before Krish asked for every fallback. Superseded the same day by `docs/FETCH_METHODS.md` and then by `docs/FALLBACKS.md`, which is what the code runs. The file carries a status note.
- `docs/FETCH_METHODS.md` "Recommended chain" and "Do not build" lists: research of 2026-10-24. The code follows `docs/FALLBACKS.md` instead where they differ (Instagram's embed player first; Instaloader, cobalt, TikWM and Tikmate included). The file carries a status note.
- `docs/STATE.md`: the compression engine's state only, not the repository's. The repository's state is this file.
- `COPY-PASTE-PROMPT.md` and `video_compression/feedback.py` still name the old address `krishanraja/video-compression`, which `tests/test_prompt_contract.py` pins. Left as it is until the test and the code change together; GitHub should forward the old address to the new one (not re-checked).
