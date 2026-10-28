# The reading format

Status: Current. Format `content-watcher.read/1`, engine revision `cw-2026.10.29` (`content_watcher/__init__.py`).

A reading is one piece of media turned into text on Krish's machine, with no model watching it. Each one is written as
two files and stored as one `content_reads` row, keyed by the sha256 of the file's exact bytes as filed:

- `read.json`: everything measured (this document).
- `read.md`: the same as plain text, at most 40,000 characters, written for a model or a session to read instead of
  frames. The most useful parts come first (caption, the whole post, the hook, pace, shots), and the full transcript
  comes last, so a reader that keeps only the first 30,000 characters loses the least.

Readers: inspirationhouse tags cards from `read_md` and these top-level fields of `read`: `post`, `heard`,
`words_text`. Those three are a promise: they are always present.

## Top level (every reading)

| Field | Type | Meaning |
|---|---|---|
| `format` | string | `content-watcher.read/1` |
| `engine_rev` | string | The engine revision that measured it. A newer revision may read the same sha256 again. |
| `sha256` | string | Lowercase hex sha256 of the file's bytes as filed (for a text post, of the Markdown file as filed). |
| `shape` | string | `video`, `carousel`, `image`, `text`, `document`. Every file of a carousel says `carousel`. |
| `file` | object | `name`, `bytes`, `mime`. |
| `post` | object or null | `{ author, posted_at, caption, url, platform }` when the file came from a post; null for a hand-dropped file (a filed text post fills it from its own header). |
| `heard` | string | `words`, `silent` or `failed`. |
| `heard_class` | string or null | Why, when not `words`: `no_audio_stream`, `digital_silence`, `no_speech`, `empty_audio`, `empty_captions`, `not_applicable` (an image or text), `no_whisper`, `decode_error`, `whisper_error`. |
| `words_text` | string | The plain transcript ("" when nothing was heard). |
| `position` | object | `{ index, of }`: where this file sits in its post (fetched posts only). |
| `unmeasured` | list | Measures this machine could not take, by name (`words`, `screen_text`, `faces`, `camera_moves`). Missing measures are named, never silently zero. |

## A video

| Field | Meaning |
|---|---|
| `video` | `duration_s`, `width`, `height`, `fps`, `aspect` (`9:16`, `4:5`, `1:1`, `16:9`, ...), `has_audio`. |
| `words` | `source` (`captions` when the platform supplied subtitles, else `whisper`), `language`, `segments` (`start`, `end`, `text`), `word_count`. |
| `shots` | `count`, `cuts` (seconds), `cuts_per_min`, `length_s` (`median`, `mean`, `min`, `max`), `list`: one entry per shot with `start`, `end`, and when measured `face_share`, `face_height`, `move`, `screen_text`. Cuts come from ffmpeg's scene score at 0.3. |
| `camera_moves` | Per shot that moves: `kind` (`push_in`, `pull_out`, `pan_left`, `pan_right`, `tilt_up`, `tilt_down`), `zoom` (total scale across the shot), `shift_x_share`. Measured by matching consecutive frames (4 a second) for scale and shift. |
| `screen_text` | Words on screen: `t`, `shot`, `text`, `text_area_share`, from tesseract on the middle of each shot and every 3 seconds in long shots. Repeats are dropped. |
| `faces` | `available`, `share_on_face`, `face_height_median` (share of frame height), `eye_line_median` (share from the top), `framing` (`close`, `medium`, `wide`), from OpenCV's frontal face detector about twice a second. |
| `hook` | The first 3 seconds: `words`, `screen_text`, `cuts`, `face_on_screen`, `move`. |
| `pace` | `words_per_min`, `speech_share`, `pauses_over_0_6s`, `longest_pause_s`, `first_word_s`, `sound_without_words_share` (a rough sign of music or b-roll under no speech). |
| `audio` | `integrated_lufs`, `range_lu`, `true_peak_dbfs` (EBU R128), `silences`, `longest_silence_s`. |
| `frames` | At most two chosen frames kept beside the reading on the machine: `hook` (at 1 second) and `most_text` (the frame with the most screen text). `role`, `t`, `file`. They are not uploaded. |

## A carousel slide or an image

`slide`: `index`, `width`, `height`, `aspect`, `text` (OCR), `text_area_share`, `line_count`, `word_count`, `face`,
`layout` (any of `one_number`, `list`, `text_heavy`, `no_text`, `face`, `image_led`), `colours` (up to five, `hex` and
`share`). A video slide inside a carousel is read as a video.

