# Camoufox as a browser adapter: evaluated, not adopted

Status: Current, 2026-11-15. Decision record for this repository's fetch chains. Nothing was installed or built. The
chains the code runs are still `docs/FALLBACKS.md` and `content_watcher/fetch/__init__.py` (`_methods`).

The question: would Camoufox (the anti-detect Firefox, <https://github.com/daijro/camoufox>), or jo-inc's server that
wraps it (<https://github.com/jo-inc/camoufox-browser>, which also answers as `jo-inc/camofox-browser`), make the watcher
more reliable where the browser it already has falls short, without getting round any site's access controls or
restrictions?

**The call: no.** No adapter was built and no new browser framework was installed. Three findings decide it, each on
its own.

1. **No failure in the record is one a browser would fix.** Every Instagram and YouTube link Krish has pasted became a
   reading; the only failures are private Google Drive and Docs files.
2. **Camoufox's one addition over the Chromium the watcher already uses is getting past bot detection.** On the
   platforms in scope that would mean getting round restrictions the sites state, which this work must not do.
3. **It would add a third browser, a second runtime and an upstream with a year-long maintenance gap**, for a fallback
   that already works and runs rarely.

## 1. What the live record shows

Read-only query of Control Center's `content_watch_requests` joined to `content_reads` on `read_id` (project Mindmaker
OS, 2026-11-15). All 23 requests ever made, 27 October to 12 November 2026:

| Platform | Requests | Became a reading | Within 15 minutes | Failed |
|---|---|---|---|---|
| Instagram (7 videos, 2 carousels) | 9 | 9 | 8 | 0 |
| YouTube | 9 | 9 | 8 | 0 |
| Google Drive and Docs links (platform `web`) | 5 | 0 | 0 | 5 (`other`, 3 attempts each) |
| TikTok | 0 | | | |
| LinkedIn | 0 | | | |

- **The two late readings** were both pasted on 27 October, before the pipeline was proved live on 28 October
  (`NOW.md`). One is the age-restricted carousel `/p/DfAY9PWFuEX` (`docs/FALLBACKS.md`): only a signed-in account or
  the approved paid downloader can see it. An age gate that needs a sign-in is an access control, and no logged-out
  browser should get past it. The other is a YouTube Short, read about 12 hours after it was pasted. The record does
  not show why it was late, and nothing in it points at a page that needed a browser to render.
- **The five failures** are private files in Krish's own Drive (two `drive.google.com/file` links, three
  `docs.google.com/document` links). The watcher treats them as ordinary web pages (`urls.py` gives them the platform
  `web`) and sends them to yt-dlp and cobalt, which cannot open them. A browser cannot open them either without his
  Google sign-in. The fix is the access the engine already has: it adds files to his Drive as him
  (`docs/WATCH_API.md`, `POST /api/watch/upload`). That is a separate piece of work, and it is the real gap in the
  North Star number today (the five are 5 of the 7 misses in its 16 of 23 baseline).
- **No TikTok or LinkedIn link has ever been pasted**, so there is no evidence of any kind for those chains.
- **Which step got each post is not stored.** The readings do not record the fetch method, and the per-step counts
  (`method.<step>.<outcome>`, `watch.py`) live in each machine's local log, which a cloud session cannot read (the
  worker is behind SSH). How often the existing headless-browser step is reached in practice is therefore unknown.

## 2. Why Camoufox conflicts with the brief

**What the two projects say they are for** (each quote checked against its source on 2026-11-15: jo-inc's
`README.md` on its `master` branch, upstream's `README.md`, camoufox.com and PyPI):

- jo-inc's README calls it an "Anti-detection browser server for AI agents" and says it "bypasses Google, Cloudflare,
  and most bot detection".
- Upstream calls itself "an open source anti-detect browser built for webscraping & AI agents" that gives each launch
  "a fresh, internally consistent device identity" (README), and its site says it changes fingerprint data "at the
  C++ implementation level".

**What the three platforms in scope say** (their `robots.txt`, read 2026-11-15):

- Instagram: `User-agent: *` then `Disallow: /`.
- LinkedIn: `User-agent: *` then `Disallow: /`, under the notice "The use of robots or other automated means to
  access LinkedIn without the express permission of LinkedIn is strictly prohibited."
- TikTok: disallows every path to a list of named agents that includes `ClaudeBot`, `Claude-User` and
  `anthropic-ai`, and for everyone else disallows `/embed/v2`, `/embed/@` and `/embed/curated`, among other paths.

The only pages where Camoufox would do better than Chromium are pages a platform refuses to an automated browser it
can recognise. Spoofing a device identity to get such a page anyway gets round the platform's restriction. That is the one thing this
work must not do. Every other rendering need, a page that only shows its data after JavaScript runs, is met by the
Chromium the watcher already drives through Playwright.

When a step is refused today (a challenge page, `ip_blocked`, a login wall), the watcher records it as `blocked` or
`login_wall` and moves on to the next step Krish has already approved: his own signed-in Firefox session on a home
computer, the Apify steps under his $5 a month cap (D2), or the words alone (`docs/FALLBACKS.md`). That is the right
shape, and this evaluation leaves it as it is.

**No live comparison was run against the platforms.** Their `robots.txt` rules leave no page on Instagram, LinkedIn
or TikTok that this agent was permitted to fetch for a test, and the brief allowed only permitted pages. The
comparison below uses the repository's own fixture, served on the test machine itself.

## 3. What the existing browser step costs (measured)

The watcher already has one headless-browser step: `instagram_embed._browser`, used only when a plain request for
Instagram's embed page comes back without the post's data. It launches Playwright's Chromium (or the one
`CONTENT_WATCH_CHROMIUM` names), opens the embed page, returns the HTML and closes the browser.

