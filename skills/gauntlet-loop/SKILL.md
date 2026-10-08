---
name: gauntlet-loop
description: Autonomous build loop where work only gets accepted after passing an independent critic review, cycling through a backlog on its own and surfacing to the human only when the queue is empty or a real decision is needed. Use when asked to "run the gauntlet", "set up a gauntlet loop", "gauntlet this project", invokes /gauntlet-loop, or wants an autonomous build/dev loop that self-manages a backlog with a builder plus independent critic gate and fix cycles — an unattended build-and-verify cycle over a task list, not a single one-off coding task.
---

# Gauntlet Loop

Run a backlog to completion without checking in after every task. Each item
must clear an independent review before it counts as done. Interrupting the
human is reserved for the queue finishing or a call that genuinely isn't
yours to make — not for routine progress.

## Setup — confirm these before the first task

Ask for anything not already given; don't guess at ambiguous ones.

1. **Where the work happens.** Repo/workspace path.
2. **Where the backlog lives.** A tracker, a doc, a checklist — pick one
   source of truth. If a second list exists, treat it as a mirror to sync
   into the primary, never the reverse.
3. **Who builds.** You directly, a sub-agent you spawn, or an external tool.
   If the work spans specialties (e.g. backend and frontend), route each
   task to the right one rather than splitting a single task across two.
4. **What's off-limits this pass.** Check for previously parked or deferred
   items before assuming something is fair game.
5. **What's owner-only.** Purchases, credentials, legal, anything subjective
   that only the human can decide. Leave these visibly queued — never
   attempt them.
6. **Commit and push authority.** Whether the loop may commit on PASS, and
   whether it may push. If not stated, assume neither: leave accepted work
   uncommitted and list it in the handover.

## Per-task cycle

1. **Pick** the highest-priority unblocked item.
2. **Mark it in-progress** in the backlog immediately — status has to be
   live, not just accurate in hindsight.
3. **Brief the builder.** Give a cold-start spec: what to build, which
   existing conventions to reuse, what's explicitly out of scope. The
   builder reports back but does not merge or mark anything done itself —
   that's the reviewer's call, after the gate below.
4. **Review independently.** Come at the output fresh — no inherited trust
   from the builder's own summary. Work from the actual diff/output against
   the original spec and relevant docs, and re-run verification yourself
   rather than accepting reported results:
   - Does it actually work, not just "it runs"?
   - Does the real behavior match the spec, including cases where scope was
     quietly narrowed or a shortcut was taken?
   - Did it touch anything beyond what the task asked for?
   - Verdict is binary: **PASS**, or **FAIL** with specific, actionable
     findings — never a vague "needs polish."

   Prefer handing this review to a fresh-context reviewer sub-agent. A
   ready-made definition ships with this skill in `gauntlet-reviewer.md`
   (see **Reviewer agent** below). Give it the original spec, the diff or
   changed-file list, and the verification commands — not the builder's
   narrative.
5. **On FAIL, loop back to the builder** with the concrete findings. Two fix
   attempts max. Still failing after that is a real blocker, not more
   iteration — escalate per below.
6. **On PASS, sanity-check the reviewer too** — a quick direct look of your
   own, not a full re-review, before trusting the verdict.
7. **Land it.** Only a PASS that survived step 6 is landed, and the builder
   never lands work itself. If commits are authorized (setup item 6), commit at
   a clean boundary: split cleanly separable changes, keep genuinely
   entangled ones together, follow existing conventions rather than
   hand-splitting a diff after the fact, and never push beyond what was
   authorized. If commits are not authorized, leave the change in place and
   record it for the handover.
8. **Close it out** with a short handover: what shipped, how it was
   verified, and any judgment call made along the way.
9. **Move to the next item immediately.** No prompt needed to continue —
   staying in motion across the whole backlog is the point of the loop.

## Reviewer agent

`gauntlet-reviewer.md`, in this skill's folder, is the critic's full prompt
as a sub-agent definition: read-only, no build history, returns
`VERDICT: PASS` or `VERDICT: FAIL` with findings a builder can act on.

- **Installed as an agent** (`cp gauntlet-reviewer.md ~/.claude/agents/`, or
  `.claude/agents/` in a project): spawn it by name, `gauntlet-reviewer`.
- **Not installed:** read `gauntlet-reviewer.md`, drop the frontmatter, and
  pass the body as the prompt of a general-purpose sub-agent, together with
  the spec, the diff, and the verification commands. Do not review your own
  builder's work inline if a sub-agent can be spawned.
- A `FAIL` goes back to the builder as-is; the two-fix-attempt cap in step 5
  applies.

## When to stop and surface to the human

Only these:

- **Backlog cleared** — report what shipped and what's left, calling out
  owner-only items by name rather than leaving them implied.
- **A real decision** — an ambiguous product/design call, a missing
  credential or asset, a tradeoff that isn't yours to make.
- **Stuck past the two-fix-cycle limit.**
- **Something looks unsafe** — data-loss risk, an irreversible step, or
  anything that shouldn't ship in its current state.
- **An external failure with no self-fix** — a rate limit or outage. State
  plainly what's blocked and roughly when it should clear; don't hammer it
  in a retry loop. Once it clears, resume on your own — only re-surface if
  the same failure recurs enough to look like a pattern rather than a blip.

When something does need the human, present it as clearly labeled options —
what each choice is, the rough effort, the tradeoff — not buried in a status
paragraph.

## Guardrails

- Never trust a self-report — yours or the builder's — without an
  independent check at the point it matters.
- No silent scope creep. A task drifting toward a rewrite, or pulling in
  something already deferred, is an escalation, not a call to make solo.
- No destructive or irreversible action anywhere in the loop.
- An explicit pause stops the loop immediately and holds until told to
  resume — it never restarts itself.
- If the project already has its own recorded specifics for this loop
  (locked scope, backlog source, builder routing), load and follow that
  first — this file is the general mechanism; project-level notes hold the
  particulars.
