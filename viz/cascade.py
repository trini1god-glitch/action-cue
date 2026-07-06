import html
from pathlib import Path
from typing import Optional

from models import Case, Cue, RuleFiring
from viz._common import bool_attr, wrap_text, render_style


_CLASS_ORDER = ["validity", "completion", "sensitivity", "interpretation"]
_FORCE_ORDER = ["advisory", "strong", "mandatory", "blocking"]


# Layout in viewBox units.
_BAND_X = 40
_BAND_WIDTH = 320
_BAND_HEIGHT = 80
_BAND_GAP = 10
_BAND_Y0 = 20
_ACCENT_WIDTH = 6

_OUTPUT_X = 420
_OUTPUT_Y = 140
_OUTPUT_WIDTH = 140
_OUTPUT_HEIGHT = 100

# --- Horizontal force strip (below the bands) ---
# Replaces the vertical force scale on the right. Reads as a vocabulary axis
# (four ordinal levels in reading order) with the active level highlighted.
# Sits flush below band 3 (which ends at y = _BAND_Y0 + 4 * (_BAND_HEIGHT + _BAND_GAP) - _BAND_GAP = 370).
_STRIP_Y = _BAND_Y0 + 3 * (_BAND_HEIGHT + _BAND_GAP) + _BAND_HEIGHT + 4  # band 3 bottom + 4-unit gap = 374
_STRIP_CELL_W = 120
_STRIP_CELL_H = 28
_STRIP_GAP = 4
_STRIP_TOTAL_W = 4 * _STRIP_CELL_W + 3 * _STRIP_GAP    # 492
_STRIP_X = (720 - _STRIP_TOTAL_W) // 2                  # centered for default width=720
_STRIP_SAFETY_ARROW_Y = _STRIP_Y + _STRIP_CELL_H + 14

# --- Safety banner (textual rationale for the safety lift) ---
_BANNER_HEIGHT = 32
_BANNER_PAD_X = 16
_BANNER_ACCENT_W = 3
_BANNER_TEXT_INSET_X = 12     # text starts this far right of the accent strip
_BANNER_TITLE_DY = 12         # title baseline relative to banner top
_BANNER_DETAIL_DY = 26        # detail baseline relative to banner top
_BANNER_TOP_Y_GAP = 22        # vertical gap between strip safety arrow and banner top


def _band_y(index: int) -> int:
    return _BAND_Y0 + index * (_BAND_HEIGHT + _BAND_GAP)


