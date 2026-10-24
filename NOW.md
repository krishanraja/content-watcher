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

- 2026-10-24 **The inspiration folders moved** (Krish: "Can you ensure absolutely everywhere recalibrates to this moving forward first?"). Fetched media now files into Drive > Ventures > Inspiration: Production Inspo or Content Inspo. The installer takes `-ProductionInspo` and `-ContentInspo`. The same correction went to content-engine, Control Center and inspirationhouse (whose video folder ID had gone dead).

- 2026-10-24 **Instagram and YouTube Shorts made reliable** (Krish: "Instagram and YouTube Shorts are the main ones, you need to find a reliable way"). Instagram now starts with its own embed player, which answers logged out and carries the post's data: tested live from a cloud machine on a reel, a three-video carousel and a photo post, and a full fetch and reading through `content-watch`. Licensed-music reels go on to Apify; if everything misses, the cover and caption still make a card. Shorts: the installer starts YouTube's token helper (Docker) and cobalt, and Apify gets a Short at 720p for about $0.02 when YouTube refuses. 78 tests pass.

- 2026-10-24 **Every fallback built** (Krish: "Build all the fallbacks. This needs to be bulletproof."). Each platform now has four to seven ways in, free first, then Apify under the $5 cap, then words alone as a text card: Instaloader for Instagram; TikWM and Tikmate for TikTok (TikWM tested live); an oEmbed check, youtube-transcript-api and Apify transcripts for YouTube; document posts, two Apify actors and Jina Reader for LinkedIn; and an optional cobalt on the home computer for every platform. Video is capped at 720p. PDFs are read page by page. The chains: `docs/FALLBACKS.md`. 71 tests pass; no live run at home yet.

- 2026-10-24 **Fetchers aligned to the verified research** (`docs/FETCH_METHODS.md`, landed on main as #2). Fixed against it: TikTok's 10204 is a blocked IP, not a removed post; an Instagram reel no longer asks Apify for a stored copy (about 12 times the cost); YouTube captions are the language spoken (`.*-orig`), never a machine translation; LinkedIn drops yt-dlp and never files a sign-in page as the post (one `/embed/` retry, then fail); Instagram `/p/` posts try yt-dlp's free carousel mode before Apify; TikTok's Apify run is started and polled, writes no named store, and every file it stores is downloaded; a paid run counts against the $5 cap even when it times out; a failed link reports its last step's class; yt-dlp and gallery-dl run through the pinned Python. Still to build from the spec: LinkedIn document posts (PDF and page images), the LinkedIn Apify steps, YouTube's oEmbed and transcript-api steps, and Instaloader.

- 2026-10-24 **Content Watcher, first build** (branch `claude/content-watcher-build`, not merged). A `content_watcher` package beside the compression engine: `content-watch read` turns a video, carousel, image or text post into `read.json` and `read.md` measured on the machine (words, shots, push-ins and pans, screen text, faces, hook, pace, loudness, two chosen frames; no model watches it); `fetch` chains for Instagram and TikTok per the brief (YouTube and LinkedIn provisional); `watch --once`, `doctor`, `config`; a Windows installer that checks first. 52 tests pass, including known-content tests on generated media and fixture tests for every fetcher. Format: `docs/READ_FORMAT.md`; routes it calls: `docs/WATCH_API.md`.

- 2026-10-23 **The North Star now has a number, a weekly ladder and an urgency rating.** Ruling (Krish, 2026-10-23): every repository chases one aggressive number on a weekly ladder, and urgency U1 to U5 sets how hard it pushes. The number is in `docs/NORTH_STAR.md`; contract: ai-harness `contract/north-star-metric.md`.

## What is next and what is waiting on Krish

- **D1 answered** (2026-10-24, "Yes to Drive filing"): fetched media files into his two Drive folders. D2 answered ("Apify with $5 cap"). **Waiting on Krish: D3** (the North Star for the renamed repository).
- **Engine routes merged** (content-engine #161, 2026-10-24, Krish: "Merge it all."). No live call has reached them yet; the first comes from a home computer once the watcher is installed.
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
