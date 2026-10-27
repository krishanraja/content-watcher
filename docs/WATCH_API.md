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
"lane", "note", "attempts" }] }`. A request that has failed 3 times is not claimed again until Krish pastes it again.

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

## `POST /api/watch/read`

Body: `{ "machine", "reads": [row, ...] }`: readings of files Krish dropped by hand, with no request. Same upsert as
above. Decision (2026-10-24): a separate route rather than folding into `report`, because a drop has no request id
and the report route's job is moving one request through its states.

## Logs

Neither side logs a URL, caption, transcript, file name or reading text. Counts and class names only.
