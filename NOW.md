---
repo: krishanraja/content-watcher
product: Content Watcher
as_of: 2026-10-27
head: 622001d
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

Content Watcher turns a link Krish pastes (a TikTok, Instagram, YouTube or LinkedIn post) or a file he drops into a full text reading on his own machine, with no model watching it. This repository, `krishanraja/content-watcher` (renamed from `video-compression` on 2026-10-24), holds two things: Content Watcher itself (package `content_watcher`, command `content-watch` with `read`, `fetch`, `watch --once`, `doctor` and `config`, plus a Windows installer), and the Video Compression Engine it grew from (package `video_compression`, command `video-compress`), which compresses large videos locally and cuts the useful clips with nothing uploaded.

## Who it is for and why it matters for Mindmake

Krish, and the systems that learn his taste. Posts he saves all day reach the content engine, the taste ledger and Control Center's Inspiration board as text measured on his own machine, so no Claude session spends his subscription watching frames (`docs/BRIEF.md` section 1). His own raw recordings get the same reading and have their best clips cut, ready for the content engine.

## Where it is right now (as of 2026-10-27)

<!-- north-star-state {"week_of": "2026-10-26", "week_target": 25.0, "current": null, "current_as_of": null, "current_source": null, "urgency": 4, "urgency_reason": "not measured yet"} --> **North Star number: U4, far behind.** Share of the week's raw recordings compressed with their best clips cut, with no manual step: not measured yet, against 25% this week, on the way to 100% by 16 November 2026. A bold swing every day; work that does not move the number waits.

Lifecycle: beta. Content Watcher is built, merged and installed on both home computers, but no pasted link has been followed end to end yet. The Video Compression Engine is published and unchanged since 2026-09-15 (`git log -- video_compression`). The detail is in `README.md`.

