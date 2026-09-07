# Claude Skills

<div align="center">

<img src="https://img.shields.io/badge/python-3.10%2B-blue.svg?style=flat-square" alt="Python 3.10+">
<a href="https://github.com/jimsimoy/claude-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>

**A collection of original [Claude Code](https://claude.com/claude-code) skills — each independently designed and implemented, security-reviewed from the ground up.**

by [Jan Ivan Simoy](https://github.com/jimsimoy)

</div>

---

## What is this?

Skills extend Claude Code with a packaged workflow — instructions plus, where needed, bundled scripts — invoked with `/name` or automatically when the description matches the task. This repo collects the ones built here, each an original implementation rather than an installed third party's code: same category of capability, own design and own code, reviewed end to end before being trusted to run locally.

## Skills

| Skill | Type | What it does |
|---|---|---|
| [**watch**](skills/watch) | Instructions + scripts | Watch a video (URL or local file) — download, extract representative frames, get a timestamped transcript from captions or Whisper, answer questions about it |
| [**transcribe**](skills/transcribe) | Instructions + script | Transcribe audio/video fully offline via local whisper.cpp, then produce a structured critical analysis (outline, claims, reasoning issues, quotes) |
| [**gauntlet-loop**](skills/gauntlet-loop) | Instructions only | Autonomous build loop: work a backlog unattended, gate every item behind an independent critic review, only surface for a real decision |
| [**visual-verdict**](skills/visual-verdict) | Instructions only | Score a UI implementation against a design reference across weighted dimensions, return PASS/REVISE/FAIL with concrete fixes |

## Installing a skill

Copy the skill's directory into `~/.claude/skills/` (personal, all projects) or `.claude/skills/` inside a project (project-scoped):

```bash
cp -r skills/watch ~/.claude/skills/watch
```

`watch` and `transcribe` bundle scripts with their own setup steps — see each skill's own `SKILL.md` for requirements (ffmpeg/yt-dlp for `watch`; a local whisper.cpp build for `transcribe`).

## Security posture

Every skill here that runs code documents exactly what it does and doesn't do in its own `SKILL.md`, under **Security & Permissions**:

- `watch` only ever contacts `api.groq.com` / `api.openai.com`, and only an extracted audio clip — never the video — when Whisper is actually needed.
- `transcribe` makes no network calls for transcription at all — everything runs locally via whisper.cpp. Only URL input touches the network (yt-dlp fetching public video/audio, same as any browser would).
- Neither touches credentials, platform accounts, browser sessions, or anything outside its own working directory and config file.

No skill here shells out to unreviewed remote code, executes anything dynamically constructed from external input, or exfiltrates data beyond what's explicitly documented.

## License

[MIT](./LICENSE) — free to use, modify, and distribute.
