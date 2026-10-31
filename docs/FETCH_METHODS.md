# Every way to fetch a post (verified 2026-10-24)

This is every way the research found to fetch a post Krish pastes from Instagram (reels and video posts, then
carousels and single images), TikTok, YouTube and LinkedIn, the order to try them in, and what each costs and risks.
It comes from one research run on 2026-10-24: five researchers, one per section, each checked by a skeptic the same
day, then checked twice more against the raw research. It replaces the provisional parts of `docs/BRIEF.md` section 6.
Prices, actor health and breakages move weekly, so each method names the version and the date it was read at; past
that date, treat a figure as unknown until it is read again. Anything that spends money or touches one of Krish's
accounts waits for his yes: D2 (brief section 3), a standing cap he sets with it, or his yes given immediately before
the run. No step was run against a post he saved; the live tests that were run are named where they appear.
"Unverified" and "inference" mean exactly that throughout.

> **Status, 2026-10-27.** This is the research record of 2026-10-24, kept as evidence. Its "Recommended chain" and
> "Do not build" lists are recommendations from before Krish asked for every fallback; the chains the code runs are in
> `docs/FALLBACKS.md` and `content_watcher/fetch/__init__.py` (`_methods`), and where they differ the code wins.
> Differences a reader would act on:
>
> - D2 is answered ("Apify with $5 cap", `docs/DECISIONS.md`), so the "until D2 is answered" and "only once D2 says
>   Apify" gates below are open. One $5 monthly cap covers every Apify step on every platform
>   (`content_watcher/fetch/apify.py`, `allowed`). Steps that use his cookies are not run unless a Firefox profile is
>   set per platform with `content-watch config --cookies`.
> - Instagram starts with its own embed player (`instagram_embed.py`, tested live 2026-10-24), which this file lists as
>   do not build, and the chains include Instaloader, cobalt, TikWM and Tikmate. Krish agreed to the free sites on
>   2026-10-24, which lifts the "only once Krish has agreed" hold on TikWM.
> - The code sends no `videoKvStoreIdOrName` on TikTok's Apify run, so no named store is left on his Apify account.
>   Whether the actor then keeps the files in the run's own store (open question 6 below) has not been tested.
> - Firecrawl, Gemini, ScrapeCreators and Supadata steps are not built.
> - The YouTube and LinkedIn chains described here are built (#4) and covered by fixture tests; no fetch of either has
>   run on a home computer yet.

## Across all five

These facts hold for more than one section. Each is stated once here; the sections carry the detail.

**What D2 decides, per platform.** The brief frames D2 as his own session or Apify for Instagram and LinkedIn. For
Instagram it opens the paid and logged-in steps, and the free logged-out steps run before he answers (both Instagram
sections give the step order for each answer). For LinkedIn it decides only the fallbacks and the login-only posts,
because a public post loads in full for a guest (inference from the guest tests). YouTube needs no D2, though three of
its steps need his yes. TikTok's paid and cookie steps need his yes too. If he sets an Apify cap with D2, ask whether it
also covers TikTok and LinkedIn.

**yt-dlp 2026.10.21 is a security release: install it fresh, never reach it with the self-updater.** Its notes open:
"Old yt-dlp executables are vulnerable to man-in-the-middle attacks... it is strongly recommended to avoid using the
self-updater (e.g. the -U, --update, --update-to command-line options), and instead manually download and install this
release's executable" (certifi advisory GHSA-6q48-6c7w-9gw2,
[Changelog](https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/Changelog.md)). The TikTok section reads the advice
as applying if you suspect you are targeted; every section that uses yt-dlp installs 2026.10.21 fresh either way. This
replaces the brief's rule to run `yt-dlp -U` before each batch: a pip install updates through pip. That self-updating
is safe once 2026.10.21 is installed by hand is an inference (Instagram reels, open question 4). The pinned lines
differ by extra, and no section tested one install carrying both:

