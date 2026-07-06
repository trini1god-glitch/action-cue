# ActionCue: Demo Build Specification (v2)

A lightweight Streamlit prototype demonstrating the uncertainty-to-action binding framework. This document is the build specification — it defines the data models, the rule engine, the three-panel UI (post-2f; was four-panel pre-2f), the Panel 3 composition trace renderer (which now also carries the cue display), the three-way comparison mode, and the seven pre-built demonstration cases. It is detailed enough to drop into a Claude Code session as a build target.

**v2 changes (prior revision).** Force-level vocabulary updated end-to-end (advisory, strong, mandatory, blocking). Constraint matrix added to the engine. Within-class plurality assertion added. `Rule` gains `signal_name` to bind each rule to its triggering Panel 2 signal; `RuleFiring` carries a `triggering_signal` field for the on-demand back-reference. Panel 3 specification fully rewritten as an annotated precedence cascade with explicit resolution step, rendered as inline SVG via `st.components.v1.html` with hover and click affordances (true overview-first-then-details-on-demand per Shneiderman 1996). All four panels are now rendered by pure SVG functions in `viz/` (`render_case_input`, `render_signals`, `render_cascade`, `render_cue_output`); two compositors (`render_four_panel`, `render_three_way`) assemble per-panel SVGs into Figures 1 and 2 in a 2×2 Z-scan grid and a three-column comparison respectively. The Streamlit panels are thin wrappers around these renderers (single source of truth: every paper figure is produced by code the demo also runs). Three-way comparison mode added (confidence-only / data-level interval bar / ActionCue compact); the middle column reuses `render_interval_bar` from `viz/case_input.py` so the data-level foil is a faithful instance of current practice. `CASE_DR` risk interval corrected so sensitivity rule actually fires. Tests expanded for constraint validation and plurality assertion. Build sequence remains four weeks; week-2 scope now covers all four per-panel renderers and both compositors.

**v3 changes (current revision, 2f refactor).** Panel 4 collapsed into Panel 3: `viz/cue_output.py` and `viz/cue_output_styles.css` deleted, and `render_cascade` now renders the cue display (action word + force-tint pill + "via {rule_class}" caption + safety banner) inline alongside the bands. The vertical force scale on the right of the cascade is replaced by a horizontal force strip below the bands (advisory · strong · mandatory · blocking, with the active level tinted and a left-to-right vermillion arrow underneath when the safety modifier lifted the force). `render_four_panel` is now a three-panel composite (case input + signals top row, full-width cascade bottom row) at 720×760; function name kept for backward compat. `render_cascade`'s `include_output_box` and `include_force_scale` parameters were removed — the cascade always renders both. Three panel renderers remain (`render_case_input`, `render_signals`, `render_cascade`). Figure 3 reveal="all" overlap bug fixed by dropping the duplicate on-demand rationale tspan and the debugging-only rule-id text.

---

## 1. What the prototype must demonstrate

The same AI risk score produces structurally different oversight cues depending on which pre-specified uncertainty rules fire and how those rules compose under a precedence-based policy with a safety modifier.

The prototype must also make the *composition reasoning* visible — not just the inputs and the output, but the step from rule firings to the selected primary cue. Visibility of the composition reasoning is what distinguishes process-transparency visualization from data-level uncertainty disclosure. The Panel 3 implementation is therefore load-bearing for the contribution claim, not merely informative.

The prototype is not a clinical model. It uses synthetic cases with hard-coded risk scores and pre-computed uncertainty signals. The contribution is the rule engine, the cue composition, and the visualization of the composition trace — not predictive accuracy.

**Stack:** Python 3.11+, Streamlit, dataclasses. Inline SVG and a small amount of vanilla JavaScript for Panel 3 interactivity (no React, no charting library, no framework). No external ML libraries.

---

## 2. Project structure

```
actioncue/
├── app.py                       # Streamlit entry point, panel layout, mode switching
├── models.py                    # Dataclasses: Case, Rule, UncertaintySignal, RuleFiring, Cue
├── rules.py                     # Rule definitions and the rule registry
├── engine.py                    # Rule firing, composition, constraint validation, safety modifier
├── cases/
│   ├── __init__.py
│   ├── healthcare.py            # Cases A–E
│   └── cross_domain.py          # Cases CR (credit), DR (disaster)
├── ui/                          # Streamlit wrappers — Week 3 scope
│   ├── __init__.py
│   ├── case_input.py            # Panel 1 wrapper (thin; calls viz/case_input)
│   ├── signals.py               # Panel 2 wrapper (thin; calls viz/signals)
│   ├── composition.py           # Panel 3 — wraps viz/cascade (which now carries the cue display)
│   ├── comparison.py            # Three-way comparison mode wrapper (thin; calls viz/composite)
│   └── rule_table.py            # The visible rule registry tab
├── viz/
│   ├── __init__.py
│   ├── _common.py               # bool_attr, wrap_text, render_style helpers shared by panel renderers
│   ├── case_input.py            # render_case_input(case), render_interval_bar(case) -> svg string
│   ├── case_input_styles.css    # Scoped CSS for .case-input and .interval-bar
│   ├── signals.py               # render_signals(case) -> svg string
│   ├── signals_styles.css       # Scoped CSS for .signals
│   ├── cascade.py               # render_cascade(case, cue, options) -> svg string (includes the cue display)
│   ├── cascade_styles.css       # Scoped CSS for .cascade (bands, force strip, output box, safety banner)
│   ├── cascade_interact.js      # Hover and click handlers
│   └── composite.py             # render_four_panel(case, cue), render_three_way(case, cue) -> svg
├── figures/                     # Exported paper-ready SVGs (figure_1.svg, figure_2.svg, figure_3.svg)
├── export_figures.py            # Offline script: calls viz/composite and viz/cascade for paper figures
├── tests/
│   └── test_engine.py           # Per-case assertions plus engine invariants
├── requirements.txt
└── README.md
```

The `viz/` package holds all SVG-emitting code. Three panel renderers (`render_case_input`, `render_signals`, `render_cascade`) return SVG fragments with known fixed `viewBox`es. `render_cascade` is the load-bearing renderer and now carries the cue display (action + force pill + via + horizontal force strip + safety banner) inline alongside the bands — there is no separate `render_cue_output`. The Streamlit panels in `ui/` are thin wrappers: each calls its `viz/` counterpart and passes the SVG to `components.v1.html`. The compositors in `viz/composite.py` assemble the per-panel SVGs into the two paper figures (three-panel composite for Figures 1 and 4; three-way comparison for Figure 2).

This is the single-source-of-truth design carried through: the same code that renders Panel 3 in the live demo also produces Figure 3 in the paper; the same code that renders Panel 1 also contributes its sub-SVG to Figure 1 and to the middle column of Figure 2 (via `render_interval_bar`, defined inside `viz/case_input.py`). Nothing in the figure pipeline runs code the demo does not also run.

---

## 3. Data models

All in `models.py` as dataclasses.

### Case

A synthetic decision context with pre-computed uncertainty signals.

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Case:
    id: str                                     # "A", "B", ..., "CR", "DR"
    domain: str                                 # "healthcare" | "credit_risk" | "disaster"
    description: str                            # human-readable case summary
    risk_score: float                           # 0.0–1.0
    risk_interval: tuple[float, float]          # (low, high)
    decision_threshold: float                   # action threshold

    # Uncertainty signals (pre-computed for the demo)
    has_missing_critical: bool = False
    missing_fields: list[str] = field(default_factory=list)
    is_outside_scope: bool = False
    scope_reason: Optional[str] = None
    has_explanation_instability: bool = False
    explanation_disagreement: Optional[str] = None

    # Decision context (drives the safety modifier)
    is_high_harm: bool = False
    is_low_reversibility: bool = False

    # Workflow context
    expected_actor: str = "clinician"           # role to whom cues are addressed
