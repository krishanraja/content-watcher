# Every way the watcher tries to get a post

Status: Current, 2026-10-24. Krish, 2026-10-24: "Build all the fallbacks. This needs to be bulletproof. There's got
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
| Instagram reel | yt-dlp, Instaloader, cobalt (if set up), Apify reel scraper |
| Instagram post or carousel | yt-dlp carousel mode, Instaloader, cobalt, Apify post scraper |
| TikTok video | yt-dlp (a file with no sound moves on), gallery-dl, the post page, TikWM, Tikmate, cobalt, Apify |
| TikTok photo post | gallery-dl, the post page, TikWM, cobalt, Apify |
| YouTube | oEmbed check (a removed or private video stops here), yt-dlp, yt-dlp as the mobile client, cobalt, then words only: youtube-transcript-api, Apify transcripts |
| LinkedIn | the public post page (with one embed retry; document posts bring their PDF or page images), Apify harvestapi, Apify supreme_coder, then words only: Jina Reader |

## The free sites, and what was tested

Tested live on 2026-10-24 from a cloud machine with the research's public TikTok test post:

- **TikWM** (TikTok): answered with the caption, author, date and counts, and its video downloaded with sound.
- **Tikmate** (TikTok): answered with the caption, author and counts; its download host sits on port 8443, which the
  cloud machine could not reach, so the download is unverified until the first run at home.
- **cobalt's public instance**: refuses without a key (`error.api.auth.jwt.missing`), so the watcher uses a cobalt
  run on the home computer (`scripts/cobalt/README.md`) or a hosted one with `COBALT_API_KEY`.
- **Instagram download sites** (snapinsta, saveig, sssinstagram, fastdl, igram, saveinsta): none answered a plain
  request; they hide the download step behind tokens their pages compute in the browser. Not built. cobalt covers the
  same ground on the home computer.

Every free site sees the link it is sent and has no contract or published terms. Krish's message above is the go-ahead
for them; Apify, the only paid step, stays under the $5 cap.
