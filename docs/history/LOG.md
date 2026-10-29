# History log

Newest first. Entries are written by the docs steward (see the steward link in NOW.md) and by humans doing the same job by hand. Nothing in this file describes current behaviour; NOW.md and the state doc do.

## 2026-10-29

- moved NOW.md "What changed recently" (20 entries, 2026-10-23 to 2026-10-28) verbatim to `docs/history/NOW-changes.md`, and capped NOW.md at 12,000 bytes (`tests/test_layout.py`). W2.12 in Krish's saved Wave 2 brief.

## 2026-10-27

- reconciled at `622001d`: NOW.md, AGENTS.md and the README still named the repository `video-compression`, called the first Content Watcher build "not merged" on branch `claude/content-watcher-build` (it landed as #3, and #4, #6, #7 and #8 followed), and listed the YouTube and LinkedIn chains as provisional or still to build (#4 built them). Corrected against `git log` and `content_watcher/`. `docs/BRIEF.md` and `docs/FETCH_METHODS.md` gained status notes saying which of their recommendations the code no longer follows; `docs/STATE.md` was scoped to the compression engine. No file was moved.
- created `docs/history/LOG.md`: NOW.md named it as its `history_log` but the repository had none.