```

### UncertaintySignal

A detected condition surfaced in Panel 2.

```python
@dataclass
class UncertaintySignal:
    name: str                                   # "missing_critical_data" — stable identifier
    label: str                                  # display label
    detected: bool
    detail: Optional[str] = None                # e.g., "oxygen saturation missing"
```

### Rule

A pre-specified rule mapping an uncertainty condition to a base action and force. **`signal_name` is new in v2** and binds each rule to the Panel 2 signal that triggers it; the renderer uses this binding to draw the back-reference line from the cascade band to the corresponding signal.

```python
from typing import Callable

@dataclass
class Rule:
    id: str                                     # "validity_outside_scope"
    rule_class: str                             # "validity" | "completion" | "sensitivity" | "interpretation"
    precedence: int                             # 1=validity, 2=completion, 3=sensitivity, 4=interpretation
    description: str                            # human-readable
    base_action: str                            # one of the six action families
    base_force: str                             # one of the four force levels
    signal_name: str                            # the UncertaintySignal name this rule binds to
    trigger: Callable[[Case], bool]             # pure function: does this rule fire for this case?
    rationale: Callable[[Case], str]            # pure function: produce the rationale text
```

### RuleFiring

A rule that fired for a case, with its rendered rationale and back-reference. **`triggering_signal` is new in v2** and carries the resolved `UncertaintySignal` that the renderer uses to draw the on-demand back-reference.

```python
@dataclass
class RuleFiring:
    rule: Rule
    rendered_rationale: str
    base_action: str
    base_force: str
    triggering_signal: Optional[UncertaintySignal] = None
```

### Cue

The final composed output.

```python
@dataclass
class Cue:
    primary_action: str
    primary_force: str
    primary_rationale: str
    primary_actor: str
    supporting: list[RuleFiring] = field(default_factory=list)
    safety_modified: bool = False
    safety_reason: Optional[str] = None
    primary_firing: Optional[RuleFiring] = None         # the winning RuleFiring (None if no firings)
```

`primary_firing` is also new in v2; it lets the renderer access the winning class and triggering signal without re-deriving them from the rationale text.

---

## 4. The rule engine

### Constants

```python
ACTION_FAMILIES = ["proceed", "inspect", "complete", "reassess", "escalate", "abstain"]
FORCE_LEVELS = ["advisory", "strong", "mandatory", "blocking"]
RULE_CLASSES = ["validity", "completion", "sensitivity", "interpretation"]
PRECEDENCE = {"validity": 1, "completion": 2, "sensitivity": 3, "interpretation": 4}
```

### Constraint matrix

The framework restricts which `(action, force)` combinations are valid. The engine validates every composed `Cue` against this matrix; an invalid combination is a programming error (a rule definition or safety modifier produced a forbidden pairing).

```python
CONSTRAINT_MATRIX: dict[str, set[str]] = {
    "proceed":  {"advisory"},
    "inspect":  {"advisory", "strong", "mandatory"},
    "complete": {"strong", "mandatory", "blocking"},
    "reassess": {"strong", "mandatory", "blocking"},
    "escalate": {"mandatory", "blocking"},
    "abstain":  {"blocking"},
}
```

The matrix is permissive enough to accommodate the safety modifier raising force by one step. For example, `inspect / advisory` (interpretation rule) can be raised to `inspect / strong` under the safety modifier without leaving the matrix; `escalate / mandatory` (validity rule) can be raised to `escalate / blocking`.

### Rule definitions

In `rules.py`, define exemplar rules — one per class is enough for the demo. Each rule binds to a single `signal_name` so the on-demand layer of Panel 3 can draw the back-reference.

```python
RULES = [
    Rule(
        id="validity_outside_scope",
        rule_class="validity",
        precedence=1,
        description="Case falls outside the model's validated population or operating envelope.",
        base_action="escalate",
        base_force="mandatory",
        signal_name="out_of_scope",
        trigger=lambda c: c.is_outside_scope,
        rationale=lambda c: f"Case is outside the validated scope: {c.scope_reason}.",
    ),
    Rule(
        id="completion_missing_critical",
        rule_class="completion",
        precedence=2,
        description="A field required for the decision is missing or unreliable.",
        base_action="complete",
        base_force="mandatory",
        signal_name="missing_critical_data",
        trigger=lambda c: c.has_missing_critical,
        rationale=lambda c: f"Critical inputs missing: {', '.join(c.missing_fields)}.",
    ),
    Rule(
        id="sensitivity_threshold_crossing",
        rule_class="sensitivity",
        precedence=3,
        description="The risk interval contains the action threshold.",
        base_action="inspect",
        base_force="strong",
        signal_name="threshold_crossing",
        trigger=lambda c: c.risk_interval[0] <= c.decision_threshold <= c.risk_interval[1],
        rationale=lambda c: (
            f"Risk interval ({c.risk_interval[0]:.2f}–{c.risk_interval[1]:.2f}) "
            f"crosses the action threshold ({c.decision_threshold:.2f})."
        ),
    ),
    Rule(
        id="interpretation_explanation_instability",
        rule_class="interpretation",
        precedence=4,
        description="Explanations or models disagree across runs.",
        base_action="inspect",
        base_force="advisory",
        signal_name="explanation_instability",
        trigger=lambda c: c.has_explanation_instability,
        rationale=lambda c: f"Explanation instability detected: {c.explanation_disagreement}.",
    ),
]
```

### Signal registry

A small helper resolves a `signal_name` against a `Case` to produce the corresponding `UncertaintySignal`. This is what populates `RuleFiring.triggering_signal`.

```python
def signal_for(case: Case, signal_name: str) -> Optional[UncertaintySignal]:
    if signal_name == "missing_critical_data":
        return UncertaintySignal(
            name=signal_name,
            label="Missing critical data",
            detected=case.has_missing_critical,
            detail=", ".join(case.missing_fields) if case.missing_fields else None,
        )
    if signal_name == "out_of_scope":
        return UncertaintySignal(
            name=signal_name,
            label="Out of scope",
            detected=case.is_outside_scope,
            detail=case.scope_reason,
        )
    if signal_name == "threshold_crossing":
        return UncertaintySignal(
            name=signal_name,
            label="Interval crosses threshold",
            detected=case.risk_interval[0] <= case.decision_threshold <= case.risk_interval[1],
            detail=f"interval ({case.risk_interval[0]:.2f}–{case.risk_interval[1]:.2f}) contains threshold {case.decision_threshold:.2f}",
        )
    if signal_name == "explanation_instability":
        return UncertaintySignal(
            name=signal_name,
            label="Explanation instability",
            detected=case.has_explanation_instability,
            detail=case.explanation_disagreement,
        )
    return None
```

Panel 2 also uses `signal_for` so that signal labels and detail text are consistent across Panel 2 and the Panel 3 back-references.

### Composition algorithm

In `engine.py`. The function is pure — same inputs always produce the same `Cue`.

```python
from collections import Counter

def raise_force(force: str) -> str:
    idx = FORCE_LEVELS.index(force)
    return FORCE_LEVELS[min(idx + 1, len(FORCE_LEVELS) - 1)]

