# nofluff — Answer-First Output for Claude Code

<div align="center">

<img src="https://img.shields.io/badge/type-instructions_only-lightgrey.svg?style=flat-square" alt="Instructions only, no bundled code">
<a href="https://github.com/jimsimoy/claude-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/Claude_Code-skill-5A67D8.svg?style=flat-square" alt="Claude Code Skill">

**Strips the padding from agent output and leaves the substance — answer first, ceremony gone, every technical fact and certainty qualifier intact.**

by [Jan Ivan Simoy](https://github.com/jimsimoy)

</div>

---

## What is this?

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) — pure instructions, no bundled scripts — that turns down the verbosity without turning down the information.

Agent replies are padded at both ends: a sentence announcing what is about to happen, a sentence recapping what just did. Neither carries information, you pay for both, and in a terminal they push the real answer off the top of the screen.

```
/nofluff
/nofluff tight
stop nofluff
```

## Three levels

| Level | Keeps | Use when |
|---|---|---|
| `lite` | Full sentences and grammar; only ceremony removed | Output a mixed audience may read, or that's being pasted elsewhere |
| `default` | Short complete sentences, fragments where unambiguous | Ordinary technical back-and-forth |
| `tight` | Minimum words carrying the full fact set | Throwaway lookups, quick confirmations, long mechanical lists |

Same answer, three densities — note that the path, the setting name and both numbers survive all three:

```
lite      The connection pool is exhausted. `maxPoolSize` in
          `config/database.yml` is set to 5, which is too low for this
          traffic. Raise it to 20.

default   Connection pool exhausted. `maxPoolSize` in
          `config/database.yml` is 5, too low for this traffic. Raise to 20.

tight     Pool exhausted. `maxPoolSize` in `config/database.yml`: 5 → 20.
```

## What makes it different

**Certainty is treated as payload.** Most "be concise" instructions protect code and numbers but let qualifiers go. Collapsing *"the pool appears exhausted, unconfirmed"* into *"pool exhausted"* isn't a terser sentence — it's a stronger claim invented by the compression, and the user then acts on a verified finding that was never verified. Words like *unverified*, *assumed*, *only*, *not* and *except* are facts, and they survive at every level.

**It switches itself off where terseness costs more than it saves.** Security and incident work, irreversible or outward-facing actions, order-dependent instructions, questions put to the user, and — importantly — anything persisted outside the conversation: commits, PRs, code comments, docs, tickets, notes files, client documents. Those are read later by people without the conversation around them, and they can't ask a follow-up. You asked for terser *replies*, not a terser permanent record.

**It won't trigger by accident.** A bare "be brief" doesn't activate it. Turning on a persistent session-wide mode because someone wanted one short answer is a surprise, not a feature — so activation requires naming the skill.

**It's a density setting, not a dialect.** No dropped articles, no telegraphic grammar, no mode labels on replies. The output should read as a competent engineer being efficient, not as an affect. Adding words to sound terse is self-defeating.

**It reports its own state honestly.** There's no hook or state file, so the active level lives in the conversation and can genuinely be lost when context is compacted. Asked which mode is on, it says what it can determine and admits when it can't, rather than asserting a level it's guessing at.

## Provenance

The "strip the filler, keep the facts" idea is widely implemented; the best-known version is the `caveman` skill, and reviewing it is what prompted building one of these. This is an independent implementation rather than a port — written from the pattern and from our own operating rules, with no text carried across. Phrase-overlap against that skill measures zero shared seven-word sequences; what remains are stock filler phrases both of them quote as bad examples, plus shared vocabulary lists. The departures are deliberate: three levels instead of six, no hooks or state files of any kind, activation that refuses to fire on a bare "be brief", certainty qualifiers treated as payload, and a considerably wider set of situations where terseness switches itself off. Similar skills exist and will overlap in structure, because the underlying idea is a simple one.

## Installation

```bash
cp -r skills/nofluff ~/.claude/skills/nofluff
```

No dependencies. Works in any Claude Code session, and the instructions are host-agnostic enough to drop into other agents that read skill files.

## Security posture

Instructions only — no scripts, no code execution, no network calls, no file reads or writes, no state on disk, no credentials touched. It changes the wording of replies in the session where you turn it on, and nothing else.

Full rules, worked examples and the complete exemption list: [SKILL.md](SKILL.md).

---

[← Back to all skills](../../README.md)
