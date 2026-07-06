# ActionCue: Uncertainty-to-action binding

## Manuscript

Visualizing Uncertainty-to-Action Composition for Human Oversight

Authored by:

<!-- - Chisom Ezekannagha
- *(co-authors TBD)* -->

The manuscript is in preparation. Please cite the following article should you use any part of this code or build upon it:

```bibtex
citation placeholer
```

## Abstract

AI systems are becoming more transparent about uncertainty but rarely make clear what response that uncertainty should trigger. Most uncertainty visualization work encodes uncertainty in the model output — confidence intervals, distributional summaries, ensembles — leaving users to compose the oversight response themselves. ActionCue addresses a complementary part of the design space: uncertainty in the decision *process*. We introduce an uncertainty-to-action binding framework that composes multiple uncertainty conditions into a single oversight response under a precedence policy with a contextual safety modifier, and a process-transparency visualization — an annotated precedence cascade — that makes that composition explicit. The framework specifies what gets composed; the visualization makes the composition inspectable.

## Dependencies

| Dependency | Version |
|------------|---------|
| Python     | 3.11+ |
| streamlit  | latest |
| pytest     | latest |

Full pin list in [`requirements.txt`](requirements.txt). No external API calls, no model loading, no network — the prototype is fully offline and deterministic.

## Data

The prototype runs on seven synthetic decision cases stipulated as Python objects. No external data files are read.

| Location | Description |
|----------|-------------|
| [`cases/healthcare.py`](cases/healthcare.py) | `CASE_A`–`CASE_E`: clinical decisions covering proceed, sensitivity-driven inspection, completion-wins-precedence, validity-escalation, and safety-modifier-lifted abstention. |
| [`cases/cross_domain.py`](cases/cross_domain.py) | `CASE_CR` (credit risk, validity dominates completion) and `CASE_DR` (disaster forecasting, sensitivity with safety lift). |

| Case | Domain | Behavior |
|------|--------|----------|
| `CASE_A`  | healthcare  | No rules fire → **proceed / advisory**. |
| `CASE_B`  | healthcare  | Sensitivity fires → **inspect / strong**. |
| `CASE_C`  | healthcare  | Completion wins precedence over sensitivity → **complete / mandatory**. |
| `CASE_D`  | healthcare  | Validity fires → **escalate / mandatory**. |
| `CASE_E`  | healthcare  | Validity + high harm + low reversibility → **abstain / blocking** (safety lift). |
| `CASE_CR` | credit risk | Validity dominates completion → **escalate / mandatory**. |
| `CASE_DR` | disaster    | Sensitivity under high-harm / low-reversibility context → **inspect / mandatory** (safety lift). |

## Code

| Location | Description |
|----------|-------------|
| [`models.py`](models.py)         | Dataclasses: `Case`, `Rule`, `UncertaintySignal`, `RuleFiring`, `Cue`. |
| [`rules.py`](rules.py)           | The four rule definitions (`RULES`) and the `signal_for` resolver. |
| [`engine.py`](engine.py)         | Rule firing, constraint-matrix validation, precedence resolution, safety modifier, `compose_cue`. |
| [`viz/`](viz/)                   | SVG renderers (case input, signals, cascade) + the two compositors. Each renderer is pure: takes a `Case` / `Cue`, returns a string. |
| [`ui/`](ui/)                     | Streamlit wrappers — thin pass-throughs to `components.html`. No SVG generation, no engine logic. |
| [`app.py`](app.py)               | Streamlit entry point: page config, mode + case selectors, layout. |
| [`export_figures.py`](export_figures.py) | Offline figure generator. Produces the six paper figures + an HTML index without launching Streamlit. |
| [`tests/test_engine.py`](tests/test_engine.py) | 11 tests: one per case plus engine invariants. |
| [`SPEC.md`](SPEC.md)             | Full build specification: data models, panel specs, rule definitions, color tokens (§9). |

Force levels: `advisory`, `strong`, `mandatory`, `blocking`. The CVD-deliberate color palette (deep navy + vermillion ramp for force; Wong 2011 categorical hues for rule class) is documented in [SPEC §9](SPEC.md#9-visual-design).

## Installation and running

### Setup

```bash
# Python 3.11+ required.
pip install -r requirements.txt
```

### Engine tests

```bash
pytest tests/
```

11 tests, ~10ms. Pass means the rule engine, constraint matrix, precedence resolution, and safety modifier all behave per [SPEC §4](SPEC.md#4-the-rule-engine).

### Paper figures

```bash
python export_figures.py
```

Regenerates six SVG + PDF pairs into [`figures/`](figures/) and an `index.html` viewer. Every figure the paper shows is produced by code the live demo also runs (single source of truth).

| File | What it shows |
|------|---------------|
| `figure_1_four_panel.svg`        | Three-panel composite for `CASE_C` (filename is a legacy artifact from the pre-2f four-panel design). |
| `figure_2_three_way.svg`         | `CASE_C` across three displays: confidence-only, interval bar, ActionCue cascade. |
| `figure_3_panel_3_detailed.svg`  | Standalone cascade with the on-demand layer expanded. |
| `figure_4_generativity_a.svg`    | `CASE_A` — no rules fire. |
| `figure_4_generativity_cr.svg`   | `CASE_CR` — credit decision, validity wins. |
| `figure_4_generativity_dr.svg`   | `CASE_DR` — disaster forecasting, safety lift. |

### Live demo

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. The sidebar exposes two view modes and a case selector:

- **ActionCue (full).** Three-panel layout: case input + signals on the top row, the annotated cascade full-width below. The cascade carries the cue display, force strip, and safety banner inline. Hover the resolution arrow and the strip-safety arrow for tooltips; click a fired band to reveal its rationale and triggering signal.
- **Three-way comparison.** Three side-by-side columns: confidence-only, data-level uncertainty (interval bar with threshold marked, same renderer as Panel 1), and the ActionCue cascade. `CASE_C` is the recommended starting case — confidence-only says "act"; uncertainty-only says "borderline"; ActionCue surfaces the missing input as the primary issue.

A **rules registry** expander at the bottom of the page shows the four rule definitions — same data the engine reads — with precedence, class, base action, base force, bound signal, and description.

## License

Released under the MIT License — see [`LICENSE`](LICENSE).

## Contribution

Contributions are welcome and must comply with the MIT License. The prototype is structured around stable contracts: `models.py`, `rules.py`, `engine.py`, the renderers in `viz/`, and the figure pipeline are treated as the contract.