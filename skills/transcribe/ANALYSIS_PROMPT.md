# Transcript Analysis Template

Analyze the transcript titled: [TITLE]

Base the analysis strictly on what's in the transcript — don't bring in
outside knowledge of the speaker, channel, or their usual positions. Define
any domain-specific term using only the context the speaker gives.

Before writing anything: read the full transcript with the Read tool
(chunk through it with offset/limit if it's long — don't start summarizing
until you've seen all of it).

Timestamp format: `[HH:MM:SS]` for a single point, `[HH:MM:SS--HH:MM:SS]`
(double hyphen) for a range. In headings, write timestamps without
backticks; everywhere else, wrap them in backticks. Keep tone neutral —
describe, don't editorialize.

## Overview
3-5 sentences: what this is and what it covers.

## Source
- **Source:** [SOURCE]

(One line only. A URL renders as a markdown link; a local path renders as
inline code. No extra commentary.)

## Outline
A timestamped walk through the structure — one subheading per major
section or topic shift, each with its time range:

### Section title [HH:MM:SS--HH:MM:SS]
What happens in this section, in enough detail that someone who hasn't
watched it understands the content, not just the topic label.

## Key Terms
Notable terms, frameworks, or concepts the speaker introduces, defined from
context, each with the timestamp of first mention:
- **Term** `[HH:MM:SS]`: definition

## Claims and Support
Notable claims, categorized by what backs them. A claim's evidence may span
multiple lines — cite the full range.
- **Anecdotal** `[HH:MM:SS--HH:MM:SS]`: personal experience offered as
  support
- **Appeal to authority** `[HH:MM:SS--HH:MM:SS]`: cites someone else's view
  without a traceable source
- **Reasoned argument** `[HH:MM:SS--HH:MM:SS]`: logic without external data
- **Cited source** `[HH:MM:SS--HH:MM:SS]`: a specific study, article, or
  verifiable reference

## Reasoning Issues
Fallacies or weak reasoning that materially undermine an argument — skip
rhetorical flourish that isn't actually a fallacy. If none, say so
explicitly rather than leaving the section blank.

For each: `[HH:MM:SS--HH:MM:SS]` covering premise through conclusion, what
the issue is, and why it weakens the point. Watch for: ad hominem, straw
man, false dichotomy, appeal to emotion, whataboutism, slippery slope,
hasty generalization, false authority — but don't force a fit if none
apply.

## Notable Quotes
2-5 short, verbatim quotes worth surfacing on their own, each with its
timestamp and one line of context for why it's notable.

## Open Questions
Points left ambiguous, underdeveloped, or worth follow-up, with the
timestamp where the gap shows up. Say plainly when your own reading of
something is uncertain rather than presenting a guess as settled.