Measured on 2026-11-15 in the cloud container (4 vCPU, 16 GB), Python 3.13, Playwright 1.56.0 for Python, Chromium
build 1243. The function under test was called seven times against `tests/fixtures/ig_embed_video.html`, served on
127.0.0.1, so no outside site was contacted. Memory is the proportional set size (PSS) summed over every process in
the tree (Python, Playwright's driver and each Chromium process), sampled every 20 ms.

| Path | Median time | Peak memory (PSS) | CPU time | Post data found |
|---|---|---|---|---|
| Plain request (`_plain`), run once | 0.008 s | inside the Python process (23 MB before any launch) | negligible | 1 of 1 |
| Headless Chromium (`_browser`) | 0.59 s (first launch 1.24 s) | 389 MB median, 398 MB highest | 0.66 s median | 7 of 7 |

The measuring script is not committed. It served the fixture on 127.0.0.1, pointed `instagram_embed.EMBED` at that
server, and sampled `/proc/<pid>/smaps_rollup` for every process under the Python process while
`instagram_embed._browser` ran.

On the worker (4 vCPU, 8 GB) one launch at a time is affordable: about 5% of its memory for under a second. Nothing
in the record shows this step being short of anything Camoufox would add.

## 4. What Camoufox would cost if it were added

| Item | Camoufox (upstream, Python) | jo-inc server |
|---|---|---|
| How it runs | `from camoufox.sync_api import Camoufox` returns a normal Playwright `Browser`, so `_browser`'s page code would not change | A Node.js REST server (default port 9377) or Docker; no Python API, so `_browser` would become HTTP calls |
| Install | `pip install -U "camoufox[geoip]"`, then `camoufox fetch` for the browser | `npx @askjo/camofox-browser`, which downloads Camoufox on first run |
| Browser on disk | Not stated; the install guide's example output shows a 1.2 GB browsers folder | "~300MB" download, its README says |
| Memory | "<200MB footprint" (vendor claim, no method given); not measured here | "~40MB when idle" for the server alone, plus the browser |
| CPU | No published figures | No published figures |
| Platforms | Linux; `headless="virtual"` needs Xvfb. Running the browser on Windows (both home computers) is not stated | Docker on x86_64 and aarch64; Windows through Docker Desktop with WSL2 |
| Licence | MPL-2.0 browser, MIT Python package | MIT |
| Maintenance | "There has been a year gap in maintenance due to a personal situation" (camoufox.com/stealth); "This project is under development. It may not be suitable for stable production use." (README). Latest package 0.5.9, 1 November 2026 (PyPI) | Activity not re-checked here (GitHub's page refused this session). Crash and hang reports go to GitHub Issues by default; `CAMOFOX_CRASH_REPORT_ENABLED=false` turns them off |

**Upkeep it would add:** a pinned Camoufox package and browser build to update beside yt-dlp, gallery-dl and
Playwright's Chromium; a browser that upstream says "has gone down in performance due to the base Firefox version and
newly discovered fingerprint inconsistencies";
for the jo-inc server, a second runtime (Node.js) and a long-running service on every machine; and a third browser
(Chromium for the embed step, Firefox for his session cookies, Camoufox) to keep working on two Windows computers and
one Linux server.

**If Krish ever decides to add it**, which is his call, the contained shape is one environment variable,
`CONTENT_WATCH_BROWSER=chromium|camoufox`, read inside `instagram_embed._browser` only, defaulting to Chromium.
Because Camoufox hands back a Playwright `Browser`, the step's name, its order in `_methods`, the engine's three
attempts, the sha256 de-duplication, the `Post` shape and the failure classes would all stay as they are. Rollback
would be unsetting the variable, then `camoufox remove` and `pip uninstall camoufox`. That decision would need a new
ruling, because the brief for this evaluation rules out the one job the tool exists to do.

## 5. What would change the call

- **For any headless browser** (Chromium included): if a machine's per-step counts show `instagram_embed` missing the
  post's data on public posts, and the embed page answers an ordinary browser, the repair belongs in the existing
  Chromium step, not in a new browser.
- **For Camoufox specifically:** only a change to the rule against getting round site restrictions, or a site giving
  written permission for automated access that its bot detection still refuses. Neither exists today.

## Changed files and rollback

- Added `docs/CAMOUFOX.md` (this file).
- `docs/FALLBACKS.md`: one line pointing here from the headless-browser note.
- No code, configuration, dependency, schedule or data contract changed. Rollback is `git revert` of the commit.

## Open items found on the way

- **Google Drive and Docs links** (section 1): the five private-file failures are the gap worth closing next, through
  the engine's own Drive access rather than any browser.
- **Whether the worker has Chromium installed** for the embed step is not checkable from a cloud session. `_browser`
  returns an empty page on any browser error, and `content-watch doctor` has no browser row, so a machine without
  Chromium would skip the step without saying so. Reading `content-watch doctor` and the local log on the worker
  would settle it.
- **The `NOW.md` byte cap test fails on `main`** (12,013 bytes against 12,000, `tests/test_layout.py`), from the
  closeout fold before this work. It is for the docs steward to trim, as the test's message says.