For a carousel, **the first file's reading covers the whole post**: it adds `post_slides` (every slide in order with
its `sha256`, `kind`, `text`, `layout` and `words_text`) and its `read_md` lists all slides in order, because the card
is tagged from the first file. A TikTok photo post's sound is transcribed into the first file's `heard` and
`words_text`, with `post_audio: true`.

## A text post

`text`: `body`, `word_count`, `paragraphs`, `first_line`, `list_lines`, `hashtags`. A LinkedIn post is filed as a
Markdown file whose header lines (`Author:`, `Posted:`, `Link:`, `Platform:`) fill `post`.

## The timeline (every video, from engine revision `cw-2026.10.29`)

Krish, 2026-10-28: turning a video into easily understood structured data is a core benefit of Content Watcher for
inspirationhouse, and every reel the watcher reads should get it. So every video reading carries `timeline`: stills
taken at the moments that matter, each with what was said and shown then, and tags. It is additive (the promised
fields are unchanged) and it can never fail a reading: if it errors, or runs past its budget (240 s, or
`CONTENT_WATCH_TIMELINE_BUDGET`), the reading goes out as before with `timeline` in `unmeasured`. In `read.md` it is
the `## Timeline` section, one line a still, before the full transcript. The still images stay on the machine in
`stills/` beside `read.json`; only this text and JSON reach the engine. Code: `content_watcher/timeline/`.

| Field | Meaning |
|---|---|
| `format` | `content-watcher.timeline/1` |
| `profile`, `profile_reason` | `social` for a reading. `ux` (a narrated screen recording) is for `content-watch timeline` on its own. |
| `words` | `source` (`whisper`, `captions`, or `captions+whisper` when both exist: the captions' text with the transcription's word timings), `language`, `captions`, `whisper`, and `agreement` (word overlap of the two, 0 to 1). |
| `counts` | `stills`, `images` (pictures taken; a still over an unchanged screen reuses the picture before it), `by_trigger`. |
| `lexicon` | The version of the UX signal rules (`ux-1`). |
| `post_tags` | `platform:`, `author:` and each `hashtag:` of the post. |
| `ux_signals` | Each `friction`, `confusion`, `expectation` or `delight` term heard, once: `t`, `index` (the still), `term`, `said` (its sentence). |
| `entries` | One per still, in time order (below). |

A still (`entries[]`): `index`, `t`, `triggers` (why it was taken: `start`, `cut`, `screen_change`, `caption_change`,
`speech`), `shot`, `file` (`stills/...jpg`), `still_sha256`, `dhash` (a 64-bit picture hash), `same_as` (when the
picture is an earlier still's), `said` (the words within 2 s either side), `words` (those words with their times),
`sentence` (the sentence being spoken), `screen_text` (OCR of the picture), `colours`, `face` (`on`, `framing`),
`layout`, `change_score` (the share of the picture that changed), `motion` (`scroll`, or the shot's camera move),
`ux_signals`, and `tags`.

Moments: the opening; just after each cut; each time the picture changes and settles; each time the words on screen
change (OCR about twice a second, skipping repeated frames, a word misread by a letter counting as the same); and
each spoken sentence. Moments closer than 1.5 s merge and keep every trigger; at most 40 in a reading.

Tags, all rules over what was measured: `trigger:*`, `hook` (first 3 s), `layout:*`, `face:*`, `framing:*`,
`change:large|small` (15% of the picture), `motion:*`, `speech:yes|none`, `ux_signal:*`.

## What is not measured, honestly

- Music versus speech is not classified; `sound_without_words_share` is the hint.
- Layout labels are simple rules over OCR and face detection, not a picture model. A chart is not recognised.
- Words on screen come from sampled frames, so a caption shown for less than the gap between samples can be missed.
- Timeline tags are rules, not a picture model: a still is not described in words beyond its OCR, colours, faces
  and layout labels. UX signals are a small word list (`content_watcher/timeline/tags.py`), so sarcasm or a
  problem described without its words is missed.
- OCR reads dark text on light backgrounds best: light text on a coloured button, or a caption over a busy moving
  picture, can be missed.
- A scroll is named only when it moves less than a quarter of the screen between samples; a long jump reads as a
  screen change.
