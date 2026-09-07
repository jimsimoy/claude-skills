# Gauntlet Loop — Autonomous Build Loop for Claude Code

<div align="center">

<img src="https://img.shields.io/badge/type-instructions_only-lightgrey.svg?style=flat-square" alt="Instructions only, no bundled code">
<a href="https://github.com/jimsimoy/claude-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/Claude_Code-skill-5A67D8.svg?style=flat-square" alt="Claude Code Skill">

**Work a backlog to completion, unattended — every item gated behind an independent critic review, human interruptions reserved for real decisions.**

by [Jan Ivan Simoy](https://github.com/jimsimoy)

</div>

---

## What is this?

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) — pure instructions, no bundled scripts — that turns Claude into an autonomous build orchestrator for a task backlog. Instead of one task then a check-in, then another task then a check-in, the loop runs continuously: pick the next item, brief a builder, review the result independently before accepting it, fix on failure (capped), land it, move on — surfacing to the human only when the queue is empty or something genuinely needs their call.

```
run the gauntlet loop on this repo's backlog
```

## Why the independent critic gate matters

The core mechanism this skill enforces: **the entity that builds something never gets to also be the entity that decides it's done.** After a builder reports finished work, review comes from a fresh standpoint — working only from the actual diff and the original spec, re-running verification rather than trusting a self-report. This is the check most likely to catch a builder that quietly narrowed scope, took a shortcut, or reports success without it being true.

## The cycle, per task

1. Select the highest-priority unblocked item, mark it in-progress immediately.
2. Brief the builder with a cold-start spec — full context, explicit out-of-scope guardrails.
3. Independent review: correctness (re-verify, don't trust), spec match (not just "it runs"), scope creep. Binary verdict — PASS or FAIL with specific findings.
4. On FAIL, loop back to the builder. Capped at 2 fix attempts before it's escalated as a real blocker.
5. On PASS, a quick direct sanity-check before trusting the reviewer's verdict.
6. Land the change at a clean boundary, close the task with a handover note, move immediately to the next item.

## What actually interrupts the human

Only: the backlog is fully cleared, a genuine decision that isn't the loop's to make, stuck past the 2-fix-cycle cap, something that looks unsafe, or an external failure (rate limit, outage) with no self-fix. Routine progress — a task passing review, a commit landing — is never a reason to check in.

## Installation

```bash
cp -r skills/gauntlet-loop ~/.claude/skills/gauntlet-loop
```

No dependencies, no setup — it's a behavioral definition Claude follows, not code that runs.

## Before starting a run

The skill asks for (or expects you to already have decided): where the work happens, where the backlog lives (pick one source of truth), who builds (you directly, a sub-agent, an external tool), what's explicitly out of scope this pass, and what's owner-only (credentials, purchases, subjective calls) and should stay queued rather than attempted.

Full mechanism, guardrails, and escalation format: [SKILL.md](SKILL.md).

---

[← Back to all skills](../../README.md)
