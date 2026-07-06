"""Export Week 2 figures for the ActionCue paper.

Six static SVGs, six PDFs, and an HTML index. All static — no JS.
Per SPEC §6 and the §4 paper draft:

    figure_1_four_panel.svg        — four-panel composite (CASE_C)
    figure_2_three_way.svg         — three-way comparison (CASE_C)
    figure_3_panel_3_detailed.svg  — standalone cascade, reveal="all" (CASE_C)
    figure_4_generativity_a.svg    — four-panel composite (CASE_A)
    figure_4_generativity_cr.svg   — four-panel composite (CASE_CR)
    figure_4_generativity_dr.svg   — four-panel composite (CASE_DR)

Every figure the paper shows is produced by code the live demo also runs
(SPEC §6, §12: single source of truth between demo and paper).

Run from repo root: .venv/bin/python export_figures.py
"""

from pathlib import Path

import cairosvg

from cases.healthcare import CASE_A, CASE_C
from cases.cross_domain import CASE_CR, CASE_DR
from engine import compose_cue
from rules import RULES
from viz.cascade import render_cascade
from viz.composite import render_four_panel, render_three_panel_row, render_three_way


FIGURES_DIR = Path("figures")


def _write_pair(svg: str, stem: str) -> Path:
    """Write an SVG and its PDF sibling. Return the SVG path."""
    svg_path = FIGURES_DIR / f"{stem}.svg"
    pdf_path = FIGURES_DIR / f"{stem}.pdf"
    svg_path.write_text(svg)
    cairosvg.svg2pdf(bytestring=svg.encode("utf-8"), write_to=str(pdf_path))
    print(f"wrote {svg_path} and {pdf_path}")
    return svg_path


def _write_index(rendered: list[tuple[str, str]]) -> None:
    """Write figures/index.html embedding every figure inline with its title."""
    sections = "\n".join(
        f'  <section>\n    <h2>{title}</h2>\n    {svg}\n  </section>'
        for title, svg in rendered
    )
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>ActionCue figures — Week 2 export</title>
  <style>
    body {{ font: 14px -apple-system, "Segoe UI", Roboto, sans-serif; padding: 24px; max-width: 1600px; margin: 0 auto; color: #212121; }}
    section {{ margin-bottom: 48px; }}
    h2 {{ font-size: 14px; margin: 0 0 8px 0; }}
    svg {{ display: block; }}
  </style>
</head>
<body>
  <h1 style="font-size: 16px;">ActionCue — Week 2 figure export</h1>
{sections}
</body>
</html>'''
    (FIGURES_DIR / "index.html").write_text(html)
    print(f"wrote {FIGURES_DIR / 'index.html'}")


if __name__ == "__main__":
    FIGURES_DIR.mkdir(exist_ok=True)

    # Compose cues once per case.
    cue_a = compose_cue(CASE_A, RULES)
    cue_c = compose_cue(CASE_C, RULES)
    cue_cr = compose_cue(CASE_CR, RULES)
    cue_dr = compose_cue(CASE_DR, RULES)

    rendered: list[tuple[str, str]] = []

    # Figure 1 — horizontal three-panel row (CASE_C, the §4 worked example)
    # Wide-aspect layout (P1 | P2 | P3 side-by-side) keeps the paper PDF
    # from forcing a page break; filename stays `figure_1_four_panel` for
    # citation stability.
    svg = render_three_panel_row(CASE_C, cue_c, css=True, interactive=False)
    _write_pair(svg, "figure_1_four_panel")
    rendered.append(("Figure 1 — three-panel row (Case C)", svg))

    # Figure 2 — three-way comparison (CASE_C)
    svg = render_three_way(CASE_C, cue_c, css=True, interactive=False)
    _write_pair(svg, "figure_2_three_way")
    rendered.append(("Figure 2 — three-way comparison (Case C)", svg))

    # Figure 3 — standalone detailed cascade (CASE_C, reveal="all")
    svg = render_cascade(
        CASE_C, cue_c,
        reveal="all", css=True, interactive=False,
    )
    _write_pair(svg, "figure_3_panel_3_detailed")
    rendered.append(("Figure 3 — Panel 3 detailed (Case C, reveal=all)", svg))

    # Figure 4 — generativity across cases
    svg = render_four_panel(CASE_A, cue_a, css=True, interactive=False)
    _write_pair(svg, "figure_4_generativity_a")
    rendered.append(("Figure 4a — generativity (Case A, healthcare, no rules fire)", svg))

    svg = render_four_panel(CASE_CR, cue_cr, css=True, interactive=False)
    _write_pair(svg, "figure_4_generativity_cr")
    rendered.append(("Figure 4cr — generativity (Case CR, credit, validity wins)", svg))

    svg = render_four_panel(CASE_DR, cue_dr, css=True, interactive=False)
    _write_pair(svg, "figure_4_generativity_dr")
    rendered.append(("Figure 4dr — generativity (Case DR, disaster, safety lift)", svg))

    _write_index(rendered)
    print(f"done. {len(rendered)} figures, {len(rendered)} PDFs, 1 index.")
