---
name: realchrome
description: Drive a real Google Chrome window instead of an automation-launched browser. Claude attaches over the Chrome DevTools Protocol to a Chrome the user started and logged into themselves, so sites with Cloudflare Turnstile, reCAPTCHA or bot scoring see an ordinary browser. Use for any browser task - opening a site, checking a page, reading wp-admin, taking screenshots, testing a form - and always when a site blocks or challenges a scripted browser. Replaces launching Chromium through dev-browser's own daemon.
argument-hint: "[url]"
allowed-tools: Bash, Read
---

# /realchrome

Automation-launched browsers (Playwright Chromium, headless Chrome, a
`dev-browser` daemon browser) carry signals that bot checks look for.
Cloudflare Turnstile answers them with an interactive challenge that keeps
failing even when a human clicks it. A Chrome the user launched themselves
does not carry those signals, so the fix is to let the user own the browser
and the login, and have Claude **attach** to it afterwards.

## The two ways to attach

**A. Dedicated debug profile (default).** A separate, real Chrome instance with
its own profile folder and remote debugging on `127.0.0.1:9222`. The user's
everyday Chrome and its sessions are untouched. Logins made in this profile
persist between runs, so the user logs in once per site.

```bash
scripts/chrome-debug.sh start "https://example.com/login"   # opens the window
scripts/chrome-debug.sh status                              # is it up?
scripts/chrome-debug.sh tabs                                # list open tabs
scripts/chrome-debug.sh stop                                # closes ONLY this instance
```

`REALCHROME_PROFILE` overrides the profile folder (default `~/.realchrome-profile`)
and `REALCHROME_PORT` the port (default `9222`). Several sites can share one
profile; use separate profiles only to keep logins apart.

**B. The user's everyday Chrome.** Chrome (recent versions) has built-in remote
debugging: the user opens `chrome://inspect/#remote-debugging` and turns it on.
Claude then attaches with `dev-browser --connect` (no URL, it auto-discovers).
This reaches the user's real tabs and sessions, so use it only when the user
asks for it, and treat every existing tab as theirs. If Chrome asks to approve
the connection, the **user** approves it.

Chrome refuses `--remote-debugging-port` on its default profile, so mode A always
uses a separate profile folder. Do not try to point mode A at the everyday
profile.

## Driving the attached browser

The client is the `dev-browser` CLI in **connect mode only**. It never launches
a browser here, it just speaks CDP to the one that is open.

```bash
dev-browser --connect http://127.0.0.1:9222 --timeout 120 <<'EOF'
const page = await browser.getPage("claude");          // Claude's own named tab
await page.goto("https://example.com/", {waitUntil: "load", timeout: 60000});
console.log(await page.title());
await saveScreenshot(await page.screenshot(), "example.png");
EOF
```

- `browser.getPage("<name>")` opens or reuses **Claude's own tab**. Use it for
  navigation.
- To read a tab the user already opened, find it with `browser.listPages()`
  (returns `{id, url, title}`) and pass its `id` to `getPage()`. **Read it only. Never navigate, reload or
  close a tab the user opened.**
- Screenshots land in `~/.dev-browser/tmp/`; open them with the Read tool.
- Scripts are killed after 30 s by default: pass `--timeout <seconds>`.
- If `dev-browser` fails with a `SyntaxError` or "Daemon failed to start", an
  old Node is first on PATH. Prefix a Node 18+ bin directory to PATH.

## Login and challenge rules

1. **The user logs in, by hand, in the window.** Start the window on the login
   page and wait until the user says they are in.
2. **Do not attach before the login is finished** on a site with Turnstile or
   reCAPTCHA. Attaching during the challenge can itself trip it.
3. **Never solve, click or bypass a CAPTCHA or "verify you are human" check**,
   and never automate one. That is the user's step.
4. If you must fill a login form, read the password from the file the user
   names, inside the command (e.g. `sed -n Np file`). Never print it, never put
   it in a message, never write it anywhere else.
5. A failed login is a stop signal. Report what the page said and ask, never
   retry in a loop (security plugins lock accounts after repeated failures).

## Live and production sites

- **Read-only unless the user explicitly asks for a change on that site.** No
  saving settings, no "Update" clicks, no form submissions.
- State the number of page loads before a batch, space them a few seconds
  apart, and report the real count afterwards.
- Opening an editor can write a lock (WordPress writes `_edit_lock` when a post
  editor opens). Treat editor screens on live as writes.

## Cleanup

- Close Claude's own named tabs when the task is done (`browser.closePage(name)`).
- `scripts/chrome-debug.sh stop` only when the user is finished with the
  window. It matches the profile folder, so it never closes the everyday
  Chrome.

## Security & Permissions

- The launcher binds DevTools to `127.0.0.1` only. Nothing on the network can
  attach to the browser.
- Anything attached to the debug port can act as the logged-in user in that
  profile. Keep the port local, stop the instance when done, and do not leave
  long-lived admin sessions in a profile you no longer use.
- The skill bundles one shell script, `scripts/chrome-debug.sh`. It starts,
  inspects and stops a Chrome instance; it makes no network calls of its own
  beyond querying the local DevTools endpoint.
- No credentials are stored by the skill. Logins live in the Chrome profile
  folder, exactly as in any Chrome profile.
