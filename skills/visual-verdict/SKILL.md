---
name: visual-verdict
description: Scores a UI implementation against a reference (screenshot, Figma export, or a previous version) across weighted visual dimensions and returns a PASS/REVISE/FAIL verdict with concrete, file-and-line fixes. Use after implementing UI from a design reference, after CSS changes, or before marking any UI task complete.
---

# Visual Verdict

A quick glance says "looks close enough." A scored comparison catches the
3-5 small mismatches that glance misses and that compound into a visibly
broken experience. This skill replaces the glance with a number and a
concrete fix list.

## When to run it

- Right after a UI component or page is implemented from a design reference.
- After any CSS change that could shift layout, before calling it done.
- When cloning an existing site or page, as the acceptance gate.
- Whenever a task claims "matches the design" — verify it rather than take
  the claim at face value.

## Requirements

- A way to capture the current implementation: a browser automation MCP
  tool, or a manually-provided screenshot.
- A reference to compare against: a design export, a prior-version
  screenshot, or a second live URL (e.g. staging vs. production).
- The implementation reachable (local dev server or a deployed URL).

## Procedure

1. Capture a full-page screenshot of the current implementation.
2. Load the reference image or URL.
3. Score six dimensions, 0-100 each (see below).
4. Combine them into one weighted score.
5. Assign a verdict from the score.
6. List every mismatch found, ranked by how much it hurts, each with a
   specific fix (file + what to change).
7. If REVISE or FAIL, hand the fix list back to whoever is implementing,
   then re-screenshot and re-score after the fix. Repeat, capped at 5
   passes total — if it's still not PASS by then, stop and report what's
   blocking it rather than continuing to iterate blind.

## Dimensions and weights

| Dimension | Weight | What it covers |
|---|---|---|
| Layout | 0.25 | Element positions, spacing, alignment |
| Typography | 0.15 | Font family, size, weight, line-height, letter-spacing |
| Color | 0.15 | Backgrounds, text, borders, shadows, gradients |
| Responsiveness | 0.15 | Behavior at each breakpoint tested |
| Interaction states | 0.15 | Hover, focus, active, disabled, loading |
| Content completeness | 0.15 | Every piece of text/image/icon/label present |

Total = sum of each dimension's score × its weight.

## Scoring guide per dimension

**Layout** — 90-100 if spacing/position match closely; 75-89 for sub-4px
drift; 50-74 for 4-16px misalignment; below 50 if elements are missing or
structurally wrong (swapped columns, broken grid).

**Typography** — 90-100 if family/size/weight/line-height/letter-spacing all
match; deduct roughly 20 points per attribute that's off; below 50 if the
font family itself is wrong.

**Color** — compare computed values, not a visual impression. Convert to a
perceptual difference (Delta E) where practical:
- ΔE < 2 → imperceptible, full score
- ΔE 2-5 → barely visible, small deduction
- ΔE 5-10 → visible, moderate deduction
- ΔE > 10 → clearly wrong, major deduction (e.g. an inverted light/dark
  theme scores in the 0-39 range)

**Responsiveness** — test at minimum mobile (375px), tablet (768px), and
desktop (1440px) unless told otherwise. 90-100 if all three render
correctly; each breakpoint that breaks costs roughly 25 points.

**Interaction states** — 90-100 if hover/focus/active/disabled/loading are
all implemented and visible; missing a minor state (loading) costs little;
missing hover or focus costs more; no interactive states at all scores
below 50.

**Content completeness** — 90-100 if every text/image/icon/label from the
reference is present; a missing non-critical element costs little, a
missing critical one (primary CTA, main heading) costs more; multiple
missing items score below 50.

## Verdict thresholds

| Score | Verdict | Meaning |
|---|---|---|
| 90-100 | PASS | Ship it |
| 60-89 | REVISE | Fixable, not yet shippable |
| 0-59 | FAIL | Needs substantial rework |

## Reading computed styles instead of guessing from pixels

Typography and color checks should read the actual rendered values, not
eyeball the screenshot:

```javascript
const el = document.querySelector('.hero-title')
const style = window.getComputedStyle(el)
// style.fontFamily, style.fontSize, style.fontWeight,
// style.lineHeight, style.letterSpacing
```

## Report format

```markdown
## Visual Verdict: <component/page>

**Score: 85/100 — REVISE**  (pass 2 of 5; previous score 72)

| Dimension | Score | Weight | Weighted | Notes |
|---|---|---|---|---|
| Layout | 92 | 0.25 | 23.0 | minor mobile padding |
| Typography | 68 | 0.15 | 10.2 | H2 weight wrong |
| Color | 96 | 0.15 | 14.4 | — |
| Responsive | 80 | 0.15 | 12.0 | grid breaks at 768px |
| Interaction | 82 | 0.15 | 12.3 | CTA missing hover |
| Content | 91 | 0.15 | 13.7 | — |
| **Total** | | | **85.6** | |

### Fixes, ranked by impact

1. **[Typography, high]** `src/components/Hero.tsx` — H2 renders at
   `font-weight: 400`, reference is `700`. Add `font-bold` to the `<h2>`.
2. **[Responsive, medium]** `src/components/CardGrid.tsx` — grid collapses
   at 768px, reference collapses at 1024px. Change `md:grid-cols-3` to
   `lg:grid-cols-3`.
3. **[Interaction, medium]** `src/components/Hero.tsx` — CTA has no hover
   state; reference darkens to `bg-blue-700`. Add
   `hover:bg-blue-700 transition-colors`.

### Next step
Apply 1-3 above, re-run visual-verdict. Estimated result: ~94 (PASS).
```

## If it never reaches PASS

After 5 passes without a PASS verdict, stop iterating and report instead:

```
Visual QA did not reach PASS after 5 passes.
Best score: <score>
Persistent blocker: <the specific issue that keeps recurring>
Needs: <designer clarification, or a different implementation approach>
```

## Common causes worth checking first

- Bold not applying because the weight class isn't in the build's safelist.
- A breakpoint using `px` where the design system expects `rem` (or vice
  versa).
- Hover state dropped during copy-paste from the design tool.
- An icon component imported at the wrong size.
- A CSS custom property referenced but never defined in the active theme.
- Spacing utility off by one step (e.g. `px-3` where the design calls for
  `px-4`).
- Z-index burying an interactive element under a sibling.
- `line-clamp` missing, so text overflows instead of truncating on mobile.

---

Trust the score over the impression. Something that looks "basically right"
at a glance is exactly the case this exists to catch.
