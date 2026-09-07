# /localtranscribe — Offline Audio/Video Analysis for Claude Code

<div align="center">

<img src="https://img.shields.io/badge/python-3.10%2B-blue.svg?style=flat-square" alt="Python 3.10+">
<a href="https://github.com/jimsimoy/claude-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/Claude_Code-skill-5A67D8.svg?style=flat-square" alt="Claude Code Skill">
<img src="https://img.shields.io/badge/transcription-100%25_local-brightgreen.svg?style=flat-square" alt="100% local transcription">

**Transcribe audio or video fully offline, then produce a structured critical analysis — outline, key terms, claims and their support, reasoning issues, notable quotes.**

by [Jan Ivan Simoy](https://github.com/jimsimoy)

</div>

---

## What is this?

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) that takes a `.vtt` file, an audio/video file, or a URL, transcribes it with a **local** [whisper.cpp](https://github.com/ggerganov/whisper.cpp) build (no audio ever leaves the machine), and has Claude write a structured markdown analysis — not just a transcript, but a critical read of it: the argument's structure, what claims are backed by what kind of evidence, where the reasoning is weak, and what's left ambiguous.

```
/localtranscribe https://youtu.be/example
```

## Why local transcription

Unlike the [`stream-watch`](../stream-watch) skill — which falls back to a cloud Whisper API when captions are missing — `localtranscribe` never sends audio anywhere. Transcription runs entirely on-device via whisper.cpp. That makes it the right choice when the content itself is sensitive, or when you'd rather not depend on (or pay for) a cloud API at all.

## The analysis format

The bundled [`ANALYSIS_PROMPT.md`](ANALYSIS_PROMPT.md) template produces:

- **Overview** — a short thesis-and-scope summary
- **Outline** — a timestamped walk through the content's structure
- **Key Terms** — concepts introduced, defined from context, first-mention timestamped
- **Claims and Support** — each notable claim categorized (anecdotal, appeal to authority, reasoned argument, cited source)
- **Reasoning Issues** — fallacies that materially weaken an argument, not rhetorical nitpicks
- **Notable Quotes** — a handful of verbatim lines worth surfacing
- **Open Questions** — what's left ambiguous or underdeveloped

## Requirements

| Requirement | Notes |
|---|---|
| Python | 3.10+ |
| `ffmpeg` | Audio format conversion |
| [whisper.cpp](https://github.com/ggerganov/whisper.cpp) | Built locally, with a downloaded model — see its own quick-start guide |
| `yt-dlp` | Only needed for URL input |

## Installation

```bash
cp -r skills/localtranscribe ~/.claude/skills/localtranscribe
```

Set `WHISPER_CPP_ROOT` if your whisper.cpp build isn't at the default `~/github.com/ggerganov/whisper.cpp`, and `WHISPER_CPP_MODEL` if you're using a model other than `ggml-medium.en.bin`.

## Usage

```
/localtranscribe <file-or-url>
```

Accepts a `.vtt` file directly (skips transcription), an audio/video file, or a URL. Output is a `.md` file written next to the transcript, same basename.

## Security

- **No network call for transcription, ever** — whisper.cpp runs entirely on this machine.
- The only network access at all is `yt-dlp` fetching public video/audio for URL input — no login, no account access.
- Nothing is sent to any third-party analysis or AI service beyond Claude itself.

Full breakdown in [SKILL.md's Security & Permissions section](SKILL.md#security--permissions).

## Project Structure

```
SKILL.md              # Skill definition Claude reads
ANALYSIS_PROMPT.md    # The critical-analysis template
scripts/
  transcribe.sh        # Local file/URL → .txt + .vtt via whisper.cpp
```

---

[← Back to all skills](../../README.md)
