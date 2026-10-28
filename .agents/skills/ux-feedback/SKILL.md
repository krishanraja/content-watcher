---
name: ux-feedback
description: Turn a recording of Krish narrating his way through a product (a screen recording with his voice) into timestamped stills, each with what he said and what was on screen, plus the friction, confusion, expectation and delight he voiced. Use when he hands over a feedback recording, says "UX feedback", "feedback video" or "I recorded myself using it". Local only; it never touches inspirationhouse, the engine or Drive. Not for reels or inspiration (those go through the watcher).
---

# UX feedback recording

One recording in, one folder out: `timeline.md` (a line a still, then everything said), `timeline.json`, and
`stills/`. It runs on this machine with `content-watch timeline`; nothing is filed, reported or uploaded, and the
recording itself is never moved, changed or deleted.

## Run it

1. Ask only for what is missing: where the recording is, and what product or flow it covers (for the summary).
2. Run it with the profile given explicitly:

   ```sh
   content-watch timeline "<recording>" --profile ux --out "<folder beside the recording>/feedback timelines"
   ```

   It makes a new folder `<name>_<hash>` and never writes over an earlier one. `content-watch doctor` names anything
   missing on the machine (the `timeline` line); without faster-whisper there are no words, without tesseract no
   screen text, and the timeline says so under "Not measured".
3. Check the output before reporting: `timeline.json` exists, every `entries[].file` exists in `stills/`, and the
   counts in the command's output match `counts` in the JSON. If a check fails, say which and stop.

## Report back

- Clickable absolute paths to `timeline.md` and the `stills` folder.
- The UX signals in time order (the `UX signals:` line), each with its time, the sentence and the still to open.
- The moments where the screen changed with no words, and the longest stretch of words with no screen change:
  places he may have been stuck.
- Say plainly that tags are rules over his words and the screen text, not a model's judgement of the screen. Open
  the stills you cite before describing what they show; never describe a still you have not looked at.

## From Control Center

Krish can also add a recording in Control Center's feedback box. A home computer then does the same run on its own
and the engine emails him the Claude Code prompt with links to the feedback file and the stills in Drive
(`docs/WATCH_API.md`, "Feedback videos"). This skill is for a recording he hands over in a session instead.

## Keep it separate

Do not run `content-watch read` or `watch` on a feedback recording, and do not put it in the Production Inspo or
Content Inspo folders: both send readings to inspirationhouse.
