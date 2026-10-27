# cobalt on the home computer (optional)

cobalt is the open-source downloader behind many of the free "paste a link, press download" sites. Running it on
the home computer gives the watcher one more free way to get a post, with no third party seeing the link. It is
optional: every chain works without it, it just has one more fallback with it. The Windows installer (`scripts/install-content-watch.ps1`) does steps 2 and 3 itself when Docker is installed.

1. Install Docker Desktop (`winget install Docker.DockerDesktop`) and start it once.
2. In this folder: `docker compose up -d`
3. Tell the watcher: `content-watch config --cobalt-url http://localhost:9000`
4. Check: `content-watch doctor` shows `ok  cobalt`.

The watcher asks cobalt for 720p at most. To stop it: `docker compose down` in this folder.