def _render_band(rule_class: str, fired: bool, is_winner: bool, y: int,
                 firing: Optional[RuleFiring] = None, interactive: bool = False) -> str:
    """Render one cascade band.

    Where the rationale lives depends on `interactive`:
      - interactive=False (static figures): rationale is always-visible
        directly inside the band, beneath the class label. Figures 1, 3,
        and 4 all use this path so the paper figures stay information-
        dense without depending on hover/click.
      - interactive=True (live Streamlit demo): rationale moves into the
        on-demand <g>, hidden by default and revealed by click. This
        restores the overview-first / details-on-demand pattern
        (Shneiderman 1996) in the interactive setting where reader can
        actually click.
    """
    label = rule_class.capitalize()
    label_y = y + 30
    status_cx = _BAND_X + _BAND_WIDTH - 20
    status_cy = y + _BAND_HEIGHT // 2
    text_x = _BAND_X + _ACCENT_WIDTH + 8
    if firing is not None:
        rationale = html.escape(firing.rendered_rationale, quote=True)
        signal_label = html.escape(firing.triggering_signal.label, quote=True) if firing.triggering_signal else ""
        data_attrs = f' data-rationale="{rationale}" data-signal-label="{signal_label}"'
        rationale_lines = wrap_text(rationale, max_chars=46)
        rationale_tspans = "".join(
            f'<tspan x="{text_x}" dy="{0 if i == 0 else 11}">{line}</tspan>'
            for i, line in enumerate(rationale_lines)
        )
        rationale_y = y + 48
        signal_y = rationale_y + 11 * max(1, len(rationale_lines)) + 6

        rationale_block = (
            f'<text class="band-rationale" x="{text_x}" y="{rationale_y}">{rationale_tspans}</text>'
        )
        signal_block = (
            f'<text class="on-demand-signal" x="{text_x}" y="{signal_y}">from signal: {signal_label}</text>'
        )

        if interactive:
            # Live demo: both rationale and signal label live inside on-demand,
            # revealed together on click. Band default-state shows only class
            # label + status circle.
            band_rationale = ""
            on_demand_content = rationale_block + "\n        " + signal_block
        else:
            # Static figures: rationale always visible; on-demand keeps
            # signal label (revealed by `reveal="all"` in Figure 3).
            band_rationale = rationale_block
            on_demand_content = signal_block
    else:
        data_attrs = ""
        band_rationale = ""
        on_demand_content = ""
    return f'''    <g class="band" data-class="{rule_class}" data-fired="{bool_attr(fired)}" data-winner="{bool_attr(is_winner)}"{data_attrs}>
      <rect class="band-bg" x="{_BAND_X}" y="{y}" width="{_BAND_WIDTH}" height="{_BAND_HEIGHT}" />
      <rect class="band-accent" x="{_BAND_X}" y="{y}" width="{_ACCENT_WIDTH}" height="{_BAND_HEIGHT}" />
      <text class="band-label" x="{text_x}" y="{label_y}">{label}</text>
      {band_rationale}
      <g class="status">
        <circle cx="{status_cx}" cy="{status_cy}" r="6" />
      </g>
      <g class="on-demand" aria-hidden="true">
        {on_demand_content}
      </g>
    </g>'''


def _render_output(action: str, force: str, rule_class: Optional[str] = None) -> str:
    """Render the cascade's canonical cue display (now absorbing what was
    Panel 4 in earlier iterations): action word + force-tint pill + optional
    "via {rule_class}" caption.

    The action is the typographic hero; the pill is the visual hero (force
    tint at full strength); the "via" caption anchors the cue to the band
    that produced it.
    """
    text_x = _OUTPUT_X + _OUTPUT_WIDTH // 2

    # Action word at the top of the output box.
    action_y = _OUTPUT_Y + 28

    # Force pill below the action.
    pill_w = _OUTPUT_WIDTH - 24            # 12-unit inset on each side
    pill_x = _OUTPUT_X + 12
    pill_top_y = _OUTPUT_Y + 42
    pill_h = 24
    pill_text_y = pill_top_y + 16

    # "via {rule_class}" caption at the bottom (only when a rule won).
    via_y = pill_top_y + pill_h + 18

    force_attr = html.escape(force, quote=True)
    action_word = html.escape(action.upper())
    force_word = html.escape(force.upper())

    if rule_class is not None:
        via = (
            f'    <text class="cue-via" x="{text_x}" y="{via_y}" text-anchor="middle">'
            f'via {html.escape(rule_class)}</text>'
        )
    else:
        via = ""

    return f'''  <g class="output" data-force="{force_attr}">
    <text class="cue-action" x="{text_x}" y="{action_y}" text-anchor="middle">{action_word}</text>
    <rect class="force-pill" data-force="{force_attr}" x="{pill_x}" y="{pill_top_y}" width="{pill_w}" height="{pill_h}" rx="12" />
    <text class="force-word" data-force="{force_attr}" x="{text_x}" y="{pill_text_y}" text-anchor="middle">{force_word}</text>
{via}
  </g>'''


