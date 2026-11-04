---
repo: krishanraja/content-watcher
product: Content Watcher
as_of: 2026-11-04
head: 802c2e1
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

Its readings feed the content engine, which is a makeyourmindup product, not a Mindmake one (Ruling, Krish, 2026-10-28: "content-engine, which is not a mindmake product, it's a makeyourmindup product"). The heading above is the fleet's own wording, and it changes only through the docs steward.

## Where it is right now (as of 2026-11-04)

<!-- north-star-state {"week_of": "2026-10-26", "week_target": 25.0, "current": null, "current_as_of": null, "current_source": null, "urgency": 4, "urgency_reason": "not measured yet"} --> **North Star number: U4, far behind.** Share of the week's raw recordings compressed with their best clips cut, with no manual step: not measured yet, against 25% this week, on the way to 100% by 16 November 2026. A bold swing every day; work that does not move the number waits.

Lifecycle: beta. Content Watcher is built, merged and installed on both home computers, and links have been followed end to end on both computers since 28 October (below). The Video Compression Engine is published and unchanged since 2026-09-15 (`git log -- video_compression`). The detail is in `README.md`.

- **Merged since 29 October** (`git log`): `content-watch audio` (#23); the one local layout, the taste backstop and the Machine stills sync (W2.11, W3.3, W3.2; #20 to #25); the original-language words for an auto-dubbed YouTube video (#26, #27); and `doctor` proving cobalt can fetch, with gallery-dl 1.32.18 and cobalt's YouTube session generator (#28). Each is in `docs/history/NOW-changes.md`. Not yet run on the home computers: the updater, and the re-read of the Hannah Fry Short that came back in Arabic.
- **Built and on main** (`git log`, `content_watcher/`): the reading engine, the fetch chains for Instagram, TikTok, YouTube and LinkedIn (`docs/FALLBACKS.md`, `content_watcher/fetch/__init__.py`), the watch loop, `doctor`, and `scripts/install-content-watch.ps1`. Merged as #3, #4, #6, #7 and #8; the build branch is gone.
- **Tests** (run 2026-11-04, `python3 -m unittest discover -s tests`, Linux container, no network): 197 tests, all pass, 4 skipped. They use fixtures, fake responses and generated media; none reaches a platform. With OpenCV 5 installed, which pyproject excludes (`<5`), 7 face tests fail because the cascade loads empty; `doctor` does not catch it.
- **Tested live** (`docs/FALLBACKS.md`): from a cloud machine on 2026-10-24, Instagram's embed player on a reel, a three-video carousel and a photo post, and TikWM on a TikTok video and photo post; on Lorimer on 2026-10-28, a YouTube Short through yt-dlp, and three Apify scraper runs plus the snapinsta test (`docs/history/NOW-changes.md`). **Not tested live:** the LinkedIn chain, Tikmate's download and cobalt.
- **Installed on both home computers** (2026-10-24, readback pasted by Krish; not checkable from this repository). On 2026-10-28 a Short reached its Inspiration card on Lorimer, and on Surface a pasted reel was claimed, fetched, read and reported (below).
- **Engine routes** (`docs/WATCH_API.md`): content-engine's `api/watch` and `api/ux-feedback`; Lorimer and Surface called them on 2026-10-28.

## What changed recently

Each change, newest first, is in `docs/history/NOW-changes.md` (moved there verbatim on 2026-10-29). `NOW.md` stays under its byte cap (12,000 bytes, `tests/test_layout.py`).

## What is next and what is waiting on Krish

- Next (2026-11-04): on each home computer, paste `scripts/update-content-watch.ps1` (it upgrades gallery-dl and adds cobalt's YouTube session generator), then run `content-watch doctor` and read the `cobalt` and `gallery-dl` lines (a miss names its class); then re-queue the Hannah Fry Short (wh3D5Zx6Prg) so `watch --once` reads its original English words.
- **D1 answered** (2026-10-24, "Yes to Drive filing"): fetched media files into his two Drive folders. **D2 answered** ("Apify with $5 cap"). Both are in `docs/DECISIONS.md`.
- **Waiting on Krish: D3**, the North Star for the renamed repository. `docs/NORTH_STAR.md` still holds the compression-only wording and number (set 2026-10-18, metric added 2026-10-23, both before the rename); no answer to D3 is in the record. The proposed wording is in `docs/BRIEF.md` section 3. Only Krish changes the North Star.
- **Proved live on 28 October (at `2348567`):** on Surface a pasted Instagram reel, queued again at 08:27:43 UTC, was claimed, fetched, read with its words and reported by 08:29:09, with its one filed copy reused and nothing added to Drive. The YouTube file Krish shared, dropped in Content Inspo at 08:27:29, was read at 08:31:09 (140 s, words heard, 8 shots). Both computers run this head; neither holds a Firefox Instagram session (`session.instagram.none`), so an age-restricted post goes to the paid downloader, through the engine when a machine has no key of its own. content-engine's recordings pass now runs every console task of his with no window (Lorimer 7 of 7; Surface 4, with 3 installed with admin rights waiting on one admin run).
- **Open check:** the first dropped file read on one computer and then skipped on the other (`drop.held` in its counts), which proves the engine's held check from both ends.
- Checkpoint still open (brief section 10 step 2): read one real saved video from his Inspiration folder and compare its `read.md` token count with the taste ledger's eight 512px frames. Needs the home computer or his go-ahead to read one Drive file.
- **W3.2 stills folder** (Krish's default, 2026-10-29): Drive > Ventures > Active Ventures > makeyourmindup > 4 Growth > Machine stills, id `1ryqrwjUloZwlKjn8UroVb6buwKIAPvwf`. A machine whose synced Drive has it files the stills there; inspirationhouse reads it by that id.
- Measure the North Star number and record it on the first line under "Where it is right now".
- North Star check (2026-11-04): holds.

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
- `docs/FETCH_METHODS.md` "Recommended chain" and "Do not build" lists: research of 2026-10-24. Each platform section now opens with a note of the chain the code runs (status note dated 2026-11-04); where they differ, `docs/FALLBACKS.md` and the code win.
- `docs/STATE.md`: the compression engine's state only, not the repository's. The repository's state is this file.
- `COPY-PASTE-PROMPT.md` and `video_compression/feedback.py` still name the old address `krishanraja/video-compression`, which `tests/test_prompt_contract.py` pins. Left as it is until the test and the code change together; GitHub should forward the old address to the new one (not re-checked).
