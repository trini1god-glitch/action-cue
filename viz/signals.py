"""Panel 2 — uncertainty signals renderer.

One public function:
    render_signals(case) — full Panel 2 SVG.

Layout splits into two stacked groups:
    - Detected rail (top): one ~36-unit row per fired signal, with a
      vermillion accent strip, filled indicator, label, and wrapped
      detail text. Weighty so the *cause* of cascade firing reads as
      load-bearing.
    - Undetected list (bottom, under a dashed divider): one ~18-unit
      row per unfired signal, hollow indicator + label only.

Every row carries id `signal-row-{name}` so the cascade's
back-reference layer (2e / Week 3) can target it.

A synthetic fifth signal `decision_context` is composed from
case.is_high_harm + case.is_low_reversibility. It gets
`data-kind="context"` and a triangle indicator (vs. circles for the
four detection signals).
"""

from models import Case, UncertaintySignal
from rules import signal_for
from viz._common import render_style, wrap_text
import html


# --- Signal order (fixed; partition preserves this order in each group) ---
_SIGNAL_NAMES = [
    "missing_critical_data",
    "out_of_scope",
    "threshold_crossing",
    "explanation_instability",
]

# --- Outer panel layout ---
_PANEL_PAD_X = 16
_SECTION_LABEL_Y = 20

# Detected rail (variable height — depends on count)
_RAIL_TOP_Y = 38
_RAIL_ROW_HEIGHT = 36
_RAIL_ROW_GAP = 4
_RAIL_ACCENT_X = _PANEL_PAD_X
_RAIL_ACCENT_W = 3
_RAIL_INDICATOR_CX = _PANEL_PAD_X + 14   # 3-unit strip + 11-unit gap
_RAIL_LABEL_X = _PANEL_PAD_X + 24
_RAIL_LABEL_DY = 14                       # label baseline relative to row top
_RAIL_DETAIL_DY = 28                      # detail baseline relative to row top

# Undetected list (compact)
_LIST_ROW_HEIGHT = 18
_LIST_INDICATOR_CX = _PANEL_PAD_X + 6
_LIST_LABEL_X = _PANEL_PAD_X + 16
_LIST_LABEL_DY = 12

_INDICATOR_R = 4
_DIVIDER_GAP_ABOVE = 10   # gap between bottom of last rail row and the divider line
_DIVIDER_GAP_BELOW = 14   # gap between the divider caption and the first list row


# ---------------------------------------------------------------------------
# Signal collection
# ---------------------------------------------------------------------------

def _decision_context_signal(case: Case) -> UncertaintySignal:
    """Synthesize the fifth row from case.is_high_harm + case.is_low_reversibility.

    Detected if either flag is true; detail composes from whichever flags
    are set, e.g. "high harm, low reversibility".
    """
    parts: list[str] = []
    if case.is_high_harm:
        parts.append("high harm")
    if case.is_low_reversibility:
        parts.append("low reversibility")
    return UncertaintySignal(
        name="decision_context",
        label="Decision context",
        detected=bool(parts),
        detail=", ".join(parts) if parts else None,
    )


def _signal_kind(signal: UncertaintySignal) -> str:
    """Categorical class for indicator shape swap. The other four signals
    describe the inference; decision_context describes deployment stakes."""
    return "context" if signal.name == "decision_context" else "detection"


# ---------------------------------------------------------------------------
# Indicator markup (both shapes always emitted; CSS hides one per kind)
# ---------------------------------------------------------------------------

def _render_indicator(cx: int, cy: int) -> str:
    """Emit both a circle and a triangle sharing the same bounding box.
    CSS hides the one that doesn't match data-kind on the parent row."""
    r = _INDICATOR_R
    # Triangle: equilateral-ish, point up, centered on (cx, cy).
    tri = f"{cx},{cy - r} {cx - r},{cy + r} {cx + r},{cy + r}"
    return (
        f'<circle class="signal-indicator" cx="{cx}" cy="{cy}" r="{r}" />'
        f'<polygon class="signal-indicator" points="{tri}" />'
    )


# ---------------------------------------------------------------------------
# Row renderers
# ---------------------------------------------------------------------------