def _render_safety_banner(cue: Cue, panel_width: int) -> str:
    """Vermillion accent strip + caption shown only when cue.safety_modified.

    Sits below the force strip. The strip's safety arrow shows *the lift*
    visually; the banner carries the textual rationale ("Force raised from
    strong to mandatory" + "Reason: high harm"). Together they show *what
    happened* and *why*.
    """
    if not cue.safety_modified or cue.primary_firing is None:
        return ""

    base_force = html.escape(cue.primary_firing.base_force)
    primary_force = html.escape(cue.primary_force)
    reason = html.escape(cue.safety_reason or "")

    title = f"Force raised from {base_force} to {primary_force}"
    detail = f"Reason: {reason}" if reason else ""

    banner_top_y = _STRIP_SAFETY_ARROW_Y + _BANNER_TOP_Y_GAP
    banner_w = panel_width - 2 * _BANNER_PAD_X
    text_x = _BANNER_PAD_X + _BANNER_TEXT_INSET_X
    title_y = banner_top_y + _BANNER_TITLE_DY
    detail_y = banner_top_y + _BANNER_DETAIL_DY

    detail_block = (
        f'    <text class="safety-detail" x="{text_x}" y="{detail_y}">{detail}</text>'
        if detail else ""
    )

    return f'''  <g class="safety-banner">
    <rect class="safety-bg" x="{_BANNER_PAD_X}" y="{banner_top_y}" width="{banner_w}" height="{_BANNER_HEIGHT}" rx="4" />
    <rect class="safety-accent" x="{_BANNER_PAD_X}" y="{banner_top_y}" width="{_BANNER_ACCENT_W}" height="{_BANNER_HEIGHT}" />
    <text class="safety-title" x="{text_x}" y="{title_y}">{title}</text>
{detail_block}
  </g>'''


def _render_force_strip(cue: Cue, panel_width: int) -> str:
    """Horizontal force strip below the bands.

    Four ordinal cells (advisory → strong → mandatory → blocking) laid out
    left-to-right. Active cell gets the force tint at full strength + bold
    label; inactive cells stay muted. When the safety modifier raised the
    force, a left-to-right arrow under the strip spans from the base_force
    cell's center to the primary_force cell's center, with a small caption.

    This replaces the old vertical force scale + safety arrow combination.
    """
    active_force = cue.primary_force
    base_force = cue.primary_firing.base_force if cue.primary_firing else None
    safety_modified = cue.safety_modified and base_force is not None and base_force != active_force

    strip_x = (panel_width - _STRIP_TOTAL_W) // 2

    cells = []
    cell_centers: dict[str, int] = {}
    for i, level in enumerate(_FORCE_ORDER):
        cell_x = strip_x + i * (_STRIP_CELL_W + _STRIP_GAP)
        center_x = cell_x + _STRIP_CELL_W // 2
        cell_centers[level] = center_x
        is_active = level == active_force
        text_y = _STRIP_Y + 18
        cells.append(
            f'<g class="strip-cell" data-level="{level}" data-active="{bool_attr(is_active)}">'
            f'<rect class="strip-cell-bg" data-level="{level}" '
            f'x="{cell_x}" y="{_STRIP_Y}" width="{_STRIP_CELL_W}" height="{_STRIP_CELL_H}" rx="4" />'
            f'<text class="strip-cell-label" x="{center_x}" y="{text_y}" text-anchor="middle">{level}</text>'
            f'</g>'
        )
    cells_svg = "\n    ".join(cells)

    if safety_modified:
        x_from = cell_centers[base_force]
        x_to = cell_centers[active_force]
        tip = html.escape(f"Force raised from {base_force} to {active_force} due to {cue.safety_reason}", quote=True)
        # Visual-only safety arrow: the textual explanation lives in the
        # safety banner below, so the arrow doesn't restate it.
        safety = (
            f'\n    <g class="strip-safety" data-tip="{tip}">'
            f'<path class="strip-safety-arrow" d="M {x_from} {_STRIP_SAFETY_ARROW_Y} L {x_to} {_STRIP_SAFETY_ARROW_Y}" '
            f'marker-end="url(#cascade-arrowhead)" />'
            f'</g>'
        )
    else:
        safety = ""

    return f'''  <g class="force-strip">
    {cells_svg}{safety}
  </g>'''


