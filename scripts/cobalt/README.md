# cobalt on the home computer (optional)

cobalt is the open-source downloader behind many of the free "paste a link, press download" sites. Running it on
the home computer gives the watcher one more free way to get a post, with no third party seeing the link. It is
optional: every chain works without it, it just has one more fallback with it. The Windows installer (`scripts/install-content-watch.ps1`) does steps 2 and 3 itself when Docker is installed.

1. Install Docker Desktop (`winget install Docker.DockerDesktop`) and start it once.
2. In this folder: `docker compose up -d`
3. Tell the watcher: `content-watch config --cobalt-url http://localhost:9000`
4. Check: `content-watch doctor` shows `ok  cobalt` with its version. That line now means cobalt fetched a real public
   TikTok and handed back the file (a running Docker alone does not earn it); a miss names why (`blocked (cobalt_rate)` and so on).

For YouTube, cobalt needs a session (a poToken and visitor_data). The compose file also runs cobalt's own
`yt-session-generator` beside it and points `YOUTUBE_SESSION_SERVER` at it; it only works from the address YouTube
sees, which is why it runs here. yt-dlp with the bgutil token helper stays ahead of cobalt in YouTube's chain. Running
the installer again (or `docker compose up -d` here) adds the generator to a machine that already has cobalt.

The watcher asks cobalt for 720p at most. To stop it: `docker compose down` in this folder.