- **Built and on main** (`git log`, `content_watcher/`): the reading engine, the fetch chains for Instagram, TikTok, YouTube and LinkedIn (`docs/FALLBACKS.md`, `content_watcher/fetch/__init__.py`), the watch loop, `doctor`, and `scripts/install-content-watch.ps1`. Merged as #3, #4, #6, #7 and #8; the build branch is gone.
- **Tests** (run 2026-10-27, `python3 -m unittest discover -s tests -v`, Linux container with FFmpeg): 80 tests, all pass, 2 skipped because this container has no tesseract (`test_known_screen_text`) and no faster-whisper tiny model with espeak (`test_known_words`). 72 cover Content Watcher and 8 the compression engine. They use fixtures, fake responses and generated media; none reaches a platform.
- **Tested live, from a cloud machine on 2026-10-24** (`docs/FALLBACKS.md`): Instagram's embed player on a reel, a three-video carousel and a photo post, with a full fetch and reading of the reel through `content-watch`; TikWM on a TikTok video and photo post. **Not tested live:** the YouTube and LinkedIn chains (built from the research in `docs/FETCH_METHODS.md`, fixture tests only), Tikmate's download, and any Apify run.
- **Installed on both home computers** (2026-10-24, readback pasted by Krish; not checkable from this repository). No live end-to-end run is recorded: a link pasted on the Inspiration board, fetched, filed and read back on the engine.
- **Engine routes** (`docs/WATCH_API.md`): recorded as merged in content-engine (#161, 2026-10-24). No live call from a home computer has reached them yet. This repository cannot read content-engine, so the merge is taken from the record.

## What changed recently

- 2026-10-27 **Docs reconciled to the code.** NOW.md called the first Content Watcher build "not merged" on a branch that merged as #3 on 2026-10-24, still listed LinkedIn and YouTube steps as provisional or "to build" after #4 built them, and named the repository `video-compression`. A cold reader would also have found no `docs/history/LOG.md`, which this file names. `docs/BRIEF.md` and `docs/FETCH_METHODS.md` now say which of their recommendations the code no longer follows; `docs/STATE.md` is scoped to the compression engine. The count of tests is 80, not 52 or 78.
- 2026-10-24 **Installed on both home computers** (readback pasted by Krish). Scheduled task `Mindmake Content Watcher` Ready on each; `doctor` all ok for Python, FFmpeg, faster-whisper, yt-dlp, curl_cffi, the bgutil token helper, cobalt (Docker), Deno, Instaloader, the engine key, Apify (cap $5, $0 spent) and both Drive folders. Tesseract and Poppler were then installed on the Surface; `tools.which` finds them off PATH since #7, because the Windows installers do not put them on PATH.
- 2026-10-24 **The inspiration folders moved** (Krish: "Can you ensure absolutely everywhere recalibrates to this moving forward first?"). Fetched media now files into Drive > Ventures > Inspiration: Production Inspo or Content Inspo (#6). The installer takes `-ProductionInspo` and `-ContentInspo`. The same correction went to content-engine, Control Center and inspirationhouse (whose video folder ID had gone dead).
- 2026-10-24 **Instagram and YouTube Shorts made reliable** (Krish: "Instagram and YouTube Shorts are the main ones, you need to find a reliable way"; #4). Instagram now starts with its own embed player, which answers logged out and carries the post's data. Licensed-music reels go on to Apify; if everything misses, the cover and caption still make a card. Shorts: the installer starts YouTube's token helper (Docker) and cobalt, and Apify gets a Short at 720p for about $0.02 when YouTube refuses.
- 2026-10-24 **Every fallback built** (Krish: "Build all the fallbacks. This needs to be bulletproof."; #4). Each platform now has four to seven ways in, free first, then Apify under the $5 cap, then words alone as a text card: Instaloader for Instagram; TikWM and Tikmate for TikTok; an oEmbed check, youtube-transcript-api and Apify transcripts for YouTube; document posts, two Apify actors and Jina Reader for LinkedIn; and an optional cobalt on the home computer for every platform. Video is capped at 720p. PDFs are read page by page. The chains: `docs/FALLBACKS.md`.
- 2026-10-24 **Fetchers aligned to the verified research** (`docs/FETCH_METHODS.md`, landed on main as #2). Fixed against it: TikTok's 10204 is a blocked IP, not a removed post; an Instagram reel no longer asks Apify for a stored copy (about 12 times the cost); YouTube captions are the language spoken (`.*-orig`), never a machine translation; LinkedIn drops yt-dlp and never files a sign-in page as the post (one `/embed/` retry, then fail); Instagram `/p/` posts try yt-dlp's free carousel mode before Apify; TikTok's Apify run is started and polled, writes no named store, and every file it stores is downloaded; a paid run counts against the $5 cap even when it times out; a failed link reports its last step's class; yt-dlp and gallery-dl run through the pinned Python. The steps it listed as still to build (LinkedIn documents and Apify steps, YouTube's oEmbed and transcript steps, Instaloader) were built the same day in #4.
- 2026-10-24 **Content Watcher, first build** (landed on main as #3, commit 99b250a). A `content_watcher` package beside the compression engine: `content-watch read` turns a video, carousel, image or text post into `read.json` and `read.md` measured on the machine (words, shots, push-ins and pans, screen text, faces, hook, pace, loudness, two chosen frames; no model watches it); `fetch`, `watch --once`, `doctor`, `config`; a Windows installer that checks first. Known-content tests on generated media and fixture tests for every fetcher. Format: `docs/READ_FORMAT.md`; routes it calls: `docs/WATCH_API.md`.
- 2026-10-23 **The North Star now has a number, a weekly ladder and an urgency rating.** Ruling (Krish, 2026-10-23): every repository chases one aggressive number on a weekly ladder, and urgency U1 to U5 sets how hard it pushes. The number is in `docs/NORTH_STAR.md`; contract: ai-harness `contract/north-star-metric.md`.

## What is next and what is waiting on Krish

- **D1 answered** (2026-10-24, "Yes to Drive filing"): fetched media files into his two Drive folders. **D2 answered** ("Apify with $5 cap"). Both are in `docs/DECISIONS.md`.
- **Waiting on Krish: D3**, the North Star for the renamed repository. `docs/NORTH_STAR.md` still holds the compression-only wording and number (set 2026-10-18, metric added 2026-10-23, both before the rename); no answer to D3 is in the record. The proposed wording is in `docs/BRIEF.md` section 3. Only Krish changes the North Star.
- **Next action: the live test.** One Instagram reel and one YouTube Short pasted on the Inspiration board, read back on the engine.
- Checkpoint still open (brief section 10 step 2): read one real saved video from his Inspiration folder and compare its `read.md` token count with the taste ledger's eight 512px frames. Needs the home computer or his go-ahead to read one Drive file.
- Measure the North Star number and record it on the first line under "Where it is right now".
- North Star check (2026-10-27): recalibration proposed. The North Star still names only the compression engine, and this repository now also holds Content Watcher (D3 in `docs/DECISIONS.md`; the wording proposed to Krish is in `docs/BRIEF.md` section 3).

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
