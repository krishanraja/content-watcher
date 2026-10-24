---
repo: krishanraja/video-compression
product: Video Compression Engine
as_of: 2026-10-24
head: a446183
lifecycle: live
production_url: none
state_doc: README.md
history_log: docs/history/LOG.md
truth_files: [docs/NORTH_STAR.md]
authority_order: [docs/NORTH_STAR.md, README.md]
steward: https://github.com/krishanraja/ai-harness/blob/main/docs/steward/RUNBOOK.md
---

# Content Watcher (and the Video Compression Engine): where it is right now

## What it is

Compresses large videos on Krish's machine and cuts the useful clips, with nothing uploaded.

## Who it is for and why it matters for Mindmake

Krish's own recordings, ready for the content engine.

## Where it is right now (as of 2026-10-24)

<!-- north-star-state {"week_of": "2026-10-26", "week_target": 25.0, "current": null, "current_as_of": null, "current_source": null, "urgency": 4, "urgency_reason": "not measured yet"} --> **North Star number: U4, far behind.** Share of the week's raw recordings compressed with their best clips cut, with no manual step: not measured yet, against 25% this week, on the way to 100% by 16 November 2026. A bold swing every day; work that does not move the number waits.

Lifecycle: live. The detail is in `README.md`.

## What changed recently

- 2026-10-24 **Content Watcher, first build** (branch `claude/content-watcher-build`, not merged). A `content_watcher` package beside the compression engine: `content-watch read` turns a video, carousel, image or text post into `read.json` and `read.md` measured on the machine (words, shots, push-ins and pans, screen text, faces, hook, pace, loudness, two chosen frames; no model watches it); `fetch` chains for Instagram and TikTok per the brief (YouTube and LinkedIn provisional); `watch --once`, `doctor`, `config`; a Windows installer that checks first. 52 tests pass, including known-content tests on generated media and fixture tests for every fetcher. Format: `docs/READ_FORMAT.md`; routes it calls: `docs/WATCH_API.md`.

- 2026-10-23 **The North Star now has a number, a weekly ladder and an urgency rating.** Ruling (Krish, 2026-10-23): every repository chases one aggressive number on a weekly ladder, and urgency U1 to U5 sets how hard it pushes. The number is in `docs/NORTH_STAR.md`; contract: ai-harness `contract/north-star-metric.md`.

## What is next and what is waiting on Krish

- **D1 answered** (2026-10-24, "Yes to Drive filing"): fetched media files into his two Drive folders. D2 answered ("Apify with $5 cap"). **Waiting on Krish: D3** (the North Star for the renamed repository).
- **Engine routes: this session builds them** (Krish, 2026-10-24, "you build them") in content-engine from `docs/WATCH_API.md`. Nothing reaches the queue until they merge.
- Checkpoint still open (brief section 10 step 2): read one real saved video from his Inspiration folder and compare its `read.md` token count with the taste ledger's eight 512px frames. Needs the home computer or his go-ahead to read one Drive file.
- Live fetch once per platform on the home computer, with his yes. Then install the scheduled task on both home computers: `powershell -ExecutionPolicy Bypass -File scripts\install-content-watch.ps1 -CheckOnly`, then without `-CheckOnly`; readback is `content-watch doctor` and `Get-ScheduledTask "Mindmake Content Watcher"`.
- YouTube and LinkedIn chains wait for the Inspiration session's verified research run.
- Measure the North Star number and record it on the first line under "Where it is right now".
- North Star check (2026-10-23): holds.

## Read next

- `docs/NORTH_STAR.md`: the North Star, its number and its weekly ladder.
- `README.md`: what this repository is and how it runs.
- `docs/BRIEF.md`: the content-watcher build brief.
- `docs/READ_FORMAT.md`, `docs/WATCH_API.md`: the reading and the routes.

## Do not trust

Nothing at the moment.
