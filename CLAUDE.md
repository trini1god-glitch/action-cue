# ActionCue

A Streamlit prototype demonstrating the uncertainty-to-action binding framework.

## Build specification

The complete build target is in `SPEC.md` at the repo root. Read it before
any change. Reference sections by anchor (e.g., "§9", "§11") rather than
restating them.

## Stable from Weeks 1, 2 & 3 — modify only when an audit identifies a fix

Through end of Week 3, all source files are in their working contract.
Week 4 is polish, not redesign. Files may be edited only when an audit
or a live-demo issue identifies a specific inconsistency, and only after
I confirm the fix.

Week 1: `models.py`, `rules.py`, `engine.py`, `cases/*`, `tests/test_engine.py`
Week 2: `viz/*` (renderers, styles, JS), `export_figures.py`, `figures/*`
Week 3: `app.py`, `ui/*`

If you want to refactor or restructure anything in this list, stop and
explain — do not edit. "I noticed this could be cleaner" is not a Week 4
authorization.

## Active phase

**Week 4: polish, README, demo recording.**

The verification gate from §11 is: "Demo runs end-to-end without
explanation." If a viewer would need narration to understand what they're
seeing — what fired, what won, why the force changed — the polish work
isn't done yet.

In scope this phase:
- Force-level color token consistency across every renderer (§9)
- Visual polish: alignment, spacing, typography, safety banner finish
- Any rendering inconsistencies surfaced by clicking through all 7 cases
  in both modes
- `README.md` — project documentation
- Demo recording (capture itself happens outside Claude Code; see the
  "Verification" section)

Out of scope:
- New rules, new cases, new renderers, new panels
- Structural changes to the cascade SVG, the compositors, or the
  Streamlit layout
- New dependencies
- Spec changes (if a polish pass surfaces a real spec gap, raise it and
  we'll discuss; do not edit SPEC.md unilaterally)

Verification gate:
1. `pytest tests/ -v` still clean.
2. `python export_figures.py` regenerates all six SVGs cleanly after any
   renderer change.
3. `streamlit run app.py` walks all 7 cases in both modes without
   visible errors or layout glitches.
4. `README.md` is complete enough that someone cloning the repo can
   install, run, and understand the contribution without asking me.
5. A demo recording exists that walks through Case C in ActionCue mode,
   switches to three-way comparison, and visits at least one
   safety-modifier case (E or DR) — without me narrating.

## Checkpoint structure for this phase

Four passes, in order. Wait for me to confirm before moving from one to
the next.

**4a — color token consistency audit.** Read every renderer in `viz/`
and every CSS file. For each use of a force-level color, verify it
matches the §9 token table exactly (hex codes, foreground/background
roles). Produce a written audit: each file, each occurrence, match or
drift. Do not change anything yet — I'll review the audit and decide
which drifts get fixed.

**4b — visual polish pass.** With the audit in hand and the live demo
running, work through fixes one at a time. Likely areas:
- Force-token drift identified in 4a
- Safety banner finish (typography, vermillion accent strip, spacing)
- Alignment between bands, force strip, and output box
- Three-way comparison column alignment
- Any case-specific layout glitches (Case A has no firings, Case E
  has the safety modifier; these stress different code paths)

After each fix, regenerate figures if a `viz/` renderer changed
(`python export_figures.py`) and verify the live demo still renders
correctly. Commit at each meaningful fix; "polish" PRs that conflate
twenty changes are hard to roll back.

**4c — README.** Write `README.md` covering at minimum: what ActionCue
demonstrates, how to install and run, the structure of the repo
(spec → models → engine → renderers → UI), the seven demo cases and
what each is meant to show, and how the paper figures are produced.
Keep it factual, not promotional. Audience: a reviewer or collaborator
opening the repo for the first time.

**4d — demo recording.** Plan the script first (which cases, which
mode transitions, which affordances to demonstrate), then record.
Recording itself is outside Claude Code; see "Verification."

## How to work with me

The posture shifts slightly for Week 4. The default is now:

1. **Audit first, fix second.** When I open an audit pass (4a, the
   color tokens), produce a written report — file by file, occurrence
   by occurrence — and stop. Do not "helpfully" fix what you find. I
   want to see the full picture before deciding what to change.

2. **For fixes: review, don't rewrite.** When I share polish code I
   wrote, point out what's wrong, missing, or non-idiomatic. Describe
   what to change and where — not the corrected version.

3. **For the README: I write, you edit.** When I share a README draft,
   suggest changes in prose ("paragraph 3 should mention X", "the
   install section is missing the Python version") rather than
   producing a rewritten version. I am writing this in my voice.

4. **Resist redesign.** If you find code in Weeks 1–3 that you would
   have written differently, that is not a Week 4 finding. Week 4
   surfaces inconsistencies with the spec or with the other files in
   the repo, not aesthetic preferences. If you're not sure whether
   something is a real inconsistency or a preference, ask before
   raising it.

5. **Ask before creating or modifying files**, except when I've said
   "audit X" (read-only) or "fix the issue we just identified" (write
   permitted on that file). Reading files is always fine.

6. **Briefly explain idioms when they come up**, same as before. By
   Week 4 this is mostly relevant for CSS specificity quirks and
   Streamlit rerun behavior surfacing in polish work.

## Conventions

- All conventions from Weeks 1–3 still hold. The polish pass must not
  break:
  - `viz/` renderers return strings and do not touch Streamlit
  - All four panel renderers share `(*, width, height, css, interactive)`
  - Compositors pass `css=False` to sub-renderers
  - Rule logic, `signal_for`, and `compose_cue` remain pure
  - JS is vanilla, scoped, no dependencies
- After any change to a `viz/` renderer or CSS file, regenerate figures
  (`python export_figures.py`) and verify they still match the locked
  design.
- After any change to a `ui/` file, restart Streamlit (Ctrl+C, rerun)
  and re-walk all 7 cases — auto-reload sometimes misses state changes.
- Force-level vocabulary: `advisory`, `strong`, `mandatory`, `blocking`.
- No new dependencies. `streamlit` and `pytest` are it.
- File layout matches §2 of SPEC.md exactly.

## Verification

- `pytest tests/ -v` clean after every change.
- `python export_figures.py` regenerates all six SVGs cleanly after
  every `viz/` change. Diff the regenerated figures against the prior
  versions when you're not sure a change was intentional.
- `streamlit run app.py` walks all 7 cases in both modes cleanly after
  every `ui/` or `app.py` change.
- Demo recording is on me, not Claude Code. I'll use a screen recorder
  (QuickTime on macOS, OBS on Linux, the built-in tool on Windows) and
  capture the planned walkthrough from 4d. Claude Code's role ends at
  helping me plan the script.