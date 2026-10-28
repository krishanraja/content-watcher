# Every way the watcher tries to get a post

Status: Current, 2026-10-24 (the chain table re-checked against `_methods` on 2026-10-27). Krish, 2026-10-24: "Build all the fallbacks. This needs to be bulletproof. There's got
to be a tonne of ways to do this reliably. There are so many free sites out there that I just copy a link in, press
download, and it lets me select the quality and whatnot. I never really need to download a high-quality video when I'm
doing this job."

Each chain runs in order and stops at the first step that returns the post. Free steps come first, then free sites,
then Apify under the standing $5 a month cap, then words alone when no file can be had (filed as a text card, so a
pasted link always becomes something). Video is fetched at 720p at most. A step that is not installed or not set up is
skipped with its class in the local log. The code is `content_watcher/fetch/__init__.py` (`_methods`); the evidence for
each step is `docs/FETCH_METHODS.md`.

| Platform | Chain |
|---|---|
| Instagram reel | Instagram's embed player, yt-dlp, Instaloader, cobalt (if set up), his signed-in Firefox session through gallery-dl (on a home computer that has one; 2026-10-28), Apify reel scraper, Apify downloader (`snapinsta~instagram-downloader-api`, for age-restricted posts), then the cover picture and caption as a last resort |
| Instagram post or carousel | Instagram's embed player, yt-dlp carousel mode, Instaloader, cobalt, his signed-in Firefox session through gallery-dl, Apify post scraper, Apify downloader (age-restricted posts), then the cover picture and caption |
| TikTok video | yt-dlp (a file with no sound moves on), gallery-dl, the post page, TikWM, Tikmate, cobalt, Apify |
| TikTok photo post | gallery-dl, the post page, TikWM, cobalt, Apify |
| YouTube | oEmbed check (a removed or private video stops here), yt-dlp with Deno and the bgutil token helper, yt-dlp as the mobile client, cobalt, for a Short the Apify downloader (about $0.02), then words only: youtube-transcript-api, Apify transcripts |
| LinkedIn | the public post page (with one embed retry; document posts bring their PDF or page images), Apify harvestapi, Apify supreme_coder, then words only: Jina Reader |

## Instagram and YouTube Shorts, the two that matter most

Krish, 2026-10-24: "Instagram and YouTube Shorts are the main ones, you need to find a reliable way".

- **Instagram: the embed player, first.** The page Instagram serves to websites that embed a post answers without a
  login, and its HTML carries the post's own data: every slide in order with whether it is a video, the file
  addresses, the caption, the account and the counts (`content_watcher/fetch/instagram_embed.py`). Tested live on
  2026-10-24 from a cloud machine, where the normal reel page sends a logged-out visitor to the login page: a reel
  (video with sound, caption, account, likes, comments and views), a three-video carousel (all three, in order) and a
  photo post, then a full fetch and reading of the reel through `content-watch`. It needs a browser's navigation
  headers; if the data ever stops coming, the same page opens in a headless browser. The one thing it cannot give is a
  reel with licensed music ("Watch on Instagram"): that goes on to yt-dlp, Instaloader, cobalt and Apify, which does
  handle it, and if every step misses, the cover picture and caption still make a card.
- **YouTube Shorts: the home connection, set up properly, then a paid backstop.** YouTube refuses cloud machines
  (confirmed again on 2026-10-24), so Shorts are fetched from the home computers with yt-dlp, Deno and the bgutil token
  helper the research names; the installer starts the helper in Docker. If YouTube still refuses, the Apify downloader
  gets the Short at 720p for about $0.02, under the $5 cap, so a Short does not fail outright. Words-only steps come
  last.

## The free sites, and what was tested

Tested live on 2026-10-24 from a cloud machine with the research's public TikTok test post:

- **TikWM** (TikTok): answered with the caption, author, date and counts, and its video downloaded with sound.
- **Tikmate** (TikTok): answered with the caption, author and counts; its download host sits on port 8443, which the
  cloud machine could not reach, so the download is unverified until the first run at home.
- **cobalt's public instance**: refuses without a key (`error.api.auth.jwt.missing`), so the watcher uses a cobalt
  run on the home computer (`scripts/cobalt/README.md`) or a hosted one with `COBALT_API_KEY`.
- **Instagram download sites** (snapinsta, saveig, sssinstagram, fastdl, igram, saveinsta): none answered a plain
  request; they hide the download step behind tokens their pages compute in the browser. Their sites are not called.
  But snapinsta's Apify actor (`snapinsta~instagram-downloader-api`, about $0.0004 a request) is a step since
  2026-10-28: Krish's carousel `/p/DfAY9PWFuEX` was age-restricted, so every logged-out route was refused (Apify's
  scraper: "Restricted access ... The post is age-restricted"), and this actor returned all 16 slides. It gives the
  files only, so such a reading carries no caption or author; each file's extension comes from its file type, because
  the address can say `.heic` over JPEG bytes.

Every free site sees the link it is sent and has no contract or published terms. Krish's message above is the go-ahead
for them; Apify, the only paid step, stays under the $5 cap.
