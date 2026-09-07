# Visual Verdict — Screenshot QA for Claude Code

<div align="center">

<img src="https://img.shields.io/badge/type-instructions_only-lightgrey.svg?style=flat-square" alt="Instructions only, no bundled code">
<a href="https://github.com/jimsimoy/claude-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/Claude_Code-skill-5A67D8.svg?style=flat-square" alt="Claude Code Skill">

**Scores a UI implementation against a design reference across six weighted dimensions and returns a PASS/REVISE/FAIL verdict with concrete, file-and-line fixes.**

by [Jan Ivan Simoy](https://github.com/jimsimoy)

</div>

---

## What is this?

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) — pure instructions, no bundled scripts — that replaces "looks close enough" with a scored, structured verdict. A quick glance at an implementation misses the 3-5 small mismatches that compound into a visibly broken experience; this skill catches them by scoring computed styles and layout against a reference, not just eyeballing a screenshot.

```
visual-verdict this component against the Figma export
```

## The six dimensions

| Dimension | Weight | Checks |
|---|---|---|
| Layout | 0.25 | Element positions, spacing, alignment |
| Typography | 0.15 | Font family, size, weight, line-height, letter-spacing |
| Color | 0.15 | Backgrounds, text, borders, shadows — compared via perceptual difference (ΔE), not eyeballed |
| Responsiveness | 0.15 | Behavior at mobile/tablet/desktop breakpoints |
| Interaction states | 0.15 | Hover, focus, active, disabled, loading |
| Content completeness | 0.15 | Every text/image/icon/label present |

Combined into one weighted score, 0-100. **90-100 → PASS**, **60-89 → REVISE**, **0-59 → FAIL**.

## The iteration loop

```
implement from reference
  → visual-verdict scores it
  → REVISE: concrete fix list (file + exact change)
  → apply fixes
  → visual-verdict rescores
  → repeat until PASS (capped at 5 passes)
```

If it's still not PASS after 5 passes, the skill stops and reports what's actually blocking it — a designer clarification needed, or a fundamentally wrong approach — rather than continuing to iterate blind.

## Requirements

- A way to capture the current implementation — a browser automation MCP tool (e.g. `browser-use`), or a manually-provided screenshot.
- A reference to compare against — a design export, a prior-version screenshot, or a second live URL.
- The implementation reachable (local dev server or deployed URL).

## Installation

```bash
cp -r skills/visual-verdict ~/.claude/skills/visual-verdict
```

No dependencies beyond having a screenshot-capable tool available in the session.

## When to run it

After implementing UI from a design reference, after any CSS change before calling it done, when cloning an existing site as the acceptance gate, or whenever a task claims "matches the design" — verify it rather than take the claim at face value.

Full scoring rubric, report format, and common-bug checklist: [SKILL.md](SKILL.md).

---

[← Back to all skills](../../README.md)