def _render_script() -> str:
    js = Path(__file__).with_name("cascade_interact.js").read_text()
    return f'<script>{js}</script>'


def _render_defs() -> str:
    return '''  <defs>
    <marker id="cascade-arrowhead" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="8" markerHeight="8" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
    </marker>
  </defs>'''


def _render_resolution(winner_index: int, interactive: bool = True) -> str:
    """Resolution arrow from the winner band to the output box's force pill.

    The pill is the visual hero of the cue display, so the arrow lands on
    the pill's vertical center rather than on the output box's geometric
    middle.
    """
    start_x = _BAND_X + _BAND_WIDTH
    start_y = _band_y(winner_index) + _BAND_HEIGHT // 2
    end_x = _OUTPUT_X
    end_y = _OUTPUT_Y + 42 + 12  # pill_top_y + pill_h/2
    mid_x = (start_x + end_x) // 2
    return f'''  <g class="resolution">
    <path class="resolution-arrow" data-tip="highest-precedence fired class wins" d="M {start_x} {start_y} L {mid_x} {start_y} L {mid_x} {end_y} L {end_x} {end_y}" marker-end="url(#cascade-arrowhead)" />
  </g>'''


def render_cascade(
    case: Case,
    cue: Cue,
    *,
    reveal: str = "none",
    width: int = 720,
    height: int = 500,
    css: bool = True,
    interactive: bool = True,
) -> str:
    """
    Return a complete SVG fragment that renders the composition trace for `case` and `cue`.

    Per the 2f redesign, the cascade is the canonical home for the cue
    display (action + force pill + via caption + safety banner) — Panel 4
    no longer exists as a separate panel. The cascade always renders:
    bands, resolution arrow, output box, horizontal force strip, and the
    safety banner when applicable.

    - reveal="none" -> compact variant (Figures 1 and 2).
    - reveal="all"  -> detailed variant with on-demand layer expanded (Figure 3).
    """
    winner_class = (
        cue.primary_firing.rule.rule_class if cue.primary_firing else None
    )
    fired_classes = {f.rule.rule_class for f in cue.supporting}
    if cue.primary_firing:
        fired_classes.add(winner_class)

    firings_by_class: dict[str, RuleFiring] = {}
    if cue.primary_firing:
        firings_by_class[cue.primary_firing.rule.rule_class] = cue.primary_firing
    for f in cue.supporting:
        firings_by_class[f.rule.rule_class] = f

    bands = "\n".join(
        _render_band(
            rule_class=cls,
            fired=cls in fired_classes,
            is_winner=cls == winner_class,
            y=_band_y(i),
            firing=firings_by_class.get(cls),
            interactive=interactive,
        )
        for i, cls in enumerate(_CLASS_ORDER)
    )

    if winner_class is not None:
        resolution = _render_resolution(
            _CLASS_ORDER.index(winner_class),
            interactive=interactive,
        )
    else:
        resolution = '  <g class="resolution"></g>'

    primary_class = cue.primary_firing.rule.rule_class if cue.primary_firing else None
    output = _render_output(cue.primary_action, cue.primary_force, primary_class)
    scale = _render_force_strip(cue, width)
    # Safety banner shows the textual rationale ("Force raised from X to Y" +
    # reason). The visual lift arrow lives inside _render_force_strip; the
    # two together show what happened and why.
    safety = _render_safety_banner(cue, width)
    style = render_style("cascade_styles.css") if css else ""
    script = _render_script() if interactive else ""
    defs = _render_defs()

    svg_body = f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" class="cascade" data-reveal="{reveal}" xmlns="http://www.w3.org/2000/svg">
{defs}
  {style}
  <g class="back-references"></g>
  <g class="cascade-bands">
{bands}
  </g>
{resolution}
{output}
{scale}
{safety}
</svg>'''

    if interactive:
        return f'<div class="cascade-wrapper">\n{svg_body}\n{script}\n</div>'
    return svg_body