- Instagram and TikTok: `python -m pip install "yt-dlp[default,curl-cffi]==2026.10.21" "curl_cffi==0.16.0"` (the
  curl_cffi pin is for TikTok, #17604), and the nightlies with
  `python -m pip install -U --pre "yt-dlp[default,curl-cffi]" "curl_cffi==0.16.0"`.
- YouTube: `"yt-dlp[default,deno]==2026.10.21"` beside `"bgutil-ytdlp-pot-provider==2.0.2"`, updated before each batch
  and at least weekly with `python -m pip install -U "yt-dlp[default,deno]" bgutil-ytdlp-pot-provider`.
- LinkedIn does not use yt-dlp.

**gallery-dl: two pins, two trackers.** The Instagram sections use 1.32.17 (17 Oct 2026). TikTok runs master until the
release after 1.32.17, because the fix for "Many posts return 403" (commit 912138b7ca, Codeberg #549, closed 2026-10-22)
is not in 1.32.17. No section says which one the home machine should run for both. gallery-dl's home has moved to
Codeberg: new TikTok bugs are filed there, about half its issues are there, and mikf placed the Instagram profile-feed
fix (#9829) in Codeberg PR 541, so watch Codeberg as well as GitHub. The brief's "eight gallery-dl releases between
2026-09-12 and 2026-10-17" was six (1.32.12 to 1.32.17), and none of them fixed the Instagram single-post call, which
with cookies has been the stable part.

**Cookies.** Never put a cookie for any platform on GitHub Actions, and never send one to a cloud actor (all five;
LinkedIn rules out the one actor that runs his session cookie from Apify's servers, and YouTube never passes
`youtubeCookies` to an actor). On Windows, `--cookies-from-browser chrome` fails: yt-dlp
[#10927](https://github.com/yt-dlp/yt-dlp/issues/10927) is open and locked since 7 Jan 2026, and gallery-dl has no
Chrome v20 handling either (#6162, still true in master on 2026-10-24). The Instagram and TikTok sections, like the
brief, give Chrome 127+ app-bound encryption as the cause. The YouTube check found #10927 is a DPAPI decrypt failure
whose link to app-bound encryption is a contributor's prediction, so the brief should call that cause suspected; it
also cites "Permission denied" while Chrome is open (#7271), which a contributor called "99.99% likely never going to
be fixed". The way round is the same everywhere: a dedicated Firefox profile (`--cookies-from-browser
firefox:<profile>`) or a `cookies.txt` exported from one. Always name the profile: with none, gallery-dl takes the
cookies of the most recently used Firefox profile, which could be his main account (Instagram carousels). Whose
account it is stays his call: the Instagram sections suggest a secondary account, YouTube a throwaway Google account
and never krish@mindmake.co, TikTok asks his yes for the account it uses, and LinkedIn's login-only steps use his own
signed-in browser only on his written yes.

**Links expire: fetch every file in the job that read the post, and store files, never media URLs.**

- Instagram CDN URLs are signed: `oe` is the expiry as a hexadecimal Unix time, and changing it returns 403. The only
  measured figure for post media is 24 to 36 hours for a reel video (memo23; its test reel expired after 31 hours), so
  treat every post URL as lasting about a day and log each link's remaining life in hours. Whether the URLs are tied
  to the requesting IP is untested.
- TikTok's CDN links expire too; their life was not measured.
- LinkedIn document and PDF links expire within days: on the Canva document read 2026-10-24 the config's `expiresAt`
  was 2026-10-31. Its video and image URLs carry `e=2147483647`, which does not expire in practice, but
  `supreme_coder/linkedin-post` video streams carry their own `expiresAt`, and rewriting an image size in a URL
  returns 403.
- Firecrawl's `audio` and `video` formats return signed Google Cloud Storage URLs that last 1 hour (YouTube).

This extends the brief's "Instagram's and TikTok's CDN links expire" to LinkedIn documents.

**Apify, on every platform.**

- Tier: the Apify API reported BRONZE for the connected account on 2026-10-24, and the sections quote BRONZE prices
  unless they say otherwise. Whether that is his billing plan is open (Instagram reels question 5, TikTok question 4,
  LinkedIn question 13; the carousels section takes it as his tier): read it in the Apify console.
- Spend: print the estimate first (brief section 9), then run only on his yes given immediately before the run or
  inside a standing monthly cap he set; otherwise stop with `apify_spend_not_approved`. Each of brief section 7.4's
  three attempts runs the paid steps again, and a second actor tried after a first is a second paid run, so both count
  against the yes or the cap.
- Token: read `APIFY_TOKEN` by name at run time and send it in an `Authorization: Bearer` header, never as `?token=`
  in the URL, which Apify's docs call less secure because "URLs are often stored in browser history and server logs".
- Results: check every item, even when the run says SUCCEEDED. An item with its error fields set (`error`,
  `errorDescription`, `requestErrorMessages` on Instagram; `error`, `errorCode` on TikTok), an Instagram item with no
  media URL, an empty dataset or an item without the post's text is `apify_item_error`. Whether error items are charged
  is unverified.
- Calls: no section ran an Apify call, so every endpoint path is unverified until the first approved run. A
  synchronous `run-sync-get-dataset-items` run that passes 300 seconds returns 408 (Apify docs), which is why TikTok
  starts its run asynchronously and polls. Apify's current docs write the path as `/v2/actors/:actorId/...`; the
  sections use `/v2/acts/` (TikTok, open question 7).
- Never turn on an AI transcript add-on: $0.041 per started minute at BRONZE on the Instagram reel scraper, the
  clockworks TikTok actors and the `streamers` YouTube actors.
- No Apify step uses an account of his on the platform it reads.

**Firecrawl is out of the chains until its credits reset on 2026-11-09.** The account had 0 of 1,000 credits on
2026-10-24 (billing period 2026-10-09 to 2026-11-09), and the TikTok and YouTube scrapes returned "Insufficient
credits". Plain page scrapes would not help anyway: instagram.com answered "we do not support this site" (one test,
2026-10-24), linkedin.com is on its blocklist (PR #5011), and the TikTok refusal rests on one test and a competitor's
blog. A top-up is spend and needs his yes. The only Firecrawl step in any chain is the Instagram reels text-only lookup
(provider `oriane`), blocked until then.

**GitHub Actions.** No section tested a runner. The runners are on Azure, each section's open question 1 is a one-run
test, and the minutes come from the private repositories' monthly allowance. The cloud IPs tested on 2026-10-24 were
not runners.

| Section | Starts at, on Actions | A cloud datacenter IP, 2026-10-24 |
|---|---|---|
| Instagram reels | Step 2 (Apify), only once D2 says Apify | Plain curl got Instagram's error page for a `/reel/` page and two embed pages |
| Instagram carousels | Step 3 (Apify) only | The reels check's test above |
| TikTok | Step 4 (Apify) | The post page read returned HTTP 200 with full fields, twice |
| YouTube | Step 7: oEmbed and the channel RSS feed, metadata only, never yt-dlp or youtube-transcript-api; then steps 8 and 9 with his yes | Watch pages returned 302 to google.com/sorry; oEmbed, the channel page and the RSS feed returned 200 |
| LinkedIn | Step 1 (the guest-page reader), because it uses no cookie | 22 guest GETs, 14 back to back, all returned 200 with full JSON-LD |

So the brief's "If Actions ever runs a fetch, it starts at the Apify step" holds for Instagram and TikTok, is
replaced for LinkedIn, and YouTube adds free metadata before its paid step.

**How the fetcher calls tools.** From Python, with an argument list passed to `subprocess.run`, a timeout and no
shell, through the pinned Python: `[sys.executable, "-m", "yt_dlp", ...]` and `[sys.executable, "-m", "gallery_dl",
...]`. Then the `%` in an output template and the quotes need no escaping, and the copy pip just updated is the one
that runs: on Windows a bare `yt-dlp` can resolve to another copy on the PATH, and gallery-dl #9346 was a stale 1.27.0
left there. In a `.bat` file every `%` must be doubled, and in PowerShell use `curl.exe`, because there `curl` is an
alias for `Invoke-WebRequest`. A timeout is a failure with the class `timeout` (brief section 7.1).

**Logs and classes.** Logs carry counts and fixed class names only. Together the sections forbid logging a link, a
video id, a title, a caption, post text, an author, a transcript, a file name, a model's answer, an error message, a
tool's raw output, a cookie or its path, and a token. Match an error message in memory, map it to its class, and keep
only the class; record the step that worked as a class too (brief section 7.2). Every class name in the sections is a
proposal from no source. Instagram, TikTok and LinkedIn prefix theirs (`ig_`, `tt_`, `li_`), YouTube's are unprefixed
(`bot_check`, `http_403`), four sections share `apify_item_error` and `apify_spend_not_approved`, and all five use
`timeout`. Settling one scheme is the build's job (a proposal).

**Words, with no model watching.** No step in any chain calls a model. The words come from the platform's own
captions where it has them (yt-dlp's `--write-subs`, TikTok's `subtitleInfos` and `claInfo.captionInfos`, YouTube's
`-orig` auto captions, LinkedIn's caption file or `VideoObject` transcript), from a LinkedIn document's PDF and then
OCR on its page images, and otherwise from faster-whisper 1.2.1 on the home machine (brief section 7.3). Hand
faster-whisper float32 samples decoded with ffmpeg, never the file: letting it open a file returns empty transcripts
with no error (brief section 4, repeated in YouTube). Check every downloaded video for an audio stream with
`ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 <file>` (empty output means none):
Instagram music reels (#16327) and some gallery-dl TikTok videos (#9764) come out silent. A silent file goes on to
the next open step for its audio, and is filed as `silent` when none is open (Instagram reels). The one model route
found is YouTube's step 8, Gemini reading the video from its URL: it is Google's model, so it spends no Anthropic
tokens, but it waits on his call because section 7.3 and the North Star wording proposed in D3 say no model watches.

**Terms.** Every section finds that every automated method breaks the platform's terms as written, logged in or not,
and that the sanctioned routes do not do this job: Instagram's Business Discovery covers only Business and Creator
authors, looked up by username; TikTok's sanctioned routes return no one else's media; YouTube sanctions only its
official API and oEmbed; LinkedIn's post API is closed, and would read only for the signed-in member. Meta's Content
Library and TikTok's Research API are for academic or not-for-profit researchers, so Mindmake does not qualify. In
practice the sections expect blocks for logged-out fetching and outside actors, and restriction or loss of whichever
account's session is used. One disagreement to settle: the Instagram sections (and the brief) say private study lowers
the exposure, while the TikTok check found that under UK law "private study" excludes study with a commercial purpose
(CDPA 1988 s.178). Which country's terms and law bind him is not established (TikTok, open question 3), and that the
UK point bears on the other platforms too is an inference. The TikTok section also replaces the brief's "TikTok's US
Terms section 3.4" with the EEA/UK terms, section 4.5. None of this is legal advice.

**Held in reserve.** ScrapeCreators is in all five sections and untested in each. One key covers TikTok, Instagram
(20 endpoints), LinkedIn (6 endpoints) and YouTube; $47 buys 25,000 credits (about $1.88 per 1,000, verified on its
homepage by the TikTok check), 100 credits are free, and credits never expire. A new account is a new vendor and needs
his yes; on TikTok its Apify actor runs on his existing token instead. Supadata (YouTube section) also spans
platforms, untested. In the YouTube section's words, both are worth a test only if he wants one vendor across
platforms.

## Instagram: reels and video posts

Researched on 2026-10-24 against issue trackers, release notes, Apify actor pages and the Apify API's prices for the
connected account. A second reader then checked it, and every one of its corrections is applied below. Nothing here
was run against a live reel. "Unverified" and "inference" mean exactly that.

### Recommended chain

**Before step 1, every time.**

- Normalise the link. Follow the redirect on any `instagram.com/share/...` link to its `/reel/<code>/` or
  `/p/<code>/` URL, and drop `?igsh=` and every other query string. That canonical form,
  `https://www.instagram.com/reel/<code>/` or `https://www.instagram.com/p/<code>/`, is `url_key`. yt-dlp refuses
  `/share/` links on purpose, so that its generic extractor follows the redirect ("Support `share` URLs", #11677, in
  2024.12.03: https://github.com/yt-dlp/yt-dlp/commit/360aed810ad85db950df586282d256516c98cd2d). Normalising first is
  still the safe design. gallery-dl does it by reading the redirect's location without following it
  (`request_location`) and taking the shortcode from it
  (https://raw.githubusercontent.com/mikf/gallery-dl/master/gallery_dl/extractor/instagram.py). That a plain request
  doing the same works from the home machine is an inference, not tested: record one real share link as a fixture.
- Call every tool from Python with an argument list, never through a shell. Then the `%` in `-o "%(id)s.%(ext)s"`,
  the quotes and Instaloader's `--` need no escaping in cmd or PowerShell.
- Record which step worked as a class name (brief section 7.2), and every failure as a fixed class in `status_class`
  (brief section 5). Logs carry counts and class names only (brief section 4), never a URL, a caption, a file name or
  an error message. Suggested classes for this platform (a proposal, not from any source): `ig_empty_media`,
  `ig_rate_limited`, `ig_restricted`, `ig_no_video_formats`, `ig_no_audio`, `ig_cookies_invalid`, `ig_other`,
  `apify_item_error`, `apify_wrong_item`, `apify_spend_not_approved`, `firecrawl_spend_not_approved`, `timeout`.
  Match an error message in memory, map it to its class, and keep only the class.

**Which steps run, by D2.** Run the open steps in number order and stop at the first that returns the video (or, for
step 5, the text). The one exception is a video with no sound, which goes on to step 2 for the audio (step 1). This is
the first report's order with the check's changes, split by the gate each step carries below.

- Until D2 is answered: 1, then 4.
- D2 says Apify: 1, 2, 4.
- D2 says his own session: 1, 3, 4.
- Both: 1, 2, 3, 4. The first report puts the cookie path only after Apify fails.
- Step 5 joins after step 4 only once Firecrawl has credits and his yes. Step 6 is his, by hand, never the fetcher's.
- When every open step fails, the attempt reports `failed` with the last step's class. Brief section 7.4 allows three
  attempts, and each one runs the paid steps again, so count retries against his yes or his cap.

**On the home Windows machine, in this order.**

1. **yt-dlp, logged out, with browser impersonation. Free. No account, so no ban risk.**
   - Install 2026.10.21 fresh. Do not reach it with the self-updater. The 2026.10.21 release notes open with:
     "Old yt-dlp executables are vulnerable to man-in-the-middle attacks... it is strongly recommended to avoid using
     the self-updater (e.g. the -U, --update, --update-to command-line options), and instead manually download and
     install this release's executable" (certifi advisory GHSA-6q48-6c7w-9gw2,
     https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/Changelog.md). Pick one of two installs:
     - pip, in the machine's pinned Python. Use the TikTok section's line, so one install serves both platforms:
       `python -m pip install "yt-dlp[default,curl-cffi]==2026.10.21" "curl_cffi==0.16.0"`. The curl_cffi pin is
       there for TikTok (yt-dlp #17604). Whether it helps or hurts Instagram is not in this research (unverified).
     - the standalone 64-bit `yt-dlp.exe` from the 2026.10.21 release
       (https://github.com/yt-dlp/yt-dlp/releases/download/2026.10.21/yt-dlp.exe), never `yt-dlp_x86.exe`. curl_cffi
       is "included in most builds *except* `yt-dlp` (Unix zipimport binary) and `yt-dlp_x86` (Windows 32-bit)"
       (https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/README.md).
   - Updates. Brief section 6 says run `yt-dlp -U` before each batch. For the exe that holds only once 2026.10.21 is
     installed by hand, and that self-updating is safe from there is an inference, unverified. A pip install updates
     with pip: the TikTok section's `python -m pip install -U --pre "yt-dlp[default,curl-cffi]" "curl_cffi==0.16.0"`
     takes the nightly builds, which the first report advised "while Instagram is breaking it".
   - `doctor` checks: `yt-dlp --version` prints 2026.10.21 or later, and curl_cffi is present. Using
     `yt-dlp --list-impersonate-targets` and looking for Chrome targets marked available is a design choice the
     research did not cover (unverified). Without curl_cffi, yt-dlp skips the logged-out GraphQL call (it runs only
     `if self._can_impersonate`) and falls back to the /p/ web page
     (https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/yt_dlp/extractor/instagram.py). From the cloud on
     2026-10-24, plain curl got Instagram's error page for a `/reel/` page and two `/p/.../embed/captioned/` pages;
     whether a residential IP gets the same page is unverified (open question 13).
   - Command: `yt-dlp -o "%(id)s.%(ext)s" --write-info-json --write-thumbnail <canonical url>`. No `--impersonate`
     flag: the extractor asks for impersonation by itself.
   - It gets the video (DASH video and audio merged by ffmpeg, or a progressive MP4), the thumbnail, and an
     `.info.json` with `description` (the caption), `channel` (username), `uploader` (full name), `uploader_id`,
     `timestamp`, `duration`, `view_count`, `like_count` and `comment_count` when Instagram returns them. Logged out
     it fetches no comments, there are no subtitles, and there is no music or audio-track metadata.
   - Then check for sound: `ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 <file>`. Empty
     output means no audio stream. Issue #16327, "Instagram downloads missing audio (music reels)", is still open
     (opened 2026-03-23, last comment 2026-09-12, https://github.com/yt-dlp/yt-dlp/issues/16327). bashonly thinks it
     happens "_only_ when logged-in". On no audio, keep the video, record `ig_no_audio`, and take the audio from
     Apify's `audioUrl` in step 2 (paid, so the step 2 gate applies). If step 2 is not open, file the silent video;
     the reading then says `silent` (brief section 4).
   - Fall through to the next open step on: "Instagram sent an empty media response" (#17074), "You have exceeded the
     rate-limit for accessing posts anonymously" (a redirect to login), "Restricted Video", or a timeout. The research
     names only these. Treat any other error the same way, as `ig_other` (a design choice, not from the research).
   - On "No video formats found" the post is an image or an image carousel. Hand it to the carousels section.
     `--write-thumbnail --ignore-no-formats-error` keeps the thumbnail
     (https://github.com/yt-dlp/yt-dlp/issues/17077).
   - Cost: free.

2. **Apify, only once D2 says Apify. Paid. Krish's Instagram account is never used.**
   - Spend gate: print the estimate first. Run only on his yes given immediately before the run, or inside a standing
     monthly cap he set in D2 (brief section 3). Otherwise stop with `apify_spend_not_approved`.
   - For `/reel/` links, `apify/instagram-reel-scraper` (id `xMc5Ga1oCONPmWJIa`):

     ```
     POST https://api.apify.com/v2/acts/xMc5Ga1oCONPmWJIa/run-sync-get-dataset-items
     Authorization: Bearer <Apify token, read from the environment by its symbolic name>
     Content-Type: application/json

     {"username": ["https://www.instagram.com/reel/<code>/"], "includeDownloadedVideo": false, "includeTranscript": false}
     ```

     Cost at BRONZE (the tier the Apify API reported for the connected account on 2026-10-24): $0.0023 per reel plus
     $0.001 per run start, so $0.0033 for one reel (https://apify.com/apify/instagram-reel-scraper/pricing). Brief
     section 6 shows this call with `includeDownloadedVideo: true` at "about $0.0033 a reel". That figure is without
     add-ons.
   - For `/p/` video posts, `apify/instagram-scraper` (id `shu8hvrXbJbY3Eb9W`), same endpoint form with its id and
     body `{"directUrls": ["https://www.instagram.com/p/<code>/"], "resultsType": "posts", "resultsLimit": 1}`.
     $0.0023 per result at BRONZE, no start fee (https://apify.com/apify/instagram-scraper). Prefer it to
     `apify/instagram-post-scraper` while that actor's "blocked since Oct 20" issues are open
     (https://apify.com/apify/instagram-post-scraper/issues/open).
   - The research named `run-sync-get-dataset-items` but did not run it. The path above is Apify's v2 API form; the
     first approved run confirms it. Give the call a client timeout.
   - Check every item, even when the run says SUCCEEDED. Reject it when `error`, `errorDescription` or
     `requestErrorMessages` is set (for example "Error: BLOCKED"), or when it has neither `videoUrl` nor `displayUrl`
     (`apify_item_error`). A `/p/` item with `displayUrl` or `childPosts` but no `videoUrl` is an image or a
     carousel: hand it to the carousels section.
     Also check it is the post asked for: an open reel-scraper issue (about 2026-10-09) reports profile data coming
     back for a single reel (`apify_wrong_item`; which field carries the shortcode is to be read off the first
     fixture). Whether error items are charged is unverified.
   - Download `videoUrl` at once, and `audioUrl` when step 1 had no sound: the CDN links expire. If the direct
     download fails, a second reel-scraper run with `"includeDownloadedVideo": true` stores a copy for $0.015 per
     started MB at BRONZE on top of the $0.0033 run (an 8 MB reel comes to about $0.12, by arithmetic). It is a second
     paid run, so it needs the same yes or cap. `apify/instagram-scraper` has no stored copy. Where the stored copy
     lands and how to fetch it is not in the research (unverified; read it off the first approved run). Its stored
     copies may be 720p or 480p instead of 1080p (open issue, opened 2026-08-05,
     https://apify.com/apify/instagram-reel-scraper/issues/open).
   - Never turn on `includeTranscript` ($0.041 per started minute at BRONZE). Its open issue "Transcript completed but
     missing from output dataset" (2026-10-22) means it may charge without delivering. The words come from local
     speech-to-text (brief section 7.3), with no model watching the video.
   - Fall through on a rejected item, a failed run or a timeout.

3. **Cookie path, only once D2 says his own session. Free. Real account risk.**
   - A secondary Instagram account signed in to its own Firefox profile, never his main account. On Windows,
     `--cookies-from-browser chrome` cannot decrypt Chrome 127+ app-bound (v20) cookies (issue #10927, still open,
     https://github.com/yt-dlp/yt-dlp/issues/10927).
   - Command: `yt-dlp --cookies-from-browser firefox:<profile> -o "%(id)s.%(ext)s" --write-info-json
     --write-thumbnail --write-comments <canonical url>`. It adds comments and reaches "Restricted Video", age-gated
     posts and follower-only posts the account follows.
   - Risk, in bashonly's words on 2026-06-29: "there is the risk that your account will be flagged or banned"
     (https://github.com/yt-dlp/yt-dlp/issues/17074).
   - Run the ffprobe check again: missing audio (#16327) is thought to be a logged-in problem. One user reported
     `--force-ipv4` restored the audio (unconfirmed).
   - If yt-dlp warns "The provided Instagram account cookies are no longer valid", it falls back to the logged-out
     path. Record `ig_cookies_invalid` and leave this step.
   - For a carousel with images (yt-dlp downloads no images), gallery-dl 1.32.17 or later gets every image and video:
     `python -m pip install "gallery-dl==1.32.17"`, then
     `gallery-dl --cookies-from-browser firefox:<profile> --write-metadata <canonical url>`. The carousels section owns
     this case.
   - Never on GitHub Actions.

4. **Instaloader, anonymous. Free. No account.** `python -m pip install "instaloader==4.15.4"`, then
   `instaloader -- -<SHORTCODE>`. Never `--login`: logged-in accounts hit checkpoint and "feedback_required"
   responses (#2767, 2026-10-13; #2728, 2026-08-11). Its open 429 and GraphQL issues come from profile lookups and a
   request that looks logged in, so nothing shows anonymous single posts failing. Nothing shows them working either:
   it is untested. If open question 9 shows it works, move it before step 2, since it is free.

5. **Text only: Firecrawl Alexandria, provider `oriane`, capability `instagram/post-lookup`.** Call:
   `firecrawl_scrape {alexandria: {provider: "oriane", capability: "instagram/post-lookup", options: {url: "<canonical url>", projection: "full"}}}`.
   That is the MCP call form the research read; the HTTP form a Python fetcher would send is not in the research
   (unverified). No video. 20, 30 or 40 Firecrawl credits per non-empty call (basic, default, full); "Empty results
   cost zero" and "do not trigger ingestion". Canonical `/p/` or `/reel/` URLs only. The full projection adds a
   transcript. Blocked for now: the Firecrawl account had 0 of 1,000 credits on 2026-10-24, billing period 2026-10-09
   to 2026-11-09. A top-up is spend, so it needs his yes. Treat each lookup as spend too: run it only on his yes or
   inside a cap he set, as for Apify, otherwise stop with `firecrawl_spend_not_approved`.

6. **By hand (added by the check): Instagram's own in-app Download.** Not a fetcher step: it is what he can do once
   the request has failed. He saves the public reel on his phone and drops the file into the Inspiration folder,
   where section 7.6 reads it. It is the one sanctioned way to get the file.
   The file is watermarked according to secondary sources, and downloads are off for private accounts and for
   creators who turned them off (https://help.instagram.com/iphone-app/520831036611383; the help page did not
   render, so these facts come from a search snippet).

**On GitHub Actions (datacenter IPs).** Start at step 2, so Actions fetches Instagram only once D2 says Apify. Never
put any Instagram cookie in CI. If Actions ever runs yt-dlp, install
`python -m pip install "yt-dlp[default,curl-cffi]==2026.10.21" "curl_cffi==0.16.0"` or the `yt-dlp_linux` binary,
never the zipimport `yt-dlp`. Whether yt-dlp's logged-out path works from a runner is untested (open question 1).
Instaloader's docs say cloud, VPN and proxy IPs "might be subject to significantly stricter limits for anonymous access"
(https://instaloader.github.io/troubleshooting.html).

**Do not build.** A plain Firecrawl page scrape (instagram.com refused, tested 2026-10-24). oEmbed (its terms forbid
keeping the metadata, and it carries no media). The Graph API (Business and Creator authors only, no lookup by URL, no
media for licensed-audio reels). A homegrown og-tag or embed-page reader without browser impersonation (an error page
with no caption from the cloud, tested 2026-10-24). cobalt (its Instagram code predates the June 2026 change). The
Meta Content Library API (Krish is not eligible).

**Filling the normalised post (brief section 7.2).** Field names are from the research's "gets" lists. Neither path
was run, so record a real response of each as a fixture before relying on a field.

| Brief field | yt-dlp `.info.json` (steps 1 and 3) | Apify item (step 2) |
|---|---|---|
| post id | the shortcode in `url_key` | the shortcode in `url_key` |
| author | `channel` (username); `uploader` is the full name | `ownerUsername`; `ownerFullName` |
| posted date | `timestamp` (Unix seconds) | `timestamp` (format not in the research) |
| caption | `description` | `caption` |
| counts | `view_count`, `like_count`, `comment_count`, when returned | `videoPlayCount`, `likesCount`, `commentsCount` (an open instagram-scraper issue reports wrong counts) |
| media, in order | the video file, then the thumbnail | the file fetched from `videoUrl`, the audio from `audioUrl` when needed, the image from `displayUrl` |
| extra | comments only in step 3 (`--write-comments`) | `musicInfo`, `hashtags`, `mentions`, `latestComments` |

### Methods

| Method | Gets | Needs | Works from | Cost | Account risk | State in October 2026 |
|---|---|---|---|---|---|---|
| yt-dlp logged out, curl_cffi impersonation, 2026.10.21 | Video file (DASH merged or MP4), thumbnail, info.json: caption, username, full name, uploader id, timestamp, duration, view, like and comment counts when returned. No comments, no subtitles, no music metadata. A carousel is a playlist; image items fail "No video formats found". | 64-bit `yt-dlp.exe` or `yt-dlp[default,curl-cffi]`; ffmpeg for DASH. No login, no key. | Home machine. Actions untested. | Free | None. bashonly, 2026-06-29: "An account will not be flagged/banned if you're not passing logged-in cookies." | Broke in June 2026 ([#17074](https://github.com/yt-dlp/yt-dlp/issues/17074)). Rebuilt around impersonation in [#17075](https://github.com/yt-dlp/yt-dlp/pull/17075), merged 2026-06-28, shipped in 2026.07.04 with #17126. 2026.10.21 has no Instagram change ([Changelog](https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/Changelog.md)). No new reel breakage found to 2026-10-24. Missing audio [#16327](https://github.com/yt-dlp/yt-dlp/issues/16327) open. Not run. |
| yt-dlp with a logged-in session (`--cookies-from-browser firefox:<profile>` or `--cookies cookies.txt`) | All of the above, plus comments, and "Restricted Video", age-gated and follower-only posts. Uses `/api/v1/media/{id}/info/`. | A logged-in session in a Firefox profile. Chrome 127+ cookies cannot be read on Windows ([#10927](https://github.com/yt-dlp/yt-dlp/issues/10927), open, last comments January 2026). | Home machine | Free | Real: flag or ban (bashonly, 2026-06-29). From datacenter IPs likely higher (inference). | HTTP 404 in July 2026 (#17275), fixed by [#17278](https://github.com/yt-dlp/yt-dlp/pull/17278), shipped in 2026.08.19. Detects invalidated cookies since 2026.07.04. Stories broken September to October (#17707, #17903; fix #17885 still open 2026-10-21). No open breakage for reels and posts found. |
| Apify `apify/instagram-reel-scraper` (`xMc5Ga1oCONPmWJIa`) | caption, ownerUsername, ownerFullName, timestamp, likesCount, commentsCount, videoPlayCount, videoDuration, hashtags, mentions, taggedUsers, coauthorProducers, paidPartnership, musicInfo, latestComments, videoUrl, audioUrl, displayUrl, images. Optional: sharesCount, transcript, stored video. | Apify token only | Both | BRONZE: $0.0023 per reel plus $0.001 per run start. FREE: $0.0026 per reel. GOLD: $0.001. DIAMOND: $0.0004. Add-ons at BRONZE: transcript $0.041 per started minute, download $0.015 per started MB, shares $0.006 per reel. | None to his account; Apify spend only | Last modified 2026-10-23; 174,130 users, 20,866 monthly, 4.39 from 103 reviews. Open: transcript missing from dataset (2026-10-22), profile data for a single reel (about 2026-10-09), "No clear Results" (2026-09-19), 720p or 480p stored copies (2026-08-05) ([issues](https://apify.com/apify/instagram-reel-scraper/issues/open)). Not run. |
| Apify `apify/instagram-scraper` (`shu8hvrXbJbY3Eb9W`) | caption, ownerUsername, ownerFullName, ownerId, timestamp, likesCount, commentsCount, videoPlayCount, videoDuration, videoUrl, audioUrl, displayUrl, images, type, productType, alt, musicInfo, hashtags, mentions, taggedUsers, latestComments, childPosts (each slide's displayUrl and videoUrl). Comments capped at the top 15 on the free plan. No stored video. | Apify token only | Both | BRONZE: $0.0023 per result, no start fee. FREE: $0.0027. GOLD: $0.0015. DIAMOND: $0.0005. | None to his account | Last modified 2026-10-23; 447,732 users, 58,063 monthly, 4.67 from 603 reviews. Open issues that bear on single URLs: "restricted_page for a photo post" (2026-10-23), "The output is far less than the input" (2026-10-22), "107 of 161 requests failed with retryCount: 0" (2026-08-20). Also open: "Incorrect Likes and Comment Counts on Instagram Posts (Huge Difference)" (about 2026-10-15) ([issues](https://apify.com/apify/instagram-scraper/issues/open)). Not run. |
| Apify `apify/instagram-post-scraper` (`nH2AHrwxeTRJoN5hX`), `dataDetailLevel: "detailedData"` | caption, ownerUsername, ownerFullName, timestamp, likesCount, commentsCount, displayUrl, images, childPosts, videoUrl, latestComments, hashtags, mentions, taggedUsers, coauthorProducers, productType, alt. Music data for image and carousel posts is a paid add-on. | Apify token only | Both | BRONZE: $0.0015 per post plus $0.0008 for details, $0.0023 in all; music add-on $0.006. FREE: $0.0017 plus $0.001. GOLD: $0.001 per post. DIAMOND: $0.0004 per post. The details charge at GOLD and DIAMOND is not in the research. | None to his account | The least healthy of the three now: "Since Oct 20: blocked runs, id = "POLARIS"..." (2026-10-21), "Runs return only BLOCKED errors (marked SUCCEEDED)" (2026-10-20), pagination blocked after about 36 to 48 posts (2026-10-15) ([issues](https://apify.com/apify/instagram-post-scraper/issues/open)). Last modified 2026-10-23; 147,304 users, 17,975 monthly, 4.28 from 138 reviews. |
| Apify `apify/instagram-api-scraper` (`RB9HEZitC8hIUXAha`), added by the check | Posts, reels or comments from `directUrls` and `resultsType`. Comments beyond latestComments come from `apify/instagram-comments-scraper` (`SbK00X0JYCPblD2wp`). | Apify token only | Both | BRONZE: $0.002 per result plus $0.001 per run start | None to his account | 3.0 from 34 reviews, 859 monthly users, last modified 2026-10-23. No better than `apify/instagram-scraper`; listed so the choice is deliberate ([page](https://apify.com/apify/instagram-api-scraper)). |
| gallery-dl with browser cookies, 1.32.17 or later | Every image and video in a post; video via yt-dlp from DASH, or merged; background music with `extractor.instagram.audio`. JSON: caption, username, date, post_date, likes, tags. Resolves `/share/` links itself. | Instagram cookies in practice ("Login with username & password is no longer supported"). Firefox: no Chrome v20 handling ([#6162](https://github.com/mikf/gallery-dl/issues/6162), 2024-11-04, still true in master on 2026-10-24). | Home machine | Free | A logged-in session: flags or checkpoints. Default `request_interval` of 6 to 12 seconds. | Six releases from 2026-09-12 to 2026-10-17 (1.32.12 to 1.32.17); 1.32.12's fix was the profile-feed extractors ([CHANGELOG](https://raw.githubusercontent.com/mikf/gallery-dl/master/CHANGELOG.md)). [#9829](https://github.com/mikf/gallery-dl/issues/9829) (the profile-feed query): mikf said on 2026-10-21 it was fixed in Codeberg PR 541 and on 2026-10-23 linked commit c0e3747a44; users said it still failed until a PolarisSEOIsCrawler parameter was added; a commenter says single post links still download. Without cookies, the single-post code points to failure (inference from [the code](https://raw.githubusercontent.com/mikf/gallery-dl/master/gallery_dl/extractor/instagram.py)). About half its issues are on Codeberg. |
| Instaloader 4.15.4, `instaloader -- -<SHORTCODE>` | The video, or every image in a carousel. Caption to .txt; metadata to .json.xz: owner, date, likes, comment count, video_play_count. Comments only with `--comments`, which needs login. | Nothing, anonymous. `--load-cookies` needs browser_cookie3 (Chrome v20 unverified). `--login` stores a session file. | Home machine | Free | None anonymous. Logged in: checkpoint and "feedback_required" (#2767, 2026-10-13; #2728, 2026-08-11). | 4.15.4 (2026-10-12) "Fixed profile resolution and logged-in post fetching"; 4.16b1 pre-release on 2026-10-21 ([releases](https://github.com/instaloader/instaloader/releases)). The 429s in [#2786](https://github.com/instaloader/instaloader/issues/2786) are profile lookups; the 2 to 3 point drop in [#2738](https://github.com/instaloader/instaloader/issues/2738) looks logged in. Neither shows anonymous single posts failing. Cloud IPs get stricter anonymous limits ([docs](https://instaloader.github.io/troubleshooting.html)). |
| Firecrawl Alexandria `oriane`, `instagram/post-lookup` | Text only: caption, publishedAt, handle, display name, views, likes, shares, comments, duration, hashtags, mentions, coAuthors, audio title, author and copyrighted flag, popularComments, thumbnailMediaUrl. Full projection adds transcript, transcriptChunks and frames. | Krish's Firecrawl key. The post must already be in Oriane's index. Canonical URLs only. | Both | 20, 30 or 40 credits (basic, default, full) per non-empty call; empty results free. A 1,000-credit plan funds 25 to 50 lookups a month. | None | Contract confirmed by free discovery on 2026-10-24; not run. The account had 0 of 1,000 credits on 2026-10-24, period to 2026-11-09. Index coverage unknown. ([docs](https://docs.firecrawl.dev/features/scrape)) |
| Instagram Graph API, Business Discovery, `GET https://graph.facebook.com/v26.0/{ig-user-id}?fields=business_discovery.username(<author>){media{...}}` | Business or Creator authors only: caption, media_type, permalink, timestamp, like_count, comments_count, view_count. No `media_url` for licensed-audio videos or reels with downloads turned off. No lookup by URL. | A Meta developer app; his Business or Creator account linked to a Page; a token with instagram_basic, instagram_manage_insights, pages_read_engagement. Whether App Review is needed is unverified. | Both | Free | None; sanctioned | Official and stable; v26.0 released 2026-07-29 ([v26](https://developers.facebook.com/blog/post/2026/07/29/introducing-graph-api-v26-and-marketing-api-v26/)). Does not fit: no video for most reels, no personal authors (Basic Display retired 2024-12-04) ([reference](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/business_discovery)). |
| Instagram oEmbed, `GET https://graph.facebook.com/v26.0/instagram_oembed?url=<post-url>` | Embed HTML, version, provider_name, provider_url, type, width. No thumbnail or author since 2025-11-03. No video, no counts. | A Meta app with oEmbed Read, which needs App Review and business verification. 1,000 requests an hour. | Both | Free | None, but its terms forbid "consuming, manipulating, extracting, or persisting the metadata and content" | Do not use ([oEmbed](https://developers.facebook.com/docs/instagram-platform/oembed), [oEmbed Read](https://developers.facebook.com/docs/features-reference/oembed-read)). |
| Instagram in-app Download, added by the check | The video file, watermarked (secondary sources) | His phone; a public reel with downloads on (on by default for public adult accounts, off for private ones, and creators can turn it off) | His phone, by hand | Free | None; sanctioned | Help page did not render; facts from a search snippet ([help](https://help.instagram.com/iphone-app/520831036611383)). Corroborated by the Graph API's "reels whose owner has turned off reel downloads". |
| ScrapeCreators API, added by the check: `GET /v1/instagram/post?url=<url>` with an `x-api-key` header | `video_url`, `display_resources`, `edge_sidecar_to_children` for carousels, caption, owner, play and like counts. Transcripts from `/v2/instagram/media/transcript`. | A new vendor account and key he does not have | Both | $47 for 25,000 credits ($1.88 per 1,000); credits never expire; 100 free. 1 credit a call, about 10 more with `download_media` (the docs disagree); cached responses free. | None to his account; same terms position as Apify | 2026 reliability unverified ([docs](https://docs.scrapecreators.com/v1/instagram/post)). A new vendor needs his yes. |
| cobalt, self-hosted with Docker, added by the check | Photos and videos; a picker for carousels | Docker on the home machine; optional cookies | Home machine | Free | None logged out | Not recommended. Its Instagram service was last changed 2025-04-02, before the June 2026 change. Open: #1509 (2026-02-10), #1568 (2026-06-27), #1587 (2026-08-23). That it is broken now is an inference ([service](https://raw.githubusercontent.com/imputnet/cobalt/main/api/src/processing/services/instagram.js)). |
| Browser automation with Playwright, added by the check | Caption from the page; media captured from the page's responses | Playwright and a real logged-out Chrome on the home machine | Home machine | Free | None logged out | Design option only. No maintained tool found. Would pass the browser-fingerprint check in principle. Unverified. |
| Meta Content Library API, added by the check | Not assessed | Affiliation with a qualified academic or not-for-profit research institution, vetted by ICPSR | Not applicable | Not applicable | Not applicable | Excluded: Krish is not eligible ([access](https://developers.secure.facebook.com/docs/content-library-api/get-access)). |

### Corrections applied

1. Core yt-dlp facts confirmed against the changelog and extractor source (#17074, #17075 and #17126 in 2026.07.04,
   #17278 in 2026.08.19, nothing in 2026.10.21; the logged-out GraphQL call runs only with impersonation; no comments
   logged out). Nothing changed.
2. "Run `yt-dlp -U` before each batch" became "install 2026.10.21 by hand, then self-update from there", because of
   the man-in-the-middle advisory GHSA-6q48-6c7w-9gw2. This also corrects the update line in brief section 6.
3. "The Windows exe includes curl_cffi" became "the 64-bit `yt-dlp.exe` includes it; never `yt-dlp_x86.exe` or the
   zipimport `yt-dlp`", and Actions uses the pip extra or `yt-dlp_linux`. Without curl_cffi the code falls back to
   the /p/ web page.
4. Missing audio (#16327, open) added: ffprobe every download for an audio stream, and take Apify's `audioUrl` when it
   is missing.
5. yt-dlp's "gets" now says it carries no music or audio-track metadata. The "intended" remark on #17077 is attributed
   to contributor ruben1PvP; bashonly closed it as not planned.
6. Share links: yt-dlp refuses `/share/` by design so its generic extractor follows the redirect (2024.12.03, #11677),
   and gallery-dl resolves `/share/` itself. Normalising first stays.
7. Apify headline prices: the store's "from" prices are GOLD, not the top tier. DIAMOND prices added. BRONZE figures
   unchanged.
8. Reel scraper: the 720p or 480p issue is dated 2026-08-05, not July. "No clear Results" (2026-09-19) added. The
   transcript add-on is dropped in favour of local speech-to-text.
9. `apify/instagram-scraper` issues: "unable to get post" is a missing post-count field, and "says blocked by
   instagram" (2026-08-02) is about search. The table now lists the three that bear on single URLs.
10. `apify/instagram-post-scraper` is now marked the least healthy, the chain prefers `apify/instagram-scraper`, and
    every Apify item is rejected on `error`, `errorDescription` or `requestErrorMessages` even when the run says
    SUCCEEDED.
11. gallery-dl had six releases from 2026-09-12 to 2026-10-17, not eight (brief section 6 also says eight).
    1.32.12's fix was the profile feeds. About half its issues live on Codeberg.
12. gallery-dl attributions: "It should be fixed now" on #9834 is from commenter JuanForge, not a maintainer. On
    #9829 mikf said on 2026-10-21 it was fixed in Codeberg PR 541 and on 2026-10-23 linked commit c0e3747a44; users
    said it still failed until a PolarisSEOIsCrawler parameter was added.
13. gallery-dl without cookies moved from "unverified" to "expected to fail" (inference from its code). The #6162
    quote is dated 2024-11-04 and still holds.
14. Instaloader's "shakiest" rating is withdrawn for anonymous single posts: its 429s are profile lookups and its
    GraphQL drop looks logged in. It stays late in the chain because it is untested.
15. Firecrawl went from "running low" to "0 of 1,000 credits on 2026-10-24". Step 5 is blocked until 2026-11-09 or a
    top-up he approves.
16. The Instagram terms quote is verified word for word against the Open Terms Archive copy, with an effective date
    of 1 January 2025, and a clause on selling or licensing data is added.
17. The embed-page question is half answered: from the cloud, plain curl got Instagram's error page with no caption.
    A homegrown embed or og-tag reader without impersonation is now on the do-not-build list.
18. oEmbed needs business verification as well as App Review. Graph API v26.0 is confirmed, released 2026-07-29.

### Open questions

1. Does yt-dlp's logged-out path work from a GitHub Actions IP? Test: one workflow run with
   `python -m pip install "yt-dlp[default,curl-cffi]==2026.10.21" "curl_cffi==0.16.0"` against
   `https://www.instagram.com/reel/Chunk8-jurw/`
   (@instagram's own reel, a yt-dlp test case). No cost beyond runner minutes. It downloads a file, so it needs his
   yes.
2. Does step 1 work on the home machine for the reels Krish saves? Test: step 1 on one reel he picks, as the brief's
   once-per-platform live check, with his yes. Free.
3. Does a logged-out download lose the audio on music reels (#16327)? `--force-ipv4` as a fix is unconfirmed. Test:
   make test 2 a music reel and run the ffprobe check. Free.
4. Is self-updating safe once 2026.10.21 is installed by hand? This is an inference. Test: read the next release's
   notes before the first `-U`. Free.
5. Is BRONZE Krish's Apify billing tier? Test: read the plan in the Apify console. Free.
6. Are Apify error items charged? Test: read the charged events on the first run that returns an error item. Free.
7. The open 720p or 480p issue is about the reel scraper's stored copies (`includeDownloadedVideo`). Does its raw
   `videoUrl` come at full resolution, and does the study need 1080p? The endpoint path is not run either. Test: one
   approved reel-scraper run with downloads off ($0.0033 at BRONZE), fetch `videoUrl`, and compare its ffprobe height
   with the step 1 file.
8. Does gallery-dl fetch a single public post without cookies? The code points to no. Test: one
   `gallery-dl --write-metadata <public post url>` on the home machine with no cookies. Free, no account.
9. Does Instaloader fetch a single post anonymously? Test: `instaloader -- -<SHORTCODE>` once from the home machine.
   Free. If it works, move it before Apify.
10. Can Instaloader's `--load-cookies` read Chrome v20 cookies on Windows? Test: none needed while cookies come from
    Firefox.
11. Can a Meta app in development mode reach Business Discovery for his own account without App Review? Test: not
    worth running; the route cannot give the video for most reels.
12. How many reels does Oriane's index hold? Test: after 2026-11-09, look up five reels he saved. Empty lookups are
    free.
13. Does the public `/p/<code>/embed/captioned/` page give caption text to a plain client from a residential IP?
    Test: from the home machine, in PowerShell (`curl.exe`, because plain `curl` is another command there),
    `curl.exe -sS -A "<a current desktop Chrome User-Agent>" "https://www.instagram.com/p/<code>/embed/captioned/"`,
    and look for the caption text. `httpErrorPage` in the reply is the error page the cloud got. Free. If the caption
    comes back, the cloud failure was the IP, not the missing browser fingerprint.
14. Is the in-app Download watermarked, and on by default as the search snippet says? Test: Krish downloads one public
    reel on his phone and looks at the file. Free.
15. Is ScrapeCreators reliable in 2026, and what does `download_media` cost? Test: one reel on its 100 free credits.
    A new vendor account needs his yes first.
16. Is "Effective Date: 1 January 2025" the date of the terms that apply to him, or a regional variant? Test: none
    needed for the build; it does not change the terms position.

### Terms

Instagram's Terms of Use say: "This includes creating accounts or accessing or collecting information in an automated
way without our express permission, regardless of whether such automated access or collection is undertaken while
logged-in to an Instagram account" (https://help.instagram.com/581066165581870, verified against
https://raw.githubusercontent.com/OpenTermsArchive/pga-versions/main/Instagram/Terms%20of%20Service.md). The Open
Terms Archive copy also says: "You can't sell, license, or purchase any account or data obtained from us or our
Service, regardless of whether such data was obtained while logged-in". It shows "Effective Date: 1 January 2025",
which may be a regional variant (open question 16). The same terms say: "You may use someone else's works under
exceptions or limitations to copyright and related rights under applicable law." Meta's Automated Data Collection
Terms (effective 2024-10-07, https://www.facebook.com/legal/automated_data_collection_terms) require Meta's express
written permission; they cover "Meta Company Products", defined by reference to the Facebook Terms, so that they reach
Instagram is an inference. So every unofficial method above breaks the terms as written, logged in or not. Private
study lowers the practical exposure but does not make it permitted, and a logged-in session adds a separate risk that
the account is flagged or banned.

## Instagram: carousels and single images

Scope: a post at `instagram.com/p/SHORTCODE/` that holds one image, or a carousel ("sidecar") of several images or
videos. Reels and single video posts have their own section. The research was checked against issue trackers, release
notes, Apify listings and Meta's docs on 24 Oct 2026. A second reader then checked it, and where the two disagree the
second reader's correction is used here. Nothing here was run against a live post. A few facts come from the reels
research and its check, because they cover the same Apify actors; each is marked "(reels research)" or "(reels check)".

This replaces brief section 6's carousel list, and its order differs. Brief section 6 puts Apify first and says
`childPosts` holds every slide in order. That is untested (open question 1).

### Recommended chain

**Before any step.**

- Call every tool from Python with an argument list, never through a shell, and through the pinned Python:
  `[sys.executable, "-m", "gallery_dl", ...]` and `[sys.executable, "-m", "yt_dlp", ...]`. Then the `%` in yt-dlp's
  `-o` template and the quotes need no escaping in cmd or PowerShell (a `.bat` file would need every `%` doubled). It
  also runs the copy pip just updated: in gallery-dl [#9346](https://github.com/mikf/gallery-dl/issues/9346) the fault
  was a stale gallery-dl 1.27.0 left on the PATH. `python` in the commands below means that pinned Python (brief
  section 4). With the placeholders filled in (quoted if a path has spaces), they also run as typed in PowerShell.
- Give every call a timeout (brief section 7.1).
- Record which step worked as a class name, and every failure as a fixed class in `status_class` (brief sections 5 and
  7.2). Suggested classes (a proposal, not from any source): `ig_login_redirect`, `ig_rate_limited`,
  `ig_empty_media`, `ig_missing_slides`, `ig_small_image`, `apify_item_error`, `apify_spend_not_approved`, `cdn_403`,
  `timeout`, `ig_other`. Match an error message in memory, map it to its class, and keep only the class.
- Set `shape` (brief section 5) to `carousel` for two or more slides and `image` for one.

**Which steps run, by D2.** A step whose gate is closed is skipped, never tried. Run the open steps in number order
and stop at the first that passes the closing check (below the steps). This is the first report's order with the
check's changes.

- Until D2 is answered: 0, then 2.
- D2 says his own session, and names the account: 0, 1, 2, 4.
- D2 says Apify, with a standing monthly cap: 0, 2, 3.
- Both: 0, 1, 2, 3, 4.
- When every open step fails, report `failed` with the last step's class. Brief section 7.4 allows three attempts, and
  each one runs the paid step again, so count retries against his cap.

The gates:

- Steps 1 and 4 run under a signed-in Instagram session. They wait for D2, and for Krish to say which account (his
  main one or a secondary one). The report suggests a secondary account. The saved-collection option below needs his
  own account and its own yes.
- Step 3 spends money on Apify. It waits for D2 and a standing monthly cap from Krish, or his yes given immediately
  before the run. Print the estimate first; with neither, stop with `apify_spend_not_approved`.
- Steps 0 and 2 need neither. They can be built and run now.
- Nothing in this chain calls a model.

**0. Clean the link (added by the check).** Follow any `instagram.com/share/...` redirect, then strip the query
(`?igsh=...`) down to `https://www.instagram.com/p/SHORTCODE/`. That is the `url_key`. gallery-dl resolves share links
itself, by reading the redirect's location (`request_location` in its instagram.py), and yt-dlp has done so since
2024.12.03. That a plain request does the same from the home machine is untested, so record one real share link as a
fixture. Apify's `directUrls` wants the `/p/` or `/reel/` shortcode form and does not take numeric post IDs. A stable
key also removes duplicates. Cost: free. Sources:
[gallery-dl instagram.py](https://github.com/mikf/gallery-dl/blob/master/gallery_dl/extractor/instagram.py),
[apify/instagram-scraper](https://apify.com/apify/instagram-scraper).

**1. gallery-dl 1.32.17 or later, with cookies (home machine, after D2). Free. Real account risk.**

```
python -m pip install -U "gallery-dl>=1.32.17"
python -m gallery_dl --cookies-from-browser firefox:<profile> -o extractor.instagram.videos=merged -D <job folder> --write-info-json --write-metadata "https://www.instagram.com/p/SHORTCODE/"
```

- `<profile>` is the dedicated Firefox profile: its folder name under `%APPDATA%\Mozilla\Firefox\Profiles`, or that
  folder's full path. Always pass it. With no profile, gallery-dl takes the cookies of the most recently used Firefox
  profile, which could be Krish's main account (read in 1.32.17's
  [cookies.py](https://github.com/mikf/gallery-dl/blob/master/gallery_dl/cookies.py), `_firefox_cookies_database`).
  A `cookies.txt` exported from that profile, passed with `--cookies cookies.txt`, works instead.
- Chrome's cookies on Windows will not decrypt: gallery-dl's `cookies.py` has no branch for Chrome 127+ App-Bound
  Encryption (inferred from the source), and yt-dlp issue #10927 is open but locked since 7 Jan 2026.
  Sources: [cookies.py](https://github.com/mikf/gallery-dl/blob/master/gallery_dl/cookies.py),
  [yt-dlp #10927](https://github.com/yt-dlp/yt-dlp/issues/10927).
- `-o extractor.instagram.videos=merged` makes video slides come as Instagram's pre-merged files, with no yt-dlp or
  ffmpeg needed. The default (`true`) fetches DASH through yt-dlp and needs both. The same key can sit in a config file
  passed with `-c`. That `-o` sets this key was checked against 1.32.17's option parser, not on a live post.
  Source: [configuration.rst](https://github.com/mikf/gallery-dl/blob/master/docs/configuration.rst).
- `-D` puts the files in the job's own folder. Add `-j` to print the raw JSON without downloading anything.
- It returns every slide in the post's own order, at the highest resolution Instagram's REST API serves, with caption,
  username, full name, date, likes, slide number, tags, location and coauthors. It waits 6 to 12 seconds between API
  calls by default. Source: [instagram.py](https://github.com/mikf/gallery-dl/blob/master/gallery_dl/extractor/instagram.py).
  Which metadata field gives the post's slide count, for the closing check, is unverified (open question 15).
- Fall through, in these cases:
  - "HTTP redirect to login page": the cookies are missing or no longer valid. Record `ig_login_redirect`, do not
    retry, go to the next open step, and let `doctor` say the cookies need renewing.
  - A 429: record `ig_rate_limited` and go on without a retry under the account (a design choice, to keep the
    account's traffic low).
  - Any other error: update it and retry once, because the maintainer ships Instagram fixes within days. If it still
    fails, go on.
- If it prints its low-resolution warning (option `warn-images`), export a `cookies.txt` from the profile, delete the
  `wd` cookie from it, and retry once with `--cookies cookies.txt`. gallery-dl 1.32.17 lists `--cookies-export FILE`
  in its `--help`; whether that is the easiest way to export is untested. The `wd` fix is one user's report; the
  maintainer could not reproduce the problem. Source: [gallery-dl #8300](https://github.com/mikf/gallery-dl/issues/8300).
- Cost: free. Risk: every request runs under the account whose cookies it holds, and the worst case is losing that
  account. Never on GitHub Actions.

**2. yt-dlp 2026.10.21 or later, logged out (home machine, no gate). Free. No account.**

```
python -m pip install -U "yt-dlp[default,curl-cffi]>=2026.10.21"
python -m yt_dlp --ignore-no-formats-error --write-thumbnail --write-info-json -P <job folder> -o "%(id)s_%(playlist_index)02d.%(ext)s" "https://www.instagram.com/p/SHORTCODE/"
```

- One install serves every platform. If the reels or TikTok section pins a different install line, use that one.
- Update with pip, never with `yt-dlp -U`. The 2026.10.21 release notes say "it is strongly recommended to avoid
  using the self-updater (e.g. the -U, --update, --update-to command-line options)" (reels check,
  [Changelog](https://github.com/yt-dlp/yt-dlp/blob/master/Changelog.md)).
- A carousel comes back as a playlist with one entry per slide, in order. Video slides download as video. Image slides
  have no formats, so `--ignore-no-formats-error` keeps it going and `--write-thumbnail` saves the image. Whether that
  image is the full original size is inferred from the source code, not tested. A single-image post is not a playlist,
  so its file is named `<id>_NA.<ext>` (checked with 2026.10.21's filename code).
- The info JSON carries caption, username, full name, timestamp, and like, comment and view counts.
- Logged out it needs curl-cffi. The maintainer: "The site blocks anonymous API requests that do not have a browser
  fingerprint". A contributor called images out of scope ("Yt-dlp is a video and audio downloader, not an image
  downloader") and #17077 was closed "not planned", so this is the fallback, not the first choice.
  Sources: [yt-dlp #17077](https://github.com/yt-dlp/yt-dlp/issues/17077),
  [yt-dlp #17074](https://github.com/yt-dlp/yt-dlp/issues/17074).
- Fall through, in these cases:
  - "You have exceeded the rate-limit for accessing posts anonymously": record `ig_rate_limited` and go on at once,
    with no retry (a design choice).
  - "Instagram sent an empty media response": update it and retry once, then go on. That was the June 2026 break, and
    an update fixed it.
  - Fewer files than slides, or an image smaller than its original size: record `ig_missing_slides` or
    `ig_small_image` and go on. Which info JSON field holds the original size is unverified (open question 2).
- Cost: free. Risk: none to any account. Maintainer bashonly, 29 Jun 2026: "An account will not be flagged/banned if
  you're not passing logged-in cookies."

**3. Apify `apify/instagram-scraper` (home machine or Actions, after D2 and a monthly cap). Paid.**

Spend gate first: print the estimate ($0.0023 for one post at his tier), then run only inside his standing monthly cap
or on his yes given immediately before the run. Otherwise stop with `apify_spend_not_approved`.

```
POST https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items
Authorization: Bearer <APIFY_TOKEN>
Content-Type: application/json

{"directUrls":["https://www.instagram.com/p/SHORTCODE/"],"resultsType":"posts","resultsLimit":1}
```

- Send it from Python with `urllib.request` (standard library first, brief section 7.1), with a client timeout. The
  research names `run-sync-get-dataset-items` but did not run it; the first approved run confirms the path.
- The token goes in the header, never as `?token=` in the URL. Apify's API docs call the query form less secure
  because "URLs are often stored in browser history and server logs". Source: [Apify API v2](https://docs.apify.com/api/v2).
  Read it by its symbolic name, `APIFY_TOKEN`, from wherever `doctor` finds it, and never print it.
- It returns URLs, not files: `type` (Image, Video or Sidecar), `caption`, `displayUrl`, `images[]` and `childPosts[]`
  (each with `type`, `displayUrl`, `videoUrl`, `dimensionsWidth`, `dimensionsHeight`, `alt`), owner, `timestamp` and
  counts. Download every URL in the same job. The actor "sees the logged-out version of the page", so private posts
  generally do not come back. Source: [apify/instagram-scraper](https://apify.com/apify/instagram-scraper).
- Check every item, even when the run says SUCCEEDED. Reject it as `apify_item_error` when `error`,
  `errorDescription` or `requestErrorMessages` is set (for example "Error: BLOCKED"), or when it has neither
  `videoUrl` nor `displayUrl`.
  The three official Instagram actors share that schema (reels check). An open issue of 23 Oct 2026, "restricted_page
  for a photo post", is a `/p/` photo post run with `resultsLimit: 1` (reels check,
  [open issues](https://apify.com/apify/instagram-scraper/issues/open)). Whether error items are charged is
  unverified.
- Fall through when `type` is Sidecar and `childPosts` is empty or shorter than the slide count (when an earlier step
  gave one), or when a download returns 403. The docs do not say how `childPosts` and `images[]` relate, so until open
  question 1 is answered, also treat the two lists having different lengths as a failure (a design choice). Then run
  the community actor `memo23/instagram-video-downloader` with re-hosting on. It is a second paid run under the same
  cap or yes: about $0.012 for a 10-image carousel.

```
POST https://api.apify.com/v2/acts/memo23~instagram-video-downloader/run-sync-get-dataset-items
Authorization: Bearer <APIFY_TOKEN>
Content-Type: application/json

{"posts":["https://www.instagram.com/p/SHORTCODE/"],"downloadCarouselImages":true,"storeFiles":true}
```

- memo23 downloads every slide and re-hosts each file in the run's key-value store, at a URL that needs no headers and
  lasts as long as Apify keeps the data. Those claims come from its own README only. Download the re-hosted files in
  the same job anyway (a design choice). Source:
  [memo23/instagram-video-downloader](https://apify.com/memo23/instagram-video-downloader).
- `apify/instagram-post-scraper` costs the same as the first call
  (`{"username":["https://www.instagram.com/p/SHORTCODE/"]}`; `dataDetailLevel` defaults to `detailedData`). Its
  carousel output is unverified. Prefer `apify/instagram-scraper` while the post scraper's open issues stand: "Since
  Oct 20: blocked runs, ... profiles returned without posts" (21 Oct 2026) and "Runs return only BLOCKED errors (marked
  SUCCEEDED)" (20 Oct 2026) (reels check, [open issues](https://apify.com/apify/instagram-post-scraper/issues/open)).
  Source: [apify/instagram-post-scraper](https://apify.com/apify/instagram-post-scraper).
- Cost. Krish's account is on the Bronze tier: that is the tier the Apify API reported for the connected account on
  24 Oct 2026 (reels research). instagram-scraper: $0.0023 a post on Bronze, with no start fee (reels check), so $2.30
  per 1,000; it is $0.0027 on Free. instagram-post-scraper: $0.0023 Bronze, $0.0027 Free. memo23 on Bronze: $0.0001 a
  start (charged per GB of run memory, at least one), $0.002 a post, $0.001 per re-hosted image, $0.003 per re-hosted
  video, so about $0.012 for a 10-image carousel.
- Risk: none to Krish's Instagram account. He still commissions collection the terms forbid.

**4. Own Playwright capture (home machine, after D2, last resort).** Custom code that nobody has built or tested.

- Install: `python -m pip install -U playwright`, then `python -m playwright install chromium`. The research did not
  check a Playwright version.
- `playwright.chromium.launch_persistent_context(user_data_dir=<dedicated folder>)`, logged in once by hand. Playwright
  says "automating the default Chrome user profile is not supported", so use a separate folder.
  Source: [Playwright BrowserType](https://playwright.dev/python/docs/api/class-browsertype).
- Open the `/p/` URL. Catch the `/graphql/query` response holding
  `data.xdt_api__v1__media__shortcode__web_info.items[0]`. Read `carousel_media[*].image_versions2.candidates[0]` (the
  largest), `video_versions` and `caption.text`. Download each URL with the same context's `context.request.get`.
- These JSON paths come from yt-dlp's source and instaloader #2738 and are unverified. Instagram renames these fields,
  so the parser needs upkeep. Source: [instaloader #2738](https://github.com/instaloader/instaloader/issues/2738).
- When it fails, record the failure as a class name and stop. Nothing is left in the chain.
- Cost: free. Risk: low at low volume (a real browser on a residential IP), but still automated collection under that
  account.

**The same check ends every path, in our own code.**

- The number of files saved equals the slide count (`carousel_media` length, `childPosts` length or the playlist
  count). gallery-dl warns only about low resolution, never about a missing slide.
- Each image's pixel size equals `original_width` x `original_height` where the metadata gives them.
- A path that fails the check counts as a failed step: record `ig_missing_slides` or `ig_small_image` and go to the
  next open step.
- Logs carry counts and class names only: the fetcher class that worked, slides expected, files saved, and each link's
  remaining life in hours, decoded from `oe` (a hexadecimal Unix time on every CDN URL). Never a URL, a caption, a
  file name, a cookie or a token.
- Treat every post media URL as lasting about a day, and download in the same job. The only measured figure for post
  media is memo23's 24 to 36 hours for a reel video (its test reel expired after 31 hours). Changing `oe` returns 403.

**On GitHub Actions (fallback only).** Use step 3 only, with the token in the header, because Actions logs are kept.
Never put Instagram cookies on a runner. Fetch the returned CDN URLs at once from the runner. If that returns 403
(whether the URLs are tied to the requesting IP is untested), let Apify fetch and re-host them: memo23 with
`storeFiles: true`, or `lukaskrivka/images-download-upload`. That actor has no fee of its own, but its run's Apify
platform usage is billed (the price is not in the research), so it sits under the same cap.
Source: [lukaskrivka/images-download-upload](https://apify.com/lukaskrivka/images-download-upload).

**Option that needs his yes: his saved collection.** If Krish would rather tap Save into a named collection than
paste links, gallery-dl can poll it from the home machine. It must use his own account, on a schedule, so the risk is
higher. Here `<profile>` is a Firefox profile signed in to his own account, not the secondary one. Unverified in 2026.

```
python -m gallery_dl --cookies-from-browser firefox:<profile> --write-info-json "https://www.instagram.com/USERNAME/saved/COLLECTION_NAME/COLLECTION_ID"
```

Use the full URL Instagram shows, numeric ID included. A URL that ends at the name matches no extractor. All saved
posts are at `https://www.instagram.com/USERNAME/saved/` (or `/saved/all-posts/`).
Source: [instagram.py](https://github.com/mikf/gallery-dl/blob/master/gallery_dl/extractor/instagram.py).

**The permitted route, narrow.** Business Discovery is the only route Meta permits that Mindmake can use (the Meta
Content Library is the other, and only accredited researchers qualify). It works only for posts
by Business or Creator accounts, and looks posts up by username, not by link, so page through until `shortcode`
matches. Use it when the poster qualifies and Krish wants a fully permitted path. Setting it up means a Meta app, his
professional account linked to a Facebook Page, and a user token with the permissions in the table. That creates an
app and grants permissions, so each step needs his yes. The research did not check an API version for
`<api-version>`. Logs never carry the request URL or the token.

```
GET https://graph.facebook.com/<api-version>/<krish-ig-user-id>?fields=business_discovery.username(TARGET){media{id,shortcode,permalink,caption,media_type,media_url,timestamp,like_count,comments_count,children{media_type,media_url}}}
```

**Not in the chain.** Skip instaloader, cobalt, oEmbed, Firecrawl, instagrapi, the Oriane lookup, the Meta Content
Library and the small Apify actors; the table gives each reason. Hold HikerAPI and ScrapeCreators in reserve. Each
needs a new account and costs money, which is Krish's call, and neither is verified on carousels. Consider them only
if Apify fails the carousel test.

### Methods

| Method | Gets | Needs | Works from | Cost | Account risk | State in October 2026 |
|---|---|---|---|---|---|---|
| [gallery-dl](https://github.com/mikf/gallery-dl) 1.32.17, single post (`InstagramPostExtractor`, REST `/api/v1/media/{id}/info/`) | Every slide in post order at the REST API's highest resolution; video slides; caption, username, full name, owner id, date, likes, shortcode, slide number, tags, location, coauthors. Comment text is not in the default output (unverified). | A logged-in session (`sessionid` cookie) from a dedicated Firefox profile or an exported cookies.txt. Password login was removed. Video slides need yt-dlp and ffmpeg, or `videos: "merged"` for neither. | Home machine | Free (open source) | Real but low at a few posts a day (the report's judgement). None of the cited issues shows a checkpoint: [#8978](https://github.com/mikf/gallery-dl/issues/8978) (Feb 2026) was 429s on the username-to-user-ID lookup, [#9777](https://github.com/mikf/gallery-dl/issues/9777) (Sep 2026) 429s on avatar and tagged with posts and reels still working, and [#9346](https://github.com/mikf/gallery-dl/issues/9346) a stale gallery-dl 1.27.0 left on the PATH. Worst case is losing the account. Never on Actions. | The single-post path with cookies has been the stable part. 1.32.12 (12 Sep 2026) fixed the profile posts and reels tabs ([#9731](https://github.com/mikf/gallery-dl/issues/9731)). 1.32.13 to 1.32.17 fixed profile, stories, highlights, tagged, avatar and user lookups, none of them the single-post call ([CHANGELOG](https://github.com/mikf/gallery-dl/blob/master/CHANGELOG.md)). Without cookies a single post raises "HTTP redirect to login page" (the source). In [#9564](https://github.com/mikf/gallery-dl/issues/9564) a commenter, not a maintainer, said anonymous access works only for profile listings; the reporter closed it on 6 Aug 2026 with no maintainer comment. 1.32.17 dated 17 Oct 2026 on [PyPI](https://pypi.org/pypi/gallery-dl/json). |
| gallery-dl saved posts and collections (`InstagramSavedExtractor`, `InstagramCollectionExtractor`) | The same files and metadata for every post saved to a collection. No link pasting. | Krish's own cookies, since the collection is his. The full collection URL with its numeric ID; all saved posts at `/USERNAME/saved/`. | Home machine | Free | Higher: it must use his own account, polled on a schedule. Keep polling infrequent. | Unverified in 2026. Both extractors are in the current [source](https://github.com/mikf/gallery-dl/blob/master/gallery_dl/extractor/instagram.py) (`/v1/feed/collection/{collection_id}/posts/` and `/v1/feed/saved/posts/`). No 2026 issues were checked. |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) 2026.10.21, logged out with curl-cffi | A playlist with one entry per slide in order; video slides as video; image slides as thumbnails (full size inferred from source, untested); caption, username, full name, timestamp, like, comment and view counts. `--get-comments` adds the comments themselves. | `yt-dlp[default,curl-cffi]`. Cookies only for private or age-gated posts. | Home machine (datacenter IPs untested) | Free | None logged out (bashonly, 29 Jun 2026). With cookies, the same as gallery-dl. | Logged-out extraction broke on 27 to 28 Jun 2026 ([#17074](https://github.com/yt-dlp/yt-dlp/issues/17074)) and was fixed in 2026.07.04 (PR #17075). Logged-in fixed in 2026.08.19 (#17278). Image carousels are out of scope ([#17077](https://github.com/yt-dlp/yt-dlp/issues/17077), closed "not planned"). The [source](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/instagram.py) has an anonymous rate limit. 2026.10.21 is the latest ([Changelog](https://github.com/yt-dlp/yt-dlp/blob/master/Changelog.md)). |
| [instaloader](https://instaloader.github.io/cli-options.html) 4.15.4 (4.16b1 pre-release, 21 Oct 2026) | Every slide as numbered files (`--slide` picks a range); caption as .txt; metadata JSON (`--no-compress-json` for plain JSON). | Nothing for some public posts. A session for anything gated: `--load-cookies firefox`, or `--login`, which triggers checkpoints. `--load-cookies` reads browsers through browser_cookie3, likely with the same Chrome limit (unverified). | Home machine (a [Stack Overflow](https://stackoverflow.com/questions/79392301/instaloader-returning-401-from-instagram-api-when-run-on-vps-but-ok-from-pc-ubu) report of 401 from a VPS, seen in search results only) | Free | None logged out. Logged in, open reports of "feedback_required" and "Checkpoint required" ([#2767](https://github.com/instaloader/instaloader/issues/2767), #2744, #2728). | Skip. The single-post GraphQL path returns a growing share of "execution error" ([#2738](https://github.com/instaloader/instaloader/issues/2738), open, no maintainer reply). Logged-in images are smaller: 1080x794 against 2842x1971 anonymous in a 16 Oct 2026 report ([#2733](https://github.com/instaloader/instaloader/issues/2733); fix PR #2778 unmerged). [#2786](https://github.com/instaloader/instaloader/issues/2786) is 429s on the profile endpoint, not single posts. |
| [apify/instagram-scraper](https://apify.com/apify/instagram-scraper) (official, id shu8hvrXbJbY3Eb9W) | URLs, not files: `type`, caption, `displayUrl`, `images[]`, `childPosts[]` (type, displayUrl, videoUrl, width, height, alt, id, shortCode), owner, timestamp, likes, comments, latest comments, hashtags, mentions, tagged users, music, location, paid partnership. | Apify token (Krish has one) in an `Authorization: Bearer` header. No Instagram login. A `/p/` or `/reel/` shortcode URL, not a numeric ID. | Both | Per 1,000 posts: Free $2.70, Bronze $2.30, Silver $1.90, Gold $1.50, Platinum $0.90, Diamond $0.50. One post: $0.0027 Free, $0.0023 Bronze, no start fee (reels check). Krish's account is on Bronze (reels research). | None to his account. He still commissions collection the terms forbid. | 447,738 users, 58,069 monthly, 4.67/5 from 603 reviews, modified 23 Oct 2026. The inferred output schema from recent runs shows `childPosts` and `images[]` filled for some posts. Every slide in order for a `/p/` link is untested. Sees the logged-out page only. Open issue "restricted_page for a photo post" (23 Oct 2026, a `/p/` photo post with `resultsLimit: 1`; reels check, [open issues](https://apify.com/apify/instagram-scraper/issues/open)). |
| [apify/instagram-post-scraper](https://apify.com/apify/instagram-post-scraper) (official) | Caption, metrics, images, mentions, coauthors, recent comments, sponsored status, video duration and views. URLs only. Carousel children unverified. | Apify token. Post URLs in the `username` field. `dataDetailLevel` defaults to `detailedData`; `resultsLimit` does not apply to post URLs. | Both | Per detailed post: Free $0.0017 + $0.0010 = $0.0027; Bronze $0.0015 + $0.0008 = $0.0023. Music add-on $0.006 on Bronze, paid plans only. | None to his account. | 146,701 users, 17,802 monthly, 4.28/5 from 138 reviews, modified 23 Oct 2026. An open issue titled ["CDN images expire"](https://apify.com/apify/instagram-post-scraper/issues/cdn-images-expire-kJ1JJ7t5CmS5BkTrT) (text unread). Also open: "Since Oct 20: blocked runs" (21 Oct 2026) and "Runs return only BLOCKED errors (marked SUCCEEDED)" (20 Oct 2026) (reels check, [open issues](https://apify.com/apify/instagram-post-scraper/issues/open)), so prefer apify/instagram-scraper for now. |
| [memo23/instagram-video-downloader](https://apify.com/memo23/instagram-video-downloader) (community) | Downloads every slide (images and videos) and the cover. With `storeFiles` on (the default) it re-hosts each file in the run's key-value store, at a URL that lasts as long as Apify keeps the data. Fields: postId, shortcode, postType, caption, createdAt, authorUsername, slides[], slideCount, coverUrl, videoUrl, sourceUrlsExpireAt, filesStored, notes. | Apify token. No Instagram login. | Both | Bronze: $0.0001 a start (per GB of run memory, at least one), $0.002 a post, $0.001 per re-hosted image, $0.003 per re-hosted video. About $0.012 for a 10-image carousel. | None to his account. | Small and young: 182 users, 87 monthly, one 5-star rating, modified 23 Oct 2026. Claims come from its own README. The only source that measured post-media link expiry: 24 to 36 hours, its test reel 31 hours. |
| [data-slayer/instagram-post-details](https://apify.com/data-slayer/instagram-post-details) | About 128 fields from Instagram's raw media object (caption.text, image_versions.items, video_versions, like, comment, save and share counts, user). Carousel handling unverified. | Apify token; input `postUrls`. | Both | $0.002 a start plus $0.00217 a result (Bronze listing). | None to his account. | 4,856 users, 1,721 monthly, 1 rating (5.0), modified 7 Oct 2026. Not tested on carousels. |
| [apidojo/instagram-scraper-api](https://apify.com/apidojo/instagram-scraper-api) | Posts with media URLs ("Instagram Single Post Query" through `startUrls`). Carousel handling unverified. | Apify token. | Both | $0.005 flat per single-post query; the $0.0005 post-item charge applies only beyond each query's free posts. One link: about $0.005 (Bronze listing). | None to his account. | 2,903 users, 447 monthly, 9 ratings at 5/5. Not tested on carousels. |
| Direct HTTPS GET of the CDN URLs any method returns (`scontent-*.cdninstagram.com`, `instagram.*.fbcdn.net`) | The file itself. The URL is signed: `oe` is the expiry as a hexadecimal Unix time, `oh` the signature. Changing `oe` returns 403. | The unmodified URL. yt-dlp sends `Referer: https://www.instagram.com/`; no source says the CDN requires it. | Unclear (an IP tie is untested) | Free | None. No Instagram session. | Every link expires. The only measured post-media figure is memo23's 24 to 36 hours for a reel video. An Apify developer said "normally 24-48 hours" (search results only). [SociaVault's](https://sociavault.com/blog/profile-picture-url-expired) 4.5 days was for profile pictures, not posts. A 403 can also mean a blocked or datacenter IP. |
| Own Playwright capture (custom code) | Everything Instagram's web page receives: every slide in order, video slides, caption, owner, taken_at, like and comment counts. JSON paths unverified. | Python [Playwright](https://playwright.dev/python/docs/api/class-browsertype) (version not checked), a dedicated logged-in profile folder, the machine left on. | Home machine | Free | Low at low volume. Still automated collection under that account. | Unverified: nobody has built or tested it. Instagram renames GraphQL fields and doc_ids ([#2738](https://github.com/instaloader/instaloader/issues/2738)), so the parser needs upkeep. Slowest option. |
| [Business Discovery](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/business_discovery) (official Instagram API with Facebook Login) | For Business or Creator accounts only: caption, media_type (CAROUSEL_ALBUM, IMAGE, VIDEO), media_url, children with media_url, shortcode, permalink, timestamp, like_count, comments_count, username, view_count. Looked up by username, not link. | His professional account linked to a Facebook Page, a Meta app, and a user token with instagram_basic, instagram_manage_insights and pages_read_engagement (plus ads_management or ads_read if the Page role came through Business Manager). | Both | Free (unverified; Meta lists no price). | None. A permitted route. | Stable but narrow. No personal accounts; age-gated business accounts return nothing. media_url is omitted for videos with copyrighted or licensed audio, a carousel's video children included ([IG Media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-media)). Standard Access, with no App Review, covers your own professional accounts ([overview](https://developers.facebook.com/docs/instagram-platform/overview)); whether business_discovery runs under it is unverified. Rate limits not stated. |
| Instagram oEmbed (`GET /instagram_oembed`) | Embed HTML only. No slide images. | A Meta app with Meta oEmbed Read, which needs App Review. | Both | Free | None. | A dead end for media. thumbnail_url, thumbnail_width and thumbnail_height were removed on 3 Nov 2025 ([announced 8 Apr 2025](https://developers.facebook.com/blog/post/2025/04/08/oembed-updates/)). The [reference](https://developers.facebook.com/docs/graph-api/reference/instagram-oembed) now documents only html, provider_name, provider_url, type, version and width. |
| [cobalt](https://github.com/imputnet/cobalt/blob/main/api/README.md), self-hosted (`ghcr.io/imputnet/cobalt`) | In principle photos and videos, with a picker for multi-media posts. No metadata. | Self-hosting. There is no public hosted API. | Unclear | Free plus hosting | None by default. | Skip: no metadata, self-hosting, open Instagram reports (#1509 Feb 2026, #1568 Jun 2026, [#1587](https://github.com/imputnet/cobalt/issues/1587) Aug 2026, a carousel under a `/reel/` code returning only its cover), and image posts failing on a cloud VM, put down to IP reputation ([#1463](https://github.com/imputnet/cobalt/issues/1463), closed 20 Nov 2025). |
| Firecrawl scrape of instagram.com | Nothing reliable. | Firecrawl key (Krish has one). | Unclear | Firecrawl credits. Balance 0 of 1,000 until 9 Nov 2026. | None. | Reportedly refuses Instagram with "...please reach out to help@firecrawl.com for more info on how to activate it on your account" ([competitor blog](https://scrapecreators.com/blog/firecrawl-social-scraping-restrictions); unverified, no official statement). Not tested by this research. The reels research reports one plain scrape of instagram.com on 24 Oct 2026 that returned "we do not support this site". |
| [HikerAPI](https://hikerapi.com/pricing) (added by the check) | Media object by URL or code (`GET /v2/media/info/by/url`, `/v2/media/info/by/code`), plus `/v1/media/download/photo/by/url` and `/v1/media/download/video/by/url` ([OpenAPI v1.8.3](https://api.hikerapi.com/openapi.json)). Every carousel slide unverified. | A HikerAPI account, prepaid. It runs its own Instagram accounts; the pricing page does not state a login. | Both | $1 per 1,000 requests at the popular rate, $0.60 per 1,000 at volume, prepaid; 100 free requests. One test call about $0.001. | None to his account. Same terms position as Apify. | Not tested on carousels. |
| [ScrapeCreators](https://scrapecreators.com/tutorials/how-to-scrape-instagram-post-with-nodejs) (added by the check) | `GET https://api.scrapecreators.com/v1/instagram/post?url=<url>` with an `x-api-key` header. `download_media=true` returns permanent hosted copies. Slide field names unverified. | A ScrapeCreators account and key. | Both | 1 credit a plain call; 10 credits with `download_media` when media is found (1 otherwise); 0 for a cached copy (`cache_max_age`). $47 per 25,000 credits, about $1.88 per 1,000 ([prices checked Jul 2026 by a competitor](https://www.socialcrawl.dev/blog/best-instagram-data-apis-2026)). About $0.002 a post, $0.019 with permanent media. | None to his account. | Its [free photo and carousel tool](https://scrapecreators.com/free-tools/instagram-photo-downloader) runs on this endpoint. Not tested. |
| Oriane `instagram/post-lookup` through Firecrawl's Alexandria catalogue (added by the check) | Caption, counts, mediaCount, thumbnailMediaUrl, coauthors; on the 'full' tier a transcript, transcriptChunks and frames. No per-slide media URLs. | Firecrawl credits. It reads Oriane's existing index only; "Empty results do not trigger ingestion". | Not stated | 20, 30 or 40 Firecrawl credits per call that finds the post; misses are free. | None. | Cannot run now: the balance is 0 until 9 Nov 2026. A caption and metadata fallback for posts Oriane already holds, nothing more. |
| [instagrapi](https://pypi.org/project/instagrapi/) 3.2.0 (added by the check) | Full `carousel_media` from Instagram's private mobile API. | A username and password, or a saved session. | Not stated | Free to install from PyPI | The highest of any route: mobile-API logins are what Instagram checkpoints. | Released 24 Oct 2026, with releases every few days in October. Listed and deliberately rejected. |
| Link cleaning before any fetcher (added by the check; a step, not a fetcher) | The canonical `/p/SHORTCODE/` URL and a stable key for removing duplicates. | Follow the `/share/` redirect; strip `?igsh=` and other query strings. | Both | Free | None. | gallery-dl resolves `/share/` itself ([instagram.py](https://github.com/mikf/gallery-dl/blob/master/gallery_dl/extractor/instagram.py)); yt-dlp since 2024.12.03. [Apify](https://apify.com/apify/instagram-scraper) needs the shortcode form: "Not supported: numeric post IDs in URL form". |
| [Meta Content Library API](https://developers.facebook.com/docs/content-library-api/get-access) (added by the check) | Meta's permitted research access to public content. | Researchers at accredited academic institutions or research non-profits, vetted by ICPSR, recertified yearly. | Not applicable | Free | None. | Ruled out: Mindmake does not qualify ([Meta transparency](https://transparency.meta.com/researchtools/meta-content-library/)). |
| [seemuapps/instagram-video-downloader](https://apify.com/seemuapps/instagram-video-downloader) (added by the check) | Takes a post URL; has a `saveFiles` option. Output not checked. | Apify token. | Both | $0.005 a post "regardless of carousel size" (tier not stated). | None to his account. | Not recommended: 477 users, one 1/5 rating. |
| [igview-owner/instagram-video-downloader](https://apify.com/igview-owner/instagram-video-downloader) (added by the check) | Takes a post URL. Output not checked. | Apify token. | Both | $0.005 a start plus $0.005 a result (tier not stated). | None to his account. | Not recommended: 862 users, one rating. |
| Bright Data Instagram records (added by the check) | Instagram post records. Output not checked. | A Bright Data account, which Krish does not have. | Not stated | About $1.50 per 1,000 ([comparison checked Jul 2026](https://www.socialcrawl.dev/blog/best-instagram-data-apis-2026)). | None to his account. | Not recommended: a new vendor. |
| Logged-out embed page `https://www.instagram.com/p/SHORTCODE/embed/captioned/` (added by the check) | Probably the cover image and caption only (unverified). | Nothing. | Home machine (test it there) | Free | None. | The old anonymous fallback. [cobalt #1587](https://github.com/imputnet/cobalt/issues/1587) reports its page format changed. From a cloud sandbox on 24 Oct 2026, plain curl with a Chrome user agent got Instagram's error page, with no caption or media, for two `/p/.../embed/captioned/` pages (reels check); that test cannot tell an IP block from a missing browser fingerprint. Unverified from a residential IP: test once there before ruling it in or out. |

### Corrections applied

1. Saved collection: the command now uses the full collection URL with its numeric ID; all saved posts sit at `/USERNAME/saved/` or `/saved/all-posts/`.
2. Link lifetime: dropped "images last about 4.5 days" (SociaVault measured profile pictures); every post URL is now treated as lasting about a day, downloaded in the same job, with its life logged in hours.
3. cobalt: still skipped, but for no metadata, self-hosting, open Instagram reports and cloud-VM IP reputation; #1587 covers a carousel under a `/reel/` code only.
4. The `wd` cookie: moved from a setup rule to a troubleshooting step after gallery-dl's low-resolution warning.
5. Account risk: the gallery-dl issues no longer stand for checkpoints. #8978 and #9777 are 429s on profile lookups, avatar and tagged; #9346 was a stale gallery-dl 1.27.0 on the PATH. Only instaloader #2767 shows a checkpoint.
6. gallery-dl reliability: the single-post path is now described as stable, and "breaks every few weeks" applies to profile listings. This also qualifies BRIEF.md section 6's "eight gallery-dl releases" line; the reels check counts six releases in that span, 1.32.12 to 1.32.17.
7. gallery-dl #9564: the "anonymous access only for profile listings" line is now a commenter's, backed by the source code, not a maintainer's.
8. Video slides: `extractor.instagram.videos: "merged"` now avoids yt-dlp and ffmpeg; the slide count is checked by our code, because gallery-dl warns only about resolution.
9. Business Discovery: a carousel's video children can lack media_url; Standard Access without App Review covers your own professional accounts, and business_discovery under it stays unverified.
10. apify/instagram-post-scraper price: $0.0027 a detailed post on Free, $0.0023 on Bronze; the music add-on is paid plans only; `dataDetailLevel` defaults to detailed; `resultsLimit` is ignored for post URLs.
11. apify/instagram-scraper: `childPosts` is filled in some real runs, unlike the docs' empty sample; slide order is still untested; it sees the logged-out page and takes no numeric IDs.
12. Apify token: moved from `?token=` in the URL to an `Authorization: Bearer` header.
13. Smaller Apify facts: data-slayer has 1 rating and 4,856 users; apidojo costs about $0.005 a link; memo23's start fee is per GB of run memory.
14. Firecrawl: the refusal text suggests access on request (unverified), and the balance is 0 of 1,000 until 9 Nov 2026.
15. Chrome cookies: gallery-dl's own `cookies.py` is now cited (no App-Bound branch, inferred), and yt-dlp #10927 is noted as locked since 7 Jan 2026.
16. oEmbed: the removed-field list now names only the thumbnail fields, since author_name and author_url are listed for the Facebook endpoints; the conclusion is unchanged.
17. Confirmed with no change: yt-dlp 2026.10.21 and its June to August fixes, instaloader's versions and issue states, and the terms quotes; added the 16 Oct 2026 instaloader report (1080x794 against 2842x1971) and that #2786 is the profile endpoint.
18. From the reels research and its check, which cover the same actors and tools: Krish's Apify account is on Bronze; instagram-scraper has no start fee; every Apify item is checked for `error`, `errorDescription` and `requestErrorMessages` even when the run succeeded; the open "restricted_page for a photo post" issue; the post scraper's open "blocked" issues; never yt-dlp's self-updater; the cloud test of the embed page; and Firecrawl's "we do not support this site" reply.
19. Added for the builder, not from the research, and each marked where it appears: the order of steps for each D2 answer, the class names, the fall-through action for each error, the `-D` and `-P` job folders, and calling each tool through the pinned Python. Checked against the installed gallery-dl 1.32.17 and yt-dlp 2026.10.21 on 24 Oct 2026, with no live post: every flag in the commands exists in their `--help`, `-o extractor.instagram.videos=merged` sets that key, a Firefox profile is a folder name or a path (with none, the most recently used profile's cookies are taken), and a single-image post's file is named `<id>_NA.<ext>`.

### Open questions

1. Does apify/instagram-scraper return every slide, in display order, for a `/p/` carousel? Test: one run on a known carousel of five or more slides, $0.0023 at his Bronze tier, comparing `childPosts` and `images[]` with the app. It spends, so it needs Krish's yes first.
2. Does yt-dlp's `--write-thumbnail` save each image slide at full size? Test: run step 2 on one carousel and compare each image's pixel size with the original size Instagram reports. Which info JSON field holds that size is unverified; read it off this run. Free, no account.
3. Does any single post work in gallery-dl without cookies? The source says no. Test: `python -m gallery_dl -j "https://www.instagram.com/p/SHORTCODE/"` once from the home machine with no cookies. Free, no account.
4. Are Instagram CDN URLs tied to the IP that requested them? Test: fetch one URL obtained at home from a GitHub Actions runner, and the reverse, passing the URL without printing it. Free.
5. How long do post image and video links live? Test: decode `oe` on every URL the fetcher gets for one week and log the remaining hours as counts, split by image and video. Free.
6. Whose cookies does the home machine use: Krish's main account or a secondary one? This is his call inside D2. Test: ask him. The saved-collection route needs his own.
7. Would Krish rather tap Save into a collection than paste links, and does the collection extractor work in 2026? Test: ask him; then, with his yes, one `python -m gallery_dl -j` on the full collection URL with his cookies.
8. Do most posts Krish likes come from Business or Creator accounts? Test: note the account type of the first 20 links he pastes. If most qualify, a second test follows: one Business Discovery call from a Standard Access app against one Creator account settles whether App Review is needed.
9. Do the Playwright capture's JSON paths (`xdt_api__v1__media__shortcode__web_info`) hold today? Test: one capture of one carousel in the dedicated profile, after D2. Free, but it uses the account.
10. Does the logged-out embed page give anything beyond the cover and caption, from a residential IP? From the cloud it gave only Instagram's error page (reels check). Test: one GET of `/p/SHORTCODE/embed/captioned/` from the home machine. Free, no account.
11. Does memo23 re-host every slide as its README claims? Test, only if question 1 fails: one run on the same carousel, about $0.012 on Bronze for 10 images, with Krish's yes.
12. Does HikerAPI return every carousel slide? Test, only if Apify fails: one `/v2/media/info/by/url` call inside its 100 free requests. It needs a new account, so Krish's yes first.
13. What are ScrapeCreators' slide field names, and does it return every slide? Test, only if Apify fails: one plain call, 1 credit (about $0.002). New account, so Krish's yes first.
14. Can Firecrawl be switched on for instagram.com? Low value, since the chain covers Instagram. Test: one scrape of one `/p/` URL after the balance resets on 9 Nov 2026.
15. Which gallery-dl metadata field gives a post's slide count, so the closing check has a number that does not come from the files themselves? Test: one `python -m gallery_dl -j` on a known carousel of five or more slides with the D2 profile, compared with the app. Free, but it uses the account, so after D2.

### Terms

Instagram's [Terms of Use](https://www.facebook.com/help/instagram/581066165581870): "You can't attempt to create accounts or access or collect information in unauthorized ways. This includes creating accounts or accessing or collecting information in an automated way without our express permission." Meta's [Automated Data Collection Terms](https://www.facebook.com/legal/automated_data_collection_terms) (effective 7 Oct 2024) also require written permission, though that page does not say whether it covers Instagram.

So gallery-dl, yt-dlp, instaloader, cobalt, the Apify actors, HikerAPI and a Playwright script all break the terms,
whether Krish's machine runs the code or Apify does. The two routes Meta permits are Business Discovery and the Meta
Content Library, and Mindmake does not qualify for the second. Private study lowers copyright exposure, not the breach
(not legal advice). In practice Instagram enforces with rate limits, checkpoints and restrictions on the session used.

## TikTok: videos and photo posts (slideshows)

Researched on 2026-10-24 against issue trackers, release notes, Apify actor pages and TikTok's own pages. A second
reader then checked it. Every one of its corrections is applied below, and where the two disagree the correction is
used. Nothing here was run against a post Krish saved. "Unverified" and "inference" mean exactly that.

### Recommended chain

**The gates, before anything runs.**

- Steps 0 to 3a are free and use no account of his. Build them now. Their first live run is the once-per-platform
  check on the home machine, with his yes (brief section 7.2).
- Step 3b sends each link to an anonymous outside service. No rule of his covers that, so ask him once before turning
  it on (a recommendation, not his ruling).
- Step 4, and the paid half of step 5, spend on his Apify account. Each runs only on his yes given right before the
  run, or inside a standing monthly cap he sets. If he sets a cap with D2, ask whether it covers TikTok too. Without
  either, stop with `apify_spend_not_approved`.
- Step 6, and any route that uses his cookies or his signed-in browser, waits on his yes for that account.
- Nothing here calls a model. The text comes from TikTok's own captions or from faster-whisper on the home machine
  (brief section 7.3). Leave every Apify AI transcript option off.
- Logs carry counts and class names only: never a link, a caption, a transcript, a file name, an error message, a
  cookie or a token (yt-dlp's and gallery-dl's error text carries the link). Read the Apify token by its name,
  `APIFY_TOKEN`, at run time. Record which step worked as the fetcher's class name, and every failure as a fixed
  `status_class` (brief section 4). Suggested classes (a proposal, from no source): `tt_unsupported_url`,
  `tt_challenge`, `tt_rehydration`, `tt_http_403`, `tt_ip_blocked`, `tt_impersonation_blocked`, `tt_no_audio`,
  `tt_login_wall`, `tt_media_url_failed`, `tikwm_error`, `apify_item_error`, `apify_spend_not_approved`, `timeout`,
  and `tt_other` for any error no rule below names.
- Files land in the fetcher's local work folder. Where they are filed waits on D1.
- Download every media URL at once. TikTok's CDN links expire (brief section 6).
- Run every tool through the pinned Python the fetcher itself runs on: `[sys.executable, "-m", "yt_dlp", ...]` and
  `[sys.executable, "-m", "gallery_dl", ...]`, passed as a list to `subprocess.run` with a timeout and no shell. On
  Windows a bare `yt-dlp` can resolve to another copy on the PATH, without the pins below. The commands below are
  written for a PowerShell or cmd prompt; in a `.bat` file every `%` in an output template must be doubled.

**The fall-through, in one line.** Step 0, then step 1 for a video or step 2 for a photo post (a silent file from
step 1 also goes to step 2), then 3a, then 3b (only once he has agreed), then 4 (only with his yes or inside his cap),
then stop with the last class. The first step that gives the post's media wins. Step 5 runs only for
comments. Step 6 runs only for a login-walled post, only with his yes for that account; without it, stop with
`tt_login_wall`.

**On the home Windows machine (residential IP), for each pasted link.**

**0. Normalise the link.** Follow a `vm.tiktok.com`, `vt.tiktok.com` or `tiktok.com/t/` short link to its canonical
`https://www.tiktok.com/@<user>/video/<id>` or `/photo/<id>` URL and drop the query string. That is `url_key`. A
`/photo/` path is a photo post. yt-dlp has a `vm.tiktok` extractor and added "Support share URLs" in 2026.08.19, and
gallery-dl accepts `vm.` and `vt.` links, so this is for a stable key, not for the tools
([yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases),
[gallery-dl tiktok.py](https://raw.githubusercontent.com/mikf/gallery-dl/master/gallery_dl/extractor/tiktok.py)).
A sketch in the standard library (brief section 7.1), untested against TikTok's short links. `BROWSER_UA` is a
current desktop browser User-Agent string:

```python
import urllib.request

req = urllib.request.Request(link, headers={"User-Agent": BROWSER_UA})
with urllib.request.urlopen(req, timeout=20) as r:  # follows redirects
    url_key = r.geturl().split("?")[0]
```

Then a `/video/<id>` key goes to step 1 and a `/photo/<id>` key to step 2. Anything else (a profile, a login page)
is `tt_unsupported_url`: stop there.

Skip oEmbed. From Google Cloud on 2026-10-24 it returned no caption, it answered a `/photo/` URL with HTTP 400, and
TikTok says it "will be deprecated soon" ([embed-videos](https://developers.tiktok.com/doc/embed-videos)). Cost: free.

**1. A video post: yt-dlp 2026.10.21, with curl_cffi pinned at 0.16.0. Free, no login.**

Install it fresh with pip rather than self-updating an older copy. 2026.10.21 is a security release, "Old yt-dlp
executables are vulnerable to man-in-the-middle attacks" (certifi advisory GHSA-6q48-6c7w-9gw2), and it advises a
fresh manual install rather than `-U` if you suspect you are targeted
([Changelog](https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/Changelog.md)). Pin curl_cffi in the same
command. Without the pin, pip resolves the extra to curl_cffi 0.16.3 (the extra's range starts at 0.5.10 and stops
below 0.17, and yt-dlp's own `pin-curl-cffi` extra fixes 0.16.3, [pyproject.toml](https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/pyproject.toml)).
The check quoted that range with its middle left out, so whether it excludes 0.16.0 is unverified; if pip refuses
the pair as a conflict, use the user-agent fix below instead. The chrome-150 target from curl_cffi 0.16.2 has been
"blocked outright" since 2026-09-01, and whether 0.16.3 is blocked too is unverified
([#17604](https://github.com/yt-dlp/yt-dlp/issues/17604), open, no maintainer reply).

```
python -m pip install "yt-dlp[default,curl-cffi]==2026.10.21" "curl_cffi==0.16.0"
python -m yt_dlp --write-info-json --write-subs --sub-langs all --write-thumbnail -P "<work folder>" -o "%(id)s.%(ext)s" "<url_key>"
```

- The other working fix in #17604: keep curl_cffi 0.16.3 (install with the first requirement only) and add
  `--user-agent "<a current desktop browser User-Agent>"` to every yt-dlp run. Three users confirmed it through
  2026-09-25.
- It gets the video (separate video and audio merged by ffmpeg, so ffmpeg must be on the path), the caption, the
  uploader handle, the timestamp, view, like, comment, repost and save counts, the thumbnail, music info, and
  TikTok's subtitles when the post has them. The `.info.json` is the text record. No comments: tiktok.py has no
  comment extractor ([tiktok.py](https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/yt_dlp/extractor/tiktok.py)).
- Then check for sound: `ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "<file>"`. Empty
  output means no audio stream. Record `tt_no_audio` and go to step 2.
- Updates: no stable release has touched TikTok since 2026.08.19, so a weekly update only helps through the nightly
  builds on PyPI (2026.10.23.dev0 was there when read on 2026-10-24, [PyPI](https://pypi.org/pypi/yt-dlp/json)). Update with
  `python -m pip install -U --pre "yt-dlp[default,curl-cffi]" "curl_cffi==0.16.0"`, keeping the pin. This replaces
  the brief's `yt-dlp -U` line for TikTok.
- Fall through to step 2 on "Unsupported URL" (a photo post that slipped past step 0). Fall through to step 3 on
  HTTP 403, "Unexpected response from webpage request" ([#17403](https://github.com/yt-dlp/yt-dlp/issues/17403)),
  "Unable to extract universal data for rehydration" ([#17393](https://github.com/yt-dlp/yt-dlp/issues/17393), open),
  the impersonation block, a timeout, or any other error (`tt_other`). The impersonation block's error text is not in
  the research, so the catch-all is what catches it until the live check records it. Go to step 6 only on "This
  post may not be comfortable for some audiences. Log in for access" or a private post (the private post's error
  text is not in the research either). Without his yes for an account, stop there with `tt_login_wall`: no later
  step logs in.
- Cost: free.

**2. A photo post, or a silent video file: gallery-dl from master. Free, no login.**

The fix for "Many posts return 403" (GitHub [#9796](https://github.com/mikf/gallery-dl/issues/9796), refiled as
Codeberg #549, closed 2026-10-22) is merged: master's `_solve_challenge` now keeps the base64 padding
([commit 912138b7ca](https://codeberg.org/mikf/gallery-dl/commit/912138b7ca95ea83db0f91c0037299f4f5c67143),
[Codeberg #549](https://codeberg.org/api/v1/repos/mikf/gallery-dl/issues/549)). It is not in 1.32.17 (released
2026-10-17, [PyPI](https://pypi.org/pypi/gallery-dl/json)). Run master until the first release after 1.32.17, or
apply that commit as a patch. The GitHub master carries the fix (the check read it there). Once a later release is
on PyPI, go back to `python -m pip install -U gallery-dl`.

```
python -m pip install -U --force-reinstall https://github.com/mikf/gallery-dl/archive/master.tar.gz
python -m gallery_dl --write-metadata -o covers=true -D "<work folder>" "<url_key>"
```

`-D` puts the files in that folder exactly, rather than in gallery-dl's own nested folders.

- Pass a `/photo/` URL as it is. gallery-dl rewrites it to `/video/` before it fetches the page. Audio is on by
  default, so `-o audio=true` adds nothing. Covers are off by default, hence `-o covers=true`.
- It gets every slide at full size (with its number, width and height), the post's audio as an mp3, and a metadata
  JSON (`desc` as `title`, `author.uniqueId` as `user`, `createTime` as `date`, `post_type`, and the full post
  dictionary). For a video it takes the direct file from `bitrateInfo` or `playAddr`. No comments
  ([supportedsites](https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md)).
- Run the same ffprobe check. Some gallery-dl videos come out silent
  ([#9764](https://github.com/mikf/gallery-dl/issues/9764), open). mikf's workaround on
  [#9748](https://github.com/mikf/gallery-dl/issues/9748) is `-o videos=ytdl -o audio=ytdl`, which hands the video
  back to yt-dlp. That helps only when yt-dlp itself is healthy, and in this chain yt-dlp has already given its file
  for a video, so do not retry with it here. If yt-dlp's file and gallery-dl's file are both silent, go to step 3.
- Watch Codeberg as well as GitHub. gallery-dl's home moved there, and new TikTok bugs are filed there: #547 (open,
  a fallback when rehydration data cannot be extracted), #540 (open) and #244 (open, 403)
  ([Codeberg TikTok issues](https://codeberg.org/api/v1/repos/mikf/gallery-dl/issues?q=tiktok&state=all)). mikf
  wrote "I do not get any JS/WAF challenges", so he cannot test TikTok fixes himself.
- Fall through to step 3 on HTTP 403, "You may need cookies to continue", a rehydration failure, a timeout, or any
  other error (`tt_other`).
- Cost: free.

**3. Free fallbacks, before any spend.**

3a. **Read the post page directly.** `GET https://www.tiktok.com/@<user>/video/<id>` with a browser User-Agent
(a photo post fetched as `/video/` works), then parse `<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">` and take
`__DEFAULT_SCOPE__['webapp.video-detail'].itemInfo.itemStruct`. It holds `desc` (the caption), `author.uniqueId`,
`createTime`, `stats` (playCount, diggCount, commentCount, shareCount, collectCount), `video.playAddr` and
`bitrateInfo`, `imagePost.images` for a photo post, `music.playUrl`, and `video.subtitleInfos` and
`video.claInfo.captionInfos`. Those last two say whether TikTok captions exist before anything is transcribed
(`noCaptionReason` when they do not). The `comments` key is an empty list, so the page has no comments.
- Tested twice on 2026-10-24 from a Google Cloud IP with plain curl: HTTP 200, statusCode 0, full fields, for a video
  post and a photo post (1 image, audio present). No challenge was served. Single samples.
- It is the same request yt-dlp and gallery-dl make. If a WAF challenge stopped them, it will likely stop this too
  (inference). It can help when only yt-dlp's impersonation is blocked, since plain curl was not blocked in the test
  (inference).
- The metadata worked in both tests. The media URLs are signed CDN links, and downloading them was not tested. Send
  the media GET with the same User-Agent and the cookies the page response set; whether those cookies are needed is
  open question 9.
- It failed if the script tag is missing (`tt_rehydration`, or `tt_challenge` when a challenge page came back), if
  `statusCode` is not 0 (the research quotes 10204 as "Your IP address is blocked": `tt_ip_blocked`), or if
  `itemStruct` is absent. A media URL that will not download is `tt_media_url_failed`. Either way go to 3b; when the
  metadata came and only the media failed, keep the metadata.
- Cost: free. Sources: [tiktok.py](https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/yt_dlp/extractor/tiktok.py),
  [test post](https://www.tiktok.com/@scout2015/video/6718335390845095173) (own fetch).

3b. **TikWM, only once Krish has agreed.** `GET https://www.tikwm.com/api/?url=<url_key>&hd=1`. On 2026-10-24 from a
Google Cloud IP it returned code 0 for a video post, with `title` (the caption), `author.unique_id`, play, digg,
comment, share, collect and download counts, `create_time`, `music_info`, and `play`, `hdplay` and `wmplay` media
URLs. For a `/photo/` post it returned an `images` list and the music. No key, no login. Its rate limits and terms
are unverified (the homepage returned 403 and no docs page was found). It is an anonymous third party with no
contract, and it sees every link sent to it. A free fallback for metadata and media URLs, never the main route.
Whether its media URLs download is untested. Treat any `code` other than 0 as `tikwm_error`. Until he has agreed,
skip 3b. Cost: free. Source: [TikWM API](https://www.tikwm.com/api/).

Fall through to step 4 when 3a and 3b give no media.

**4. Apify `clockworks/tiktok-video-scraper` (id `S5h7zRLfKFEr8pdj7`). Paid. No TikTok account.**

Before asking for his yes, show the estimate (brief section 9, "Estimate before any paid run"): the number of posts
times about $0.003 at BRONZE, with photo posts marked as unpriced (open question 5). Then start the run
asynchronously and poll. The synchronous `run-sync-get-dataset-items` call returns 408 when a run passes 300 seconds,
and a run with downloads may pass it ([Apify docs](https://docs.apify.com/api/v2/act-run-sync-get-dataset-items-post)).

```
POST https://api.apify.com/v2/acts/clockworks~tiktok-video-scraper/runs
Authorization: Bearer <APIFY_TOKEN>
Content-Type: application/json

{"postURLs": ["<url_key>"], "shouldDownloadVideos": true, "shouldDownloadSlideshowImages": true,
 "shouldDownloadCovers": true, "downloadSubtitlesOptions": "DOWNLOAD_SUBTITLES",
 "videoKvStoreIdOrName": "content-watcher"}
```

- Keep `downloadSubtitlesOptions` at `DOWNLOAD_SUBTITLES`. Its two other values the research names,
  `DOWNLOAD_AND_TRANSCRIBE_VIDEOS_WITHOUT_SUBTITLES` and `TRANSCRIBE_ALL_VIDEOS`, turn on the paid AI transcript.
- Poll `GET https://api.apify.com/v2/actor-runs/<run id>` until `status` is `SUCCEEDED`, read
  `GET https://api.apify.com/v2/datasets/<defaultDatasetId>/items`, and download every file in `mediaUrls` at once.
  Stop polling on any other end state too, and give the poll its own time limit (`timeout`). The run stats count
  failed, aborted and timed-out runs, but the exact status strings for those are not in the research. Whether the
  `mediaUrls` downloads need the token is not in the research either.
  These start, poll and dataset paths are not in the research (unverified); confirm them in Apify's API reference
  along with open question 7. Apify's current docs write the actor path as `/v2/actors/:actorId/...`. The
  `/v2/acts/` form above is the one the research read actor data from, and was not re-checked for starting runs.
- A run can succeed while the item for one URL is an error record (`error`, `errorCode`). Check every item, and
  record `apify_item_error`. Run success is not post success.
- It gets the caption (`text`), `textLanguage`, `createTimeISO`, `authorMeta`, play, digg, comment, share, collect
  and repost counts, hashtags, mentions, `musicMeta`, `videoMeta` (duration, width, height, `coverUrl`,
  `downloadAddr`, `subtitleLinks`), `isSlideshow`, `slideshowImageLinks`, and `mediaUrls` for the stored files. No
  comments.
- Storage: a named key-value store is kept until it is deleted, and storage is billed while it exists (rate not
  checked, [storage usage](https://docs.apify.com/platform/storage/usage)). Pull each file, then remove it. That
  removal is a delete on his Apify account, so make it part of what he approves for this step. Whether the actor runs
  without `videoKvStoreIdOrName`, leaving the files in the run's own store, which follows the plan's retention, is
  open question 6.
- Cost at BRONZE (the tier the connected Apify account reports, unverified as his plan): $0.002 per video plus $0.001
  for the video-download add-on, about $0.003 a post with the file. At FREE: $0.003 plus $0.0013. The actor has no
  pricing event for slideshow images, so they have no listed price. Never turn on the transcript add-on ($0.041 per
  started minute at BRONZE): transcribe on the home machine instead
  ([actor](https://apify.com/clockworks/tiktok-video-scraper),
  [actor API](https://api.apify.com/v2/acts/clockworks~tiktok-video-scraper)).
- Health: modified 2026-10-23. Over the 30 days to 2026-10-24, 636,089 of 638,682 runs succeeded (99.6%) and 2,216
  failed. 4.6 from 35 reviews, 2.7K monthly users.
- A second actor lists a lower price: `scrape-creators/best-tiktok-video-scraper` (id `rFfyNgnvUxD1bm8hh`) at
  $0.002 a result at BRONZE, with an images field and an optional transcript. Its input fields are `videos` (a list
  of URLs), `shouldGetTranscript`, `shouldDownloadVideos` and `shouldDownloadCovers`; their types and defaults are not
  in the research. Leave `shouldGetTranscript` off. Whether its video download costs extra is not in the research. It
  has 137 monthly users and was last modified 2026-09-04, so keep clockworks first (a judgment) and hold this one as
  the second Apify try. That try is a second paid run, so it needs its own yes or room in his cap.

**5. Comments, only if Krish wants them.** yt-dlp, gallery-dl and the page read give none.
- Free, on the home machine: TikTokApi 7.3.3, `Video.comments(count=20, cursor=0)`
  ([video.py](https://raw.githubusercontent.com/davidteather/TikTok-Api/main/TikTokApi/api/video.py)). Install with
  `python -m pip install "TikTokApi==7.3.3"` then `python -m playwright install`. It needs an `ms_token` cookie and
  a Playwright browser, and it is prone to bot detection ("EmptyResponseException"). An `ms_token` from his
  signed-in browser ties the requests to his session (unverified risk), so that needs his yes. Whether a logged-out
  `ms_token` works is open question 14.
- Paid, with his yes: `clockworks/tiktok-comments-scraper` (id `BDec00yAmCm1QbMEI`) at $0.001 per comment (BRONZE),
  with input fields `postURLs` and `commentsPerPost`, so the estimate is posts times `commentsPerPost` times $0.001;
  or `commentsPerPost` on `clockworks/tiktok-scraper` (id `GdWCkxBtKWOsKjdch`) at $0.003 per result, $0.001 per actor
  start, $0.001 per video download and $0.001 per comment (BRONZE)
  ([tiktok-scraper](https://apify.com/clockworks/tiktok-scraper),
  [comments scraper](https://apify.com/clockworks/tiktok-comments-scraper)).

**6. A login-walled post only (private, or "not comfortable for some audiences"): yt-dlp with Firefox cookies.**
Only with his yes for the account it uses.

```
python -m yt_dlp --cookies-from-browser firefox:<profile> --write-info-json --write-subs --sub-langs all --write-thumbnail -P "<work folder>" -o "%(id)s.%(ext)s" "<url_key>"
```

Or `--cookies cookies.txt` exported from a Firefox profile. Without his yes for that account, this step does not
run: the request stops with `tt_login_wall`. Chrome's cookies fail on Windows because of its app-bound
encryption ([#10927](https://github.com/yt-dlp/yt-dlp/issues/10927), open, locked 2026-01-07). His cookies tie the
automated access to his account. No reports of bans for this were found (unverified). Cost: free.

**On GitHub Actions.** Start at step 4, as brief section 6 says, and never put a TikTok cookie there. The free steps
are untested on Azure runner IPs; open question 1 settles that. One hosting-VPS tester failed in #17604, and the
Google Cloud page reads worked.

**Text after the fetch.** Use TikTok's own captions when the post has them (yt-dlp's `--write-subs`, or the page
JSON's `subtitleInfos` and `claInfo.captionInfos`). Otherwise transcribe with faster-whisper on the home machine. The
paid transcript actors in the table are not needed.

**Filling the normalised post (brief section 7.2).** The post id comes from `url_key` on every route. The names are
the ones the research read. yt-dlp's `.info.json` key names are not in it, so read them from the first live file.

| Field | yt-dlp `.info.json` | gallery-dl metadata JSON | Page read (3a), `itemStruct` | TikWM (3b) | Apify clockworks (4) |
|---|---|---|---|---|---|
| Author | the uploader handle | `user` (from `author.uniqueId`) | `author.uniqueId` | `author.unique_id` | `authorMeta.name` (that this is the handle and `nickName` the display name is inference) |
| Posted | the timestamp | `date` (from `createTime`) | `createTime` | `create_time` | `createTimeISO` |
| Caption | the description | `title` (from `desc`) | `desc` | `title` | `text` |
| Counts | view, like, comment, repost and save | not listed in the research | `stats`: playCount, diggCount, commentCount, shareCount, collectCount | `play_count`, and the digg, comment, share, collect and download counts | playCount, diggCount, commentCount, shareCount, collectCount, repostCount |
| Media, in order | the merged video file | the slides by their number, then the mp3 | `video.playAddr` or `bitrateInfo`, `imagePost.images`, `music.playUrl` | `play`, `hdplay`, `wmplay`, `images`, the music | `mediaUrls` |
| TikTok's captions | the `--write-subs` files | optional (ASR or MT; the option name is not in the research) | `video.subtitleInfos`, `video.claInfo.captionInfos` | not listed | `videoMeta.subtitleLinks` |

**A one-off backfill, if he wants it.** TikTok's own "Download your data" export (Settings > Account > Download your
data, JSON or TXT) is the one route TikTok sanctions that lists what he has already liked. It gives links and
metadata, not media, so a batch of its links could go through steps 0 to 3. Only he can request it.

**Do not build on:** Firecrawl (every scrape on 2026-10-24 returned "Insufficient credits", and the refusal claim rests on one test and a competitor's
blog), oEmbed (embed only, being deprecated), the Display API (his own videos only), the Research API (not eligible,
no media), cobalt (open TikTok failures in 2026), `epctex/tiktok-video-downloader` (no photo posts, 98 monthly users),
`apidojo/tiktok-scraper` (metadata only, no files). TikTokApi only for comments.

**Cost per post:** $0 when steps 1 to 3 work. About $0.003 at BRONZE when step 4 runs on a video post. A photo post
has no listed price: about $0.003 if it is charged like a video (inference), and open question 5 settles it. Comments
add $0.001 each at BRONZE, paid, or nothing through TikTokApi.

### Methods

| Method | Gets | Needs | Works from | Cost | Account risk | State in October 2026 |
|---|---|---|---|---|---|---|
| yt-dlp 2026.10.21 (`TikTokIE` and `vm.tiktok` extractors) | Video posts: the video (best format, separate streams merged by ffmpeg), caption, uploader handle, timestamp, view, like, comment, repost and save counts, thumbnail, music info, TikTok's subtitles when the post has them. No comments. Photo posts: no. `_VALID_URL` accepts only `/video/`, `/share/video/` and `/embed/`; a `/photo/` URL is "Unsupported URL", and the same post as `/video/` gets the audio only. | Nothing for public posts. curl_cffi 0.16.0 (pinned), ffmpeg. Cookies only for private or age-gated posts, from Firefox or cookies.txt (Chrome fails on Windows, [#10927](https://github.com/yt-dlp/yt-dlp/issues/10927)). | Home machine. Actions (Azure) untested; a hosting-VPS tester failed in #17604; one Google Cloud page fetch got HTTP 200 (media not tested). | Free | None without cookies. With his cookies the automated access is tied to his account; no ban reports found (unverified). | Breaks every few weeks and is fixed: 2026.03.13 "Fix challenge solving"; 10 to 19 Aug "Unexpected response from webpage request" ([#17403](https://github.com/yt-dlp/yt-dlp/issues/17403)), fixed in 2026.08.19. Since 1 Sep the chrome-150 target from curl_cffi 0.16.2 is blocked ([#17604](https://github.com/yt-dlp/yt-dlp/issues/17604), open). Intermittent "Unable to extract universal data for rehydration" ([#17393](https://github.com/yt-dlp/yt-dlp/issues/17393), open). No stable release has touched TikTok since 2026.08.19; 2026.10.21 is a security release; nightly 2026.10.23.dev0 is on PyPI ([Changelog](https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/Changelog.md)). |
| gallery-dl (`TiktokPostExtractor`, `TiktokVmpostExtractor`), master until the release after 1.32.17 | Photo posts: every image at full size (number, width, height), the post's audio (mp3), a metadata JSON (desc, author, date, post_type, the full post dictionary). Video posts: the direct file from `bitrateInfo` or `playAddr`; some come out silent. Optional covers (off by default) and subtitles (ASR or MT). No comments. Takes `/photo/` (rewritten to `/video/`), `/video/`, `/share/`, `vm.` and `vt.` links. | Nothing for one public post. Cookies only for feeds and non-default ordering. | Home machine. Not tested from a datacenter. | Free | None without cookies. With cookies, as yt-dlp (unverified). | Country-dependent 403s from 9 Jul to 12 Sep, fixed in 1.32.10 on 29 Aug ([#9643](https://github.com/mikf/gallery-dl/issues/9643)). The 403s on many posts ([#9796](https://github.com/mikf/gallery-dl/issues/9796), Codeberg #549) are fixed in master ([commit 912138b7ca](https://codeberg.org/mikf/gallery-dl/commit/912138b7ca95ea83db0f91c0037299f4f5c67143), closed 2026-10-22), not in 1.32.17. Silent posts ([#9764](https://github.com/mikf/gallery-dl/issues/9764)) open. Codeberg #547, #540 and #244 open. Weekly releases. Home moved to Codeberg. |
| Apify `clockworks/tiktok-video-scraper` (`S5h7zRLfKFEr8pdj7`) | Caption, textLanguage, createTimeISO, authorMeta (name, nickName, signature, fans, following, heart, verified, privateAccount), play, digg, comment, share, collect and repost counts, hashtags, mentions, musicMeta, videoMeta (duration, width, height, coverUrl, downloadAddr, subtitleLinks), isSlideshow, slideshowImageLinks, mediaUrls to stored files, isAd, isSponsored, isPinned. An error record per failed URL. Optional AI transcript. No comments. | `APIFY_TOKEN`. No TikTok login, cookies or proxy. | Both | BRONZE: $0.002 per video plus $0.001 video-download add-on (about $3 per 1,000 with the file); transcript add-on $0.041 per started minute. FREE: $0.003 plus $0.0013. No pricing event for slideshow images. Named stores billed while they exist (rate not checked). | None to any TikTok account. Spend on his Apify account. | Modified 2026-10-23. 30 days to 2026-10-24: 636,089 of 638,682 runs succeeded (99.6%), 2,216 failed. 4.6 from 35 reviews, 2.7K monthly users. Synchronous runs return 408 after 300 s ([Apify docs](https://docs.apify.com/api/v2/act-run-sync-get-dataset-items-post)) ([actor](https://apify.com/clockworks/tiktok-video-scraper)). |
| Apify `clockworks/tiktok-scraper` (`GdWCkxBtKWOsKjdch`) with `commentsPerPost`, or `clockworks/tiktok-comments-scraper` (`BDec00yAmCm1QbMEI`) | The same post fields and downloads, plus comments and replies (commentsPerPost, topLevelCommentsPerPost, maxRepliesPerComment). Optional AI description and summary. The comments actor returns comments, plus post and profile data. | `APIFY_TOKEN`. No TikTok login. | Both | tiktok-scraper at BRONZE: $0.003 per result, $0.001 per actor start, $0.001 per video download, $0.001 per comment; transcript $0.041 per minute. Store: "from $1.70 / 1,000 results" (tier not stated). Comments scraper at BRONZE: $0.001 per comment. | None to TikTok accounts. Apify spend only. | tiktok-scraper, 30 days to 2026-10-24: 14,628,953 of 14,846,502 runs succeeded (98.5%); 139,324 failed, 68,179 timed out (the Store shows 99.1%). Modified 2026-10-23. 4.74 from 370 reviews, 31K monthly users ([tiktok-scraper](https://apify.com/clockworks/tiktok-scraper)). |
| Apify `apidojo/tiktok-scraper` (`5K30i8aFccKNF5ICs`), `{"startUrls":[url],"maxItems":1}` | Metadata: caption, uploadedAt, views, likes, comments, shares, bookmarks, hashtags, channel (username, name, followers, verified, bio), song, video (duration, cover, thumbnail, a TikTok CDN url), subtitleInformation. Takes video and photo URLs. Stores no files. No list of slideshow images in its inferred schema (unverified). | `APIFY_TOKEN` | Both | $0.0003 per post (pay per event; tier not stated) | None to TikTok accounts | Modified 2026-10-24. 30 days: 1,717,191 of 1,740,983 runs succeeded (98.6%); 22,133 aborted, 1,026 failed. 4.36 from 30 reviews. A cheap metadata check, not a media fetcher ([actor](https://apify.com/apidojo/tiktok-scraper)). |
| Apify `epctex/tiktok-video-downloader` (`9EwE2S3mGpxx665jw`), `{"startUrls":[url],"storageType":"apify"}` | The video re-hosted (downloadUrl), cover, title, sourceUrl, status. Resolves short links. Photo posts are "reported as having no video". No counts, no author. | `APIFY_TOKEN`, plus cloud storage credentials when not using Apify storage | Both | $0.003 per video download (tier not stated) | None to TikTok accounts | Modified 2026-10-24. 30 days: 44,525 of 45,980 runs succeeded (96.8%); 1,454 aborted, 1 failed. 4.96 from 14 reviews, 98 monthly users ([actor API](https://api.apify.com/v2/acts/epctex~tiktok-video-downloader)). |
| Direct page read: `GET https://www.tiktok.com/@<user>/video/<id>`, parse `__UNIVERSAL_DATA_FOR_REHYDRATION__` | desc, author.uniqueId, createTime, stats, video.playAddr and bitrateInfo, imagePost.images, music.playUrl, locationCreated, video.subtitleInfos and video.claInfo.captionInfos (with noCaptionReason). The `comments` key is an empty list. Media URLs are signed CDN links, download untested. | Nothing but a browser User-Agent. When TikTok serves its WAF JS challenge, the libraries solve it (cookies `_wafchallengeid` and `msToken`). | Both | Free | None (no login) | Tested twice on 2026-10-24 from Google Cloud (AS396982, Ohio) with plain curl: HTTP 200, about 399 KB, statusCode 0, full fields, a video post and a photo post (1 image, audio present). No challenge served. Single samples; others get the challenge at times ([#17393](https://github.com/yt-dlp/yt-dlp/issues/17393)). |
| TikTok oEmbed: `GET https://www.tiktok.com/oembed?url=<post url>` | Embed only: version, type, width, height, an iframe to `https://www.tiktok.com/player/v1/<id>`, provider_url, provider_name, embed_product_id (the post id), embed_type. No title, author or thumbnail. A `/photo/` URL returns 400. | Nothing | Both | Free | None | Works from Google Cloud (2026-10-24) without the metadata fields. The docs (23 Oct 2026) say "Embed Videos will be deprecated soon" and point to the Embed Player, where "TikTok may apply usage limits to embedded players on a per-domain basis" ([embed-videos](https://developers.tiktok.com/doc/embed-videos), [embed-player](https://developers.tiktok.com/doc/embed-player)). |
| TikTok Display API (`/v2/video/query/`, `/v2/video/list/`, `/v2/user/info/`) | The authorised user's own videos only (up to 20 ids): title, description, create_time, duration, cover, share_url, embed, counts, is_aigc. No file. Cannot read someone else's post. | A TikTok developer app, OAuth consent from the account owner, app review (unverified) | Both | Free | Low (official) | Docs updated 4 and 24 Aug 2026. Does not fit the job ([overview](https://developers.tiktok.com/doc/display-api-overview)). |
| TikTok Research API (video query) | Metadata and a voice_to_text transcript. No video or download URL. | An approved application from an eligible academic or not-for-profit body, "independent of commercial interests". Commercial users: "No". | Unclear | Free | Not applicable | Not available: Mindmake is commercial. Pages updated 1 Sep 2026 ([FAQ](https://developers.tiktok.com/doc/research-api-faq)). |
| Firecrawl `firecrawl_scrape` of a post URL | Nothing | His Firecrawl key | Unclear | 1 credit per attempt | None | Every scrape on 2026-10-24 returned "Insufficient credits". The earlier "we do not support this site" refusal rests on one test plus a blog by ScrapeCreators, which sells a competing product ([blog](https://scrapecreators.com/blog/firecrawl-social-scraping-restrictions)). |
| TikTokApi 7.3.3 (davidteather/TikTok-Api), Python with Playwright | The post's full data dictionary (`.as_dict`): caption, author, stats, video info. The file through `async bytes()` (video.py line 180). Comments through `comments()` (line 258). | Python 3.9 or later, a Playwright browser, an `ms_token` cookie. README: "you may need a proxy". | Home machine. README: "you might have success on their free data center IPs". | Free | An `ms_token` from his session ties requests to his browser session (unverified) | Last release 7.3.3 on 2026-04-01; 139 open issues. README: "EmptyResponseException - this means TikTok is blocking the request and detects you're a bot" ([repo](https://github.com/davidteather/TikTok-Api), [video.py](https://raw.githubusercontent.com/davidteather/TikTok-Api/main/TikTokApi/api/video.py)). |
| cobalt (imputnet/cobalt), self-hosted | Video (with or without watermark), slideshow images without watermark, original audio. No caption, author or counts. | A self-hosted instance ("there is currently no publicly available pre-hosted api") | Unclear | Free (self-hosted) | None | Open: #1505 "Unable to download Tik-Tok video" (21 Jan 2026), #1553 "TikTok video is not working" (5 May 2026), #1517 live photos (Mar 2026) ([README](https://github.com/imputnet/cobalt/blob/main/api/README.md)). |
| ScrapeCreators API: `GET https://api.scrapecreators.com/v2/tiktok/video?url=<post url>`, header `x-api-key` | desc, author (nickname, unique_id), statistics (play, digg, comment, share), `download_no_watermark_addr`, `play_addr`. Slideshow fields not confirmed in the docs. | A ScrapeCreators key (he has none), or its Apify actor on his existing token (row below) | Both | Free plan: 100 credits (up to 7,000 more claimable). Freelance: $47 for 25,000 credits ($1.88 per 1,000). Business: $497 for 500,000. Credits never expire; 1 credit per request for most endpoints. | None to TikTok accounts | No independent 2026 reliability data (unverified) ([docs](https://docs.scrapecreators.com/v2/tiktok/video), [pricing](https://scrapecreators.com/)). |
| TikWM: `GET https://www.tikwm.com/api/?url=<post url>&hd=1` (added by the check) | Video: title (caption), author.unique_id, play, digg, comment, share, collect and download counts, create_time, music_info, play, hdplay and wmplay URLs. Photo post: an images list and the music. | Nothing (no key, no login) | Tested from Google Cloud; home machine untested | Free | None to his accounts. An anonymous third party with no contract sees every link. | Worked on 2026-10-24 for a video and a photo post (code 0). Rate limits and terms unverified (homepage 403, no docs found). Media download untested ([API](https://www.tikwm.com/api/)). |
| Apify `scrape-creators/best-tiktok-video-scraper` (`rFfyNgnvUxD1bm8hh`) (added by the check) | description, author, counts, music.playUrl, images, transcript, videoUrl, downloadUrl. Input `{videos:[url], shouldGetTranscript, shouldDownloadVideos, shouldDownloadCovers}`. | `APIFY_TOKEN` (no new ScrapeCreators account) | Both | BRONZE: $0.002 per result, transcript included as an option | None to TikTok accounts | 30 days: 30,949 of 30,968 runs succeeded; 137 monthly users; modified 2026-09-04 ([actor](https://apify.com/scrape-creators/best-tiktok-video-scraper)). |
| Apify `clockworks/tiktok-transcript-extractor` (`vv5IWl1VaemRlGAiv`) (added by the check) | TikTok's subtitles where they exist, AI transcription where they do not. Input `postURLs` plus `downloadSubtitlesOptions`. | `APIFY_TOKEN` | Both | BRONZE: $0.003 per video, plus $0.041 per started minute of AI transcription | None to TikTok accounts | 30 days: 6,179 of 6,221 runs succeeded; 378 monthly users; modified 2026-10-23 ([actor](https://apify.com/clockworks/tiktok-transcript-extractor)). Not needed while faster-whisper runs locally. |
| Apify `scrape-creators/best-tiktok-transcripts-scraper` (added by the check) | Transcripts | `APIFY_TOKEN` | Both | $0.001 per result (tier not stated) | None to TikTok accounts | 11,688 of 11,690 runs succeeded, 340 users. Last modified 2026-04-22; whether it is maintained since April is unverified ([actor](https://apify.com/scrape-creators/best-tiktok-transcripts-scraper)). |
| ScrapeCreators `GET /v1/tiktok/video/transcript` and `GET /v1/tiktok/video/comments` (added by the check) | A post's transcript; a post's comments | A ScrapeCreators key | Both | About 1 credit each: about $1.88 per 1,000 on the $47 pack | None to TikTok accounts | Reliability unverified ([pricing and endpoints](https://scrapecreators.com/)). |
| TikTok "Download your data" export (added by the check) | Links and metadata of his own activity, including a Likes list (third-party guides). No media files. | His account. Requested by hand: Settings > Account > Download your data, JSON or TXT. | His phone or browser, by hand | Free | None; the one route TikTok sanctions for this | About 1 to 4 days (third-party guides). File and field names unverified: TikTok's help page rendered empty ([guide](https://takeoutday.org/guides/how-to-export-tiktok-data), [PIRG](https://pirg.org/edfund/resources/how-to-request-and-download-tiktok-data/), [tikfav](https://www.npmjs.com/package/tikfav)). |
| Browser-side capture: a bookmarklet or extension reads `__UNIVERSAL_DATA_FOR_REHYDRATION__` from the TikTok tab he has open, or Playwright or CDP drives his real browser profile (added by the check) | The same JSON as the direct page read, after the browser has solved the WAF challenge itself | A bookmarklet or extension, or Playwright or CDP and his browser profile | Home machine | Free | Not assessed by the check. Driving his signed-in profile is automation under his account (inference), so it needs his yes. | Untested. An inference from where yt-dlp and gallery-dl break ([#17393](https://github.com/yt-dlp/yt-dlp/issues/17393), [#9796](https://github.com/mikf/gallery-dl/issues/9796)). TikTokApi already works this way with Playwright. |
| TikTokApi `Video.comments(count=20, cursor=0)` (added by the check) | A post's comments | An `ms_token` and Playwright | Home machine | Free | As TikTokApi: an `ms_token` from his session ties requests to it (unverified) | Prone to bot detection. The only free TikTok comment fetcher found ([video.py](https://raw.githubusercontent.com/davidteather/TikTok-Api/main/TikTokApi/api/video.py)). |

### Corrections applied

1. gallery-dl #9796: "the fix has not been merged" became "merged to master" (Codeberg #549 closed 2026-10-22, commit
   912138b7ca, padding kept by `binascii.b2a_base64`). It is not in 1.32.17, so step 2 runs master until the next
   release. This replaces the brief's "1.32.17 or later".
2. gallery-dl's home: added that it moved to Codeberg and that new TikTok bugs are filed there (#549, #547, #540,
   #244). The build watches Codeberg as well as GitHub.
3. yt-dlp install: the report's `pip install -U "yt-dlp[default,curl-cffi]"` resolves to curl_cffi 0.16.3, against its
   own pin advice. Step 1 now pins `curl_cffi==0.16.0` in the same command, or keeps 0.16.3 with a browser
   `--user-agent` (confirmed by three users through 2026-09-25). The curl_cffi 0.17.0b2 question was dropped, since
   the extra excludes 0.17.
4. yt-dlp updates: "update weekly" now means the nightly builds through pip, because no stable release has touched
   TikTok since 2026.08.19. 2026.10.21 is a security release (GHSA-6q48-6c7w-9gw2), so it is installed fresh, not
   reached by self-updating an old copy. This replaces the brief's `yt-dlp -U` for TikTok.
5. "yt-dlp's maintainers send photo posts to gallery-dl" became "one contributor, ruben1PvP, said photos are out of
   scope on #17865 (closed as a duplicate of #15764)". The code agrees: `_VALID_URL` takes only `/video/`,
   `/share/video/` and `/embed/`. The brief's sentence saying the maintainers send them should go.
6. gallery-dl details: the `videos=ytdl` workaround is credited to mikf on #9748, not #9764 (which has no maintainer
   reply). `-o audio=true` was dropped as redundant (audio defaults to on). `-o covers=true` stays (covers default to
   off). `/photo/` URLs are passed as they are, since gallery-dl rewrites them to `/video/`.
7. TikTokApi: it was understated. Its row now lists the file (`bytes()`) and comments (`comments()`), and the README's
   datacenter remark. It moved from "last resort, do not build on" to the free comment route in step 5.
8. ScrapeCreators: the price is now verified from its homepage ($47 for 25,000 credits, $497 for 500,000, 100 free,
   credits never expire). Its transcript and comments endpoints were added. It no longer needs a new account, since
   its actor runs on his Apify token.
9. Terms: the EEA/UK terms (section 4.5) now lead, because content-engine keeps London as his clock
   (content-engine `scripts/quick-edit/archive.py`), unverified as his legal residence. "Private study lowers the exposure" was
   corrected: under UK law it gives no cover for study with a commercial purpose (CDPA 1988 s.178). This replaces the
   brief's "TikTok's US Terms section 3.4".
10. Direct page read: the re-test was added. The `comments` key is an empty list, so the page has no comments.
    `subtitleInfos` and `claInfo.captionInfos` (with `noCaptionReason`) show whether TikTok captions exist before
    transcribing. A photo post fetched as `/video/` returns its image and audio.
11. Apify: step 4 now starts the run asynchronously and polls (the synchronous call returns 408 after 300 seconds).
    The docs' `/v2/actors/` path is noted. Named stores are billed while they exist, so files are pulled and removed.
    "Slideshow images will increase costs (unverified)" became "no pricing event, so no listed price". epctex's 98
    monthly users were added.
12. Firecrawl: "refuses tiktok.com" became "unusable today: every scrape on 2026-10-24 returned 'Insufficient credits', and the refusal rests on one
    earlier test and a competitor's blog". This replaces the brief's reason.

### Open questions

1. **Do GitHub Actions runner IPs (Azure) get TikTok's WAF challenge, or status 10204 "Your IP address is blocked"?**
   Test: one workflow run of `yt-dlp --skip-download --write-info-json
   "https://www.tiktok.com/@scout2015/video/6718335390845095173"` and one plain page read of the same URL. Runner
   minutes only; no media, no cookies.
2. **Is curl_cffi 0.16.3 blocked like 0.16.2 (#17604), and does an older explicit impersonation target work?** The
   older target is an inference from one contributor's chrome-146 report. Test, on the home machine:
   `python -m pip install "curl_cffi==0.16.3"`, then
   `python -m yt_dlp --skip-download -v "https://www.tiktok.com/@scout2015/video/6718335390845095173"`; the same
   after `python -m pip install "curl_cffi==0.16.0"`; then reinstall 0.16.3 and run it once more with `--impersonate`
   set to the chrome-146 name that `python -m yt_dlp --list-impersonate-targets` prints. Put back whichever version
   step 1 runs at the end. Free.
3. **Which TikTok terms bind Krish: EEA/UK, US, or rest of world?** It depends on where he lives, which is not
   established. Test: one plain question to him, after D1 and D2 (one question at a time). Free.
4. **Is his Apify plan BRONZE?** Every Apify price above assumes it. Test: read the plan in the Apify console. Free.
5. **Are clockworks' slideshow image downloads charged at all, and under which event?** The actor lists no event for
   them. Test: one approved run on one photo post, then read the run's charged events. About $0.003 at BRONZE if a
   photo post is charged like a video (inference). Needs his yes.
6. **Does clockworks run without `videoKvStoreIdOrName`, leaving the files in the run's own store?** That would drop
   the delete step. Test: read the actor's input schema (its Store page, or the Apify MCP's `fetch-actor-details`).
   Free.
7. **Does starting a run still answer on `/v2/acts/`, or only on `/v2/actors/`?** Test: read Apify's API reference
   for "Run Actor". Free.
8. **How often do the posts Krish saves carry TikTok captions?** This decides whether faster-whisper is the normal
   path or the fallback. Test: a page read (step 3a) of the first 10 links he pastes, counting non-empty
   `subtitleInfos` or `claInfo.captionInfos`. Free, no media.
9. **Do the CDN media URLs from the page JSON download without the page's cookies, from home and from a datacenter?**
   Test: in the once-per-platform live check (with his yes), one GET of `playAddr` with, then without, the cookies the
   page response set. Free.
10. **Does gallery-dl master fix the 403s for the posts Krish pastes?** mikf gets no challenges and cannot test it,
    and whether to pin a commit or track weekly releases follows from this. Test: master on one photo post he
    pasted, on the home machine. Free.
11. **Did oEmbed drop title, author and thumbnail for everyone, or only for datacenter IPs?** Low value, since the
    chain skips oEmbed. Test: one `curl.exe "https://www.tiktok.com/oembed?url=https://www.tiktok.com/@scout2015/video/6718335390845095173"`
    from the home machine (`curl.exe`, because in Windows PowerShell 5.1 `curl` is an alias for `Invoke-WebRequest`).
    Free.
12. **What are TikWM's rate limits and terms, and do its media URLs download?** Test: one call from the home machine on
    the public test post above,
    `curl.exe "https://www.tikwm.com/api/?url=https://www.tiktok.com/@scout2015/video/6718335390845095173&hd=1"`,
    then one GET of its `play` URL. Free, and no link of his leaves the machine.
13. **Does a browser-side read get past the WAF challenge that stops yt-dlp and gallery-dl?** Test: the next time
    yt-dlp fails with "rehydration" on the home machine, open the same post in Firefox and run
    `JSON.parse(document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__').textContent)` in the console. If
    `itemStruct` is there, the bookmarklet route works. Free, no automation.
14. **Does an `ms_token` from a browser that is not signed in work for TikTokApi comments?** If it does, free comments
    carry no account risk. Test: one `Video.comments(count=20)` call on the test post with an `ms_token` from a
    Firefox profile that has never signed in to TikTok. Free.
15. **What files and fields hold the Likes list in TikTok's "Download your data" export?** Test: Krish requests the
    JSON export once (1 to 4 days) and a session reads its file names and fields. Free; only he can request it.

### Terms

Every automated method here breaks TikTok's terms. The EEA/UK terms (updated July 2026), which probably apply to him,
bar extracting "any data or content from the Platform using any automated system or software" without TikTok's
written approval (section 4.5, [EEA terms](https://www.tiktok.com/legal/page/eea/terms-of-service/en)), as do the US
terms (section 3.4, [US terms](https://www.tiktok.com/legal/page/us/terms-of-service/en)) and the rest-of-world terms
(sections 5, 7A and 10, [ROW terms](https://www.tiktok.com/legal/page/row/terms-of-service/en)). Under UK law "private
study" excludes study with a commercial purpose ([CDPA 1988 s.178](https://www.legislation.gov.uk/ukpga/1988/48/section/178)).
Solving the WAF challenge is arguably bypassing access measures, his own cookies tie the activity to his account, and
the only routes TikTok sanctions (Display API, Research API, oEmbed, Embed Player, Download your data) return no one
else's media.

## YouTube: videos and Shorts

Researched on 24 Oct 2026 against primary sources, then checked by a second pass. Every correction from the check is
applied below. This replaces the provisional YouTube text in section 6.

YouTube needs no D2. A guest session works from a home connection, and no account of his own is ever used. Three steps
need his yes: step 6 (a throwaway Google account's cookies, an account risk), step 8 (a Google model watching the
video, his call because section 7.3 and D3 say no model watches) and step 9 (Apify, a spend). D1 still decides where a
downloaded MP4 is filed.

### Recommended chain

Rules for every step:

- Normalise the link first (section 6 rules) and take the video id from it.
- Record the method that worked as a class (section 7.2), for example `yt_oembed`, `yt_dlp_guest`, `yt_dlp_mweb_pot`,
  `yt_transcript_api`, `whisper_local`, `yt_dlp_cookies`, `yt_rss`, `gemini_url`, `apify_johnvc`. Record each failure
  as a class too, for example `bot_check`, `age_gate`, `http_403`, `http_429`, `no_data_blocks`, `no_captions`, `drm`,
  `ip_blocked`, `not_in_feed`, `timeout`.
- Logs carry counts and class names only. Never log the link, the video id, the title, a file name (files are named by
  video id), caption or transcript text, a model's answer, a cookie path or yt-dlp's raw output (section 4).
- Steps 1 to 5 and step 7 run unattended. A step that spends (step 9, Firecrawl, any paid plan) needs his yes
  immediately before the run, or a standing cap he set in his own words (section 9). Step 6 (an account risk) and step
  8 (a model watching) are free but need his yes before first use.
- Every outside call has a timeout (section 7.1). A timeout is a failure with the class `timeout`, so the request is
  tried again until its three attempts are used (section 7.4).
- No Anthropic model watches anything. The reading in section 7.3 runs on the files these steps fetch.

Setup on each home machine, once:

```
python -m pip install -U "yt-dlp[default,deno]==2026.10.21" "bgutil-ytdlp-pot-provider==2.0.2" "youtube-transcript-api==1.2.4" "faster-whisper==1.2.1"
docker run --name bgutil-provider -d --init -p 127.0.0.1:4416:4416 brainicism/bgutil-ytdlp-pot-provider
```

- The commands are written for PowerShell. In a `.bat` file, write each `%` as `%%`. From Python, pass an argument
  list, so no shell reads them at all.
- Update before each batch (section 6) and at least weekly: `python -m pip install -U "yt-dlp[default,deno]"
  bgutil-ytdlp-pot-provider`. A pip install updates through pip, so this takes the place of section 6's `yt-dlp -U`
  ([README](https://github.com/yt-dlp/yt-dlp/blob/master/README.md)). yt-dlp changed its YouTube clients on 19 Aug and
  again on 21 Oct 2026 ([releases](https://github.com/yt-dlp/yt-dlp/releases)). `doctor` reports the versions in use.
- The `deno` extra installs Deno 2.9.8 or later from PyPI; yt-dlp needs 2.3.0 or later
  ([PyPI](https://pypi.org/pypi/yt-dlp/json), [EJS wiki](https://github.com/yt-dlp/yt-dlp/wiki/EJS)). Deno is strongly
  recommended, not strictly required. Without a JavaScript runtime, yt-dlp drops the web and tv_samsung clients and runs
  on visionos alone, with fewer formats ([README](https://github.com/yt-dlp/yt-dlp/blob/master/README.md)). Deno is
  the only runtime yt-dlp turns on by default, so a Node install for bgutil's script mode does not stand in for it.
- The standalone Windows `yt-dlp.exe` also works. It bundles the yt-dlp-ejs solver scripts, and Deno can sit beside it
  or on PATH ([EJS wiki](https://github.com/yt-dlp/yt-dlp/wiki/EJS)). The fetcher is Python, so the pip install is the
  simpler fit.
- Keep `127.0.0.1:` in the Docker port. The bgutil README warns that an open port lets other clients reach the server,
  up to remote code execution ([bgutil](https://github.com/Brainicism/bgutil-ytdlp-pot-provider)). No Docker? Its
  script mode runs on Node 22+ or Deno 2.0+ with Git; the README says that mode is not recommended for high
  concurrency. Whether Docker is on the machines is open question 6.
- The Docker image's tag and how the plugin finds the server were not recorded in this research (unverified), so the
  command pulls the latest image. `doctor` should prove the pair works with one mweb fetch of a public video. A
  container started this way does not come back after a reboot unless it was run with Docker's
  `--restart unless-stopped`.
- ffmpeg on PATH for step 3's merge and step 5's audio. Section 4 says both machines have it; its version was not
  checked in this research.

**On a home machine (the normal path)**

1. **Check the link with oEmbed.** Any machine. Free, no key.

   `GET https://www.youtube.com/oembed?url=<URL-encoded canonical URL>&format=json`

   Returns title, author_name, author_url and a 480x360 thumbnail_url. It works for watch and `/shorts/` links
   ([oembed.com providers](https://oembed.com/providers.json)), and it worked from a datacenter IP on 24 Oct 2026 (the
   report's and the check's tests). JSON back: go to step 2. Any other answer: record the class and stop for this link.
   A timeout or no connection is not an answer: record `timeout`, and the request is tried again. Which status codes
   YouTube uses for private or deleted videos is unverified.

2. **Words and metadata: yt-dlp as a guest, no video.** Home machine. Free.

   ```
   yt-dlp --skip-download --write-info-json --write-subs --write-auto-subs --sub-langs ".*-orig" --sub-format "vtt/srt/best" -t sleep -o "%(id)s.%(ext)s" "<URL>"
   ```

   It writes `<id>.info.json` (title, description, uploader, channel, upload_date as YYYYMMDD in UTC, duration,
   view_count, like_count, comment_count, tags, chapters, thumbnail URLs) and the caption files. Call it from Python
   with an argument list and a timeout, in the post's local folder (section 7.1) as the working directory, so the files
   land there and the `%` and the quotes need no shell escaping.

   - `.*-orig` takes the auto captions in the language spoken. Do not use `en.*`. On a non-English video it fetches
     YouTube's machine translation into English, not the words spoken. On an English video it fetches `en` and
     `en-orig`, the same words twice, and each extra track is one more request open to the 429s in #17412
     (inference). That comes from the check's reading of yt-dlp's source, untested
     ([_video.py](https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/yt_dlp/extractor/youtube/_video.py), lines
     about 4244 to 4335). Add `,en` only when an English translation is wanted. Uploaded tracks probably carry no
     `-orig` label, so this pattern may skip them (inference, open question 4). The last fall-through below covers
     that case.
   - A video YouTube has auto-dubbed has one machine caption track per dub, and yt-dlp labels each `<lang>-orig`,
     so `.*-orig` returns `ar-orig`, `de-orig`, `en-orig` and so on. The watcher keeps the one in the original audio
     track's language (`ytdlp.pick_captions`; the original track is the one yt-dlp marks `original`), and with
     several and no original known it keeps none, so the reading transcribes the audio. It asks for the original
     audio track by name in the format string, and fetches once more with that track's format id when yt-dlp
     still chose a dub (31 October 2026: an English Short read as Arabic from the `ar-orig` captions).
   - This is not one request. It makes one webpage request, one player request per client (three by default) and one
     request per caption track. All of them count against the guest limit of about 1,000 requests, or about 300
     videos, an hour ([Extractors wiki](https://github.com/yt-dlp/yt-dlp/wiki/Extractors)). The limit falls on the IP,
     so two machines behind one router share it, and share a bot check too (inference).
   - `-t sleep` expands to `--sleep-subtitles 5 --sleep-requests 0.75 --sleep-interval 10 --max-sleep-interval 20`
     ([README](https://github.com/yt-dlp/yt-dlp/blob/master/README.md)).

   Fall through:
   - HTTP 429 or "Did not get any data blocks" on captions ([#17412](https://github.com/yt-dlp/yt-dlp/issues/17412)):
     retry once with `-t sleep` replaced by its expansion with a longer subtitle wait: `--sleep-subtitles 60
     --sleep-requests 0.75 --sleep-interval 10 --max-sleep-interval 20`. The "more than 55 seconds" figure is from one
     comment in that thread, and the check could not re-read it (unverified). Still failing: step 3, then step 4 for
     the words.
   - HTTP 403: retry once with `--extractor-args "youtube:player_client=mweb"` and the bgutil provider running. The PO
     Token Guide lists subtitles as needing a PO token on the web client
     ([PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)). Still 403: step 3, then step 4 for the
     words.
   - "Sign in to confirm you're not a bot": no more YouTube from this IP for the rest of the pass. Try the other home
     machine if it is on another connection, then step 6 if he has said yes to it, then the steps under "When neither
     home machine can fetch".
   - An age gate: step 6 if he has said yes to it. Otherwise record `age_gate` and stop for this link; step 4 fails on
     age-restricted videos too.
   - No caption file written: step 3, then step 4 for the words. That also covers a video whose only tracks are
     uploaded ones that `.*-orig` skipped, because step 4's `list` shows manual tracks as well as generated ones.

3. **The video, for the visual reading.** Home machine. Free.

   ```
   yt-dlp -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 -t sleep -o "%(id)s.%(ext)s" "<URL>"
   ```

   An MP4 with video and audio merged by ffmpeg, capped at 1080p. Use `height<=720` for a smaller file; Shorts are
   small anyway. The reading in section 7.3 always needs the video, so steps 2 and 3 can be one call: add step 2's
   `--write-info-json --write-subs --write-auto-subs --sub-langs ".*-orig" --sub-format "vtt/srt/best"` here. That saves
   the second webpage request and the second set of player requests (inference from the request count in step 2,
   untested). If the joined call fails, run the two apart so each falls through on its own.

   Fall through:
   - HTTP 403 on formats: retry once with `--extractor-args "youtube:player_client=mweb"` through the PO token
     provider, as the PO Token Guide recommends. Still 403: step 9 for the file.
   - Formats come back DRM-protected ([#17812](https://github.com/yt-dlp/yt-dlp/issues/17812), so far reported only with
     logged-in cookies): the thread has no fix and no workaround. Go to step 9 for the file.
   - Bot check: as in step 2.
   - The MP4 came but step 2 gave no words: step 4.

4. **Captions by a second route: youtube-transcript-api 1.2.4.** Home machine. Free. Use it when step 2's caption
   requests keep failing.

   ```python
   from youtube_transcript_api import YouTubeTranscriptApi
   api = YouTubeTranscriptApi()
   tracks = api.list(video_id)                       # pick the manual or generated track in the spoken language
   snippets = api.fetch(video_id, languages=["en"])  # put that track's language code here
   ```

   Pass the video id, not the URL. It returns text, start and duration per snippet, the language, and whether the
   track is auto-generated ([README](https://github.com/jdepoix/youtube-transcript-api)). Cookie login is "currently
   not available", so age-restricted videos fail. A video with no caption tracks will have none here either
   (inference). RequestBlocked, IpBlocked or no track: step 5.

5. **Transcribe on the machine: faster-whisper 1.2.1.** Home machine. Free. Use it when no captions came back. Decode
   the audio of the MP4 that step 3 saved with ffmpeg into float32 samples and hand faster-whisper the array, never the
   file: section 4 records that letting faster-whisper open a file returns empty transcripts with no error. YouTube
   sees no second request. Report `words`, `silent` or `failed` with a class (section 4). If step 3 got no file,
   `yt-dlp -x --audio-format mp3 -t sleep -o "%(id)s.%(ext)s" "<URL>"` fetches the audio alone. Quality and speed
   depend on the model size, which was not measured
   ([faster-whisper](https://github.com/SYSTRAN/faster-whisper)).

6. **Only with his yes: a throwaway Google account's cookies.** Home machine. Free; the risk falls on the throwaway
   account. Use it only when a guest gets "Sign in to confirm you're not a bot" or a video is age-gated.

   A new IP may clear the bot check without cookies: a router restart did for one user
   ([#15796](https://github.com/yt-dlp/yt-dlp/issues/15796)). It gives a new address only if his internet provider
   hands out dynamic addresses (inference), and it cuts his home connection, so it is his to do, never the fetcher's.
   With his yes to cookies:

   ```
   yt-dlp --cookies "<path to cookies.txt>" <the step 2 or step 3 flags> "<URL>"
   ```

   or `--cookies-from-browser firefox:<profile>`, naming a Firefox profile that holds only the throwaway login, so his
   own Google session can never be read. Prefer the exported file: a live profile with YouTube open keeps rotating its
   cookies (next point).
   - Export cookies.txt from a private browser window, then close that window. YouTube rotates cookies on open tabs
     ([Extractors wiki](https://github.com/yt-dlp/yt-dlp/wiki/Extractors)).
   - Not `--cookies-from-browser chrome` on Windows: it fails
     ([#10927](https://github.com/yt-dlp/yt-dlp/issues/10927), [#15867](https://github.com/yt-dlp/yt-dlp/issues/15867)).
     Use Firefox or an exported file.
   - Never krish@mindmake.co or any account tied to his Gmail or Drive. The wiki warns the account may be banned
     "temporarily or permanently". An account is limited to about 2,000 videos an hour.
   - With a free account's cookies the default clients become web_embedded,tv_samsung,web, and every DRM report in
     #17812 came from a logged-in session.
   - The cookie file stays on the home machine. It never goes to GitHub Actions (section 6).

**When neither home machine can fetch**

7. **Metadata from the GitHub Actions runner.** Free in money. Each run uses minutes from the private repositories'
   monthly Actions allowance (how many was not measured).

   Run step 1 there, then read the channel feed for the date and the counts:
   - `GET <author_url from step 1>` and read `"externalId"` (the channel id, `UC...`) from the page.
   - `GET https://www.youtube.com/feeds/videos.xml?channel_id=<UC...>` and find this video's entry. It carries
     `<published>` (an exact timestamp), `<media:statistics views>` and `<media:starRating count>` (likes).

   The feed holds only the channel's 15 latest uploads, so an older video will not be there: record `not_in_feed`,
   keep oEmbed's title and author, and leave the date and counts empty. All three calls returned 200 from a datacenter
   IP on 24 Oct 2026, while watch pages from the same IP returned 302 to google.com/sorry (the check's own test). That
   IP was an Anthropic cloud container, not an Actions runner, so whether the runner gets the same answers is
   unverified (open question 1). Never run yt-dlp or youtube-transcript-api on the runner, and never put cookies
   there. This keeps section 6's rule that a fetch on Actions starts at the paid step.

   The Data API (`videos.list`, 1 unit of a free 10,000 a day) would also work on the runner. The report says to keep it
   separate from any tool that downloads with yt-dlp, or to use info.json and oEmbed instead (see Terms). Leave it out
   of the watcher until that open question is settled.

8. **Only with his yes: Gemini reads the video from its URL.** Any machine. Free while in preview.

   ```
   POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent
   x-goog-api-key: <Google API key, from the environment>
   {"contents":[{"parts":[{"file_data":{"file_uri":"<watch or Shorts URL>"}},{"text":"<what to read>"}]}]}
   ```

   The endpoint path and the key header are the Gemini API's usual REST form; this research did not re-read them
   (unverified). Google fetches the video, so by the docs it works from any IP, with no download and no cookies (not
   tested). It reads shots,
   on-screen text, pacing and editing as well as speech
   ([video understanding](https://ai.google.dev/gemini-api/docs/video-understanding)).
   - It is a model watching the video. The model is Google's, so no Anthropic tokens are spent. But section 7.3 and the
     North Star wording proposed in D3 say no model watches, so building it in is his call.
   - Its words are model-written. Captions stay the source of exact words.
   - Public videos only. Up to 10 videos per request on Gemini 2.5 and later. About 100 tokens a second of video plus 32
     a second of audio at default resolution.
   - Cost: "available at no charge" in preview, with the free tier capped at 8 hours of YouTube video a day. Google says
     "Pricing and rate limits are likely to change", so it becomes a spend, needing his yes, the day a price appears.
   - The docs' examples use gemini-3.8-flash. Control Center's notes say the fleet's Google key is free tier, flash
     models only. Whether that key reaches this model is unverified. Not tested.

9. **Only with his yes immediately before the run, or a standing cap: Apify.** Paid.

   Words and metadata, `johnvc/YoutubeTranscripts`:

   ```
   POST https://api.apify.com/v2/acts/johnvc~YoutubeTranscripts/run-sync-get-dataset-items
   Authorization: Bearer <Apify token, from the environment>
   {"youtube_url": "<URL>", "languages": ["en"], "include_metadata": true, "include_extended_metadata": true}
   ```

   BRONZE tier, pay per event: $0.0025 per video, charged only when a transcript comes back, plus $0.003 for
   include_extended_metadata (upload_date and like_count) when it succeeds. That is about $0.0055 a video with the date
   ([Store page](https://apify.com/johnvc/YoutubeTranscripts),
   [actor record](https://api.apify.com/v2/acts/johnvc~YoutubeTranscripts)). Set include_extended_metadata to false when
   step 7 already found the date. If johnvc fails, `starvibe/youtube-video-transcript` costs $0.005 per result (tier
   not stated). Avoid
   `pintostudio/youtube-transcript-scraper`: 17.8% of its 510,886 runs in 30 days failed.

   The file, `marielise.dev/youtube-video-downloader`:

   ```
   POST https://api.apify.com/v2/acts/marielise.dev~youtube-video-downloader/run-sync-get-dataset-items
   Authorization: Bearer <Apify token, from the environment>
   {"urls": ["<URL>"], "quality": "720p", "format": "mp4"}
   ```

   $0.02 a minute at 720p ($0.01 at 360p or MP3, $0.03 at 1080p; tier not stated), charged on success only per its
   description. An estimate of about $0.02 for a 60-second Short. Its residential proxy fallback costs $0.05 per MB, so
   keep it off unless his yes covers it. The switch is the `residentialProxyMode` input; its allowed values are not in
   this research. Never pass youtubeCookies. If it fails, `streamers/youtube-video-downloader`
   costs $0.005 per MB on the BRONZE tier, an estimate of about $0.20 for a 40 MB Short.

   - Read each actor's input schema before its first run. The field types and allowed values above (for example
     `"720p"` and `"mp4"`) are not in this research, and neither is the `run-sync-get-dataset-items` call, Apify's
     usual synchronous run (unverified here).
   - Estimate the batch from the per-video prices before asking for his yes.
   - Check every row's error fields. A SUCCEEDED run can still hold failed items. Report a failed row with its class;
     after three failed attempts the request stays failed (section 7.4).
   - Download any file URL an actor returns at once (section 6).

**Fall-through at a glance** (the same rules as the steps above, in one place)

| Step | What came back | Record | Then |
|---|---|---|---|
| 1 | JSON | `yt_oembed` | Step 2 |
| 1 | Any other answer | its class | Stop for this link |
| 1 | A timeout or no connection | `timeout` | The request is tried again (section 7.4) |
| 2 | Caption files | `yt_dlp_guest` | Step 3 |
| 2 | No caption file | `no_captions` | Step 3, then step 4 for the words |
| 2 | `http_429` or `no_data_blocks` | the class | One retry with the 60-second subtitle wait; still failing, step 3, then step 4 |
| 2 | `http_403` | the class | One retry with mweb and the provider (`yt_dlp_mweb_pot`); still failing, step 3, then step 4 |
| 3 | The MP4 | the method's class | Words in hand: done. No words: step 4 |
| 3 | `http_403` | the class | One retry with mweb and the provider; still failing, step 9 for the file, with his yes |
| 3 | `drm` | the class | Step 9 for the file, with his yes |
| 2 or 3 | `bot_check` | the class | No more YouTube from this IP this pass. The other home machine if it is on another connection, then step 6 with his yes, then steps 7 to 9 |
| 2 or 3 | `age_gate` | the class | Step 6 with his yes; otherwise stop for this link |
| 4 | Snippets | `yt_transcript_api` | Done |
| 4 | `ip_blocked`, a request block, or no track | the class | Step 5 |
| 5 | `words`, `silent` or `failed` | `whisper_local` and that result | Done |
| 6 | `bot_check` again | the class | Steps 7 to 9 |
| 7 | Not among the 15 latest uploads | `not_in_feed` | oEmbed's title and author only; steps 8 and 9 need his yes |
| 9 | A row with an error | its class | Report it; after three failed attempts the request stays failed (section 7.4) |

**What the fetcher hands back** (the normalised post in section 7.2)

- Post id: the video id. Shape: `video`.
- Author: `uploader` or `channel` from the info.json; on the runner, oEmbed's `author_name`.
- Posted date: the info.json's `upload_date` is a day (YYYYMMDD, UTC), not a time. The RSS feed's `<published>` (step
  7) is an exact timestamp. johnvc's `upload_date` (step 9) is the paid source. oEmbed has no date.
- Caption or text: `title` and `description`.
- Counts: `view_count`, `like_count` and `comment_count` from the info.json; views and likes only from the RSS feed.
- Media, in order: the MP4, then the caption file in the spoken language. The words in the reading come from the
  captions when there are any, else step 4, else step 5 (section 7.3).

Why this order: it goes from free and certain, to free and fragile, to paid. It keeps every Google login out unless one
is forced. It puts the fragile tools on the one residential IP they still work from.

Left out of the chain: Firecrawl's audio and video formats (untested, and the account is out of credits); Supadata and
ScrapeCreators (untested hosted APIs, worth a test only if he wants one vendor across platforms); pytubefix (a second
local engine if a yt-dlp release breaks); `streamers/youtube-scraper` (metadata at $0.003 a video on the BRONZE tier, and its AI options are
a model reading); the Invidious plugin (rejected by the check as stale).

### Methods

| Method | Gets | Needs | Works from | Cost | Account risk | State in October 2026 |
|---|---|---|---|---|---|---|
| yt-dlp 2026.10.21, captions and info.json, no video (step 2) | `.info.json`: title, description, uploader, channel, upload_date (YYYYMMDD, UTC), duration, view_count, like_count, comment_count, tags, chapters, thumbnail URLs. Uploaded and auto caption files (VTT or SRT). `--write-comments` adds comments (cap with `--extractor-args "youtube:max_comments=..."`); `--write-thumbnail` saves the thumbnail. Shorts use the same extractor (long-standing support, not re-tested). | No login. Deno 2.3.0+ strongly recommended; without it, visionos only and fewer formats. pip needs `yt-dlp[default]`; the Windows exe bundles yt-dlp-ejs. A PO token provider helps: the guide lists subtitles as needing one on the web client. | Home machine | Free | None as a guest. The IP carries the risk: about 300 videos or 1,000 requests an hour ([Extractors wiki](https://github.com/yt-dlp/yt-dlp/wiki/Extractors)). | Default clients tv_samsung,visionos,web since 2026.10.21 ([releases](https://github.com/yt-dlp/yt-dlp/releases), [PyPI](https://pypi.org/pypi/yt-dlp/json)). [#17412](https://github.com/yt-dlp/yt-dlp/issues/17412): "Did not get any data blocks" on English subtitles; the check confirmed only the title. [#17659](https://github.com/yt-dlp/yt-dlp/issues/17659) (`-orig` matching dubbed tracks) is unconfirmed: closed 17 Sep 2026 for lack of an example link or verbose output. `en.*` pulls machine translations (from [source](https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/yt_dlp/extractor/youtube/_video.py), untested). Sources: [README](https://github.com/yt-dlp/yt-dlp/blob/master/README.md), [EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS), [PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide). |
| yt-dlp 2026.10.21, the video file (step 3) | An MP4 with video and audio merged by ffmpeg, plus any info and subtitle flags added. `-x --audio-format mp3` gives audio only. | Deno, ffmpeg and a residential IP. A PO token provider when the mweb or web client is used. Cookies only after a bot check. | Home machine | Free | None as a guest. With cookies, see the cookies row. | 2026.08.19 dropped android_vr from the defaults and added visionos; 2026.10.21 made tv_samsung a default ([releases](https://github.com/yt-dlp/yt-dlp/releases)). [#17788](https://github.com/yt-dlp/yt-dlp/issues/17788) ("no formats" with cookies and a proxy, opened 7 Oct) closed 10 Oct 2026 by [PR #17805](https://github.com/yt-dlp/yt-dlp/pull/17805). [#17812](https://github.com/yt-dlp/yt-dlp/issues/17812) (opened 12 Oct): tv_samsung formats DRM-protected with logged-in cookies; labelled cant-reproduce, high-priority, site-bug; no fix and no workaround; one user says it clears after a few hours; guests not reported affected. [#15796](https://github.com/yt-dlp/yt-dlp/issues/15796) (Feb 2026): a home IP got the bot check, and a router restart with a new IP cleared it. Update weekly or run nightly. |
| PO token provider: bgutil-ytdlp-pot-provider 2.0.2 (7 Oct 2026), then `--extractor-args "youtube:player_client=mweb"`. Alternative: yt-dlp-getpot-wpc 1.1.2 (8 Aug 2026, experimental, mints tokens in a real Chrome window) | Nothing by itself. A fresh PO token per video, so mweb or web formats and subtitles download instead of returning 403. | `pip install -U bgutil-ytdlp-pot-provider` plus its server: `docker run --name bgutil-provider -d --init -p 127.0.0.1:4416:4416 brainicism/bgutil-ytdlp-pot-provider`, or script mode (Node 22+ or Deno 2.0+, and Git). yt-dlp 2025.05.22+. wpc needs Chrome or Chromium and yt-dlp 2025.09.26+. | Home machine | Free | None. Bind the port to 127.0.0.1: the README warns an open port could let other clients "potentially perform RCE". | [PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide) (edited 12 Jul 2026): tokens are bound to the video id, manual tokens are "no longer recommended", and a provider plugin should supply the mweb client. [#17682](https://github.com/yt-dlp/yt-dlp/issues/17682) (closed not planned, 28 Sep 2026): a contributor says a static token fails because "every video ID has its own". The bgutil README: a PO token does not bypass IP-based login restrictions, and it does not guarantee getting past a 403. Sources: [bgutil](https://github.com/Brainicism/bgutil-ytdlp-pot-provider), [PyPI](https://pypi.org/pypi/bgutil-ytdlp-pot-provider/json), [wpc](https://github.com/coletdjnz/yt-dlp-getpot-wpc). |
| yt-dlp with a throwaway account's cookies (step 6): `--cookies cookies.txt`, or `--cookies-from-browser firefox:<profile>` | The same as the guest rows, and it gets past a bot check or an age gate. | A throwaway Google login. Export in a private window, then close it (YouTube rotates cookies on open tabs). On Windows, Firefox or an exported file, not `--cookies-from-browser chrome`. His yes before first use. | Home machine | Free | High. The wiki: "you run the risk of it being banned (temporarily or permanently)... consider using a throwaway account." Never krish@mindmake.co or any account tied to his Gmail or Drive. About 2,000 videos an hour per account. Clients become web_embedded,tv_samsung,web (free account) or web_creator,tv_samsung,web (premium); the #17812 DRM reports all came with logged-in cookies. | Cookies do not rescue a datacenter IP: [#15573](https://github.com/yt-dlp/yt-dlp/issues/15573) (15 Jan 2026, AWS EC2, 403 even with cookies; a member: "YouTube regularly blocks or restrict datacenter IPs"). Chrome on Windows: [#10927](https://github.com/yt-dlp/yt-dlp/issues/10927) (open since 5 Sep 2024, a DPAPI decrypt failure, labelled external-issue) and [#15867](https://github.com/yt-dlp/yt-dlp/issues/15867) (opened 7 Feb 2026, closed that day as a duplicate of [#7271](https://github.com/yt-dlp/yt-dlp/issues/7271), "Permission denied" while Chrome is open; a contributor on 19 Aug 2026: "99.99% likely never going to be fixed"). Sources: [Extractors wiki](https://github.com/yt-dlp/yt-dlp/wiki/Extractors), [FAQ](https://github.com/yt-dlp/yt-dlp/wiki/FAQ). |
| yt-dlp on a GitHub Actions runner: `pip install -U "yt-dlp[default,deno]"` (Deno 2.9.8+ from PyPI), the bgutil image as a service container | The same as at home, but only when YouTube does not block the runner's IP. | Throwaway cookies plus a PO token provider, and most likely a residential proxy (`--proxy`). Section 6 forbids session cookies in Actions, so this row is out. | Unclear | Actions minutes from the private repositories' monthly allowance; a residential proxy would cost extra (price not researched). | The throwaway cookies would live in CI, and a ban is more likely from a flagged IP. | Unverified for Actions: no 2026 primary report. Datacenter blocks are reported on AWS EC2 ([#15573](https://github.com/yt-dlp/yt-dlp/issues/15573)), Google Colab ([youtube-transcript-api #585](https://github.com/jdepoix/youtube-transcript-api/issues/585), Apr 2026) and [Render](https://community.render.com/t/yt-dlp-sign-in-problem/26692); the [youtube-transcript-api README](https://github.com/jdepoix/youtube-transcript-api) says most AWS, GCP and Azure IPs are blocked. The check's own test from a datacenter container (not an Actions runner), 24 Oct 2026: watch and m.youtube.com watch pages returned 302 to google.com/sorry; oEmbed, the channel page, the RSS feed and `/api/timedtext?type=list` returned 200. |
| youtube-transcript-api 1.2.4 (29 Jan 2026), step 4: `YouTubeTranscriptApi().fetch(video_id, languages=[...])`, `.list(video_id)`; a CLI too | Snippets (text, start, duration), the language, whether the track is auto-generated, and translation. No title, author, date or counts. | No key and no browser. The video id, not the URL. Cookie login is "currently not available", so age-restricted videos fail. From cloud IPs, rotating residential proxies (WebshareProxyConfig on a "Residential" package, or GenericProxyConfig). | Home machine | Free. Webshare residential proxies are paid if used from a datacenter (price not researched). | None (no login). The risk is an IP block (RequestBlocked, IpBlocked). | It relies on an undocumented YouTube API ([README](https://github.com/jdepoix/youtube-transcript-api)). [#613](https://github.com/jdepoix/youtube-transcript-api/issues/613): on 21 Oct 2026 the maintainer answered "use proxies"; the same day a user with no proxy reported blocks on his own connection that clear after a reset and then come back. [#606](https://github.com/jdepoix/youtube-transcript-api/issues/606) (Jun 2026): 1.2.4 got an IP blocked. [#585](https://github.com/jdepoix/youtube-transcript-api/issues/585) (Apr 2026): blocked on Colab. No release since Jan 2026 ([PyPI](https://pypi.org/pypi/youtube-transcript-api/json)). |
| YouTube Data API v3 `videos.list`: `GET https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id=VIDEO_ID&key=API_KEY` (comments: `commentThreads.list`) | Metadata only: title, description, publishedAt, channelTitle, channelId, tags, thumbnails, defaultAudioLanguage; viewCount, likeCount, commentCount (dislikes private since 13 Dec 2021); duration; a flag that captions exist. No file and no caption text: `captions.download` costs 200 units and needs edit rights on the video. | An API key from a Google Cloud project. List methods accept unauthorised requests for public data. | Both | Free. videos.list 1 unit, commentThreads.list 1, captions.list 50. Default quota 10,000 units a day plus 100 search.list calls; it resets at midnight Pacific. | Low: a key, not a login. The project or key can be cut off for breaking the Developer Policies; using it inside a tool that runs yt-dlp risks III.E.6 (see Terms). | The official API; docs updated 15 Oct 2026; stable. Sources: [quota costs](https://developers.google.com/youtube/v3/determine_quota_cost), [videos.list](https://developers.google.com/youtube/v3/docs/videos/list), [videos](https://developers.google.com/youtube/v3/docs/videos), [captions.download](https://developers.google.com/youtube/v3/docs/captions/download), [getting started](https://developers.google.com/youtube/v3/getting-started). |
| YouTube oEmbed (step 1): `GET https://www.youtube.com/oembed?url=<watch or shorts URL>&format=json` | title, author_name, author_url, thumbnail_url (480x360), embed HTML. No date, counts or captions. | Nothing: no key, no login. | Both | Free | None | It returned the full JSON from a datacenter container on 24 Oct 2026, for a `/shorts/` URL too (the report's and the check's tests). The [oembed.com provider list](https://oembed.com/providers.json) includes youtube.com/shorts*. The first check that a link is real and public. |
| Apify `streamers/youtube-scraper` (official): startUrls, transcriptionAndSubtitle (NONE, ALWAYS_SUBTITLES, TRANSCRIPTION_AS_FALLBACK, ALWAYS_TRANSCRIBE), subtitlesLanguage, subtitlesFormat | title, text (description), date, duration, viewCount, likes, commentsCount, hashtags, thumbnailUrl, channelName, channelUrl, numberOfSubscribers, isMembersOnly, location, and subtitles on request. Optional AI description or summary (a model reading: leave it off). No file. | An Apify token (his paid account). His yes before a run. No YouTube login. | Both | BRONZE tier: $0.003 per video; transcript add-on $0.041 per started minute (event `transcribeMinute`); AI summary or description $0.01 per minute. ALWAYS_SUBTITLES probably costs only the $0.003 (inference from the event key, unverified). | None for any Google account; spend falls on Apify. | Modified 21 Oct 2026. 2,758,665 public runs in 30 days, 99.1% SUCCEEDED (a run status, not per video). Rated 4.81 from 198 reviews. Issues tab not read. Sources: [Store page](https://apify.com/streamers/youtube-scraper), [actor record](https://api.apify.com/v2/acts/streamers~youtube-scraper). |
| Apify `streamers/youtube-video-downloader` (official): videos[], preferredQuality, preferredFormat, storeInKVStore | The file (downloadedFileUrl, or videoOnlyUrl and audioOnlyUrl), durationSeconds, error and note; an optional transcript add-on. Little metadata. | An Apify token. His yes before a run. | Both | BRONZE tier: $0.005 per MB downloaded (estimate: about $0.20 for a 40 MB Short); transcript add-on $0.041 per started minute. | None for Google; Apify spend only. | Modified 21 Oct 2026. 275,651 public runs in 30 days: 94.0% SUCCEEDED, 5.3% timed out. Rated 4.26 from 28 reviews. The output carries error and note fields, so check each row. Sources: [Store page](https://apify.com/streamers/youtube-video-downloader), [actor record](https://api.apify.com/v2/acts/streamers~youtube-video-downloader). |
| Apify `marielise.dev/youtube-video-downloader` (community, yt-dlp inside), step 9: urls[], quality, format, youtubeCookies, residentialProxyMode, customProxyUrl | An MP4 or MP3 capped from 360p to 1080p, with title, uploader, duration, viewCount, deliveredQuality, fileSize, downloadUrl, status, errorCode, failurePhase and failurePlayerClient. | An Apify token. His yes before a run. Never pass youtubeCookies. | Both | $0.01 per minute at 360p or MP3, $0.02 at 720p, $0.03 at 1080p; $0.05 per MB when the residential proxy fallback is used. Charged on success only, per its description. Tier not stated. Estimate: a 60-second Short at 720p costs about $0.02. | None unless cookies are passed; then the throwaway-account rule applies. | Modified 7 Oct 2026. Its README describes a token server and a client fallback ladder. 54,530 public runs in 30 days, 99.9% SUCCEEDED. Rated 4.57 from 9 reviews. Sources: [Store page](https://apify.com/marielise.dev/youtube-video-downloader), [actor record](https://api.apify.com/v2/acts/marielise.dev~youtube-video-downloader). |
| Apify transcript actors (step 9): `johnvc/YoutubeTranscripts` first (youtube_url, languages, include_metadata, include_extended_metadata); then `starvibe/youtube-video-transcript`; `datapipe/youtube-video-downloader` with subtitlesOnly=true; `supreme_coder/youtube-transcript-scraper` | johnvc: timestamped segments and plain text, is_generated and the available languages. include_metadata (on by default, no charge) adds title, description, channel_name, channel_id, view_count, video_duration_seconds, thumbnail_url and tags; include_extended_metadata adds upload_date and like_count. starvibe: transcript with timestamps, title, description, upload date, views, likes, channel and duration. datapipe: subtitles in a chosen format, with optional stats and description. | An Apify token. His yes before a run. | Both | johnvc, BRONZE tier, pay per event: $0.0025 per video, charged only when a transcript comes back; extended metadata $0.003 more when it succeeds, so about $0.0055 with the date. starvibe $0.005 per result; datapipe $0.001 per video with subtitles; supreme_coder $0.0007 per transcript (tier not stated for these three). | None for Google. | 30-day public run success: johnvc 99.9% of 188,112 (modified 23 Oct 2026); starvibe 99.9% of 422,357 (modified 28 Mar 2026); datapipe 96.6% of 7,215 (modified 19 May 2026); supreme_coder 96.2% of 120,296. Avoid `pintostudio/youtube-transcript-scraper`: 17.8% of its 510,886 runs FAILED. Sources: [johnvc](https://apify.com/johnvc/YoutubeTranscripts), [johnvc record](https://api.apify.com/v2/acts/johnvc~YoutubeTranscripts), [starvibe](https://apify.com/starvibe/youtube-video-transcript), [starvibe record](https://api.apify.com/v2/acts/starvibe~youtube-video-transcript), [datapipe](https://apify.com/datapipe/youtube-video-downloader), [supreme_coder record](https://api.apify.com/v2/acts/supreme_coder~youtube-transcript-scraper), [pintostudio record](https://api.apify.com/v2/acts/pintostudio~youtube-transcript-scraper). |
| Firecrawl scrape with `formats: ["audio"]` on the YouTube URL | An MP3 of the audio as a signed Google Cloud Storage URL that expires after 1 hour. No video, captions or metadata. Whether a markdown scrape of the page includes the transcript is unverified. | A Firecrawl API key with credits. His yes before buying credits. | Both | 5 credits per page (1 base plus 4 for audio). | None for Google. | Untested. The Firecrawl account was out of credits during the research and again on the check's retry ("Insufficient credits"). Source: [Firecrawl scrape docs](https://docs.firecrawl.dev/features/scrape). |
| Local transcription: `yt-dlp -x --audio-format mp3 "<URL>"` (or the step 3 MP4), then faster-whisper 1.2.1 (31 Oct 2025), step 5 | A timestamped transcript of the spoken audio. | The audio; Python; the Windows machine's CPU or GPU. | Home machine | Free | None | Independent of YouTube once the audio is on disk. Quality and speed depend on the model size (not measured). Sources: [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [PyPI](https://pypi.org/pypi/faster-whisper/json). |
| Gemini API with the YouTube URL (step 8), added by the check: `generateContent` with `file_data.file_uri` set to the watch or Shorts URL | A model-written reading of the visuals (shots, on-screen text, pacing, editing) and the speech. Not a verbatim transcript. | A Google API key (Control Center's notes: the fleet's key is free tier, flash models only). Public videos only, not private or unlisted. His yes, because it is a model watching (sections 7.3 and D3). | Both (Google fetches the video) | "Available at no charge" in preview; free tier capped at 8 hours of YouTube video a day; about 100 tokens a second of video plus 32 a second of audio at default resolution; "Pricing and rate limits are likely to change". | None for any YouTube account. | Preview; docs last updated 13 Oct 2026; up to 10 videos per request on Gemini 2.5 and later; the examples use gemini-3.8-flash. Not tested. Source: [video understanding](https://ai.google.dev/gemini-api/docs/video-understanding). |
| Firecrawl scrape with `formats: ["video"]`, added by the check | Best-quality video as a signed Google Cloud Storage URL valid for 1 hour. | A Firecrawl API key with credits, through the REST API: the Firecrawl MCP tool in these sessions lists `audio` but not `video`. His yes before buying credits. | Both (Firecrawl does the fetch) | 5 credits per page. | None for Google. | Untested; the account has no credits. The docs' examples use a YouTube URL. Source: [Firecrawl scrape docs](https://docs.firecrawl.dev/features/scrape). |
| Channel RSS feed (step 7), added by the check: `GET https://www.youtube.com/feeds/videos.xml?channel_id=UC...` | The channel's 15 latest uploads, each with `<published>` (an exact timestamp), `<media:statistics views>` and `<media:starRating count>` (likes). | The channel id, read from the channel page's `"externalId"`. No key. | Both | Free | None | The check's own test from a datacenter IP, 24 Oct 2026: the feed returned 15 entries, and the channel page returned 200. Useful only when the pasted video is among the 15 latest uploads; a pasted Short is likely to be recent. |
| Supadata (hosted transcript API), added by the check; Python SDK `supadata` 1.6.0 (23 Feb 2026) | Transcripts for YouTube, TikTok, Instagram, Facebook and X; video, channel and playlist lookups. | A Supadata account and key. His yes to open the account. | Both (server-side) | 1 credit per transcript when captions exist; 2 credits per minute for an AI-generated transcript when they do not; 1 credit per lookup. Free plan 100 credits a month; Pro $17 a month for 3,000 credits. | None for Google. | Untested; reliability unknown. Sources: [pricing](https://supadata.ai/pricing), [PyPI](https://pypi.org/pypi/supadata/json). |
| ScrapeCreators, added by the check: `GET https://api.scrapecreators.com/v1/youtube/video/transcript` with an `x-api-key` header, `url` (a video or Shorts URL) and an optional `language` | A transcript. The same key also covers TikTok (including transcripts), Instagram (20 endpoints) and LinkedIn (6 endpoints). | A ScrapeCreators account and key. His yes to open the account. | Both | 1 credit per live call; a cached response is free with `cache_max_age`. 100 free credits, then $47 for 25,000 credits (about $1.88 per 1,000). | None for Google. | Untested. The endpoint details come from its tutorial pages, not the API reference. Sources: [site](https://scrapecreators.com/), [tutorial](https://scrapecreators.com/tutorials/how-to-scrape-youtube-transcript-with-python). |
| pytubefix 11.2.1 (16 Oct 2026), added by the check | Video downloads and captions (`yt.captions['a.en']`, `generate_srt_captions()`); OAuth for age-restricted videos. | Python on the home machine. OAuth means a Google login. | Home machine | Free | None as a guest. OAuth carries the same ban risk as cookies, and the yt-dlp wiki says YouTube's restrictions stopped OAuth working there, so it may fail here too (inference). | Actively maintained. Its README says nothing about PO tokens or bot checks (unverified). Useful as a second local engine if a yt-dlp release breaks. Sources: [PyPI](https://pypi.org/pypi/pytubefix/json), [GitHub](https://github.com/juanbindez/pytubefix), [Extractors wiki](https://github.com/yt-dlp/yt-dlp/wiki/Extractors). |
| Invidious through the yt-dlp-invidious plugin, considered by the check and rejected | Not assessed. | Not assessed. | Not assessed | Not assessed | Not assessed | Rejected: the last release is 0.1.1 from 6 Oct 2024, so it is stale and not worth building on. Source: [PyPI](https://pypi.org/pypi/yt-dlp-invidious/json). |

### Corrections applied

1. [#15392](https://github.com/yt-dlp/yt-dlp/issues/15392) is dropped as evidence that cookies fail on a flagged IP. The
   reporter was on a personal machine, his exported cookies.txt failed while `--cookies-from-browser firefox` worked,
   and a maintainer told a second user with the same error "You didn't export the cookies correctly".
   [#15573](https://github.com/yt-dlp/yt-dlp/issues/15573) (AWS EC2) stays as the datacenter example.
2. The johnvc price conflict is settled: pay per event, $0.0025 per video charged only when a transcript comes back,
   plus $0.003 for the upload date and likes. Step 9 now says about $0.0055 a video with the date, not $0.0025, and the
   conflict is gone from the open questions.
3. Deno is now "strongly recommended" rather than required: without it yt-dlp runs on visionos alone with fewer formats.
4. The caption pattern changed from `en.*` to `.*-orig` (with `,en` only when a translation is wanted); step 2 is no
   longer called one guest call; and [#17659](https://github.com/yt-dlp/yt-dlp/issues/17659) is marked unconfirmed, not
   a known limit. This also replaces `--sub-langs "en.*"` in section 6's provisional YouTube text.
5. The authority for using a PO token provider is now the PO Token Guide, not
   [#17682](https://github.com/yt-dlp/yt-dlp/issues/17682), which was closed not planned and whose "use a provider"
   advice came from a non-maintainer.
6. The Chrome cookie issues are re-dated and re-described: #15867 opened 7 Feb 2026 and closed that day as a duplicate
   of #7271; the "99.99%" remark is a contributor's, from 19 Aug 2026; #10927 is a DPAPI decrypt failure whose link to
   app-bound encryption is a contributor's prediction. Section 6 states that link as fact and should say "suspected".
   The advice (Firefox, or a file exported in a private window) is unchanged.
7. [#17812](https://github.com/yt-dlp/yt-dlp/issues/17812) now carries its labels (cant-reproduce, high-priority,
   site-bug), the fact that every report came with logged-in cookies, and that guests are not reported affected. Its
   open question is narrowed to guests.
8. New datacenter evidence is added (watch pages 302 to google.com/sorry; oEmbed, the channel page, RSS and the
   timedtext list return 200). Step 7 now uses oEmbed and RSS on the runner, and yt-dlp stays off it.
9. Firecrawl's `video` format is added as a method, with the note that only the REST API offers it here.
10. `streamers/youtube-scraper` now lists its four transcriptionAndSubtitle options and the `transcribeMinute` event,
    with the inference that ALWAYS_SUBTITLES costs only $0.003 a video, still marked unverified.
11. The chain is fixed three ways: (a) step 9's cost as in item 2; (b) the router restart in step 6 now says it gives a
    new IP only on a dynamic address; (c) Gemini is added as step 8, the free route that reads visuals from any IP, held
    behind his yes because sections 7.3 and D3 say no model watches.
12. #17412's opening date, open state and the "more than 55 seconds" comment are marked unverified: the check confirmed
    only its title.

Checked and unchanged: yt-dlp 2026.10.21 and its release notes; the default clients with and without cookies; the
`-t sleep` expansion; the wiki's guest and account limits and its throwaway warning; #17788 and #15796; bgutil 2.0.2
and its warnings; yt-dlp-getpot-wpc 1.1.2; youtube-transcript-api 1.2.4 and #613, #606, #585; the Data API quotas; the
Developer Policies and YouTube Terms wording; oEmbed from a datacenter IP; faster-whisper 1.2.1; and every price,
modified date, run count and success rate quoted for the other seven Apify actors (streamers/youtube-scraper,
streamers/youtube-video-downloader, marielise.dev, starvibe, datapipe, supreme_coder and pintostudio). johnvc's price is
item 2; its run count, success rate and modified date come from the first report only.

### Open questions

1. **Are GitHub Actions runner IPs blocked?** No 2026 report was found for Actions itself. Test: one manual workflow
   run (it uses Actions minutes; how many was not measured) that runs `curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n"
   "https://www.youtube.com/watch?v=dQw4w9WgXcQ"` plus the oEmbed and RSS calls. A 302 to google.com/sorry means
   blocked, as from the datacenter container.
2. **What does #17412 really say?** Its 12 Aug 2026 opening date, its open state and the "more than 55 seconds"
   comment are all unverified. Test:
   `gh issue view 17412 --repo yt-dlp/yt-dlp --comments`.
3. **Do guest caption downloads hold up from his home IP at his volume?** Test: run step 2 on 20 links in one sitting on
   one home machine, count results by class (`ok`, `http_429`, `no_data_blocks`, `bot_check`), then retry the failures
   once with `--sleep-subtitles 60`.
4. **Does `.*-orig` drop an uploaded English track?** The check found the `-orig` label on auto-caption tracks only, so
   an uploaded track may not match (inference, untested).
   Test: `yt-dlp --list-subs "<URL>"` on one English video with uploaded captions and on one non-English video, then
   compare with the files step 2 writes.
5. **Does the tv_samsung DRM problem (#17812) hit guests?** Not reported so far. Test: `yt-dlp -F "<URL>"` as a guest
   on five videos from a home machine, and look for a DRM warning on the tv_samsung formats.
6. **Is Docker on the Windows home machines?** Test: `docker version` on each. If it is missing, `node --version`
   (22+) or `deno --version` (2.0+) decides script mode.
7. **Does `streamers/youtube-scraper` charge only $0.003 for ALWAYS_SUBTITLES?** Test, with his yes: one run on one
   captioned video (about $0.003), then read the run's charged events. No `transcribeMinute` event means yes.
8. **How do the Apify actors fail per video, and what exact inputs do they take?** The success rates are run statuses,
   and the Issues tabs and input field types were not read. Test: open each actor's Issues tab and input schema on its
   Store page (free).
9. **Do Firecrawl's `audio` and `video` formats work on YouTube, and does a markdown scrape carry the transcript?**
   Untested, and the account is out of credits. Test, after a top-up he approves: one scrape of one public Short with
   `["audio"]` and one with `["video"]` through the REST API (5 credits each).
10. **Does the Data API key beside yt-dlp break Developer Policies III.E.6?** Cheapest settlement: keep the Data API out
    of the watcher. yt-dlp's info.json (home) and the RSS feed (runner) already carry the counts.
11. **Does a router restart give a new IP?** Only on a dynamic address (inference). Test: note the public IP, restart
    the router, compare.
12. **Does Gemini's YouTube URL input work on the fleet's free key, and with which model id?** Untested. Test, only after
    his yes to a model reading: one `generateContent` call on one public Short's URL, then read the response and its
    usage metadata.
13. **Does Supadata work, and how reliably?** Untested. Test, after his yes to open a free account: one transcript call
    on one captioned public video (1 of the 100 free monthly credits).
14. **Does ScrapeCreators' transcript endpoint work as its tutorials describe?** Untested. Test, after his yes to open
    an account: one call on one public video from the 100 free credits.
15. **How does pytubefix handle PO tokens and bot checks?** Its README is silent. Test: `python -m pip install
    "pytubefix==11.2.1"` on a home machine and fetch one public video's caption track as a guest.

### Terms

YouTube's Terms (effective 15 Dec 2023) forbid downloading content and accessing the Service by "automated means
(such as robots, botnets or scrapers)" without express authorisation, and forbid circumventing any part of the Service;
solving PO token and JavaScript challenges arguably falls under that ([Terms](https://www.youtube.com/t/terms)). The
API Developer Policies (updated 15 Oct 2026) bind any app using a Data API key: no storing copies of audiovisual
content (III.E.1.a), no scraping or using scraped data (III.E.6), no separating audio from video (III.I.7)
([Developer Policies](https://developers.google.com/youtube/terms/developer-policies)). Only the official API and oEmbed
are sanctioned. The practical consequence is IP blocks and suspension of any account whose cookies are used. This is a
reading of the published terms, not legal advice.

## LinkedIn posts

Researched on 2026-10-24 against LinkedIn's own pages, yt-dlp's code and issue tracker, Apify actor pages, Firecrawl's
pull requests and LinkedIn's API docs. A second reader then checked it. Every one of its corrections is applied below,
and where the two disagree the correction is used. No paid actor was run. "Unverified" and "inference" mean exactly
that.

This replaces the provisional LinkedIn list in brief section 6. Three things change. A public post loads in full for a
guest, with no login wall: 5 URLs in the first report and 22 more requests in the check all returned the whole post.
A reader of our own gets all four post types (text, image, document, video) from that page for free, so yt-dlp leaves
the chain. And for LinkedIn, D2 only decides the fallbacks and the login-only posts (groups, connections-only): a
public post needs neither his session nor Apify (inference from those tests).

### Recommended chain

**The gates, before anything runs.**

- Steps 0 and 1 are free and use no account of his. Build them now; they need no yes. Their first live run on the
  home machine is the once-per-platform end-to-end check, and that does need his yes (brief section 7.2).
- Steps 2 and 3 spend on his Apify account. Before asking, show the estimate (brief section 9; the figures are under
  "Cost per post" below). Each runs only on his yes given right before the run, or inside a standing monthly cap he
  sets with D2. If he sets a cap for Instagram, ask whether it covers LinkedIn too. Without either, skip both steps
  and record `apify_spend_not_approved`.
- Step 4 sends the link to Jina's service, anonymously. No rule of his covers that, so ask him once before turning it
  on (a recommendation, not his ruling).
- Steps 5b and 5c use his signed-in LinkedIn and wait on his written yes for that account risk (D2).
- Never put a LinkedIn cookie in GitHub Actions, and never send one to a cloud actor.
- Nothing here calls a model. The words come from the post page, LinkedIn's own caption and transcript fields, the
  document's PDF, OCR on page images, and faster-whisper on the home machine only when a video has none of these
  (brief section 7.3).
- Logs carry counts and class names only: never a link, post text, an author, an error message, a cookie or a token.
  Read secrets by name at run time: `APIFY_TOKEN`, and the proxy password under a name such as
  `APIFY_PROXY_PASSWORD` (the name is a proposal). Record which step worked as the fetcher's class name, and every
  failure as a fixed `status_class` (brief section 4). Suggested classes (a proposal, from no source):
  `li_unsupported_url`, `li_http_999`, `li_signin_page`, `li_no_post_body`, `li_doc_expired`, `li_doc_no_text`,
  `li_login_only`, `proxy_error`, `apify_item_error`, `apify_spend_not_approved`, `timeout`.
- Files land in the fetcher's local work folder. Where they are filed waits on D1.
- Fetch every media file in the same run that read the post page, never later from a saved URL. Document links
  expire within days (correction 5).

**How a link falls through (a proposal; the research gives the order, not these rules).**

- Run the steps in order and stop at the first that works (brief section 7.2). A step works when it returns the
  post's text and every media file the post shows. Step 4 returns words only, and its reading is marked text only.
- A step that fails records its class and passes the link to the next step.
- A step whose gate is closed is skipped: steps 2 and 3 with `apify_spend_not_approved`, step 4 until he has said yes
  to it once.
- A guest cannot tell a login-only post from a refused request, since both can show a sign-in page (inference). When
  every logged-out step that ran saw a sign-in page or returned no post, record `li_login_only` and go to step 5.
- When nothing works, the request is `failed` with the class of the last step tried that named one other than `other` (a last resort that can only say `other`, such as Instagram's cover-only step, never hides an earlier `login_wall`; 2026-10-28).

**On the home Windows machine (residential IP), for each pasted link.**

**0. Normalise the link. Free.**

Follow a `lnkd.in` short link or a share link to the canonical post URL and drop the query string. That is `url_key`.
The reader accepts these forms:

- `https://www.linkedin.com/posts/<slug>-activity-<id>-<4 chars>`. The 4-character suffix can hold a hyphen, as in
  the Canva test post ending `-B-78` (correction 10).
- `https://www.linkedin.com/feed/update/urn:li:activity:<id>/`
- `https://www.linkedin.com/feed/update/urn:li:ugcPost:<id>/`. Guests get the full page (correction 9).
- `https://www.linkedin.com/embed/feed/update/urn:li:activity:<id>`, as a fallback only. It returns the text and the
  video sources but no JSON-LD, so no date and no counts (correction 9).

Unverified: whether `lnkd.in` links and `/feed/update/urn:li:share:<id>/` links resolve for a guest (open question 8).
Anything else is `li_unsupported_url`.

**1. Our own guest-page reader. Free. No login, no account.**

One HTTPS GET of `url_key` with a normal desktop browser User-Agent and a timeout. One page request per pasted link
(two when the `/embed/` fallback below runs), then the media it lists: no crawling, no polling. To check a machine by hand, in PowerShell (`curl.exe`, because plain `curl` is another command
there):

```
curl.exe -sS -A "<a current desktop browser User-Agent>" -o post.html -w "%{http_code}\n" "https://www.linkedin.com/posts/satyanadella_no-one-becomes-a-clinician-to-do-paperwork-activity-7302346926123798528-jitu"
(Select-String -Path post.html -Pattern 'application/ld+json' -SimpleMatch).Count
```

A 200 and a count of 1 or more mean the reader works from that machine. The research does not record which
User-Agent it sent; keep the full string in one constant, `BROWSER_UA`, and have `doctor` report it. In the package,
standard library only (a sketch, untested):

```python
import html, json, re, urllib.request

req = urllib.request.Request(url_key, headers={"User-Agent": BROWSER_UA})
with urllib.request.urlopen(req, timeout=20) as r:  # a 999 raises HTTPError: record li_http_999
    page = r.read().decode("utf-8", "replace")      # urlopen follows redirects: a sign-in page can arrive as a 200
ld = [json.loads(b) for b in re.findall(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', page, re.S)]
# JSON held in an attribute (data-sources, data-native-document-config): html.unescape() it before json.loads()
```

What to read:

- **Kind.** JSON-LD `@type` is `VideoObject` on all 5 video post pages the check read, and `SocialMediaPosting`
  otherwise (inference from the report, which names only these two types). On a `VideoObject` the author is
  `creator`, not `author` (correction 11). For the contract's `shape` (brief section 5), test in this order: a
  `<video data-sources>` makes it `video`, an iframe with `data-native-document-config` makes it `document`,
  `feedshare` image URLs make it `image`, and none of these makes it `text` (a proposal from the markers below).
- **Text.** The commentary element `<p data-test-id="main-feed-activity-card__commentary">`, else JSON-LD
  `articleBody`.
- **Author, date, counts.** The JSON-LD author or creator (name, profile URL, logo or avatar). `datePublished`, or
  `uploadDate` on a video. Likes and comments from `interactionStatistic` (also `data-num-reactions`). No share count
  was seen for guests. Up to about 10 top comments sit in the JSON-LD (10 against a `commentCount` of 758 on one
  post), never the full thread (correction 6).
- **A video.** The `<video data-sources=...>` attribute lists progressive MP4s on
  `dms.licdn.com`. Renditions vary by post: 360p, 640p and 720p on the MathWorks post, only 640p and 720p on Satya
  Nadella's (correction 7). Take the largest. The words, with no speech-to-text, in this order. First a caption
  file, because brief section 7.3 wants words with timings: `data-captions-url` (WebVTT or SRT) or the `VideoObject`
  `caption` MediaObject (an auto-caption SRT). Else the `VideoObject` `transcript` field (543 characters on Satya's
  post; plain text, so no timings, inference). `duration` (for example `PT50S`) is there too. Run faster-whisper on
  the home machine only when none of these exist.
- **A document (PDF carousel).** The iframe's `data-native-document-config` JSON gives the title, `totalPageCount`,
  the first 3 cover images and `doc.manifestUrl`. GET that master manifest (public JSON on `media.licdn.com`). Then,
  at once, because these links expire:
  - GET `transcribedDocumentUrl`, the PDF. A guest HEAD returned 200 `application/pdf` without login on 3 of the 5
    documents the check read (127,172, 2,118,221 and 7,998,871 bytes; whether the other 2 were tried is not stated,
    correction 4). No full download of a PDF is reported, so a guest GET is untested. All 5 configs say "Sign in to
    download" with `scanRequiredForDownload` true, yet those HEADs worked.
  - GET every page image at the largest size. The master manifest's `perResolutions` holds 5 sizes, up to about
    1545px wide, and each size's image manifest lists every page image (6 of 6 pages on the Canva document). The field
    names inside those manifests are not recorded: save one as a test fixture and read them from it.
  - GET `transcriptManifestUrl` for per-page text, but do not trust it. It held text on 1 of 3 documents; every page
    was an empty string on the other 2 (Canva "The secret to portfolios", 4 pages; HubSpot, 7 pages) (correction 3).
    Take the text from the PDF itself, then OCR the page images for any page still empty (brief section 7.3; no PDF
    or OCR tool was tested here). Record `li_doc_no_text` when both come back empty.
- **Images.** The `feedshare` image URLs (`feedshare-shrink_800`, `feedshare-shrink_1280` in the path). Take the
  largest size the page lists: 800px on most posts, 1280px on 2 of 14. Never rewrite the size in a URL: the signed
  token is bound to the size, and a rewritten URL returns HTTP 403 (correction 8).

Store the files, never the media URLs (the post's own `url_key` is kept). Document URLs expire: on the Canva
document read 2026-10-24 the config's `expiresAt` was 2026-10-31, and the PDF link's `e=1793836800` is about
2026-11-05 UTC. Video and image URLs carry `e=2147483647`, which does not expire in practice (correction 5). A
document whose links have lapsed before the fetch is `li_doc_expired`: re-read the post page for fresh ones.

Fall through to step 2 on HTTP 999, a timeout, or a page with no JSON-LD and no commentary element (a sign-in page in
place of the post: `li_signin_page`; anything else: `li_no_post_body`). The markers that tell a sign-in page apart
are not recorded; keep the first one seen as a test fixture. On a timeout, a sign-in page or no post body, first make
one GET of the `/embed/` form: it may still give the text and the video sources, though whether it loads when the
main page does not is untested. If it gives the text, read the post from it and note in the reading that it has no
date or counts. On the first 999, make no more requests to linkedin.com in that run, the `/embed/` GET included: this
link and every later LinkedIn link in the run start at step 2 (a proposal: LinkedIn publishes no threshold,
correction 2).

Evidence. Tested 2026-10-24 from a Google Cloud datacenter IP (AS396982, Ohio, US), not from the home machine yet
(open question 2). The report read 5 URLs: a Canva document post, Satya Nadella's video post in the `/posts/`,
`/feed/update/` and `/embed/` forms, and a MathWorks video post. The check made 22 more GETs, 14 of them back to back
about a second apart, and every one returned 200 with full JSON-LD and no sign-in page (correction 1). The markup can
change without notice; yt-dlp's extractor and the Apify actors read the same structure. Pages:
[Satya Nadella](https://www.linkedin.com/posts/satyanadella_no-one-becomes-a-clinician-to-do-paperwork-activity-7302346926123798528-jitu),
[Canva](https://www.linkedin.com/posts/canva_usa-goals-results-activity-7519110405017853952-B-78),
[MathWorks](https://www.linkedin.com/posts/the-mathworks_2_what-is-mathworks-cloud-center-activity-7151241570371948544-4Gu7);
LinkedIn's unofficial 999 code: [http.dev/999](https://http.dev/999).

Cost: free. Risk to his account: none, since no login is used.

yt-dlp is not in the chain. The reader already downloads the same MP4 URLs. yt-dlp's URL pattern misses
hyphen-suffixed links, and by its code it returns no date, uploader or comment count on video posts (yt-dlp itself
was not run; corrections 10, 11 and 18c). This replaces brief section 6, item 4.

**2. Refused at step 1: the same reader through Apify's residential proxy. Paid, untested. No LinkedIn account.
(Added by the check.)**

It keeps one parser instead of switching to an actor's output. Only the page HTML goes through the proxy; fetch media
direct from `dms.licdn.com` and `media.licdn.com`.

```python
proxy = f"http://groups-RESIDENTIAL:{APIFY_PROXY_PASSWORD}@proxy.apify.com:8000"
# for a country: user "groups-RESIDENTIAL,country-XX"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({"https": proxy}))
```

- Cost: $8 per GB on Free and Starter, $7.5 on Scale, $7 on Business. Guest post pages measured 104 to 358 KB, so
  about $0.001 to $0.003 a post ([residential proxy docs](https://docs.apify.com/platform/proxy/residential-proxy),
  [pricing](https://apify.com/pricing), read 2026-10-24).
- Unverified: whether Apify's residential pool restricts linkedin.com. Its docs list no domain restrictions (open
  question 6).
- Fall through to step 3 on the same failures as step 1 (a 999, a timeout, a sign-in page, no post body), or on
  `proxy_error`.

**3. Apify post actors. Paid. No LinkedIn account.**

The research read each actor's page and prices; it ran none. The paths below are Apify's standard v2 run form; this
research did not check them against Apify's API docs, so they are unverified. They are HTTP requests, not shell
commands: send them from Python as in step 1, with the token in the header, never in the URL. Check each returned
item for the post's text; an empty dataset, or an item without text, is `apify_item_error`.

**3a. `harvestapi/linkedin-profile-posts` first.**

```
POST https://api.apify.com/v2/acts/harvestapi~linkedin-profile-posts/run-sync-get-dataset-items
Authorization: Bearer <APIFY_TOKEN>
Content-Type: application/json

{"targetUrls": ["<url_key>"], "maxPosts": 1}
```

- Gets `content`, `author` (name, publicIdentifier, linkedinUrl, info, avatar), `postedAt`, `engagement` (likes,
  comments, shares, reactions by type), `postImages` (url, width, height), `article`, `document` (title,
  totalPageCount, coverPages, manifestUrl, transcribedDocumentUrl, transcriptManifestUrl) and repost data. Leave
  comments and reactions off: they cost $0.002 each. Their input switches and defaults are not recorded, so read the
  actor's input schema before the first run and set them off explicitly.
- Fetch the document's PDF and page images at once, as in step 1, and read its text from the PDF and OCR, not the
  transcript manifest.
- A video URL is unverified. The README says it returns "media assets (images, videos, links)", but no video field
  appears in its schema or sample (correction 13, open question 4).
- Cost: $0.002 per post on Free and Bronze, $0.00175 on Silver, $0.0015 on Gold and above, plus $0.00005 per actor
  start. That is $0.00205 a post on Free or Bronze. A URL with no post costs $0.001.
- Health: modified 2026-09-25; 43,798 total and 12,202 monthly users; 4.4 from 55 reviews; the Store shows 100.0% of
  runs succeeded. Its issues list could not be read, so recent failures are unverified
  ([actor](https://apify.com/harvestapi/linkedin-profile-posts)).

**3b. A video post, or 3a gave no video URL: `supreme_coder/linkedin-post`.**

```
POST https://api.apify.com/v2/acts/supreme_coder~linkedin-post/run-sync-get-dataset-items
Authorization: Bearer <APIFY_TOKEN>
Content-Type: application/json

{"urls": ["<url_key>"], "deepScrape": true, "fetchDocumentDetails": true, "numComments": 0, "numLikes": 0}
```

- Gets `text`, author (name, profile URL, headline, followers), `postedAtISO`, `postedAtTimestamp`, `numLikes`,
  `numComments`, `numShares`, reaction counts, images, article, and `linkedinVideo.videoPlayMetadata`
  (progressiveStreams with height, width, bitrate and URLs; adaptiveStreams HLS playlists; transcripts with
  `captionFile`; duration).
- Download the largest progressive stream at once: these stream URLs carry their own `expiresAt` (correction 5). Take
  the words from `captionFile` before any speech-to-text.
- `fetchDocumentDetails` defaults to false, so set it. The listing promises "transcripts and all available pages as
  images", but its inferred output schema has no document field, so document output is unverified (correction 13).
- When step 1 failed, the post type is unknown. The report's rule: if 3a gives no video URL, run 3b, a second
  $0.00205. A text post also has no video URL, so this rule spends twice on text posts too (inference).
- Cost: $0.002 per post plus $0.00005 per start on Bronze, read 2026-10-24.
- Health: modified 2026-09-15; 17,463 total and 1,655 monthly users; 4.05 from 54 reviews; the Store shows 100.0%
  ([actor](https://apify.com/supreme_coder/linkedin-post)).

**3c. Both fail: `apimaestro/linkedin-post-detail`,** input `{"post_urls": ["<url_key>"]}`, sent like 3a to
`https://api.apify.com/v2/acts/apimaestro~linkedin-post-detail/run-sync-get-dataset-items` (unverified, as above).
$0.005 per result ($5 per 1,000; tier not stated). Gets text, type, created_at, URNs, author, stats and media items
(type, url, video_url, duration, width, height, bitrate, thumbnail). No document fields in its schema (unverified).
Only 470 monthly users and 3 reviews ([actor](https://apify.com/apimaestro/linkedin-post-detail)).

**4. Words only, when steps 1 to 3 fail or are skipped: Jina Reader. Free.**

```
curl.exe -sS "https://r.jina.ai/<url_key>"
```

Markdown of the guest page: the title (headline and author), the full text with links, and the reaction and comment
counts as link text. No date field, no video, no document pages. Without a key: 20 requests a minute. Worked on the
Canva document post on 2026-10-24, the one URL tried ([Jina Reader](https://jina.ai/reader/)). Mark the reading as
text only.

**5. Login-only posts (groups, connections-only).**

No logged-out method reaches them: yt-dlp's tracker records a group post as "auth-walled"
([#16531](https://github.com/yt-dlp/yt-dlp/issues/16531)). Record `li_login_only`, then in this order:

- **5a.** Krish pastes the text or a screenshot himself. Free, no risk.
- **5b. With his written yes on the account risk: a capture he triggers in his own signed-in browser on the home
  machine (added by the check).** Either the [SingleFile](https://github.com/gildas-lormeau/SingleFile) extension
  (Chrome, Edge, Firefox) saves the post as he sees it as one HTML file, which the watcher picks up as a dropped file,
  or a small "send to content-watcher" bookmarklet or extension posts the rendered page to the local service. The
  reader parses it like a guest page (inference, open question 14). Signed in, a document post's own Download control
  gives the PDF. It makes no automated requests and sets no `navigator.webdriver`, so its exposure should be lower
  than Playwright's (inference, unverified). LinkedIn's help page still names browser plug-ins and extensions that
  scrape as grounds to "risk having their accounts restricted or shut down"
  ([help page](https://www.linkedin.com/help/linkedin/answer/a1341387)). Free.
- **5c. Only if he accepts the account risk in writing: one fetch he triggers by hand with Playwright,** on a
  dedicated browser profile he signed into, on the home machine, from his usual IP, one post per paste. No safe
  threshold is published. The Playwright version was not checked in this research. Install with
  `python -m pip install playwright`, then `python -m playwright install chromium`. A sketch, untested:

  ```python
  from playwright.sync_api import sync_playwright
  with sync_playwright() as p:
      ctx = p.chromium.launch_persistent_context(PROFILE_DIR, headless=False)
      page = ctx.new_page()
      page.goto(url_key, timeout=30000)
      saved = page.content()  # parse with the step 1 reader
      ctx.close()
  ```

Never `curious_coder/linkedin-post-search-scraper`: it runs his live session cookie from Apify's servers on a proxy
IP, the pattern LinkedIn's help page says gets accounts restricted.

**6. Do not plan on these.** The official API: even if `r_member_social` reopened, it reads on behalf of the signed-in
member, not other members' posts (correction 15). Firecrawl: linkedin.com is on its blocklist, no paid route for post
URLs exists, and the account has 0 credits until 2026-11-09 (correction 14). ScrapeCreators: a new account for text
and transcripts only, so only if Apify fails, and only on his yes, since it is a new account and it spends.
`agentx/linkedin-video-downloader`: 60 to 140 times the price of the actors above.

**On GitHub Actions (the fallback machine).** The same chain, starting at step 1, because step 1 uses no cookie and
the one datacenter IP tested was not refused for post pages (corrections 1 and 18a). Pending one run on a runner,
which is on Azure, untested (open question 1). This replaces, for LinkedIn, the brief's line "If Actions ever runs a
fetch, it starts at the Apify step". Steps 5b and 5c never run on Actions.

**Cost per post.** A public post on the home machine: $0. Refused at step 1: about $0.001 to $0.003 through the
proxy, or $0.00205 for one actor run (3a on Free or Bronze, 3b on Bronze), $0.0041 when 3a and 3b both run, $0.005
for 3c. The worst case, the proxy then 3a, 3b and 3c, is about $0.0121 a post, plus any start fee for 3c (not
recorded). Jina: $0. A login-only post: $0.

### Methods

| Method | Gets | Needs | Works from | Cost | Account risk | State in October 2026 |
|---|---|---|---|---|---|---|
| Our own guest-page reader: one HTTPS GET of the public post page, parsed in Python | Text (commentary element, JSON-LD `articleBody`). Author (JSON-LD `author`, or `creator` on a `VideoObject`). Date (`datePublished`, `uploadDate`). Likes and comments; no share count. Up to about 10 top comments. Video: progressive MP4s (renditions vary, up to 720p seen), captions (WebVTT or auto SRT), the `VideoObject` transcript text and duration. Document: title, page count, the PDF, every page image up to about 1545px, a per-page text manifest that is often empty. Images: the largest size listed (800px, sometimes 1280px). | Nothing. Public ("Anyone") posts only; group and connections-only posts show a sign-in page. | Both. Tested from a Google Cloud datacenter IP only; not yet from the home machine or an Azure (Actions) runner. | Free | None: no login. LinkedIn may answer HTTP 999 or a sign-in page. | Verified 2026-10-24: 5 URLs in the report; 22 GETs in the check, 14 back to back, all 200 with full JSON-LD. Document links expire within days. Markup can change without notice ([Satya post](https://www.linkedin.com/posts/satyanadella_no-one-becomes-a-clinician-to-do-paperwork-activity-7302346926123798528-jitu), [Canva post](https://www.linkedin.com/posts/canva_usa-goals-results-activity-7519110405017853952-B-78)). |
| yt-dlp 2026.10.21, `LinkedInIE`: `yt-dlp --write-subs --write-info-json <post URL>` | Read from its code; yt-dlp was not run. Video posts only: MP4 formats from `<video data-sources>` (up to 720p for guests), English subtitles, title (og:title), truncated description, thumbnail, like_count. No date, no comment count, no images, no documents. Uploader comes back empty on `VideoObject` pages. Text, image and document posts fail with "Unable to extract video" (its regex replayed on the saved Canva document page). | Nothing for public video posts. Login-only posts need browser cookies and an unmerged patch. Password login was removed on 2026-06-26 ([PR #17039](https://github.com/yt-dlp/yt-dlp/pull/17039)). | Both | Free | None without cookies. With `--cookies-from-browser` it acts as his session. | Not in the chain. Its URL pattern misses `/posts/` links whose 4-character suffix has a hyphen, and `urn:li:share:` and `urn:li:ugcPost:` feed links. [#16531](https://github.com/yt-dlp/yt-dlp/issues/16531) (group posts) open since 2026-04-20; its fix [PR #16560](https://github.com/yt-dlp/yt-dlp/pull/16560) closed unmerged 2026-05-09 ([extractor](https://raw.githubusercontent.com/yt-dlp/yt-dlp/master/yt_dlp/extractor/linkedin.py), [PyPI](https://pypi.org/project/yt-dlp/)). |
| Apify `harvestapi/linkedin-profile-posts`, `{"targetUrls": [url], "maxPosts": 1}` | Text, author, postedAt, likes, comments, shares, reactions by type, images, article, document (title, page count, cover pages, manifestUrl, transcribedDocumentUrl, transcriptManifestUrl), repost data; comments and reactions optional. Video URL unverified. | `APIFY_TOKEN`. No LinkedIn cookies or account. | Both | $0.002 per post on Free and Bronze, $0.00175 Silver, $0.0015 Gold and above; $0.00005 per start; $0.001 for a URL with no post; comments and reactions $0.002 each | None to his LinkedIn. Apify spend. | Modified 2026-09-25; 43,798 total and 12,202 monthly users; 4.4 from 55; Store shows 100.0% succeeded; issues unreadable ([actor](https://apify.com/harvestapi/linkedin-profile-posts)). |
| Apify `supreme_coder/linkedin-post`, `{"urls": [url], "deepScrape": true, "fetchDocumentDetails": true, "numComments": 0, "numLikes": 0}` | Text, author (name, URL, headline, followers), postedAtISO, likes, comments, shares, reactions, images, article, video (progressive MP4 streams, HLS playlists, transcripts with captionFile, duration). Document pages and transcripts promised with `fetchDocumentDetails`, but no document field in its schema (unverified). | `APIFY_TOKEN`. No cookies. | Both | Bronze: $0.002 per post plus $0.00005 per start | None to his LinkedIn. Apify spend. | Modified 2026-09-15; 17,463 total and 1,655 monthly users; 4.05 from 54; Store shows 100.0%; video URLs carry their own expiry ([actor](https://apify.com/supreme_coder/linkedin-post)). |
| Apify `apimaestro/linkedin-post-detail`, `{"post_urls": [url]}` | Text, type, created_at, URNs, author (name, headline, profile_url, profile_picture, followers), reactions, comments, shares, media items (type, url, video_url, duration, width, height, bitrate, thumbnail). No document fields in its schema (unverified). | `APIFY_TOKEN`. No cookies. | Both | $0.005 per result ($5 per 1,000; tier not stated) | None to his LinkedIn. Apify spend. | Modified 2026-07-02; 1,876 total and 470 monthly users; 5.0 from only 3 reviews ([actor](https://apify.com/apimaestro/linkedin-post-detail)). |
| Apify `curious_coder/linkedin-post-search-scraper`, with his cookies | Text, images, attachments, links, type, timestamps, counts, author, comments. As his account it could reach group and connections-only posts (inferred, not tested). | His exported LinkedIn cookies, his user agent, a proxy in his login country | Datacenter | $0.0005 per result plus $0.0005 per start (tier not stated) | High: his live session used from Apify's servers on a proxy IP | Ruled out. Modified 2026-10-18; 10,348 total but 125 monthly users; 4.66 from 20; an issue "it's not working" (date unverified) ([actor](https://apify.com/curious_coder/linkedin-post-search-scraper)). |
| Apify `agentx/linkedin-video-downloader`, `{"video_url": url, "video_quality": ...}` | Video post metadata and an optional stored video file, one post per run | `APIFY_TOKEN`; public posts | Both | $0.117 per metadata record, $0.27 per downloaded video, $0.01 per start (tier not stated) | None to his LinkedIn. Apify spend. | 32 total and 16 monthly users, no rating. Not worth it ([actor](https://apify.com/agentx/linkedin-video-downloader)). |
| Jina Reader: `GET https://r.jina.ai/<post URL>` | Markdown of the guest page: title, full text with links, reaction and comment counts as link text. No video, no document pages, no date field. | Nothing up to 20 requests a minute. A free key gives 500 a minute and 10M free tokens. | Both | Free at 20 a minute; keyed use is charged in tokens by content length | None | Worked on 1 URL on 2026-10-24. Text-only fallback ([Jina Reader](https://jina.ai/reader/)). |
| Firecrawl scrape (`firecrawl_scrape` or `POST /v2/scrape`) | Untested. linkedin.com is on its blocklist; the "about" keyword exempted `linkedin.com/company/<slug>/about/`, and exemptions are substring matches, so post results may be inconsistent (inferred) ([PR #5011](https://patch-diff.githubusercontent.com/raw/firecrawl/firecrawl/pull/5011.patch)); profile URLs go to paid providers ([PR #4846](https://github.com/firecrawl/firecrawl/pull/4846)). `firecrawl_find_tools` found no provider for post URLs. | Firecrawl key and credits | Unclear | Unknown for LinkedIn posts. Account at 0 of 1,000 plan credits; resets 2026-11-09. | None | Treat as not working. A July 2026 third-party review reports 0% on LinkedIn, method not stated ([review](https://syncgtm.com/blog/firecrawl-review-2026)). |
| Playwright with his own signed-in profile on the home machine | Everything a signed-in viewer sees, including group and connections-only posts, and comments. Higher video renditions maybe (unverified). | His LinkedIn login in a dedicated browser profile; Playwright for Python and Chromium or Chrome (version not checked) | Home machine | Free | Real. User Agreement 8.2 bans scraping software and bots; the help page warns of accounts "restricted or shut down". Automated browsers set `navigator.webdriver` (vendor claim, unverified). | No LinkedIn statement on how it detects Playwright. Vendor figures (23%, 40%, 97%) conflict and are unverified ([indiehackers](https://www.indiehackers.com/post/every-linkedin-scraper-gets-your-account-banned-except-one-approach-97aff2ff54), [cleverly](https://cleverly.co/blog/why-linkedin-automation-tools-get-your-account-banned-and-what-to-do-instead)). Last resort, on his written yes. |
| Official LinkedIn Posts API, `GET https://api.linkedin.com/rest/posts/{urn}` | Commentary, author URN, publishedAt, media ids, only for posts the app may read | `r_member_social`, closed: "We're not accepting access requests at this time due to resource constraints". Even open, it reads on behalf of the signed-in member. `r_organization_social` covers only pages he administers; `r_compliance` is closed. | Both | Free, but no access | None | Not usable. Overview dated 2026-03-31, updated 2026-05-15; Posts API dated 2026-05-07, updated 2026-05-13 ([overview](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/community-management-overview), [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)). |
| Apify residential proxy in front of our own reader (added by the check) | The same as our own reader, through a residential IP | His Apify proxy password. No LinkedIn login. | Both; meant for Actions and refused GETs | $8 per GB on Free and Starter, $7.5 Scale, $7 Business: about $0.001 to $0.003 a post for the HTML only | None to his LinkedIn. Apify spend. | Untested. Whether the pool restricts linkedin.com is unverified; the docs list no domain restrictions ([docs](https://docs.apify.com/platform/proxy/residential-proxy), [pricing](https://apify.com/pricing)). |
| A capture he triggers in his own signed-in browser: SingleFile, or a "send to content-watcher" bookmarklet or extension (added by the check) | Whatever he can see, including group and connections-only posts. Signed in, the document's own Download control gives the PDF. | His signed-in browser on the home machine; [SingleFile](https://github.com/gildas-lormeau/SingleFile) (Chrome, Edge, Firefox) or a bookmarklet to build | Home machine | Free | Some. The help page names browser plug-ins and extensions that scrape. No automated requests and no `navigator.webdriver`, so lower exposure than Playwright (inferred, unverified). | Not tried. Needs his written yes ([help page](https://www.linkedin.com/help/linkedin/answer/a1341387)). |
| ScrapeCreators: `GET https://api.scrapecreators.com/v1/linkedin/post?url=<post URL>` and `/v1/linkedin/post/transcript` (added by the check) | Post: name, headline, description, datePublished, likeCount, commentCount, author name, url, followers, comments; no image, video or document fields shown. Transcript: the video's own transcript, or `transcriptNotAvailable`. | A new ScrapeCreators account (he has none) | Both | 1 credit per call. Vendor-reported packs: $47 for 25,000 credits (about $1.88 per 1,000) and $497 for 500,000, credits never expire (vendor blog, not the docs) | None to his LinkedIn. Spend. | Not tried. Only if Apify fails ([post](https://docs.scrapecreators.com/v1/linkedin/post), [transcript](https://docs.scrapecreators.com/v1/linkedin/post/transcript), [pricing blog](https://scrapecreators.com/blog/linkedin-post-scrapers)). |

### Corrections applied

1. Test IP: "IP class unknown" became "a Google Cloud datacenter IP (AS396982, Ohio)", where 22 guest GETs, 14 back to
   back, all returned 200. Step 1 now runs first on Actions too, pending one Azure runner test.
2. Rate limit: the "about 16 requests" figure was about profile pages, not posts
   ([sociavault](https://sociavault.com/blog/linkedin-public-profile-not-available)). Removed as post evidence; no
   threshold is published, and 22 post requests saw no 999.
3. Document text: the per-page transcript held text on 1 of 3 documents. Step 1 now takes text from the PDF, then OCR
   on the page images, and keeps the transcript only as a bonus.
4. Document coverage: one Canva post became 5 documents with the same structure (3 company, 2 member), with a guest
   HEAD on the PDF returning 200 for 3 of them, and page images up to about 1545px in 5 sizes. Step 1 takes the
   largest set. The question about authors who turn downloads off stays open.
5. Expiring links: added that document and PDF links expire within days, and that supreme_coder's video streams carry
   their own expiry. The chain fetches at paste time and stores files, never URLs.
6. Comments: "one comment" became "up to about 10 top comments in JSON-LD, not the full thread".
7. Video: renditions vary by post (360p to 720p, or only 640p and 720p). Added the `VideoObject` transcript text,
   caption SRT, duration and upload date, so a video that carries them gets words without speech-to-text. The
   transcript was seen on one post; how often it is there is open question 9.
8. Images: 1280px is offered on some posts (2 of 14), and rewriting a size returns 403. Step 1 takes the largest size
   listed.
9. URL forms: `/feed/update/urn:li:ugcPost:<id>/` works for guests and is accepted. The `/embed/` form has no JSON-LD
   and is a fallback only.
10. yt-dlp URL matching: its pattern misses `/posts/` links with a hyphen in the 4-character suffix, including the
    report's own Canva test link. yt-dlp left the chain.
11. yt-dlp uploader: it is empty on every video post page seen, because those pages carry `VideoObject` with
    `creator` (inferred from code, not run). The reader reads `creator`.
12. yt-dlp issues: confirmed. #16531 open since 2026-04-20, last comment 2026-04-26, labels account-needed,
    patch-available and site-bug; PR #16560 closed unmerged 2026-05-09 (its head repository was deleted); PR #17039
    merged 2026-06-26; PyPI 2026.10.21 uploaded 2026-10-21. The report's claims stand.
13. Apify facts: re-read and confirmed, with user counts one or two higher. Added that harvestapi's README mentions
    videos but its schema has none, and that supreme_coder's `fetchDocumentDetails` defaults to false and its schema has no
    document field. Step 3 sets the flag and marks both outputs unverified.
14. Firecrawl: PR #5011 is about the keyword "about" exempting `linkedin.com/company/<slug>/about/`; `/pulse/` and
    `/legal/` are not in the patch. Exemptions are plain substring matches, so a post URL holding an exempt keyword
    could pass while others fail (inferred from the patch). Added: no Exchange provider claims post URLs, and the
    account has 0 of 1,000 credits until 2026-11-09. "Blocklisted, credits out" stands, on these reasons.
15. Official API: added that even a reopened `r_member_social` reads on behalf of the signed-in member, so it would
    never cover other members' posts.
16. Terms: the section 8.2 quotes are given in full below; the "Effective on November 3, 2025" date, section 1.2 and
    robots.txt are confirmed.
17. hiQ: dated the ruling 4 November 2022 and the consent judgment 6 December 2022, and added that the injunction draws
    no line between public and logged-in pages.
18. The chain: (a) step 1 runs first on Actions too; (b) documents get PDF text and OCR; (c) yt-dlp is dropped; (d)
    document assets are fetched at paste time. All four are applied above.

### Open questions

1. **Do GitHub Actions runners (Azure) get a 999 or a sign-in page on a public post?** Test: one workflow run on the
   Satya Nadella post, logging only the status code and the JSON-LD count. On `windows-latest` (`shell: pwsh`) the two
   step 1 PowerShell lines run as they are. On `ubuntu-latest`, with `UA` set to a desktop browser User-Agent:
   `curl -sS -A "$UA" -o post.html -w "%{http_code}\n" "<post URL>"`, then `grep -c 'application/ld+json' post.html`.
   Runner minutes only; no media, no cookies.
2. **Does step 1 work from the home machine?** Every test ran from a Google Cloud IP; a residential IP should do at
   least as well (inference). Test: the step 1 `curl.exe` check on the home machine, as part of the live check that
   needs his yes (brief section 7.2). Free.
3. **Is the document PDF open to guests when the author turned downloads off?** Seen on 3 documents, none known to
   have downloads off. Test: on the next document post where his normal signed-in view shows no Download control, the
   reader's guest HEAD of `transcribedDocumentUrl`. Free.
4. **Does harvestapi return a video URL for a video post?** Test: one approved run on the Satya Nadella post. $0.00205
   on Free or Bronze. Needs his yes.
5. **Does supreme_coder return a document's pages and text with `fetchDocumentDetails` on?** Test: one approved run on
   the Canva document post. $0.00205 on Bronze. Needs his yes.
6. **Does Apify's residential proxy reach linkedin.com post pages?** Test: one GET of the Satya Nadella page through
   it. About $0.001 to $0.003. Needs his yes.
7. **How many of the posts Krish saves are group or connections-only?** If many, 5a to 5c matter, and so does his D2
   answer. Test: count `li_login_only` over the first 20 links he pastes. Free.
8. **Do `lnkd.in` links and `/feed/update/urn:li:share:<id>/` links resolve for a guest?** Neither was tried. Test: one
   GET, following redirects, of the first such link he pastes. Free.
9. **How often does a video post carry its own transcript or caption file?** Seen on Satya Nadella's post. This decides
   whether faster-whisper is the normal path or the rare one. Test: count over the first 10 video posts. Free.
10. **Do LinkedIn's document PDFs carry a text layer, or does every design-heavy deck need OCR?** Untested. Test: a
    text extraction of the PDFs of the two documents whose transcript was empty (Canva "The secret to portfolios",
    HubSpot), fetched fresh from their pages. Free.
11. **Are images larger than 1280px ever listed for guests?** Seen: 800px and 1280px only. Test: log the largest
    `feedshare` size over the first 20 image posts. Free.
12. **What request rate brings a 999 on post pages?** None published; 22 requests saw none. Test: count `li_http_999`
    per week in the class log. Free, no extra requests.
13. **Is his Apify plan Bronze?** Every Apify price above depends on it. The Instagram research in this same pass
    found the Apify API reporting BRONZE for the connected account on 2026-10-24; this LinkedIn research did not
    check it. Test: read the plan in the Apify console. Free.
14. **Does a page saved from his signed-in view parse with the guest reader?** The check infers it does. Test: one
    public post saved with SingleFile, then parsed. Free, but it uses his signed-in browser, so it needs his yes (5b).
15. **How exposed is a capture from his own browser compared with Playwright?** LinkedIn publishes nothing on
    detection. No test settles it; it is part of his D2 call.
16. **Does Firecrawl refuse every LinkedIn post URL?** Low value while step 1 works. Test: after credits reset on
    2026-11-09, one scrape of a public post. Uses plan credits (amount unverified); needs his yes.

### Terms

Every automated method here breaks LinkedIn's User Agreement, "Effective on November 3, 2025", including one-off
private study of public posts ([User Agreement](https://www.linkedin.com/legal/user-agreement), read 2026-10-24).
Section 1.2 says "This Contract applies to Members and Visitors", so logged-out fetching is covered too. Section 8.2
bars these, quoted in full:

- "Develop, support or use software, devices, scripts, robots or any other means or processes (such as crawlers,
  browser plugins and add-ons or any other technology) to scrape or copy the Services, including profiles and other
  data from the Services".
- "Copy, use, display or distribute any information (including content) obtained from the Services, whether directly
  or through third parties (such as search tools or data aggregators or brokers), without the consent of the content
  owner (such as LinkedIn for content it owns)".
- "Use bots or other unauthorized automated methods to access the Services, add or download contacts, send or
  redirect messages, create, comment on, like, share, or re-share posts, or otherwise drive inauthentic engagement".

robots.txt opens with "The use of robots or other automated means to access LinkedIn without the express permission
of LinkedIn is strictly prohibited" and sets `User-agent: *` / `Disallow: /`
([robots.txt](https://www.linkedin.com/robots.txt), read 2026-10-24). The help page "Prohibited software and
extensions" shows only "Last updated: 2 years ago". It says members who use such tools "risk having their accounts
restricted or shut down" ([help page](https://www.linkedin.com/help/linkedin/answer/a1341387)).

hiQ v. LinkedIn: a ruling dated 4 November 2022 found that hiQ "had breached LinkedIn's User Agreement due to its
scraping and creation of fake accounts". A stipulated consent judgment filed on 6 December 2022 set $500,000 and a
permanent injunction. The injunction makes "no express distinction between public and non-public/password-protected
portions of LinkedIn"
([Proskauer](https://www.proskauer.com/blog/hiq-and-linkedin-reach-proposed-settlement-in-landmark-scraping-case)).
Earlier, the Ninth Circuit had held that breaching a public site's terms alone does not trigger CFAA liability
([Wikipedia](https://en.wikipedia.org/wiki/HiQ_Labs_v._LinkedIn)).

In practice, logged-out fetching and outside actors risk a block, not his account. Anything using his login or
cookies risks his account being "restricted or shut down". Not legal advice.
