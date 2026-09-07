# /stream-watch — Video Understanding for Claude Code

<div align="center">

<img src="https://img.shields.io/badge/python-3.10%2B-blue.svg?style=flat-square" alt="Python 3.10+">
<a href="https://github.com/jimsimoy/claude-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/Claude_Code-skill-5A67D8.svg?style=flat-square" alt="Claude Code Skill">

**Gives Claude a video input it doesn't otherwise have — download, frame extraction, and transcript, all in one command.**

by [Jan Ivan Simoy](https://github.com/jimsimoy)

</div>

---

## What is this?

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) that lets Claude answer questions about a video — a YouTube link, another yt-dlp-supported site, or a local file. It downloads the video (or just its captions, when that's enough), extracts a budget of representative frames as JPEGs, gets a timestamped transcript from native captions or a Whisper API fallback, and hands both to Claude to read and reason about.

Point it at a video and ask a question, or just ask what happens in it:

```
/stream-watch https://youtu.be/jNQXAC9IVRw what does the presenter say about elephants?
```

## How it picks frames

Three engines, chosen by the depth tier:

| Depth | Frames | Engine | Speed |
|---|---|---|---|
| `captions-only` | none | — | fastest — skips video download entirely when captions exist |
| `quick` | up to 50 | keyframes only (`ffmpeg -skip_frame nokey`) | near-instant |
| `standard` (default) | up to 100 | scene-change detection | full decode, thorough |
| `deep` | uncapped | scene-change detection, every shot kept | full decode, maximum coverage |

Every tier caps at 2 fps. A video too static for scene/keyframe detection to find enough distinct shots (a talking-head recording, a screen share) falls back to uniform time-based sampling automatically. Near-duplicate frames — a held slide, a paused video — get dropped by a perceptual frame-delta pass so the frame budget goes to content that actually changes.

## Requirements

| Requirement | Notes |
|---|---|
| Python | 3.10+ |
| `ffmpeg` / `ffprobe` | Frame extraction and audio processing |
| `yt-dlp` | Video download and caption fetching |
| Groq or OpenAI API key | Optional — only needed when a video has no native captions |

## Installation

```bash
cp -r skills/stream-watch ~/.claude/skills/stream-watch
```

First run walks you through a one-time setup (installs `ffmpeg`/`yt-dlp` via Homebrew on macOS if missing, scaffolds `~/.config/stream-watch/.env` for an optional Whisper key). Nothing to configure manually beforehand.

## Usage

```
/stream-watch <video-url-or-path> [question]
```

**Focus on a specific moment** instead of scanning a whole long video:

```
/stream-watch https://youtu.be/example --start 2:15 --end 2:45
```

**Skip frames entirely, transcript only** (fastest, works from captions alone):

```
/stream-watch https://youtu.be/example --depth captions-only
```

Full flag reference is in [SKILL.md](SKILL.md).

## Security

- Only ever contacts `api.groq.com` or `api.openai.com`, and only when a Whisper fallback is actually needed — only the extracted audio goes out, never the video itself.
- No platform account access of any kind — `yt-dlp` only ever requests public data.
- API keys live in `~/.config/stream-watch/.env` (chmod `0600`), never logged or echoed.

Full breakdown in [SKILL.md's Security & Permissions section](SKILL.md#security--permissions).

## Project Structure

```
scripts/
  stream_watch.py  # Entry point — orchestrates download, frames, transcript
  download.py      # yt-dlp wrapper: video download + caption fetch
  frames.py        # ffmpeg frame extraction (scene/keyframe/uniform) + dedup
  captions.py      # WebVTT caption parsing
  whisper.py       # Groq/OpenAI Whisper fallback (chunked upload for long audio)
  setup.py         # Preflight check + first-run installer
  config.py        # Shared config helpers
```

---

[← Back to all skills](../../README.md)
