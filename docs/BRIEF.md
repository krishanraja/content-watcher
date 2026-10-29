# Content Watcher: the build brief

Written 2026-10-24 by the Claude Code session that built the Inspiration board's kinds, for the session Krish starts in
this repository. It is the brief for the whole build. Read it all before you write anything, then read the files it
names. Where it says "check", check: this was true when it was written and parts of the system move every day.

> **Status, 2026-10-27.** This brief is the starting point of the build, not its current state. Read it for the reasons;
> read `NOW.md` for where things are. What has changed since it was written on 2026-10-24:
>
> - The build is merged and installed on both home computers (`NOW.md`). `docs/FETCH_METHODS.md` replaced section 6
>   the same day, and the chains the code actually runs are in `docs/FALLBACKS.md`. Where section 6 differs from
>   either, they win. Examples: the code asks Apify for no stored reel copy (section 6, Instagram step 2, shows
>   `includeDownloadedVideo: true`), and it uses Instagram's embed player, cobalt, TikWM and Tikmate, which section 6
>   leaves out or says not to use. Krish asked for every fallback on 2026-10-24 (`docs/DECISIONS.md`).
> - D1 and D2 (section 3) are answered: "Yes to Drive filing" and "Apify with $5 cap" (`docs/DECISIONS.md`). D3 is
>   still open: no answer is in the record, and `docs/NORTH_STAR.md` still carries the compression-only wording.
> - The inspiration folders in D1 and section 4 are now Drive > Ventures > Inspiration: Production Inspo (was Video
>   Engine > Inspiration) and Content Inspo (was Cold Ideas & Inspo).
> - Section 7.4 asked for two engine routes; the build uses three (`docs/WATCH_API.md`).
> - Section 8 describes what other sessions were building. Control Center's link box and inspirationhouse's reading of
>   `content_reads` now exist in those repositories (control-center `docs/app/inspiration/README.md`, inspirationhouse
>   `README.md`); read those for their state.
> - 2026-10-28: the watcher serves makeyourmindup, whose content engine is not a Mindmake product (Ruling, Krish,
>   2026-10-28: "content-engine, which is not a mindmake product, it's a makeyourmindup product"). The `Mindmake/`
>   Credential Manager key in section 4 and the scheduled task's name stay, because both home computers find them by
>   name (`NOW.md`).
> - Section 10: steps 3 and 5 are built in this repository (the fetchers, the scheduled task and `doctor`), and step 4
>   is recorded as merged in content-engine (#161). Still open: the step 2 checkpoint, the live fetch per platform, and
>   the step 6 end-to-end run.

## 1. What Krish asked for

His words, 2026-10-24:

> "Do you recommend a separate video reading engine that runs on a machine and can parse videos and provide more
> granular text-based analysis of the video? I'd love to be able to just copy in Instagram and YouTube links and
> automate, and it would be able to automatically handle those too. I have a GitHub repository called
> video-compression, which we could expand into being that if you think that this would be a valuable standalone
> repository. The last thing I want is to burn all my AI Anthropic subscription tokens on watching a video."

Then, after the recommendation (section 3), he renamed this repository from video-compression to content-watcher and
said:

> "load in a brief inside the content-watcher repository ... to build everything out in full, including all the ways
> that we can get TikTok, Instagram, and YouTube videos, as well as Instagram carousels and LinkedIn posts. Bear in
> mind that if we're going to build this, I'm going to need somewhere really quick and easy to put links into, and I
> can't do that directly into Google Drive. I wonder if the control center is going to need a little upgrade on the
> inspiration board where I can chuck in a link really easily, and it fires the content-watcher too. After that, the
> inspiration house ingests the content-watchers output and then focuses on what it needs to, which is understanding
> what it is and asking me why i like it, and ensuring every part of my content engine and control center etc know
> what inspires me from a content or production POV."

Why he is saying it (read these before you design anything):

- He saves things he admires all day, on his phone, from Instagram, TikTok, YouTube and LinkedIn. Today a thing only
  reaches the system if he downloads it and drops the file into a Google Drive folder. That is too slow to do in the
  moment, so most of what inspires him never arrives.
- Watching a video with a model is expensive. Today the taste ledger sends eight frames of every video to Claude, about
  5,000 tokens of pictures each time, and any Claude session that looks at frames or contact sheets spends his
  subscription. Most of what matters about a video (what is said and when, the cuts, the zooms, the words on screen,
  how big the face is, the hook) can be measured on his own machine for nothing, as text.
- What he wants out of it is not the files. It is that every part of his system knows what inspires him, from a
  content point of view (topics, takes, structure, hooks) and a production point of view (pace, framing, editing,
  graphics, clarity), so the work it makes for him gets closer to that without him repeating himself.

## 2. The outcome

Done means, observably:

1. He pastes a link to a post (a TikTok, an Instagram reel or carousel, a YouTube video or Short, a LinkedIn post) into
   one box on Control Center's Inspiration board, from his phone, in under five seconds, and nothing else.
2. Within about ten minutes, without him or any session doing anything, the post's media is filed where his own drops
   go, a full text reading of it is stored, and it is a card on the Inspiration board that knows what kind of thing it
   is and asks him only that kind's question.
3. No model was used to watch it. The reading is measured on his machine. Claude, wherever it meets the post later,
   reads the text, plus at most one or two chosen frames.
4. Every file he still drops by hand gets the same reading, so there is one way a piece of media becomes text.
5. A failure says which class it is (no cookies, login wall, not found, too big, blocked, timeout) on the card, never
   silently.

## 3. Decisions only Krish makes (ask these first, one at a time, best guess first)

Ask each in a plain message, the one that changes the work most first, with your best guess, and the next only after he
answers (his standing rule, content-engine `config/learnings.json`, `one-question-at-a-time`). Record each answer in
`docs/DECISIONS.md` with his exact words, and as `Ruling (Krish, YYYY-MM-DD): ...` in the commit that acts on it.

**D1. Where fetched media is filed.** The watcher runs on his home computers, which see his Google Drive as a synced
folder (`H:\My Drive\...`). The recommendation: it saves each fetched video into `makeyourmindup > Video Engine >
Inspiration` and everything else (carousels, images, a LinkedIn post as text) into `Cold Ideas & Inspo`, exactly where
his own drops go, so the card appears through the path that already works (the taste ledger lists both folders every
morning), "Open in Drive" works, and the style study's library lane picks the videos up. This is a new writer into his
Drive. content-engine's rule is that agents never write into his Drive except the library sync's folders
(content-engine `docs/DRIVE.md`, `AGENTS.md`), so it needs his explicit yes. The alternative is to keep the media on the
home computer only and make cards from the database without a Drive file; it changes the card, the tagger and "Open in
Drive", and no other session could reach the media.

**D2. How Instagram and LinkedIn are fetched.** Both refuse anonymous downloads now. The choice is his own signed-in
browser session on the home computer (free; Instagram or LinkedIn could flag the account) or a paid scraping actor on
Apify, which he already pays for (a small cost per post; his accounts are never used). The recommendation and the full
list of ways per platform are in section 6. If he chooses Apify, ask for a standing monthly cap: his rule is that
anything that spends needs his approval, so a standing yes with a cap is what lets it run unattended.

**D3. The North Star.** `docs/NORTH_STAR.md` is about compressing his raw recordings and cutting the best clips. The
rename says the purpose has grown. Propose, and let him word it: "Anything Krish points at, a link or a file, becomes a
full text reading on his own machine and a card that asks why he likes it, with no model watching it", with the number
"share of links he pastes that become a card with a full reading within 15 minutes, with no manual step", target 100%.
Only he changes it. Keep the compression engine working either way: his own recordings still need it, and they need the
same reading (to cut the best clips you need to know what is said where).

## 4. The system today

Read these; they are the facts the build stands on.

| Part | Where | What it does |
|---|---|---|
| Inspiration board | Control Center (`krishanraja/control-center`), `src/components/inspiration/InspirationPage.tsx`, `api/inspiration.ts`, doc `docs/app/inspiration/README.md` | One card per thing he saved. Each card says its kind and asks only its kind's question: a video "the script, the narrative or the production style", an image "the clarity", a feed nothing, a research corpus which piece it is for. His answers are written by `POST /api/inspiration`. |
| Taste ledger | `krishanraja/inspirationhouse` (TypeScript; GitHub Actions `taste-daily`, `taste-weekly`, `taste-harness`, dispatched by Control Center's crons) | Lists the two Drive folders, makes a card per file (`inspiration_items`), tags it (kind, facets, guesses), watches videos today itself (`src/tag/watch.ts`: eight frames and `scripts/transcribe.py`), turns his answers into evidence, distils weekly taste claims he approves, and opens a pull request on `krishanraja/ai-harness` with the approved rules for the voice and design skills. |
| Content engine | `krishanraja/content-engine` | Owns the database DDL (`supabase/migrations/`). Its Sunday plan (`.agents/skills/plan-week`, step 0) reads routed cards, feed posts, opinions and corpora; `make-piece` reads a piece's corpus; `docs/STYLE_REFERENCES.md` studies style cards with `scripts/quick-edit/references.py study` (shots, cuts a minute, zooms, words, loudness, a contact sheet). Its API (`apps/control-plane`, called with `scripts/engine.py`) is how the home computers reach the system. |
| Home computers | Two Windows machines, always on; content-engine `scripts/install-recordings-upload.ps1` is the pattern | A scheduled task on both; whichever is online does the work; the engine key is in Windows Credential Manager (`Mindmake/engine-operator-token`), read by `scripts/engine.py`, never printed; files are deduped by sha256; Python is pinned (`npm run bootstrap:python`); ffmpeg is on the PATH. |
| Drive | content-engine `docs/DRIVE.md` | `Video Engine > Inspiration` is bound by path (never move or rename). `Cold Ideas & Inspo` is the strategy folder (its Drive id is `1FNztJOU82M8zb6IIbUAbvuI6Kr0pF5Hu` in inspirationhouse `src/config.ts`; find its synced path on the machine, never guess it). |

Lessons already paid for (do not pay for them again):

- faster-whisper 1.1.1 imports `requests` without declaring it, and every faster-whisper release calls
  `av.open(metadata_errors=...)`, which current PyAV refuses. Both made every transcription come back empty with no
  error. Decode audio with ffmpeg into float32 samples and hand faster-whisper the array (inspirationhouse
  `scripts/transcribe.py`, pinned `faster-whisper==1.2.1`). Always report whether words were heard: `words`, `silent`,
  or `failed` with a class.
- A model's structured answer can run past a limit the API never enforced; the SDK then throws and the item is lost.
  inspirationhouse `src/repair.ts` repairs overruns. If this repository calls a model at all, do the same.
- Logs that leave the machine (GitHub Actions, anything public) carry counts and fixed class names only, never a
  transcript, a caption, a file name or model text.

## 5. The contract (already live)

Applied to the Mindmaker OS database on 2026-10-24 from content-engine
`supabase/migrations/20261109090000_content_watch.sql`. Read the file; the summary:

- `content_watch_requests`: one row per pasted link. `url`, `url_key` (normalised, unique, so the same post pasted
  twice is one request), `platform` (instagram, tiktok, youtube, linkedin, x, threads, facebook, web), `lane`
  (production, strategy, or null to choose by shape), `note` (his own words if he typed any; they are his), `status`
  (queued, claimed, filed, read, failed), `status_class` (a class, never a message), `attempts`, `claimed_by`,
  `claimed_at`, `shape` (video, carousel, image, text, document), `media` (one entry per filed file: name, sha256,
  mime, bytes, folder), `read_id`, `item_id` (the card it became). Only `requested_by = 'Krish'`.
- `content_reads`: one text reading per piece of media, keyed by the file's `sha256` (for a text-only post, the sha256
  of the text as filed). `source_url`, `platform` (or `own` for his own recordings), `shape`, `engine_rev`, `read`
  (everything measured, as JSON), `read_md` (the same as plain text, at most 40,000 characters). It is the one reading
  of a piece of media whatever brought it in.
- Both are readable and writable only by the server's role. The home computers do not hold a database key.

Who writes what:

| Write | By |
|---|---|
| A request (`status` queued, `url`, `url_key`, `platform`, `lane`, `note`) | Control Center, when he pastes (being built by the Inspiration session, section 8) |
| Claim, filing, read, failure | content-watcher, through two content-engine API routes this build adds (section 7.4) |
| `item_id`, and the card's reading | the taste ledger, when it sees the filed media (being built by the Inspiration session) |

If you find the contract wrong, change it with a new content-engine migration, say why in its header, and tell the
Inspiration work (its owner is named in content-engine `NOW.md`).

## 6. Every way to get each kind of post

State of this section: the full, verified methods for all five kinds of post are in
[`docs/FETCH_METHODS.md`](FETCH_METHODS.md) (2026-10-24: five researchers, each checked by a skeptic, then checked twice
more against the raw research). Where this section and that file differ, that file wins. What follows is the short
version; YouTube and LinkedIn are now verified there too.

Rules for every platform:

- Normalise the link first: follow share and short links (instagram.com/share/..., vm.tiktok.com, vt.tiktok.com,
  tiktok.com/t, youtu.be, lnkd.in) to the canonical post URL and drop tracking parameters (igsh, si, utm_*). That
  canonical form is `url_key`.
- Keep the tool versions fresh: these platforms break the open tools every few weeks and the fixes ship fast. Install
  yt-dlp 2026.10.21 by hand, never through its self-updater (its release notes warn old executables are open to a
  man-in-the-middle attack), update through pip from there, and let `doctor` report the versions
  (`docs/FETCH_METHODS.md`, "Across all five").
- On Windows, browser cookies come from Firefox (`--cookies-from-browser firefox:<profile>`). Chrome's cookies cannot
  be read since Chrome 127's app-bound encryption (yt-dlp issue #10927, still open).
- Never put a session cookie for any platform in GitHub Actions. If Actions ever runs a fetch, it starts at the Apify
  step.
- Every automated method below breaks the platform's terms (Instagram's Terms of Use, TikTok's US Terms section 3.4,
  YouTube's Terms). Private study lowers the practical exposure; it does not make it allowed. That is why D2 is his.
- Download any media URL an actor returns at once: Instagram's and TikTok's CDN links expire.

### Instagram: reels and video posts

On the home computer, in this order:

1. **yt-dlp, logged out, with browser impersonation.** `yt-dlp -o "%(id)s.%(ext)s" --write-info-json
   --write-thumbnail <url>`, version 2026.10.21 or later (the Windows `yt-dlp.exe` includes curl_cffi; elsewhere
   `pip install "yt-dlp[default,curl-cffi]"`). Free, no account, so no ban risk. Gets the video, the thumbnail and an
   info.json with the caption, author, date and counts. It broke in June 2026 ("Instagram sent an empty media
   response", issue #17074) and was rebuilt around impersonation on 2026-06-28; quiet since July.
2. **Apify, when yt-dlp fails** (empty media response, a login redirect, "Restricted Video"). `apify/instagram-reel-scraper`
   for /reel/ links, input `{"username": ["<url>"], "includeDownloadedVideo": true}`, about $0.0033 a reel at his
   tier; or `apify/instagram-scraper` with `{"directUrls": ["<url>"], "resultsType": "posts", "resultsLimit": 1}`,
   about $0.0023 a result. An Apify token only; his Instagram account is never used. Its transcript add-on costs
   $0.041 a started minute: never use it, transcribe locally.
3. **Only if he accepts the risk:** yt-dlp or gallery-dl with cookies from a second Instagram account kept in its own
   Firefox profile, never his main account.
4. **Instaloader** (`instaloader -- -<SHORTCODE>`) as a last open resort; it is the shakiest now (429s and GraphQL
   errors through September and October 2026).
5. **Text only, when no media can be had:** Firecrawl's provider `oriane`, capability `instagram/post-lookup` (20 to
   40 credits, only for posts already in its index; empty results are free).

Do not use: a plain Firecrawl page scrape (instagram.com is refused, tested 2026-10-24), oEmbed (its terms forbid
keeping the metadata and it carries no media since 2025-11-03), or the Graph API (Business and Creator authors only,
no lookup by URL, no media for licensed-audio reels).

### Instagram: carousels and single images

1. **Apify** `apify/instagram-scraper` (resultsType posts, resultsLimit 1) or `apify/instagram-post-scraper`
   (`dataDetailLevel: "detailedData"`, about $0.0023 a post): `childPosts` holds every slide's `displayUrl` and
   `videoUrl` in order, plus the caption, author, date and counts. Download every slide at once.
2. **gallery-dl** with cookies (`gallery-dl --cookies-from-browser firefox:<profile> --write-metadata <url>`, version
   1.32.17 or later): every image and video in the post at full size. It needs a session in practice, so it carries
   the account risk of D2. Instagram changes forced eight gallery-dl releases between 2026-09-12 and 2026-10-17.
3. Instaloader, as above.

yt-dlp is for video, not image carousels.

### TikTok: videos and photo posts (slideshows)

On the home computer:

1. **Resolve the link**, and treat a `/photo/` path as a photo post.
2. **A video: yt-dlp first.** `yt-dlp --write-info-json --write-subs --sub-langs all --write-thumbnail -o
   "%(id)s.%(ext)s" <url>`, version 2026.10.21, with curl_cffi pinned at 0.16.0 (a newer one is blocked, yt-dlp
   issue #17604, open on 2026-09-25). Free, no login, the richest metadata, and TikTok's own subtitles when a post
   has them. It breaks every few weeks and is fixed fast.
3. **A photo post, or a silent video file: gallery-dl** (`gallery-dl --write-metadata -o audio=true -o covers=true
   <url>`, 1.32.17 or later): every slide image, the post's audio and the caption. yt-dlp's maintainers send photo
   posts here.
4. **If either fails** (403, a challenge page, "Unexpected response"): Apify `clockworks/tiktok-video-scraper` with
   `{"postURLs": [url], "shouldDownloadVideos": true, "shouldDownloadSlideshowImages": true, "shouldDownloadCovers":
   true, "downloadSubtitlesOptions": "DOWNLOAD_SUBTITLES", "videoKvStoreIdOrName": "content-watcher"}`, about $0.003
   a post at his tier, no TikTok login, 99.6% of runs succeeded over the 30 days to 2026-10-24.
5. Comments only if wanted: `clockworks/tiktok-scraper` with `commentsPerPost` ($0.001 a comment). Neither open tool
   reads TikTok comments.
6. A login-walled post only: yt-dlp with Firefox cookies, and the account risk is his to accept.

A free fallback that was tested on 2026-10-24 from a cloud address and worked for a video and a photo post: fetch the
post page with a browser User-Agent and read the JSON in `<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">`
(`__DEFAULT_SCOPE__['webapp.video-detail'].itemInfo.itemStruct`: caption, author, date, counts, the play address and
the photo post's images). Treat it as a fallback; TikTok can serve a challenge at any time.

Do not use: Firecrawl (refuses tiktok.com), oEmbed (embed only, no caption now, and being deprecated), the Display API
(his own videos only), the Research API (not eligible), TikTokApi or cobalt (older and broken for some in 2026).

### YouTube: videos and Shorts, and LinkedIn posts

Verified on 2026-10-24; the chains, commands, prices and open questions are in `docs/FETCH_METHODS.md` ("YouTube:
videos and Shorts" and "LinkedIn posts"). In short: YouTube is done on the home computer (yt-dlp with Deno and the
bgutil PO token provider, captions first, oEmbed for the metadata), because YouTube blocks data-centre addresses.
LinkedIn's public posts load in full for a guest (22 of 22 guest reads returned the post on 2026-10-24), with Apify as
the fallback and his own session only for posts behind a login.

A LinkedIn post is filed as a Markdown file of its text (with the author, the date and the link) in `Cold Ideas &
Inspo`, plus its media beside it: a document post's pages as a carousel, a video as a video.

## 7. What this repository builds

### 7.1 The shape

A Python package beside the compression engine (keep `video_compression` and its tests green; add `content_watcher`),
with one command, `content-watch`:

- `content-watch fetch <url>`: fetch one post into a local folder (the chain in section 6), printing what it got.
- `content-watch read <file-or-folder>`: read media into `read.json` and `read.md` (7.3), printing the path.
- `content-watch watch --once`: claim queued requests, fetch, file, read, report; then the same for new files in the
  two inspiration folders that have no reading yet. This is what the scheduled task runs.
- `content-watch doctor`: say what this machine can and cannot do (ffmpeg, the pinned Python and faster-whisper, OCR,
  yt-dlp version, a JavaScript runtime for YouTube, each platform's cookies or Apify token, the engine key, the two
  folders), naming each missing piece.

Standard library first, as the compression engine is; every outside tool optional and reported by `doctor` when absent.
Every outside call has a timeout. Nothing it fetches is ever uploaded anywhere except the filing in D1 and the reading
in `content_reads`.

### 7.2 Fetching

One fetcher per platform behind one interface, each returning the same normalised post: platform, url, post id,
author, posted date, caption or text, counts where offered, and the media files in order. Try the methods in the order
section 6 recommends, stop at the first that works, and record which one did (as a class). Fixture-based tests for each
fetcher (recorded responses, never a live call in CI). A live end-to-end check on the home computer, with his yes, once
per platform.

### 7.3 Reading (the heart of it, no model)

For a video, measured on the machine:

- the words with timings (faster-whisper, the approach in section 4), or a platform's own captions when they exist
  (YouTube's are free and better than a transcription);
- every shot: cuts, shot lengths, cuts a minute (content-engine `references.py` already does this; reuse its method);
- push-ins, pull-outs and pans;
- the words on screen per shot (OCR): captions, titles, numbers, lower thirds;
- faces: whether one is on screen, how big, where the eyes sit; the share of the video on a face versus cutaways;
- the hook: the first three seconds of words, screen text and cuts;
- pace: words a minute, pauses; loudness; speech versus music;
- one or two chosen frames (the hook frame and the frame with the most screen text), saved beside the reading, for
  the rare reader that needs to see.

For a carousel or an image: each slide in order with its text (OCR), how much text, how the slide is laid out (one
number, a chart, a list, a face), the colours, and the caption. For a text post (LinkedIn): the text, the author, the
date, and any attached document's pages read as a carousel.

Write `read.json` (the shape documented in a new `docs/READ_FORMAT.md`, versioned by `engine_rev`) and `read.md`
(plain text a model or a session reads instead of frames), and send both to `content_reads` through the engine API.
Read each sha256 once; a newer `engine_rev` may read again.

### 7.4 The queue and the two engine routes

The home computers reach the system only through the content engine's API with the engine key, as the recordings
upload does. Add two routes to content-engine `apps/control-plane` (its rules: `guardEngine`, never `preamble`; tests;
`npm run verify`; regenerate the repo map):

- `POST /api/watch/claim` `{ machine }`: atomically claims up to N queued requests (and any claimed longer than 30
  minutes ago, as stale), raising `attempts`, and returns them.
- `POST /api/watch/report` `{ id, status, status_class?, shape?, media?, read? }`: records filing, the reading (upserts
  `content_reads` by sha256 and links `read_id`) or a failure. After 3 failed attempts a request stays failed with its
  class until he pastes it again.

Also a route for a reading of a dropped file with no request (`POST /api/watch/read` `{ sha256, ... }`), or fold it into
`report`; your call, written down.

### 7.5 The scheduled task

A Windows scheduled task on both home computers, every minute, running `content-watch watch --once`, installed by one
script in this repository modelled on content-engine `scripts/install-recordings-upload.ps1` (it checks everything
first and installs nothing if a piece is missing, saying which). Both machines may run it; the claim decides who does
each request. Its log stays on the machine and carries counts and classes only.

### 7.6 Files he drops by hand

`watch --once` also reads every video, image and document in the two inspiration folders that has no reading yet (by
sha256), so the taste ledger can stop watching frames for good.

## 8. What other sessions build (do not build these here)

The Inspiration session (Claude Code, the one that wrote this brief) is building these against the same contract.
Check content-engine `NOW.md` and the open pull requests in each repository before assuming they are done.

- **Control Center: the link box.** One box at the top of the Inspiration board, paste and go, with an optional line
  for his words. It writes the request, shows a "watching" card at once with the post's platform and status, and that
  card turns into the real card when the reading lands. It is the one door for a link; the "Say it" door may also
  accept a link and hand it here.
- **inspirationhouse: reading the readings.** When it tags a card it looks up `content_reads` by the file's sha256 and
  tags from `read_md` plus at most two chosen frames, instead of eight frames and its own transcription; it links the
  request (`item_id`), carries the link and author onto the card, and keeps his paste note as his own words.
- **Everywhere else knows what inspires him.** A separate audit (2026-10-24) is mapping which repositories can read
  from and write back to the taste ledger, and the design that makes every part of the system know what inspires him.
  It is the Inspiration session's next build, not this repository's.

## 9. Guardrails

- Private study only. Nothing fetched is republished, posted or cut into his videos. A reference is a teacher, never a
  template (content-engine `docs/STYLE_REFERENCES.md`). Both Instagram's and YouTube's terms forbid automated
  downloading; the practical risk is to the account whose session is used, which is why D2 is his.
- Spend: Apify costs money. Estimate before any paid run; run nothing paid without his yes or a standing cap he set.
- Never delete or overwrite a file in his Drive; a second fetch of the same post is a no-op (sha256, `url_key`).
- Public logs: counts and classes only.
- `AGENTS.md` here says do not edit the engine unless Krish asks; he has asked (section 1). Keep the compression skill
  working for its own trigger.

## 10. Order of work, with checkpoints

1. Ask D1, D2, D3 (section 3) and record the answers.
2. `content-watch read` on local files: video, carousel slides, a text post. Tests with generated media (as the
   compression tests already make). Checkpoint: a reading of a real saved video from his Inspiration folder, compared
   by token count with what the taste ledger sends today (eight 512px frames).
3. The fetchers, platform by platform, in the order of section 6, with fixtures. Checkpoint: one live fetch per
   platform on the home computer, with his yes.
4. The two engine routes in content-engine, with tests; merged.
5. The scheduled task and `doctor`; installed on both home computers (a step on his machines: hand it over as a
   runnable command with its readback, never as a line saying it was left undone).
6. End to end: he pastes one link of each kind; each becomes a card with a full reading within 15 minutes. Measure it,
   and write the number on the North Star line in `NOW.md`.

## 11. Verification (decided before you start)

- Every fetcher has fixture tests; every reading has a test on generated media with known content (a clip with known
  words, a known cut, a known zoom, known screen text) that fails when the measure is wrong.
- End to end on live data, each of these is a pass only when seen: the request reaches `read`; `content_reads` holds a
  reading whose `read_md` has the words and the screen text; the card exists with the right kind; the taste ledger
  tagged it from the reading (its run counts say so), with no frames beyond the chosen two.
- A failure on purpose (a private post, a dead link) ends as `failed` with the right class, visible on the card.
- Report what was verified separately from what is inferred.