def validate_combination(action: str, force: str) -> None:
    if force not in CONSTRAINT_MATRIX[action]:
        raise ValueError(
            f"Invalid (action, force) combination: ({action}, {force}). "
            f"Allowed forces for {action!r}: {sorted(CONSTRAINT_MATRIX[action])}."
        )

def compose_cue(case: Case, rules: list[Rule]) -> Cue:
    # 1. Detect firings
    firings = [
        RuleFiring(
            rule=r,
            rendered_rationale=r.rationale(case),
            base_action=r.base_action,
            base_force=r.base_force,
            triggering_signal=signal_for(case, r.signal_name),
        )
        for r in rules if r.trigger(case)
    ]

    # 2. Within-class plurality assertion (Layer 2 invariant)
    class_counts = Counter(f.rule.rule_class for f in firings)
    duplicates = [cls for cls, count in class_counts.items() if count > 1]
    if duplicates:
        raise AssertionError(
            f"Within-class plurality detected in classes {duplicates}. "
            f"The framework defers within-class plurality to future work; "
            f"the demo cases must fire at most one rule per class."
        )

    # 3. No firings: proceed
    if not firings:
        cue = Cue(
            primary_action="proceed",
            primary_force="advisory",
            primary_rationale="No uncertainty conditions of decision concern detected.",
            primary_actor=case.expected_actor,
        )
        validate_combination(cue.primary_action, cue.primary_force)
        return cue

    # 4. Sort by precedence (lower = higher priority)
    firings.sort(key=lambda f: f.rule.precedence)

    # 5. Primary = highest-precedence firing; rest become supporting stack
    primary = firings[0]
    cue = Cue(
        primary_action=primary.base_action,
        primary_force=primary.base_force,
        primary_rationale=primary.rendered_rationale,
        primary_actor=case.expected_actor,
        supporting=firings[1:],
        primary_firing=primary,
    )

    # 6. Apply safety modifier
    if case.is_high_harm or case.is_low_reversibility:
        cue.primary_force = raise_force(cue.primary_force)
        cue.safety_modified = True
        reasons = []
        if case.is_high_harm:
            reasons.append("high harm")
        if case.is_low_reversibility:
            reasons.append("low reversibility")
        cue.safety_reason = " and ".join(reasons)

    # 7. Constraint matrix validation (Layer 2 invariant)
    validate_combination(cue.primary_action, cue.primary_force)

    return cue
```

### A note on same-precedence ties

For the seven demo cases below, no two rules of the same class fire simultaneously, and the within-class plurality assertion enforces this at engine level. If the case set is extended later, a deterministic tiebreaker (rule ID alphabetical, or a `tiebreak_priority` field) must be added before the plurality assertion is relaxed.

---

## 5. The three panels

Layout: `st.set_page_config(layout="wide")`. Use a two-row layout: top row split into two columns of equal width for Panel 1 (case input) and Panel 2 (signals); bottom row a single full-width column for Panel 3 (composition trace, which now carries the cue display itself).

> **2f redesign note (Week 2).** The earlier four-panel design had a separate Panel 4 ("Final action cue"). The 2f refactor collapsed Panel 4 into Panel 3 — the cascade renderer now produces the canonical cue display (action word + force-tint pill + "via {rule_class}" caption + safety banner) inline alongside the bands. The vertical force scale was replaced with a horizontal force strip below the bands. The result is one coherent visual unit ("what fired, how it resolved, what the cue is") rather than a cascade and a peer panel that restated each other. References to "Panel 4" / `render_cue_output` / four columns elsewhere in this spec are vestigial and should be read in that light.

A mode selector at the top:

```python
mode = st.radio(
    "View",
    options=["ActionCue (full)", "Three-way comparison"],
    horizontal=True,
)
```

Below the mode selector, a case selector (`st.selectbox` over the seven cases) drives all panels.

### Panel 1: Case input

Shows what is on the analyst's screen *before* any uncertainty reasoning happens.

- Case ID badge and domain tag
- Description (one or two sentences)
- AI risk score as a large number with a unit
- The risk interval bar (see `render_interval_bar` below), showing `risk_interval` with markers for the interval bounds and the decision threshold
- The decision threshold called out explicitly

The interval bar is factored into a shared helper so the same encoding is reused in the three-way comparison's middle column (§7). This guarantees the data-level foil in the comparison is the *same* display the analyst sees in Panel 1, not a weaker stand-in.

```python
# ui/case_input.py
import streamlit as st
import streamlit.components.v1 as components

def render_interval_bar(case):
    """Render the risk interval with bounds and the decision threshold marked.
    Used in Panel 1 and in the three-way comparison's middle (data-level) column."""
    low, high = case.risk_interval
    st.markdown(
        f"**Risk interval:** {low:.2f}–{high:.2f}  ·  "
        f"**Threshold:** {case.decision_threshold:.2f}"
    )
    # Horizontal bar over [0, 1]: shaded interval band, threshold tick, point estimate marker.
    # Implement with a small inline SVG; the encoding must show
    # (a) the interval span, (b) the threshold position, (c) the point estimate.
    components.html(_interval_bar_svg(case), height=64)
```

`_interval_bar_svg(case)` returns a compact inline-SVG bar (interval band, threshold tick, point-estimate marker) over the [0, 1] range. Keep it in `ui/case_input.py` so both call sites import the one implementation.

### Panel 2: Uncertainty signals

The detected signals for this case, derived via `signal_for(case, name)` so labels match Panel 3's back-references.

Group into rows:

- **Data:** missing critical, missing non-critical (if any)
- **Scope:** out-of-scope flag with reason
- **Threshold:** interval-crosses-threshold flag
- **Explanation:** instability flag with detail
- **Decision context:** high-harm flag, low-reversibility flag

For each signal, show a check/x-style indicator and the detail text when detected. Give each Panel 2 row a stable HTML id (`signal-row-{name}`) so the Panel 3 interaction layer can highlight the corresponding row when a cascade band is hovered or clicked.

### Panel 3: Composition trace + cue

Panel 3 is the load-bearing visualization. Its specification is detailed in §6 (Composition trace renderer). Per the 2f redesign it now carries the cue display itself, not just the cascade. Within `ui/composition.py`, the panel:

1. Calls `render_cascade(case, cue, options)` from `viz/cascade.py` with options derived from Streamlit state.
2. Wraps the returned SVG (plus the scoped CSS and the JS interaction layer) in a single HTML string.
3. Renders the wrapped HTML via `st.components.v1.html(html_string, height=560)`.

The cascade SVG itself includes, inline:

- The four bands (validity / completion / sensitivity / interpretation).
- The resolution arrow from the winning band into the output box.
- The output box, which carries the canonical cue display:
  - **Primary action** — large, bold ("COMPLETE", "ESCALATE", …).
  - **Force pill** — force-tint background (advisory pale-blue, strong mid-blue, mandatory vermillion-tint, blocking deep-vermillion).
  - **"via {rule_class}"** caption beneath the pill when a rule won.
- The horizontal force strip below the bands (four cells: advisory · strong · mandatory · blocking) with the active level tinted; when `cue.safety_modified == True`, a left-to-right vermillion arrow underneath spans from `base_force` to `primary_force`.
- The safety banner at the bottom (vermillion accent strip + "Force raised from X to Y" + "Reason: …") shown only when `cue.safety_modified == True`.

If no rules fired the cascade still renders the output box (e.g., "PROCEED" + advisory pill, no "via" line), and the strip shows advisory as the active level.

### Side: Rule registry tab

A separate Streamlit tab (or expander at the bottom) renders the entire rule registry — every rule, its class, precedence, base action, base force, bound `signal_name`, and description. This is the visible rule engine; reviewers should see that the framework is operationalized, not narrated.

---

## 6. The composition trace renderer

This is the load-bearing visualization component. It renders Panel 3 as inline SVG and provides hover-and-click interactivity via a small JavaScript layer wrapped in `st.components.v1.html`. The same renderer is used to export paper-ready SVG figures.

### Function signature

```python
# viz/cascade.py

