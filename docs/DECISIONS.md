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
  Answer: waiting. Until he answers, `filing` is `local` (on the home computer only) and nothing writes into his Drive.
- **D2. How Instagram and LinkedIn are fetched** (his signed-in Firefox session, or Apify with a standing monthly cap).
  To ask after D1. Until then Apify is off (`apify_enabled: false`) and no cookies are used.
- **D3. The North Star for the renamed repository.** To ask after D2.

## 2026-10-24: A separate route for hand-dropped readings

Decision: readings of files with no request go through `POST /api/watch/read`, not folded into `report`.

Why: a drop has no request id, and `report`'s job is moving one request through its states. Spec in
`docs/WATCH_API.md`.

## 2026-10-24: The general failure class is `other`

Decision: a request's `status_class` is one of `login_wall`, `not_found`, `too_big`, `blocked`, `timeout`, `other`,
the classes Control Center puts into words. The finer reason (for example `spend_not_approved`,
`empty_media_response`) stays in the local log as a count, never on the request. Told the Inspiration session.
