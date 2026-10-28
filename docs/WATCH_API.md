# The watch API (content-engine routes this machine calls)

Status: Current as designed on 2026-10-24; the routes are built in krishanraja/content-engine `apps/control-plane`
and recorded as merged there (content-engine #161, 2026-10-24, per `NOW.md`; not re-read from this repository). No
live call from a home computer has reached them yet. The client side is `content_watcher/engine.py`. The home
computers hold only the engine key and reach the system through these three routes. Every call is `POST`, JSON, with
`Authorization: Bearer <engine key>`.

## `POST /api/watch/claim`

Body: `{ "machine": "HOME-PC-1", "limit": 3 }`

Atomically claims up to `limit` requests that are `queued`, or `claimed` more than 30 minutes ago (stale), raising
`attempts` and setting `claimed_by` and `claimed_at`. Returns `{ "requests": [{ "id", "url", "url_key", "platform",
"lane", "note", "attempts", "media" }] }`. `media` is what an earlier try of the same request already filed (or null):
a file of the same name in the same folder is reused rather than filed again, and its reading takes that file's
hash, because a platform's CDN can hand a second fetch different bytes (2026-10-28). A request that has failed 3 times is not claimed again until Krish pastes it again.

## `POST /api/watch/report`

Body: `{ "id", "machine", "status", "status_class"?, "shape"?, "media"?, "reads"? }`

- `status: "filed"` with `shape` and `media`: one entry per filed file, in post order:
  `{ "name", "sha256", "mime", "bytes", "folder" }`, `folder` being `video_inspiration` (Drive > Ventures > Inspiration > Production Inspo, `1QxrzxISYFXq0er0DG0XSapm7qhvuRmh-`) or `cold_ideas` (Content Inspo, `1FNztJOU82M8zb6IIbUAbvuI6Kr0pF5Hu`). The values are the old folder names, kept because the database and the taste ledger carry them.
- `status: "read"` with `media` and `reads`: one `content_reads` row per file
  `{ "sha256", "source_url", "platform", "shape", "engine_rev", "read", "read_md" }`. The route upserts each row by
  `sha256` (a newer `engine_rev` replaces an older one, an older one never replaces a newer one) and sets the
  request's `read_id` to the first file's reading.
- `status: "failed"` with `status_class`: one of `login_wall`, `not_found`, `too_big`, `blocked`, `timeout`, `other`.
  Below 3 attempts the request goes back to `queued` (claim cleared); at 3 it stays `failed`.

The machine only reports for a request it holds (`claimed_by` = its `machine`); the route refuses others.

## The cloud backup's routes (2026-10-28)

Krish, 2026-10-28: "yes build the cloud backup". The same package runs on GitHub's machine as `cloud-gh`
(content-engine `.github/workflows/watch-cloud.yml`), with `filing: "engine"` because it has no synced Drive folder.

- `GET /api/watch/claim?machine=NAME`: `{ "waiting": n }`, how many requests this machine could claim now, claiming
  none. A machine whose name starts with `cloud` may claim a request only once it has waited 15 minutes, so the home
  computers get it first.
- `POST /api/watch/upload` with `{ "id", "machine", "folder", "name", "sha256", "bytes", "mime" }`, only from a
  `cloud` machine holding the request's claim. The engine checks the folder for the name and its `_v2`..`_v9` names
  first: the same sha256 answers `{ "exists": true, "name" }`; otherwise it opens a resumable Drive upload session as
  Krish in that folder under the first free name and answers `{ "exists": false, "name", "upload_url" }`. The machine
  `PUT`s the bytes to `upload_url` with no key, and Google answers the new file's `sha256Checksum`; a different hash
  fails the request as a filing error. Add only, as on the home computers (`filing.py`).
- `POST /api/watch/apify` with `{ "id", "machine", "actor", "input" }`, only from a `cloud` machine holding the
  request's claim: the engine runs one of this package's own Apify actors with its own key, on an input that names
  that post, under a hard charge cap, and answers `{ "items" }` (at most 5). Used when `CONTENT_WATCH_APIFY_VIA_ENGINE=1`, and on a home computer whenever it has no Apify key of its
  own or its key is refused, so no machine needs a key (`apify.via_engine`).
- `GET /api/watch/upload`: whether the engine can add a file to each folder, and the scope it would use
  (`drive.file`, then `drive`) or Google's reason for each refusal. It writes nothing.

## `POST /api/watch/read`

Body: `{ "machine", "reads": [row, ...] }`: readings of files Krish dropped by hand, with no request. Same upsert as
above. Decision (2026-10-24): a separate route rather than folding into `report`, because a drop has no request id
and the report route's job is moving one request through its states.

The same route with `{ "machine", "check": [sha256, ...], "engine_rev" }` (at most 50) writes nothing and answers
`{ "held": { sha256: engine_rev } }` for the media it holds a reading of at the same or a newer revision, or one
made from a link. The drop reader asks it
before reading: the folders also hold what the other machine and the cloud filed from links, which they read already
(`watch.unheld_drops`; 28 October 2026). An engine that cannot answer leaves the files to be read as before.

## Feedback videos (2026-10-28)

Krish, 2026-10-28: "somewhere in my control centre where I can specifically add a feedback video that's not
inspiration ... It would trigger only this one part of the system", with the result as an email holding "a neat and
tidy Claude Code prompt" and links to the feedback file and the Drive folder of stills. A queue of its own
(content-engine migration `20261116090000_ux_feedback_recordings.sql`, `apps/control-plane/api/ux-feedback/`): it
never touches `content_watch_requests`, `content_reads` or the Inspiration folders. The client is
`content_watcher/feedback.py`, one recording a run, after the Inspiration queue, on a home computer only and only
when the run has 12 minutes left; trouble with these routes is counted under `feedback.` and never stops the drop
reader.

- `POST /api/ux-feedback/claim` with `{ "machine" }`: `{ "recording": { "id", "name", "note", "mime", "bytes",
  "attempts", "download_url" } }` or `null`. The download URL is signed for an hour and takes no key. A machine whose
  name starts with `cloud` is refused. A claim is stale after an hour; the third stale claim fails as `timeout`.
- `POST /api/ux-feedback/drive` with `{ "id", "machine", "files": [{ "name", "mime", "bytes" }] }` (`image/jpeg`
  stills, `text/markdown` for `feedback.md`): the engine makes the recording's folder `<day> <name>` inside
  "UX Feedback" once and opens a resumable session per file, as Krish; the machine `PUT`s each file and Google answers
  its id. Add only.
- `POST /api/ux-feedback/report` with `{ "id", "machine", "status": "done", "feedback_file_id", "summary" }` or
  `{ ..., "status": "failed", "status_class" }`. Done sends Krish one email: the links and a Claude Code prompt
  listing the moments he flagged. Below 3 attempts a failure goes back to the queue.

The machine downloads the recording, runs `content-watch timeline --profile ux` on it, deletes its own copy (the
recording stays in the private bucket), uploads the stills, then `feedback.md`, whose every line links its still in
Drive, and reports.

## Logs

Neither side logs a URL, caption, transcript, file name or reading text. Counts and class names only.
