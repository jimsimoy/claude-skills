# localsave — Local-Only Conversation Saving for Claude Code

<div align="center">

<img src="https://img.shields.io/badge/type-instructions_+_script-lightgrey.svg?style=flat-square" alt="Instructions plus one shell script">
<a href="https://github.com/jimsimoy/claude-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/Claude_Code-skill-5A67D8.svg?style=flat-square" alt="Claude Code Skill">

**Keeps a record of a Claude Code session on your own disk, and refuses to do it from a web session or into anything that gets pushed.**

by [Jan Ivan Simoy](https://github.com/jimsimoy)

</div>

---

## What is this?

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) for people who want their
agent conversations kept locally and nowhere else. Say *"save this conversation"* and it copies the
session's raw transcript and writes a short, secrets-free summary into a local folder:

```
~/claude-conversations/2026-10-15_payment-retry-fix_a997819a/
├── transcript.jsonl   # the session's own transcript, chmod 600
└── summary.md         # goal, what changed, decisions, open items
```

It also sets a standing rule for the agent: don't create, continue or message Claude Code web
sessions (claude.ai/code) to keep or move a conversation, unless you ask for that specific action.

## How the gate works

The bundled `scripts/localsave.sh` checks before it writes anything, and exits `3` with a reason if
any check fails:

| Check | Why |
|---|---|
| `CLAUDE_CODE_REMOTE` is not `true` | Claude Code on the web sets it; a cloud session must not save |
| Exactly one local transcript exists for `CLAUDE_CODE_SESSION_ID` | Proves the session runs on this machine |
| Destination is not inside a git work tree, or is gitignored there | A later `git add .` must never pick up a transcript |

`localsave.sh --check` runs the checks and writes nothing.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `LOCALSAVE_DIR` | `~/claude-conversations` | Where saved conversations go |
| `CLAUDE_CONFIG_DIR` | `~/.claude` | Where Claude Code keeps transcripts |

Set `LOCALSAVE_DIR` for every session through the `env` block of `~/.claude/settings.json`.

## Optional hard enforcement

The skill's rules are instructions. To make the "no web sessions" half binding, add deny rules and
switch off Remote Control and session upload in `~/.claude/settings.json`. The exact snippet is in
[SKILL.md](SKILL.md#optional-hard-enforcement). Note that denying `RemoteTrigger` also disables `/schedule`.

## Provenance

Written from scratch for a standing rule on our own machines: conversations are saved locally, and
agents stay out of Claude Code web sessions. No third-party skill was reviewed or used as a source.
Other tools export or archive Claude Code transcripts and will overlap with the copy step; the
local-session gate, the refuse-inside-git check and the no-web-sessions rule are this skill's reason
to exist.

## Installation

```bash
cp -r skills/localsave ~/.claude/skills/localsave
chmod +x ~/.claude/skills/localsave/scripts/localsave.sh
```

Needs only `bash`, `git` and coreutils. Tested on macOS (bash 3.2).

## Security posture

- One shell script. No network calls, no credentials read, nothing executed from the transcript.
- Reads only this session's transcript under `$CLAUDE_CONFIG_DIR/projects/`; writes only under
  `$LOCALSAVE_DIR`, with `umask 077` and `chmod 600` on the copy.
- The transcript copy is verbatim, so it can contain whatever the session saw, credentials included.
  That is why the destination must stay out of git. The summary is written with secrets redacted.

Full rules and the summary format: [SKILL.md](SKILL.md).

---

[← Back to all skills](../../README.md)