def render_cascade(
    case: Case,
    cue: Cue,
    *,
    reveal: str = "none",            # "none" | "all"
    width: int = 480,
    height: int = 520,
    css: bool = True,                # include scoped <style> block
    interactive: bool = True,        # include <script> for hover/click
) -> str:
    """
    Return a complete SVG fragment (with optional embedded <style> and <script>)
    that renders the composition trace for `case` and `cue`.

    - reveal="none" -> compact variant (used in Figures 1 and 2)
    - reveal="all"  -> detailed variant with on-demand layer expanded (used in Figure 3)
    - interactive=True -> includes hover tooltips and click-to-expand handlers (used in live demo)
    - interactive=False -> static SVG, no script tag (used for figure export)

    Interactive=True with reveal="none" gives the live demo: bands start collapsed,
    user reveals rule-level detail per-band by clicking. This is the Shneiderman-faithful behavior.
    """
```

### SVG structure

> **2f redesign.** The cascade SVG now has `viewBox="0 0 720 500"` (was 480×520) and absorbs what was Panel 4 in the original design. The vertical force scale on the right is replaced by a horizontal force strip below the bands; the output box renders the cue display (action word + force-tint pill + "via {rule_class}" caption); a safety banner sits at the bottom when `cue.safety_modified == True`.

```
<svg viewBox="0 0 720 500" class="cascade">
  <defs>
    <!-- markers for resolution arrow head -->
  </defs>

  <g class="back-references">
    <!-- placeholder for cross-panel highlight lines from Panel 2 signal ids
         to fired bands; wired in Week 3 -->
  </g>

  <g class="cascade-bands">
    <g class="band" data-class="validity" data-fired="true|false" data-winner="true|false"
       data-rationale="..." data-signal-label="...">
      <rect class="band-bg" x="40" y="20" width="320" height="80" />
      <rect class="band-accent" x="40" y="20" width="6" height="80" />
      <text class="band-label" x="54" y="50">Validity</text>
      <text class="band-rationale" x="54" y="68">Critical inputs missing: ...</text>
      <g class="status"><circle .../></g>
      <g class="on-demand" aria-hidden="true">
        <text class="on-demand-signal">from signal: ...</text>
      </g>
    </g>
    <g class="band" data-class="completion" ...>...</g>
    <g class="band" data-class="sensitivity" ...>...</g>
    <g class="band" data-class="interpretation" ...>...</g>
  </g>

  <g class="resolution">
    <path class="resolution-arrow" d="M ..." marker-end="url(#cascade-arrowhead)" />
  </g>

  <g class="output" data-force="mandatory">
    <text class="cue-action">COMPLETE</text>
    <rect class="force-pill" data-force="mandatory" rx="12" />
    <text class="force-word" data-force="mandatory">MANDATORY</text>
    <text class="cue-via">via completion</text>
  </g>

  <g class="force-strip">
    <!-- four cells in a row: advisory · strong · mandatory · blocking -->
    <!-- active cell is force-tinted with bold label -->
    <g class="strip-cell" data-level="advisory"  data-active="false">...</g>
    <g class="strip-cell" data-level="strong"    data-active="false">...</g>
    <g class="strip-cell" data-level="mandatory" data-active="true">...</g>
    <g class="strip-cell" data-level="blocking"  data-active="false">...</g>
    <!-- when cue.safety_modified, a vermillion arrow under the strip from
         base_force cell center to primary_force cell center -->
    <g class="strip-safety" data-tip="...">
      <path class="strip-safety-arrow" marker-end="url(#cascade-arrowhead)" />
    </g>
  </g>

  <g class="safety-banner">
    <!-- shown only when cue.safety_modified -->
    <rect class="safety-bg" /> <rect class="safety-accent" />
    <text class="safety-title">Force raised from strong to mandatory</text>
    <text class="safety-detail">Reason: high harm</text>
  </g>
