# realchrome — Drive a Real Chrome from Claude Code

<div align="center">

<img src="https://img.shields.io/badge/type-instructions_+_script-lightgrey.svg?style=flat-square" alt="Instructions plus one shell script">
<a href="https://github.com/jimsimoy/claude-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/Claude_Code-skill-5A67D8.svg?style=flat-square" alt="Claude Code Skill">

**Lets Claude attach to a Chrome window you opened and logged into yourself, so sites with bot checks see an ordinary browser.**

by [Jan Ivan Simoy](https://github.com/jimsimoy)

</div>

---

## What is this?

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) for browser work on sites that
challenge automation. Browsers launched by Playwright, headless Chrome or an automation daemon carry
signals that Cloudflare Turnstile, reCAPTCHA and similar scoring pick up, and the challenge can keep
failing even when a person clicks it. realchrome flips the roles: **you** start Chrome and log in by
hand, and Claude attaches afterwards over the Chrome DevTools Protocol.

```bash
scripts/chrome-debug.sh start "https://example.com/login"   # you log in in this window
scripts/chrome-debug.sh tabs                                # what's open
scripts/chrome-debug.sh stop                                # closes only this instance
```

## Two ways to attach

| Mode | What Claude reaches | When |
|---|---|---|
| **A. Dedicated debug profile** (default) | A separate Chrome instance with its own profile folder, DevTools on `127.0.0.1:9222` | Most tasks. Logins persist in that profile, so you log in once per site. |
| **B. Your everyday Chrome** | Your real tabs, after you enable `chrome://inspect/#remote-debugging` | Only when you ask for it. Claude treats every existing tab as yours: read, never navigate or close. |

`REALCHROME_PROFILE` and `REALCHROME_PORT` pick the profile folder and port, so several logins can run
side by side on different ports.

## Ground rules it follows

- **You log in; Claude never solves, clicks or bypasses a CAPTCHA** or "verify you are human" check.
- **Live sites are read-only** unless you ask for a specific change. Page loads are counted, spaced
  out, and reported.
- A failed login stops the task instead of retrying, so security plugins don't lock the account.
- Passwords, when a form must be filled, are read from a file you name inside the command and never
  printed.

## Requirements

- macOS with Google Chrome (the launcher uses `open -na`).
- The [`dev-browser`](https://github.com/SawyerHood/dev-browser) CLI, used **only in `--connect` mode**
  as the CDP client, and a Node version it supports first on `PATH`.
- `curl` and `python3` for the launcher's `status` and `tabs` commands.

## Provenance

Built after `dev-browser`'s own launch-a-browser workflow kept failing Turnstile on sites we work on.
realchrome is an independent skill: its own instructions and its own launcher script. It reuses
`dev-browser` (MIT, by Sawyer Hood) unmodified as the client that speaks CDP, and does not bundle or
copy its code. Phrase overlap against the `dev-browser` skill text measures zero shared five-, six- or
seven-word sequences. Other "attach to an existing Chrome over CDP" setups exist and will overlap in
approach, because Chrome's remote-debugging flags are the standard way to do it.

## Installation

```bash
cp -r skills/realchrome ~/.claude/skills/realchrome
chmod +x ~/.claude/skills/realchrome/scripts/chrome-debug.sh
npm install -g dev-browser
```

## Security posture

- DevTools is bound to `127.0.0.1` only; nothing on the network can attach.
- Anything that reaches the debug port acts as the logged-in user in that profile. Stop the instance
  when you're done and don't leave admin sessions in profiles you no longer use.
- `stop` kills processes whose command line matches `--user-data-dir=<profile>`, so give profiles
  names that aren't prefixes of each other.
- The script makes no network calls beyond the local DevTools endpoint and stores no credentials;
  logins live in the Chrome profile like any other.

Full rules: [SKILL.md](SKILL.md).

---

[← Back to all skills](../../README.md)
