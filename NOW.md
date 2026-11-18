---
repo: krishanraja/content-watcher
product: Content Watcher
as_of: 2026-11-15
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

## Where it is right now (as of 2026-11-15)

<!-- north-star-state {"week_of":"2026-11-09","week_target":100,"current":75,"current_as_of":"2026-11-18","current_source":"Control Center content_watch_requests joined to content_reads on read_id: links pasted this ISO week, at least 15 minutes old, read within 15 minutes of the paste, read by Control Center","urgency":2,"urgency_reason":"at 75% of this week's target"} --> **North Star number: U2, behind.** Share of links he pastes that become a card with a full reading within 15 minutes, with no manual step: 75%, against 100% this week. The number leads every session.

Lifecycle: beta. Content Watcher is built, merged and installed on both home computers, and pasted links are followed end to end: 18 of 23 requests in `content_watch_requests` reached `read` between 27 October and 12 November (Supabase, read-only count, 2026-11-14). The Video Compression Engine is published and unchanged since 2026-09-15 (`git log -- video_compression`). The detail is in `README.md`.

- The fold holds NOW.md to its 12,000-byte cap on every push to main, note or none, moving the oldest dated status lines to `docs/history/NOW-changes.md` (ai-harness's `--now-cap`); `tests/test_layout.py` checks `checks.yml` passes the same cap. (2026-11-15)
- Camoufox evaluated as a browser adapter and not adopted, nothing installed (`docs/CAMOUFOX.md`): no miss in the record is one a browser would fix, and its one addition, getting past bot detection, would get round the platforms' stated restrictions. (2026-11-15)
- the branch sweep takes an approved list (branch@sha) on a hand run and deletes each named branch only at that exact commit, skipping and logging anything else; the weekly run is unchanged. Copied from ai-harness's canonical script and workflow. (2026-11-15)
- A weekly branch sweep (`.github/workflows/branch-sweep.yml`, Sunday 03:17 UTC, and by hand) deletes every remote branch whose work is already on main and lists each branch it keeps with why: unmerged work, an open pull request, protected (Ruling, Krish, 2026-11-15). The script is `.github/scripts/branch_sweep.py`, copied unchanged from ai-harness, which holds the canonical copy. (2026-11-15)
- the worker (cloud-vps) is first for every content-watcher task: it claims each pasted link at once and reads every dropped file; the home computers are its 15-minute backup and read no dropped file; YouTube links go to the home computers, since YouTube refuses the worker (content-engine #709 decides it on the server). (2026-11-15)
- Content Watcher also runs on the worker server as machine `cloud-vps` (filing: engine), switched on 2026-11-14 at 21:14 UTC and running every minute like the home task; it backs up the home computers on the board's pasted links and, through a read-only, new-files-only Drive mirror switched on at 21:45 UTC, on drops in Production Inspo and Content Inspo. It holds no Apify key (CONTENT_WATCH_APIFY_VIA_ENGINE=1). The home computers' task is unchanged. Evidence: ai-harness state/vps/MIGRATION-2026-11-14.md. (2026-11-14)
- Krish said yes to D3 (Ruling, Krish, 2026-11-14). `docs/NORTH_STAR.md` holds the new North Star and its number block: the share of links he pastes that become a card with a full reading within 15 minutes, with no manual step, target 100%, baseline 16 of 23 (70%), no deadline set. `docs/DECISIONS.md` records his yes. Control Center reads the number each morning (`READERS['content-watcher']`, control-center #875); this ISO week reads 4 of 4 on time. (2026-11-14)
- D3 answered yes (Ruling, Krish, 2026-11-14): the North Star is now the share of links he pastes that become a card with a full reading within 15 minutes, with no manual step, target 100%, baseline 16 of 23 (70%) (`docs/NORTH_STAR.md`, `docs/DECISIONS.md`). Control Center reads it each morning (`READERS['content-watcher']`); this ISO week reads 4 of 4 on time (Supabase, read-only, 2026-11-14). (2026-11-14)
- `content-watch doctor` proves cobalt fetches a real post (`free_sites.cobalt_probe`: version, one public TikTok, first 64 KB read), every cobalt request sends `localProcessing: disabled`, the installer pins gallery-dl 1.32.18 or later (TikTok 403 fix) and adds cobalt's yt-session-generator for YouTube (merged as #28). ArchiveBox was turned down. The real doctor row has not been seen: the cloud container runs no cobalt. (2026-11-03)
- a YouTube auto-dub no longer gives a wrong-language transcript (merged as #26 and #27): yt-dlp asks for the track marked `original`, captions are chosen by that track's language, and every video reading checks its words' language against its screen text (`content_watcher/read/language.py`), transcribing the file's own audio or withholding the words as `transcript_language_mismatch`. The cause was Short wh3D5Zx6Prg (content_reads d16a3279), read from `ar-orig` captions; its re-read has not run, because YouTube refuses the cloud container. (2026-10-31)
- **Built and on main** (`git log`, `content_watcher/`): the reading engine, the fetch chains for Instagram, TikTok, YouTube and LinkedIn (`docs/FALLBACKS.md`, `content_watcher/fetch/__init__.py`), the watch loop, `doctor`, and `scripts/install-content-watch.ps1`. Merged as #3, #4, #6, #7 and #8; the build branch is gone.
- **Tests** (run 2026-11-14, `python -m unittest discover -s tests`, Linux container): 197 tests, all pass, 4 skipped. They use fixtures, fake responses and generated media; none reaches a platform. On 2026-10-28 the count was 133, and with faster-whisper, OpenCV and tesseract hidden, as on CI, all passed with 5 skipped.
- **Tested live, from a cloud machine on 2026-10-24** (`docs/FALLBACKS.md`): Instagram's embed player on a reel, a three-video carousel and a photo post, with a full fetch and reading of the reel through `content-watch`; TikWM on a TikTok video and photo post. **Not tested live:** the YouTube and LinkedIn chains (built from the research in `docs/FETCH_METHODS.md`, fixture tests only), Tikmate's download, and any Apify run.
- **Installed on both home computers** (2026-10-24, readback pasted by Krish; not checkable from this repository).
- **Engine routes** (`docs/WATCH_API.md`): recorded as merged in content-engine (#161, 2026-10-24). No live call from a home computer has reached them yet. This repository cannot read content-engine, so the merge is taken from the record.

## What changed recently

Each change, newest first, is in `docs/history/NOW-changes.md` (moved there verbatim on 2026-10-29). `NOW.md` stays under its byte cap (12,000 bytes, `tests/test_layout.py`).

## What is next and what is waiting on Krish

- Next (2026-11-15): read pasted Google Drive and Docs links through the engine's own Drive access, the cause of all 5 failures in the record.
- **D1 answered** (2026-10-24, "Yes to Drive filing"): fetched media files into his two Drive folders. **D2 answered** ("Apify with $5 cap"). Both are in `docs/DECISIONS.md`.
- **Proved live on 28 October (head `2348567`):** on Surface a pasted Instagram reel, queued again at 08:27:43 UTC, was claimed, fetched, read with its words and reported by 08:29:09, with its one filed copy reused and nothing added to Drive. The YouTube file Krish shared, dropped in Content Inspo at 08:27:29, was read at 08:31:09 (140 s, words heard, 8 shots). Both computers run this head; neither holds a Firefox Instagram session (`session.instagram.none`), so an age-restricted post goes to the paid downloader, through the engine when a machine has no key of its own. content-engine's recordings pass now runs every console task of his with no window (Lorimer 7 of 7; Surface 4, with 3 installed with admin rights waiting on one admin run).
- Checkpoint still open (brief section 10 step 2): read one real saved video from his Inspiration folder and compare its `read.md` token count with the taste ledger's eight 512px frames. Needs the home computer or his go-ahead to read one Drive file.
- **W3.2 stills folder** (Krish's default, 2026-10-29): Drive > Ventures > Active Ventures > makeyourmindup > 4 Growth > Machine stills, id `1ryqrwjUloZwlKjn8UroVb6buwKIAPvwf`. A machine whose synced Drive has it files the stills there; inspirationhouse reads it by that id.
- Measure the North Star number and record it on the first line under "Where it is right now".
- North Star check (2026-11-15): holds.

## Read next

- `docs/NORTH_STAR.md`: the North Star, its number and its weekly ladder.
- `README.md`: what this repository is and how it runs, for both Content Watcher and the compression engine.
- `docs/DECISIONS.md`: Krish's rulings in his words, D1 to D3.
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