</svg>
```

Key encoding choices:

- **Precedence as vertical position on a common scale.** Top-to-bottom ordering: validity, completion, sensitivity, interpretation. This is the strongest channel for ordered data (Cleveland and McGill 1984).
- **Class encoded by position and reinforced by color.** Each band has a class-specific accent color in the left border (Wong CVD-safe palette).
- **Fired vs not fired encoded by opacity, accent fill, and a status indicator.** Unfired bands drop to 45% opacity with a muted label; fired bands stay at full opacity with rationale text visible.
- **Winner distinguished by border weight on the band background.** `data-winner="true"` triggers the highlight in CSS.
- **Resolution as an explicit visual event.** An arrow runs from the winning band's right edge into the output box's force pill (the pill is the visual hero of the cue display). The arrow is the visible *act* of composition, not an inference the viewer has to make.
- **Cue display inline in the output box.** Large action word, force-tint pill (CVD-safe ordinal ramp: pale blue → mid blue → vermillion-tint → deep vermillion), small "via {rule_class}" caption beneath.
- **Force vocabulary as a horizontal strip below the bands.** Four cells in reading order: advisory · strong · mandatory · blocking. The active cell takes the force tint at full strength + bold label. Safety-modifier lift renders as a left-to-right vermillion arrow underneath, spanning from the `base_force` cell to the `primary_force` cell.
- **Safety banner for the textual rationale.** When the safety modifier raised the force, a banner below the strip carries the prose ("Force raised from X to Y" + "Reason: …"). The strip arrow shows *the lift*; the banner shows *why*.
- **On-demand layer per band.** Each fired band has an inner `<g class="on-demand">` carrying the triggering signal label ("from signal: …"). Hidden by default (`opacity: 0`); revealed per-band by click (toggling `data-expanded="true"`) or globally by `reveal="all"`. Rationale is always visible — it is primary content of a fired band, not on-demand detail.

### Scoped CSS (`viz/cascade_styles.css`)

```css
.cascade .band-bg {
  fill: #FAFAFA;
  stroke: #E0E0E0;
  stroke-width: 1;
  rx: 4;
}
.cascade .band[data-fired="false"] .band-bg { fill: #FAFAFA; }
.cascade .band[data-fired="true"]  .band-bg { fill: #F5F9FF; }
.cascade .band[data-winner="true"] .band-bg {
  stroke: #1565C0;
  stroke-width: 2;
  fill: #E8F1FB;
}

.cascade .band .on-demand {
  opacity: 0;
  pointer-events: none;
  transition: opacity 120ms ease-out;
}
.cascade .band[data-expanded="true"] .on-demand { opacity: 1; }
.cascade[data-reveal="all"] .band[data-fired="true"] .on-demand { opacity: 1; }

.cascade .band:hover .band-bg { stroke-width: 2; cursor: pointer; }

.cascade .resolution-arrow {
  stroke: #1565C0;
  stroke-width: 2;
  fill: none;
}
.cascade .force-scale .tick[data-active="true"] { fill: #E65100; }
.cascade .force-scale .safety-arrow { stroke: #C62828; stroke-width: 2; fill: none; }

/* Force-level tints for the output box, mirrored from §7 color tokens */
.cascade .output[data-force="advisory"]  .output-bg { fill: #F5F5F5; }
.cascade .output[data-force="strong"]    .output-bg { fill: #E3F2FD; }
.cascade .output[data-force="mandatory"] .output-bg { fill: #FFF3E0; }
.cascade .output[data-force="blocking"]  .output-bg { fill: #FFEBEE; }
```

### JavaScript interaction layer (`viz/cascade_interact.js`)

The script runs after the SVG is mounted inside `st.components.v1.html`. It implements the Shneiderman-faithful per-element on-demand behavior:

```js
(function () {
  const root = document.currentScript.parentNode.querySelector('.cascade');
  if (!root) return;

  const tooltip = document.createElement('div');
  tooltip.className = 'cascade-tooltip';
  tooltip.style.cssText = 'position:absolute; pointer-events:none; padding:6px 10px; '
    + 'background:#212121; color:#fff; border-radius:4px; font:12px sans-serif; '
    + 'opacity:0; transition:opacity 80ms;';
  document.body.appendChild(tooltip);

  function showTip(el, text, ev) {
    tooltip.textContent = text;
    tooltip.style.left = (ev.pageX + 12) + 'px';
    tooltip.style.top  = (ev.pageY + 12) + 'px';
    tooltip.style.opacity = '1';
  }
  function hideTip() { tooltip.style.opacity = '0'; }

  // Hover affordances for each band
  root.querySelectorAll('.band').forEach(band => {
    const cls = band.dataset.class;
    const fired = band.dataset.fired === 'true';
    const rationale = band.dataset.rationale || '';
    const signalLabel = band.dataset.signalLabel || '';

    band.addEventListener('mouseenter', ev => {
      const text = fired
        ? `${cls} — fired (${signalLabel}): ${rationale}`
        : `${cls} — did not fire`;
      showTip(band, text, ev);
    });
    band.addEventListener('mousemove', ev => {
      tooltip.style.left = (ev.pageX + 12) + 'px';
      tooltip.style.top  = (ev.pageY + 12) + 'px';
    });
    band.addEventListener('mouseleave', hideTip);

    // Click-to-expand: only fired bands have an on-demand layer worth revealing
    if (fired) {
      band.style.cursor = 'pointer';
      band.addEventListener('click', () => {
        const expanded = band.dataset.expanded === 'true';
        band.dataset.expanded = expanded ? 'false' : 'true';
      });
    }
  });

  // Hover affordances for the resolution arrow and force scale
  const arrow = root.querySelector('.resolution-arrow');
  if (arrow) {
    arrow.addEventListener('mouseenter', ev => {
      showTip(arrow, 'highest-precedence fired class wins', ev);
    });
    arrow.addEventListener('mouseleave', hideTip);
  }
  root.querySelectorAll('.force-scale .tick').forEach(tick => {
    tick.addEventListener('mouseenter', ev => {
      showTip(tick, tick.dataset.tip || '', ev);
    });
    tick.addEventListener('mouseleave', hideTip);
  });

  const safetyArrow = root.querySelector('.force-scale .safety-arrow');
  if (safetyArrow) {
    safetyArrow.addEventListener('mouseenter', ev => {
      showTip(safetyArrow, safetyArrow.dataset.tip || '', ev);
    });
    safetyArrow.addEventListener('mouseleave', hideTip);
  }
})();
```

The script is vanilla JS, has no dependencies, runs scoped to `document.currentScript.parentNode` so multiple instances on the same page (e.g., the three-way comparison) do not interfere.

### Streamlit integration

`ui/composition.py` is a thin wrapper:

```python
import streamlit as st
import streamlit.components.v1 as components
from viz.cascade import render_cascade

def render_panel_3(case, cue, reveal="none", interactive=True, height=560):
    html = render_cascade(case, cue, reveal=reveal, interactive=interactive)
    components.html(html, height=height, scrolling=False)
```

`render_cascade` emits a single string that contains the `<style>` block, the `<svg>` element, and (if `interactive=True`) the `<script>` block. No iframes within iframes — Streamlit handles that already.

### The other per-panel renderers

Each of the remaining three panels follows the same shape as `render_cascade`: a pure function that takes the relevant inputs, returns an SVG fragment with a fixed `viewBox`, and does not touch Streamlit. The Streamlit wrappers in `ui/` are one-line passes to `components.v1.html`.

```python
# viz/case_input.py
def render_case_input(case: Case, *, width: int = 360, height: int = 220,
                      css: bool = True, interactive: bool = False) -> str:
    """Panel 1 SVG: case ID badge, domain tag, description, risk score,
    interval bar with threshold, threshold callout."""

def render_interval_bar(case: Case, *, width: int = 320, height: int = 48) -> str:
    """The risk interval bar alone. Used inside render_case_input AND directly in
    the three-way comparison's middle column (the data-level foil)."""

# viz/signals.py
def render_signals(case: Case, *, width: int = 360, height: int = 220,
                   css: bool = True, interactive: bool = False) -> str:
    """Panel 2 SVG: detected signal rows grouped by category (data, scope, threshold,
    explanation, decision context). Each row carries a stable id (`signal-row-{name}`)
    so the cascade's back-reference layer can target it."""

```

> **2f redesign.** There is no `render_cue_output`. The cue display lives inside `render_cascade` (action word + force pill + via caption + horizontal force strip + safety banner all render inline as part of the cascade SVG). Earlier versions of this spec described a separate Panel 4 renderer; that file no longer exists.

All three panel renderers (`render_case_input`, `render_signals`, `render_cascade`) share the same calling convention: `(*, width, height, css, interactive)`. This uniformity is what makes the compositors trivial.

The Streamlit wrappers are correspondingly thin:

```python
# ui/case_input.py
import streamlit.components.v1 as components
from viz.case_input import render_case_input

def render_panel_1(case):
    components.html(render_case_input(case, css=True, interactive=False), height=240)
```

The same shape applies to `ui/signals.py` and `ui/composition.py` (which wraps `render_cascade`).

### The two compositors

```python
# viz/composite.py
def render_four_panel(case: Case, cue: Cue, *,
                      width: int = 720, height: int = 760,
                      css: bool = True, interactive: bool = False) -> str:
    """Figure 1: three-panel composite (function name kept for backward compat).

        +---------------+---------------+
        |  Panel 1      |  Panel 2      |   y=0,   240 tall
        |  Case input   |  Signals      |   (360 wide each)
        +---------------+---------------+
        |                               |
        |  Panel 3 — cascade            |   y=240, 520 tall
        |  (carries the cue inline:     |   (720 wide, full row)
        |   action, force pill, via,    |
        |   force strip, safety banner) |
        |                               |
        +-------------------------------+

    Bottom row is taller than the top row because the cascade carries
    four bands plus the force strip plus the safety banner. Each sub-SVG
    is wrapped in <g transform="translate(...)"> with its inner viewBox
    preserved. The cascade is rendered at its native standalone width
    (720), so its internal layout is identical here and in Figure 3.
    """

def render_three_way(case: Case, cue: Cue, *,
                     width: int = 1080, height: int = 560,
                     css: bool = True, interactive: bool = False) -> str:
    """Figure 2: three side-by-side displays on the same case.

        +-----------+-----------+-----------+
        | Conf-only |  Interval | ActionCue |
        |           |  bar      | (cascade) |
        +-----------+-----------+-----------+

    Left column: a single-number risk-score card with the threshold beneath
    (rendered as a small SVG inside composite.py — no separate viz/ module).
    Middle column: render_interval_bar(case) — the same helper Panel 1 uses.
    Right column: render_cascade(case, cue, reveal="none", css=False, interactive=False)
    — the standalone cascade, which now includes the cue display, force
    strip, and safety banner.
    """
```

The compositors assemble sub-SVGs by wrapping each in `<g transform="translate(x, y)">`. The inner `viewBox`es are preserved; only the outer SVG's `viewBox` changes. CSS is included only on the outer SVG (the sub-renderers pass `css=False` when called by the compositor) so styles do not duplicate.

A small caveat on uniform widths: the three-way compositor calls the cascade with the same width it would use standalone, so the cascade is not visually compressed. The confidence-only and interval-bar columns are narrower because they encode less. This means the three columns are not equal-width — the cascade column is wider than the other two. This is encoding-faithful: the data-level displays have less to show, and giving them equal width to the cascade would either pad them (misleading the reader about their information density) or compress the cascade (defeating the comparison).

### Figure export

`export_figures.py` is an offline script (no Streamlit) that calls the compositors and the cascade renderer with `interactive=False` and writes SVG files to `figures/`:

```python
from cases.healthcare import CASE_C, CASE_A
from cases.cross_domain import CASE_CR, CASE_DR
from engine import compose_cue
from rules import RULES
from viz.cascade import render_cascade
from viz.composite import render_four_panel, render_three_way

def write(svg: str, path: str) -> None:
    with open(path, "w") as f:
        f.write(svg)

if __name__ == "__main__":
    cue_c = compose_cue(CASE_C, RULES)

    # Figure 1: three-panel composite on Case C (post-2f; function name kept)
    write(render_four_panel(CASE_C, cue_c, css=True, interactive=False),
          "figures/figure_1_four_panel.svg")

    # Figure 2: three-way comparison on Case C
    write(render_three_way(CASE_C, cue_c, css=True, interactive=False),
          "figures/figure_2_three_way.svg")

    # Figure 3: Panel 3 detailed variant on Case C — generated and ready, used only if
    # the paper later \refs it. Not referenced in the current §4 draft.
    write(render_cascade(CASE_C, cue_c, reveal="all", css=True, interactive=False),
          "figures/figure_3_panel_3_detailed.svg")

    # Section 4.4 generativity (optional small-multiples): cross-domain cases.
    # Each renders the three-panel composite so the reader can compare across cases.
    cue_a  = compose_cue(CASE_A,  RULES)
    cue_cr = compose_cue(CASE_CR, RULES)
    cue_dr = compose_cue(CASE_DR, RULES)
    write(render_four_panel(CASE_A,  cue_a,  css=True, interactive=False),
          "figures/figure_4_generativity_a.svg")
    write(render_four_panel(CASE_CR, cue_cr, css=True, interactive=False),
          "figures/figure_4_generativity_cr.svg")
    write(render_four_panel(CASE_DR, cue_dr, css=True, interactive=False),
          "figures/figure_4_generativity_dr.svg")
```

Figures in the paper come from this export, guaranteeing prototype-figure provenance: every figure the paper shows is produced by code the live demo also runs.

---

## 7. Three-way comparison mode

When the top-level mode selector is set to "Three-way comparison", the layout changes from the three-panel ActionCue view to three side-by-side comparison columns. The case selector still drives all three views; only the rendering changes.

```python
def render_comparison(case, cue):
    col_conf, col_unc, col_ac = st.columns(3)

    with col_conf:
        st.subheader("Confidence-only")
        st.metric("AI risk score", f"{case.risk_score:.2f}")
        st.caption(f"Decision threshold: {case.decision_threshold:.2f}")

    with col_unc:
        st.subheader("Uncertainty display only")
        st.metric("AI risk score", f"{case.risk_score:.2f}")
        render_interval_bar(case)   # the same data-level display used in Panel 1

    with col_ac:
        st.subheader("ActionCue (process transparency)")
        render_panel_3(case, cue, reveal="none", interactive=True, height=480)
```

The three views show the same case at three levels of decision-process transparency. The leftmost shows what a confidence-only display reveals (a point estimate). The middle shows what a data-level uncertainty display reveals — the risk interval with the decision threshold marked, rendered by the same `render_interval_bar` helper used in Panel 1, so the foil is a faithful instance of current practice rather than a weakened stand-in. The rightmost shows what ActionCue's process-transparency view reveals (which uncertainty rules fired, which class won precedence, the resulting cue and force).

The live demo uses Streamlit columns for layout (above) while the paper figure (Figure 2) is generated by `render_three_way` in `viz/composite.py` (§6, "The two compositors"). Both paths share the same underlying renderers: `render_interval_bar` for the middle column, `render_cascade` for the right column. The Streamlit version adds column headers and case-selector affordances; the SVG composite version uses the same rendered components in a publication-ready layout.

Case C is the recommended starting case for the comparison, aligning with the paper's §4.3 worked example. It holds the healthcare through-line and gives the sharpest contrast across the three displays: the confidence-only view reads as act (risk above threshold), the uncertainty-only view reads as borderline (interval crosses threshold), and the ActionCue view reveals the missing critical input as the primary issue (completion wins precedence over sensitivity, cue is complete/mandatory), reframing the interval-crossing as the supporting cue. The missing-data dimension is invisible in both other displays. Cross-domain cases (CR, DR) are reserved for the generativity view rather than the comparison.

---

## 8. Pre-built cases

All cases use the same decision threshold (`0.60`) for the healthcare set so the contrast is clean. Risk scores are deliberate.

### Healthcare cases

```python
# cases/healthcare.py

CASE_A = Case(
    id="A", domain="healthcare",
    description="Patient with stable vitals, complete record, profile within validated population.",
    risk_score=0.82, risk_interval=(0.78, 0.86), decision_threshold=0.60,
    expected_actor="clinician at point of care",
)
# Expected: no rules fire → proceed / advisory

CASE_B = Case(
    id="B", domain="healthcare",
    description="Patient with risk near the action threshold; complete record, in-scope, stable.",
    risk_score=0.62, risk_interval=(0.48, 0.75), decision_threshold=0.60,
    expected_actor="clinician at point of care",
)
# Expected: sensitivity rule fires → inspect / strong

CASE_C = Case(
    id="C", domain="healthcare",
    description="Patient with risk at threshold; oxygen saturation missing.",
    risk_score=0.62, risk_interval=(0.55, 0.69), decision_threshold=0.60,
    has_missing_critical=True, missing_fields=["oxygen saturation"],
    expected_actor="clinician at point of care",
)
# Expected: completion rule fires → complete / mandatory (sensitivity also fires; completion wins by precedence)

CASE_D = Case(
    id="D", domain="healthcare",
    description="Patient profile rare in training population (out of scope).",
    risk_score=0.62, risk_interval=(0.55, 0.69), decision_threshold=0.60,
    is_outside_scope=True,
    scope_reason="patient demographic underrepresented in training data",
    expected_actor="clinician at point of care",
)
# Expected: validity rule fires (sensitivity also) → escalate / mandatory

CASE_E = Case(
    id="E", domain="healthcare",
    description="Out-of-scope case with high harm and low reversibility.",
    risk_score=0.62, risk_interval=(0.55, 0.69), decision_threshold=0.60,
    is_outside_scope=True,
    scope_reason="patient demographic underrepresented in training data",
    is_high_harm=True, is_low_reversibility=True,
    expected_actor="clinician at point of care",
)
# Expected: validity rule fires → escalate / mandatory → safety modifier raises to blocking
```

### Cross-domain cases

```python
# cases/cross_domain.py

CASE_CR = Case(
    id="CR", domain="credit_risk",
    description="Credit decision near regulatory threshold; applicant data partly stale.",
    risk_score=0.55, risk_interval=(0.42, 0.68), decision_threshold=0.50,
    has_missing_critical=True, missing_fields=["recent income verification"],
    is_outside_scope=True,
    scope_reason="applicant profile rare in lender's portfolio",
    expected_actor="loan officer / second reviewer",
)
# Expected: validity (out of scope) primary → escalate / mandatory;
# completion supporting; sensitivity also supporting.

CASE_DR = Case(
    id="DR", domain="disaster",
    description="Evacuation trigger with model disagreement under high harm conditions.",
    risk_score=0.65, risk_interval=(0.55, 0.79), decision_threshold=0.60,
    has_explanation_instability=True,
    explanation_disagreement="two ensemble models assign different risk categories",
    is_high_harm=True, is_low_reversibility=True,
    expected_actor="emergency operations coordinator",
)
# Expected: sensitivity (interval crosses threshold) primary → inspect / strong;
# interpretation supporting; safety modifier raises strong → mandatory.
```

**v2 fix.** `CASE_DR`'s `risk_interval` was previously `(0.62, 0.79)`, which did not contain the `0.60` threshold, so the sensitivity rule did not actually fire. The interval is now `(0.55, 0.79)` so sensitivity fires as the expected-output comment and the test both assume. The risk score is adjusted to `0.65` to remain consistent with the interval.

---

## 9. Visual design

The palette is selected for color-vision-deficiency (CVD) accessibility. Force-level tokens use a deep-navy + vermillion ramp that preserves ordinal rank under deuteranopia, protanopia, and tritanopia simulation; class accents draw from Wong's categorical palette [Wong, 2011, *Nature Methods* 8(6):441], chosen because its eight hues remain mutually distinguishable across the three common CVD types. The token tables below document every CVD-deliberate color used by the renderers. General-chrome neutrals (typography, borders, dividers) are listed at the end; structural lines (the resolution arrow, status indicators) use pure black for weight contrast rather than palette membership.

### Force-level color tokens

Applied to the cascade output box's force pill *and* to the corresponding active cell of the horizontal force strip. The same ramp drives both surfaces so the pill and the strip read as one encoding system.

| Force | Pill / strip-cell fill | Pill / strip-cell stroke | Pill foreground (force word) |
|---|---|---|---|
| advisory  | `#E8F1F8` | `#BFD3E6` | `#1F3D5C` |
| strong    | `#BFD3E6` | `#5B8AB8` | `#1F3D5C` |
| mandatory | `#F2C5A3` | `#D55E00` | `#1F3D5C` |
| blocking  | `#D55E00` | `#1F3D5C` | `#FFFFFF` |

The ramp progresses light pale-blue → mid-blue → vermillion tint → saturated vermillion. Under CVD simulation the ordinal sequence remains monotonically readable; the four tints do not collapse to the same perceived value as a Material-style red/orange/yellow ramp would.

Strip-cell labels: `#888888` when inactive, `#1F3D5C` when active, `#FFFFFF` when active on the blocking cell (for contrast against the saturated fill).

Inactive strip cells: fill `#F4F4F4`, stroke `#E0E0E0`.

### Class accent colors (left border on Panel 3 cascade bands)

Drawn from the Wong 2011 categorical palette. All four classes use a Wong hue so the categorical encoding stays consistent regardless of which classes fire in a given case.

| Class | Accent fill |
|---|---|
| validity       | `#D55E00` (Wong vermillion) |
| completion     | `#009E73` (Wong bluish green) |
| sensitivity    | `#CC79A7` (Wong reddish purple) |
| interpretation | `#0072B2` (Wong blue) |

Validity reuses the vermillion already used by the highest force level, which is intentional: validity is the highest-precedence rule class and the visual rhyme reinforces the precedence ordering rather than competing with it.

### Safety banner

Visible only when `cue.safety_modified`. Vermillion accent stripe flags the force lift; the wash and border keep it readable without competing with the cascade.

| Element | Value | Role |
|---|---|---|
| `.safety-bg` fill   | `#FFF6EF` | wash |
| `.safety-bg` stroke | `#F2C5A3` | border (matches mandatory pill fill) |
| `.safety-accent`    | `#D55E00` | vermillion accent stripe |
| `.safety-title`     | `#1F3D5C` | title text |
| `.safety-detail`    | `#555555` | detail text |

The strip-safety arrow (drawn under the force strip when a safety lift is in effect) uses `#D55E00` stroke to match the banner accent.

### Panel 1 (case input) chrome

| Element | Value |
|---|---|
| Case badge fill           | `#1F3D5C` |
| Case badge ID text        | `#FFFFFF` |
| Domain tag                | `#555555` |
| Score value               | `#1F3D5C` |
| Threshold label / tick    | `#D55E00` |
| Interval bar track        | `#E0E0E0` |
| Interval bar interval     | `#BFD3E6` (matches strong-force fill — same "data uncertainty domain") |
| Score marker fill / stroke| `#1F3D5C` / `#FFFFFF` |
| Description text          | `#333333` |

### Panel 2 (signals) chrome

| Element | Value |
|---|---|
| Rail accent (detected side)         | `#D55E00` |
| Detected signal indicator           | `#D55E00` |
| Detected signal label               | `#1F3D5C` |
| Detected signal detail              | `#555555` |
| Undetected signal indicator stroke  | `#999999` |
| Undetected signal label             | `#888888` |
| Undetected divider                  | `#E0E0E0` |
| Undetected caption                  | `#999999` |

### General chrome neutrals (typography and structure)

These are consistent across all three CSS files.

| Role | Value |
|---|---|
| Primary text                 | `#212121` |
| Secondary text / detail      | `#555555` |
| Tertiary text / caption      | `#888888` |
| Quaternary text              | `#999999` |
| Description body             | `#333333` |
| Border (default)             | `#D0D0D0` |
| Divider                      | `#E0E0E0` |
| Subtle background fill       | `#FAFAFA` |
| Hover / winner background    | `#F5F5F5` |
| Pure white                   | `#FFFFFF` |
| Structural lines (resolution arrow, status circles) | `#000000` |

Black is reserved for *structural* lines that carry weight (the resolution arrow's emphasis, status indicators). It is not part of the CVD palette and does not encode class or force.

### Implementation note

Tokens are inlined as hex values in the three `viz/*_styles.css` files rather than as CSS custom properties. The audit pass in 4a verified that every hex value in the styles files matches the tables above; if a future renderer or style edit introduces a new color, it should either match an existing token here or extend §9. The five inline hex literals in `viz/composite.py` (used for the self-contained figure exports that don't load the CSS) are acknowledged as a parallel implementation of the same neutrals and are not subject to §9 governance.

### Layout

- Page in wide mode
- Header: mode selector (ActionCue full / Three-way comparison), short tagline
- Case selector
- Main: two-row layout in ActionCue mode (case input + signals side by side on top, full-width cascade-with-cue on the bottom); three columns in comparison mode (equal headers, but the cascade column is wider than the data-level columns per §6 caveat)
- Below: rule registry tab
- No clinical-system styling — the prototype should look like a research demo, not an EHR

### Typography

Streamlit defaults are fine. Inside the SVG, use a clean sans-serif (`font-family: -apple-system, "Segoe UI", Roboto, sans-serif`) and a single size hierarchy: band labels 14px, band rationale 11px, on-demand signal 10px italic, output action 22px bold, force-word inside pill 11px bold, force-strip cell labels 11px uppercase, safety banner title 11px, safety detail 10px.

---

## 10. Tests as executable specification

In `tests/test_engine.py`, one assertion per case plus engine invariants. This catches regressions and serves as the contract between the framework and the build.

```python
import pytest

# ---------- Per-case behavioral tests ----------

def test_case_a_proceeds():
    cue = compose_cue(CASE_A, RULES)
    assert cue.primary_action == "proceed"
    assert cue.primary_force == "advisory"

def test_case_b_inspects():
    cue = compose_cue(CASE_B, RULES)
    assert cue.primary_action == "inspect"
    assert cue.primary_force == "strong"

def test_case_c_completes():
    cue = compose_cue(CASE_C, RULES)
    assert cue.primary_action == "complete"
    assert cue.primary_force == "mandatory"

def test_case_d_escalates():
    cue = compose_cue(CASE_D, RULES)
    assert cue.primary_action == "escalate"
    assert cue.primary_force == "mandatory"
    assert not cue.safety_modified

def test_case_e_blocks_via_safety_modifier():
    cue = compose_cue(CASE_E, RULES)
    assert cue.primary_action == "escalate"
    assert cue.primary_force == "blocking"       # raised from mandatory
    assert cue.safety_modified

def test_case_cr_validity_dominates_completion():
    cue = compose_cue(CASE_CR, RULES)
    assert cue.primary_action == "escalate"      # validity wins
    assert any(f.rule.rule_class == "completion" for f in cue.supporting)

def test_case_dr_safety_raises_strong_to_mandatory():
    cue = compose_cue(CASE_DR, RULES)
    assert cue.primary_firing.rule.rule_class == "sensitivity"
    assert cue.primary_force == "mandatory"      # raised from strong
    assert cue.safety_modified

# ---------- Engine invariants ----------

def test_constraint_matrix_enforced_for_all_cases():
    """Every composed cue must satisfy the constraint matrix."""
    from cases.healthcare import CASE_A, CASE_B, CASE_C, CASE_D, CASE_E
    from cases.cross_domain import CASE_CR, CASE_DR
    for case in [CASE_A, CASE_B, CASE_C, CASE_D, CASE_E, CASE_CR, CASE_DR]:
        cue = compose_cue(case, RULES)
        assert cue.primary_force in CONSTRAINT_MATRIX[cue.primary_action], (
            f"Case {case.id}: invalid combination ({cue.primary_action}, {cue.primary_force})"
        )

def test_invalid_combination_raises():
    """A rule definition that produces a forbidden pairing must raise at composition time."""
    bad_case = Case(
        id="BAD", domain="test",
        description="forces a forbidden pairing",
        risk_score=0.5, risk_interval=(0.4, 0.6), decision_threshold=0.5,
        is_outside_scope=True, scope_reason="test",
    )
    bad_rule = Rule(
        id="bad", rule_class="validity", precedence=1,
        description="bad", base_action="escalate", base_force="advisory",  # forbidden
        signal_name="out_of_scope",
        trigger=lambda c: c.is_outside_scope,
        rationale=lambda c: "bad",
    )
    with pytest.raises(ValueError, match="Invalid"):
        compose_cue(bad_case, [bad_rule])

def test_within_class_plurality_raises():
    """Two rules of the same class firing simultaneously must raise."""
    case = Case(
        id="T", domain="test",
        description="trigger both validity rules",
        risk_score=0.5, risk_interval=(0.4, 0.6), decision_threshold=0.5,
        is_outside_scope=True, scope_reason="test",
    )
    r1 = Rule(
        id="v1", rule_class="validity", precedence=1,
        description="v1", base_action="escalate", base_force="mandatory",
        signal_name="out_of_scope",
        trigger=lambda c: c.is_outside_scope, rationale=lambda c: "v1",
    )
    r2 = Rule(
        id="v2", rule_class="validity", precedence=1,
        description="v2", base_action="escalate", base_force="mandatory",
        signal_name="out_of_scope",
        trigger=lambda c: c.is_outside_scope, rationale=lambda c: "v2",
    )
    with pytest.raises(AssertionError, match="plurality"):
        compose_cue(case, [r1, r2])

def test_triggering_signal_attached_to_firings():
    """Every RuleFiring must carry the triggering UncertaintySignal."""
    cue = compose_cue(CASE_CR, RULES)
    assert cue.primary_firing.triggering_signal is not None
    for f in cue.supporting:
        assert f.triggering_signal is not None
```

---

## 11. Build sequence

| Week | Output | Verification |
|---|---|---|
| 1 | Models (with v2 fields), rules (with `signal_name`), engine (with constraint matrix and plurality assertion); all 11 tests passing | `pytest tests/` clean |
| 2 | Three per-panel renderers in `viz/` (`render_case_input`, `render_signals`, `render_cascade`) plus the two compositors in `viz/composite.py` (`render_four_panel`, `render_three_way`); `export_figures.py` produces Figures 1, 2, and 3 plus the three §4.4 generativity figures. **Note (2f):** the cascade absorbs the cue display; there is no separate `render_cue_output`. The composite is three-panel, not 2×2 four-panel. | Open every exported SVG in a browser; visual review against the §6 SVG structure and the three-panel layout for Figure 1 |
| 3 | Streamlit panels wrap the per-panel renderers in `components.html`; case selector working; Panel 3 hover/click affordances functional; three-way comparison mode functional; rule registry tab | Manual click-through of all 7 cases in both modes; hover and click affordances verified per band |
| 4 | Visual polish, force-level color tokens applied consistently, safety banner, README, demo recording | Demo runs end-to-end without explanation |

After week 4, the prototype is presentation-ready. Remaining time goes to writing the paper.

The build remains four weeks. Week 2's scope (post-2f) covers three per-panel SVG renderers — `render_case_input`, `render_signals`, and a `render_cascade` that absorbs what was originally Panel 4's cue display — and both compositors. This is the work that gives every paper figure prototype-provenance — figures fall out of the same functions the demo calls.

---

## 12. Notes for Claude Code

- Treat `models.py`, `rules.py`, and `engine.py` as the contract. Build them first, get the 11 tests green, then build the renderer, then build the UI on top.
- The cases live as Python objects (not JSON) so they are typed and editable directly in the source.
- All rule logic should be pure functions over `Case`. No I/O, no global state, no side effects.
- `signal_for` is also pure: it derives an `UncertaintySignal` from a `Case` and a `signal_name`. Panel 2 and `compose_cue` both use it; do not duplicate the logic.
- `render_cascade` returns a string. It does not touch Streamlit. Streamlit-specific code lives in `ui/composition.py` and `ui/comparison.py`, which call `render_cascade` and pass the result to `st.components.v1.html`.
- The Streamlit panels should each be a function that takes the current `Case` and `Cue` and renders. This keeps them composable and individually testable.
- The JS in `viz/cascade_interact.js` is vanilla — no framework, no bundler, no dependencies. It must run scoped to its parent node so multiple cascades on the same page (three-way comparison mode) do not interfere.
- No external API calls, no model loading, no network. The prototype is fully offline and deterministic.
- If a UI choice is ambiguous, prefer the option that makes the rule engine and the composition reasoning more visible. The point of the prototype is that the binding logic is inspectable.
- Paper figures come from `export_figures.py`, not from screenshots. Single source of truth.