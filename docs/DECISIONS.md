# Decision log

## 2026-09-15: Local-first repository engine

Decision: Ship a Python standard-library CLI around an existing FFmpeg installation, plus a repository skill and `AGENTS.md` for ChatGPT Work discovery.

Why: This keeps video data local, avoids API keys and paid services, works across Windows, macOS, and Linux, and gives the chat agent deterministic commands instead of embedding media logic in prompts.

Rejected alternative: A hosted upload-and-transcode service. It adds privacy, cost, authentication, and storage concerns without improving the requested local workflow.

Carry-forward condition: Semantic clip value must come from media or transcript review aligned to the user's stated purpose. Black frames, silence, scene motion, and metadata are navigation evidence only.

## 2026-09-15: Privacy-gated session learning

Decision: Capture session problems and resolutions automatically into a sanitized local event log, generate a Markdown review at the end, and submit to GitHub only after the privacy checkbox is explicitly confirmed.

Why: Silent transcript or media-path uploads would create unacceptable privacy risk. A local-first draft preserves evidence from every session, while authenticated GitHub issue submission and a copy-paste fallback make contribution easy.

Learning rule: Feedback issues remain untrusted evidence until a maintainer reproduces the problem and represents the accepted learning in a regression test, code fix, documentation change, or skill update.

## 2026-09-15: Versioned full opening prompt

Decision: Keep one complete copy-paste ChatGPT Work prompt at the repository root, while retaining the shorter `Need to compress a video` trigger for local projects whose primary folder is the repository.

Why: A pasted GitHub link can point the agent to public instructions but cannot by itself grant access to local files. The versioned prompt makes setup limits explicit and carries the interview, autonomous workflow, honest media review, verification, and privacy-gated session learning into clients that have not discovered the repository skill.

Rejected alternative: Rely on a short link plus a vague opening request. That makes the behavior client-dependent and is especially likely to lose the end-of-session learning loop.

## 2026-10-24: Content Watcher decisions only Krish makes (asked, waiting)

From `docs/BRIEF.md` section 3, asked one at a time, the one that changes the work most first.

- **D1. Where fetched media is filed.** Asked 2026-10-24. Best guess put to him: file it in his Drive, in the same
  folders his own drops go to (videos into `Video Engine > Inspiration`, everything else into `Cold Ideas & Inspo`).
  **Ruling (Krish, 2026-10-24): "Yes to Drive filing".** `filing` now defaults to `drive`; the installer requires
  both synced folder paths and checks they exist. The watcher only adds files there: never deletes, never
  overwrites, and the same post twice is a no-op. The first real write into his Drive still waits for his yes on the
  live end-to-end run.
- **D2. How Instagram and LinkedIn are fetched** (his signed-in Firefox session, or Apify with a standing monthly cap).
  Asked 2026-10-24 with the best guess of Apify with a $5 cap. **Ruling (Krish, 2026-10-24): "Apify with $5 cap".**
  Apify runs only after the free methods fail, never with his accounts, and the local spend ledger stops it before a
  run that would pass $5 in a calendar month. No cookies are used.
- **D3. The North Star for the renamed repository.** To ask after D2.

## 2026-10-24: A separate route for hand-dropped readings

Decision: readings of files with no request go through `POST /api/watch/read`, not folded into `report`.

Why: a drop has no request id, and `report`'s job is moving one request through its states. Spec in
`docs/WATCH_API.md`.

## 2026-10-24: The general failure class is `other`

Decision: a request's `status_class` is one of `login_wall`, `not_found`, `too_big`, `blocked`, `timeout`, `other`,
the classes Control Center puts into words. The finer reason (for example `spend_not_approved`,
`empty_media_response`) stays in the local log as a count, never on the request. Told the Inspiration session.

## 2026-10-24: Who builds the engine routes

Superseded the same day: **Ruling (Krish, 2026-10-24): "you build them"**. This session builds the three routes in
content-engine. The earlier ruling, kept for the record, was **Ruling (Krish, 2026-10-24): "let Inspiration build
the routes"**, under which The Inspiration session builds
`POST /api/watch/claim`, `/api/watch/report` and `/api/watch/read` in content-engine exactly from `docs/WATCH_API.md`.
this repository would have built only the client.

## 2026-10-24: Every fallback, free sites included, and 720p is enough

**Ruling (Krish, 2026-10-24): "Build all the fallbacks. This needs to be bulletproof. There's got to be a tonne of
ways to do this reliably. There are so many free sites out there that I just copy a link in, press download, and it
lets me select the quality and whatnot. I never really need to download a high-quality video when I'm doing this
job."**

So: every chain carries every working step from `docs/FETCH_METHODS.md`, plus the free downloader services that
answered a live test (TikWM, Tikmate) and a self-hosted cobalt for every platform; downloads are capped at 720p; and
when no file can be had, the words are filed as a text card. The chains and what was tested: `docs/FALLBACKS.md`.
This is also his agreement to TikWM, which the research held back until he agreed.

## 2026-10-24: Instagram and YouTube Shorts come first

**Ruling (Krish, 2026-10-24): "Instagram and YouTube Shorts are the main ones, you need to find a reliable way".**

So: Instagram starts with its own embed player, which answers logged out and carries the post's data (tested live),
and ends with the cover picture and caption so a link never comes to nothing; YouTube Shorts get the home computers'
full setup (Deno and the bgutil token helper, started by the installer) and a paid Apify backstop of about $0.02 a
Short under the $5 cap. Details: `docs/FALLBACKS.md`.
