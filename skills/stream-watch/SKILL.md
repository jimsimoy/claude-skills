---
name: stream-watch
description: Watch a video (URL or local file). Downloads with yt-dlp, extracts representative frames with ffmpeg (scene-change or keyframe detection, with near-duplicate dropping), gets a timestamped transcript from captions or a Whisper fallback, and hands both to Claude to answer questions about the video.
argument-hint: "<video-url-or-path> [question]"
allowed-tools: Bash, Read, AskUserQuestion
---

# /stream-watch

Gives Claude a video input it doesn't otherwise have. A bundled script
fetches captions first (free), optionally downloads the video, extracts a
budget of frames as JPEGs, and prints their paths plus the transcript. Read
each frame path to see the images, then combine them with the transcript
to answer the question.

## Resolve `SKILL_DIR`

Every command below runs a script under `SKILL_DIR/scripts/`. Set
`SKILL_DIR` to the directory containing *this* SKILL.md (your harness told
you that path when it read this file):

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
test -f "$SKILL_DIR/scripts/stream_watch.py" || echo "ERROR: wrong SKILL_DIR" >&2
```

## Step 0 — setup preflight (first `/stream-watch` call in a session)

```bash
python3 "${SKILL_DIR}/scripts/setup.py" --json
```

- `can_proceed: true` → proceed to Step 1 silently.
- `first_run: true` → run the installer, which installs missing binaries
  where it can (Homebrew on macOS; prints the command elsewhere) and
  scaffolds `~/.config/stream-watch/.env`:
  ```bash
  python3 "${SKILL_DIR}/scripts/setup.py"
  ```
  A missing Whisper key is fine — encourage adding one via `AskUserQuestion`
  (Groq preferred: cheaper and faster; OpenAI as the fallback), but don't
  block on it. Without a key, `/stream-watch` still works — videos without
  captions just come back frames-only.
- On later calls in the same session, skip Step 0 entirely — nothing about
  the environment changes turn to turn.

## When to use

- A video URL (YouTube or most other yt-dlp-supported sites) or a local
  video file, with or without a specific question about it.
- `/stream-watch <url-or-path> [question]`

## Depth tiers

Set via `STREAMWATCH_DEPTH` in `~/.config/stream-watch/.env`, or `--depth`
per call. Default: `standard`.

| Depth | Frames | Engine |
|---|---|---|
| `captions-only` | none | skips video download when captions exist |
| `quick` | up to 50 | keyframes only — near-instant |
| `standard` (default) | up to 100 | scene-change detection |
| `deep` | uncapped | scene-change detection, every shot kept |

All tiers cap at 2 fps. A video with too few distinct shots for scene/
keyframe detection to be meaningful (a static talking-head recording, for
instance) falls back to uniform time-based sampling automatically.

## Running it

```bash
python3 "${SKILL_DIR}/scripts/stream_watch.py" "<source>"
```

Flags:
- `--depth captions-only|quick|standard|deep`
- `--start T` / `--end T` — focus on a range (`SS`, `MM:SS`, `HH:MM:SS`).
  Denser sampling than a full-video scan, since narrowing to a range means
  the user wants detail there.
- `--max-frames N` — override the tier's cap
- `--resolution W` — frame width in px (default 512; raise only if reading
  on-screen text matters)
- `--fps F` — override auto-fps (still clamped to 2 max)
- `--out-dir DIR` — default is an auto-created temp directory
- `--whisper groq|openai` — force a backend (default: prefer Groq)
- `--no-whisper` — never fall back to Whisper; frames-only if no captions
- `--no-dedup` — keep near-duplicate frames (only useful when judging
  subtle frame-to-frame motion)

### Focusing on a section

When the question is about a specific moment ("what happens around 2:30?",
"the last 10 seconds"), pass `--start`/`--end` rather than scanning the
whole video — this is almost always more useful than a sparse full scan,
especially past ~10 minutes:

```bash
python3 "${SKILL_DIR}/scripts/stream_watch.py" "$URL" --start 2:15 --end 2:45
```

## After it runs

1. **Read every frame path in one message** (parallel Read calls) so you
   see them together, in chronological order with their `t=MM:SS` stamps.
2. **Answer using both streams** — frames for what's visible, transcript
   for what's said. If the user asked something specific, answer it and
   cite timestamps. If not, summarize structure and key moments.
3. Even at `captions-only` depth with no frames, produce a synthesized
   summary — don't paste the raw transcript into chat. Offer the full
   transcript only if asked.
4. **Clean up** — the report prints the working directory at the end.
   Delete it (`rm -rf <dir>`) unless the user is likely to ask a follow-up
   about the same video.
5. **Don't re-run for a follow-up** in the same session — you already have
   the frames and transcript in context.

## Recommended limits

- Best accuracy under ~10 minutes; frame coverage per minute shrinks past
  that at a fixed cap.
- For a long video with a specific question, `--start`/`--end` beats a
  sparse full scan every time.

## Failure modes

- **Download fails** — yt-dlp's error lands on stderr. Region-locked or
  login-required sources: tell the user plainly, don't retry.
- **No transcript** — captions missing and Whisper unavailable/failed.
  Proceed frames-only and say so.
- **Whisper request fails** — printed to stderr (usually a bad key or rate
  limit). Audio over the 25MB API cap is chunked automatically; if some
  chunks fail the transcript is partial and the report notes it. Try the
  other backend with `--whisper`.

## Security & Permissions

**What this does:**
- Runs `yt-dlp` locally — public data only, no login or session access
- Runs `ffmpeg`/`ffprobe` locally for frames and, when Whisper is needed, a
  mono 16kHz audio extract
- Sends that audio extract (never the video) to `api.groq.com` or
  `api.openai.com`, only when `GROQ_API_KEY`/`OPENAI_API_KEY` is set and
  captions are unavailable
- Writes downloaded media, frames, and audio to a working directory under
  the system temp dir (or `--out-dir`)
- Reads/creates `~/.config/stream-watch/.env` (mode `0600`) for API keys
  and a setup-complete marker

**What this does NOT do:**
- Never uploads the video itself anywhere — only an audio extract, and only
  when Whisper is actually needed
- Never touches a platform account — no login, no cookies, no posting
- Never sends a key to the provider it doesn't belong to
- Never logs or persists an API key outside that one config file
- Never persists anything beyond the working directory and the config file

**Bundled scripts:** `scripts/stream_watch.py` (entry point),
`scripts/download.py` (yt-dlp wrapper), `scripts/frames.py` (ffmpeg frame
extraction + dedup), `scripts/captions.py` (caption parsing),
`scripts/whisper.py` (Groq/OpenAI clients), `scripts/setup.py` (preflight +
installer), `scripts/config.py` (shared config helpers).

Review the scripts before first use to verify this description.