def _render_rail_row(signal: UncertaintySignal, y: int, panel_width: int) -> str:
    """One detected-rail row: vermillion accent strip, indicator, label, wrapped detail."""
    cy = y + _RAIL_ROW_HEIGHT // 2 - 4   # indicator sits roughly on the label's optical line
    label_y = y + _RAIL_LABEL_DY
    detail_y = y + _RAIL_DETAIL_DY

    label = html.escape(signal.label)
    name = html.escape(signal.name, quote=True)
    kind = _signal_kind(signal)

    # Wrap detail text. Detail is shown only on detected rows; if it's None
    # (some cases — e.g. threshold_crossing — always set detail, others may not),
    # we omit the tspan block.
    detail_block = ""
    if signal.detail:
        inner_w = panel_width - _RAIL_LABEL_X - _PANEL_PAD_X
        max_chars = max(20, inner_w // 6)
        lines = wrap_text(html.escape(signal.detail), max_chars=max_chars)
        tspans = "".join(
            f'<tspan x="{_RAIL_LABEL_X}" dy="{0 if i == 0 else 11}">{line}</tspan>'
            for i, line in enumerate(lines)
        )
        detail_block = (
            f'    <text class="signal-detail" x="{_RAIL_LABEL_X}" y="{detail_y}">{tspans}</text>'
        )

    return f'''  <g class="signal-row" id="signal-row-{name}" data-detected="true" data-kind="{kind}">
    <rect class="rail-accent" x="{_RAIL_ACCENT_X}" y="{y}" width="{_RAIL_ACCENT_W}" height="{_RAIL_ROW_HEIGHT}" />
    {_render_indicator(_RAIL_INDICATOR_CX, cy)}
    <text class="signal-label" x="{_RAIL_LABEL_X}" y="{label_y}">{label}</text>
{detail_block}
  </g>'''


def _render_list_row(signal: UncertaintySignal, y: int) -> str:
    """One undetected-list row: hollow indicator + label only."""
    cy = y + _LIST_ROW_HEIGHT // 2
    label_y = y + _LIST_LABEL_DY
    label = html.escape(signal.label)
    name = html.escape(signal.name, quote=True)
    kind = _signal_kind(signal)

    return f'''  <g class="signal-row" id="signal-row-{name}" data-detected="false" data-kind="{kind}">
    {_render_indicator(_LIST_INDICATOR_CX, cy)}
    <text class="signal-label" x="{_LIST_LABEL_X}" y="{label_y}">{label}</text>
  </g>'''


def _render_divider(y: int, panel_width: int) -> str:
    """Dashed horizontal rule + 'not detected:' caption sitting just above it."""
    x1 = _PANEL_PAD_X
    x2 = panel_width - _PANEL_PAD_X
    caption_y = y - 4
    return f'''  <g class="undetected-divider-group">
    <text class="undetected-caption" x="{x1}" y="{caption_y}">not detected</text>
    <line class="undetected-divider" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" />
  </g>'''


# ---------------------------------------------------------------------------
# Public renderer
# ---------------------------------------------------------------------------

def render_signals(case: Case, *, width: int = 360, height: int = 220,
                   css: bool = True, interactive: bool = False,
                   responsive: bool = False) -> str:
    """Panel 2 SVG: detected-rail (fired signals, weighty) over
    undetected-list (unfired signals, compact), under a section label.

    `interactive` is accepted for compositor signature compatibility and
    ignored — Panel 2 has no JS affordances in 2d-2.

    `responsive=True` makes the outer <svg> scale with its container (live demo).
    Figures pass responsive=False (default) to keep fixed dimensions.
    """
    # Collect five signals in fixed order.
    signals: list[UncertaintySignal] = [
        s for s in (signal_for(case, n) for n in _SIGNAL_NAMES) if s is not None
    ]
    signals.append(_decision_context_signal(case))

    detected = [s for s in signals if s.detected]
    undetected = [s for s in signals if not s.detected]

    # Lay out the rail.
    rail_rows: list[str] = []
    y = _RAIL_TOP_Y
    for signal in detected:
        rail_rows.append(_render_rail_row(signal, y, width))
        y += _RAIL_ROW_HEIGHT + _RAIL_ROW_GAP

    # Divider sits below the last rail row (or below the section label
    # when nothing fired).
    if detected:
        divider_y = y - _RAIL_ROW_GAP + _DIVIDER_GAP_ABOVE
    else:
        divider_y = _RAIL_TOP_Y + _DIVIDER_GAP_ABOVE
    divider = _render_divider(divider_y, width)

    # Lay out the undetected list.
    list_rows: list[str] = []
    y = divider_y + _DIVIDER_GAP_BELOW
    for signal in undetected:
        list_rows.append(_render_list_row(signal, y))
        y += _LIST_ROW_HEIGHT

    style = render_style("signals_styles.css") if css else ""
    section_label = (
        f'  <text class="section-label" x="{_PANEL_PAD_X}" y="{_SECTION_LABEL_Y}">UNCERTAINTY SIGNALS</text>'
    )
    rail_svg = "\n".join(rail_rows)
    list_svg = "\n".join(list_rows)
    svg_dims = (
        f'width="100%" height="auto" preserveAspectRatio="xMidYMid meet" '
        f'style="max-width:{width}px"'
    ) if responsive else f'width="{width}" height="{height}"'

    return f'''<svg viewBox="0 0 {width} {height}" {svg_dims} class="signals" xmlns="http://www.w3.org/2000/svg">
  {style}
{section_label}
{rail_svg}
{divider}
{list_svg}
</svg>'''
