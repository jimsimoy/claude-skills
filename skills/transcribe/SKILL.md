---
name: transcribe
description: Transcribe and critically analyze audio or video content, fully offline. Accepts a .vtt file, an audio/video file, or a URL (YouTube or any yt-dlp-supported site). Produces a structured markdown analysis — outline, key terms, claims and their support, reasoning issues, notable quotes, open questions.
argument-hint: <file-or-url>
---

# Transcribe

Transcribe (if needed) and critically analyze content. All transcription
runs locally via whisper.cpp — no audio or video is ever uploaded to a
third-party API.

`$ARGUMENTS` is the input.

## 1. Resolve the input

- **Already a `.vtt` file** → use it directly, skip to Analysis.
- **Audio/video file, or a URL** → run:
  ```bash
  "${SKILL_DIR}/scripts/transcribe.sh" "<file-or-url>" "<output-dir>"
  ```
  `SKILL_DIR` is the directory containing this SKILL.md. The script prints
  the resulting `.vtt` path on success.
- The script requires a local [whisper.cpp](https://github.com/ggerganov/whisper.cpp)
  build (`WHISPER_CPP_ROOT`, default `~/github.com/ggerganov/whisper.cpp`)
  and a downloaded model (`WHISPER_CPP_MODEL`, default
  `ggml-medium.en.bin` under that same tree). If either is missing the
  script says exactly what's missing and points at whisper.cpp's own setup
  instructions — walk the user through that rather than trying to work
  around it.

## 2. Analysis

Once you have the `.vtt`:

1. Turn the filename into a natural title (`My_Cool_Video.vtt` →
   "My Cool Video").
2. Read `${SKILL_DIR}/ANALYSIS_PROMPT.md`, substitute `[TITLE]` with the
   inferred title and `[SOURCE]` with the original `$ARGUMENTS` value.
3. Read the **entire** `.vtt` with the Read tool (chunk through offset/limit
   if it's large) before writing anything.
4. If the target `.md` output (same basename as the `.vtt`) already exists,
   ask whether to overwrite or use a different name.
5. Write the analysis to the `.md` file per the template's structure.

## Notes

- Cite timestamps in `[HH:MM:SS]` / `[HH:MM:SS--HH:MM:SS]` form, as the
  template specifies.
- Keep the analysis neutral and descriptive — it characterizes the
  argument, it doesn't take a side on it.
- Output lands next to the `.vtt`, same directory.

## Security & Permissions

**What this does:**
- Runs `yt-dlp` locally for URL input (public data only — no login, no
  session/cookie access)
- Runs `ffmpeg` locally to convert audio to MP3
- Runs `whisper-cli` (whisper.cpp) locally for transcription
- Writes `.mp3`/`.vtt`/`.txt` files next to the source (or to the given
  output directory) and the final `.md` analysis alongside the `.vtt`

**What this does NOT do:**
- Never sends audio, video, or the transcript to any network API —
  transcription is 100% local
- Does not touch credentials, browser sessions, or any platform account
- Does not read or write anything outside the paths named above
