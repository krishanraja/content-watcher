# 2026-11-03: doctor proves cobalt can fetch

Status:
- Asked: whether cobalt, gallery-dl or ArchiveBox (from a getintoai carousel) could strengthen the engine. cobalt and gallery-dl were already in every relevant chain; ArchiveBox was turned down (no Windows without Docker or WSL, archive.org submission on by default, its media extractors are the yt-dlp and gallery-dl already here). Read: each project's README and API or config docs, not their source.
- Built on `ccr-d0ec5529-rjzf5z`: `free_sites.cobalt_probe` and the `doctor` cobalt row that uses it (version, one public TikTok, first 64 KB read), and `localProcessing: disabled` on every cobalt request.
- Not proven live: the cloud container has no cobalt running, so the real row has not been seen.

- Follow-ups done the same day: gallery-dl 1.32.18 or later (TikTok 403 fix confirmed in its changelog and code), and cobalt's yt-session-generator in the compose file for YouTube.

Next step: after this branch is merged, run the installer again on each home computer (it upgrades gallery-dl and adds the generator), then `content-watch doctor`: the `cobalt` and `gallery-dl` lines. A miss names its class.

North Star check: does not move the compression share. Krish was told before it was built and chose it.
