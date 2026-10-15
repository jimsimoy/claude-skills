---
name: localsave
description: Save the current conversation to local disk, only from a local Claude Code session (CLI, IDE extension, desktop app) and never in, to or via a Claude Code web/cloud session. Use when the user says "save conversation", "save this session", "save this chat", "export this conversation", "keep a record of this session" or "/localsave". Copies the raw transcript and writes a secrets-free summary into a local folder ($LOCALSAVE_DIR, default ~/claude-conversations). In a web session it refuses and saves nothing.
---

# localsave: save conversations locally, never via the web

Two rules, both binding while this skill is installed:

1. **Conversations are saved only from a local session**, to local disk.
2. **Don't save to, or connect to, Claude Code web sessions** (claude.ai/code) as a way of keeping a
   conversation: see "Never" below.

## Steps

1. **Gate and copy the transcript.**
   ```bash
   ~/.claude/skills/localsave/scripts/localsave.sh "<3-6 word topic>"
   ```
   (Use the skill's actual install path if it was installed per-project.)
   - Prints the folder it saved into: `<LOCALSAVE_DIR>/<YYYY-MM-DD>_<topic>_<session-id-8>/`.
   - **Exit 3 (`REFUSED: ...`)**: a web/cloud session, no local transcript, or an unsafe destination.
     Stop. Do not fall back to saving anywhere else (no other file, no hosted page or doc, no commit,
     no push). Tell the user the reason it printed.
   - `localsave.sh --check` tests the gate without writing anything.
2. **Write `summary.md`** in that folder, from the conversation itself:
   - Title, date, session id, working directory.
   - **Goal**: what the user asked for.
   - **What was done**: files changed (absolute paths), commands that mattered, commits (SHA).
   - **Decisions and user instructions**, quoted where the wording matters.
   - **Open items / next step**.
   - **No secrets.** Never copy tokens, keys, passwords, `.env` values or auth headers into the summary,
     even if they appear in the transcript. Write `<redacted>`.
3. **Reply** with the folder path and one line on what is in it.

Re-running on the same day for the same session overwrites `transcript.jsonl` with the newer snapshot.
Update `summary.md` in place.

## Never

- Save a conversation to a remote: a hosted page, a cloud doc, a chat app, a git remote. The raw
  transcript can contain credentials and private data, and the summary is still conversation content.
- Save into a git work tree unless the destination is gitignored there. The script refuses this,
  because a later `git add .` would commit the transcript.
- "Save" by creating, continuing, teleporting into or messaging a Claude Code web session:
  `claude --remote`, `--teleport`, Remote Control, cloud routines (`RemoteTrigger`, `/schedule`),
  cloud sub-agents, or opening claude.ai/code in a browser. Do these only when the user explicitly
  asks for that specific action in the current session.

## Optional hard enforcement

Instructions can be ignored; settings can't. The user can add this to `~/.claude/settings.json`
(merge it with what's already there). Offer it, don't apply it unasked:

```json
{
  "permissions": {
    "deny": [
      "RemoteTrigger",
      "Bash(claude --remote*)",
      "Bash(claude --teleport*)",
      "Bash(claude remote-control*)",
      "Bash(claude --rc*)"
    ]
  },
  "disableRemoteControl": true,
  "remoteControlAtStartup": false,
  "autoUploadSessions": false,
  "env": { "LOCALSAVE_DIR": "/absolute/path/for/saved/conversations" }
}
```

Denying `RemoteTrigger` also disables `/schedule`. `autoUploadSessions: false` stops local sessions
being mirrored to claude.ai. Settings take effect in sessions started afterwards.
