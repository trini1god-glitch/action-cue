"""Panel 1 — case input renderer.

Two public functions:
    render_case_input(case)   — full Panel 1 SVG.
    render_interval_bar(case) — the interval bar alone, standalone-renderable.

`render_interval_bar` is shared with the §7 three-way comparison's
middle column (used directly by viz/composite.py in 2e), which is why
it carries its own viewBox and its own CSS scope (`.interval-bar`).
"""

import html

from models import Case
from ._common import render_style, wrap_text


# --- Outer panel layout (in viewBox units) ---
_PANEL_PAD_X = 16
_IDENTITY_Y = 24        # baseline for badge and domain tag

_BADGE_X = _PANEL_PAD_X
_BADGE_Y_TOP = 10
_BADGE_W = 26
_BADGE_H = 22

_DOMAIN_X = _BADGE_X + _BADGE_W + 8

_SECTION_LABEL_Y = 58   # "AI risk score"
_SCORE_VALUE_Y = 90     # the score number floating above the bar
_BAR_TOP_Y = 100        # the bar group's translate-y
_THRESHOLD_LABEL_Y = 158  # under the bar

_DESCRIPTION_Y = 188

# --- Interval bar layout (standalone viewBox) ---
_BAR_PAD_X = 12
_BAR_TRACK_Y = 22
_BAR_TRACK_HEIGHT = 8
_BAR_TICK_OVERHANG = 6   # how far the threshold tick extends above/below the track
_BAR_MARKER_R = 5
_BAR_ENDPOINT_LABEL_Y = 50


def _to_x(value: float, inner_width: int, x_offset: int) -> int:
    """Map a [0, 1] value to an SVG x-coordinate inside an inner span."""
    return x_offset + int(round(value * inner_width))


def render_interval_bar(case: Case, *, width: int = 320, height: int = 56,
                        css: bool = True) -> str:
    """The risk interval bar alone: shaded interval band, threshold tick, point-estimate marker.

    Returns a complete <svg> fragment with its own viewBox so it can be
    rendered standalone (used directly in the three-way comparison's
    middle column) or embedded inside another panel via <g transform="translate(...)">.

    `css=True` (default) emits an inline <style> block so the standalone
    caller (e.g. ui/comparison.py) gets the bar styled. The embedded use
    inside render_case_input passes `css=False` to avoid double-injection
    — Panel 1 loads the same stylesheet at the panel level.
    """
    low, high = case.risk_interval
    threshold = case.decision_threshold
    score = case.risk_score

    inner_width = width - 2 * _BAR_PAD_X
    x_low = _to_x(low, inner_width, _BAR_PAD_X)
    x_high = _to_x(high, inner_width, _BAR_PAD_X)
    x_threshold = _to_x(threshold, inner_width, _BAR_PAD_X)
    x_score = _to_x(score, inner_width, _BAR_PAD_X)

    track_y = _BAR_TRACK_Y
    track_mid_y = track_y + _BAR_TRACK_HEIGHT // 2
    tick_top = track_y - _BAR_TICK_OVERHANG
    tick_bot = track_y + _BAR_TRACK_HEIGHT + _BAR_TICK_OVERHANG

    style = render_style("case_input_styles.css") if css else ""

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" class="interval-bar" xmlns="http://www.w3.org/2000/svg">
  {style}
  <rect class="bar-track" x="{_BAR_PAD_X}" y="{track_y}" width="{inner_width}" height="{_BAR_TRACK_HEIGHT}" rx="2" />
  <rect class="bar-interval" x="{x_low}" y="{track_y}" width="{x_high - x_low}" height="{_BAR_TRACK_HEIGHT}" rx="2" />
  <line class="threshold-tick" x1="{x_threshold}" y1="{tick_top}" x2="{x_threshold}" y2="{tick_bot}" />
  <circle class="score-marker" cx="{x_score}" cy="{track_mid_y}" r="{_BAR_MARKER_R}" />
  <text class="endpoint-label" x="{_BAR_PAD_X}" y="{_BAR_ENDPOINT_LABEL_Y}" text-anchor="start">0.0</text>
  <text class="endpoint-label" x="{_BAR_PAD_X + inner_width}" y="{_BAR_ENDPOINT_LABEL_Y}" text-anchor="end">1.0</text>
</svg>'''


def _render_identity(case: Case) -> str:
    case_id = html.escape(case.id)
    domain = html.escape(case.domain)
    badge_center_x = _BADGE_X + _BADGE_W // 2
    return f'''  <rect class="case-badge" x="{_BADGE_X}" y="{_BADGE_Y_TOP}" width="{_BADGE_W}" height="{_BADGE_H}" rx="4" />
  <text class="case-badge-id" x="{badge_center_x}" y="{_IDENTITY_Y + 2}" text-anchor="middle">{case_id}</text>
  <text class="domain-tag" x="{_DOMAIN_X}" y="{_IDENTITY_Y}">{domain}</text>'''


def _render_score_label(case: Case, panel_width: int, bar_inner_width: int) -> str:
    """The score value rendered as a label above the score marker's x-position.

    `panel_width` is the outer panel viewBox width; `bar_inner_width` is the
    bar's internal usable width (matches the value used in render_interval_bar).
    The marker sits inside the bar's <g translate>, but we compute the score's
    panel-space x by adding the bar's translate offset (_PANEL_PAD_X) and the
    bar's internal padding (_BAR_PAD_X).
    """
    x_score_in_panel = _PANEL_PAD_X + _to_x(case.risk_score, bar_inner_width, _BAR_PAD_X)
    return (
        f'  <text class="score-value" x="{x_score_in_panel}" y="{_SCORE_VALUE_Y}" '
        f'text-anchor="middle">{case.risk_score:.2f}</text>'
    )


def _render_threshold_label(case: Case, bar_inner_width: int) -> str:
    """The 'Threshold 0.60' label sitting under the threshold tick."""
    x_threshold_in_panel = _PANEL_PAD_X + _to_x(case.decision_threshold, bar_inner_width, _BAR_PAD_X)
    return (
        f'  <text class="threshold-label" x="{x_threshold_in_panel}" y="{_THRESHOLD_LABEL_Y}" '
        f'text-anchor="middle">Threshold {case.decision_threshold:.2f}</text>'
    )


def _render_description(case: Case, panel_width: int) -> str:
    """Multi-line wrapped description at the bottom of the panel."""
    inner_width = panel_width - 2 * _PANEL_PAD_X
    max_chars = max(20, inner_width // 6)  # ~6px per char at 12px font
    lines = wrap_text(html.escape(case.description), max_chars=max_chars)
    tspans = "".join(
        f'<tspan x="{_PANEL_PAD_X}" dy="{0 if i == 0 else 14}">{line}</tspan>'
        for i, line in enumerate(lines)
    )
    return f'  <text class="case-description" x="{_PANEL_PAD_X}" y="{_DESCRIPTION_Y}">{tspans}</text>'


def render_case_input(case: Case, *, width: int = 360, height: int = 240,
                      css: bool = True, interactive: bool = False) -> str:
    """Panel 1 SVG: case identity strip, AI risk score (as a label on the bar),
    interval bar with threshold tick, threshold label, description.

    `interactive` is part of the shared signature for the compositor in 2e;
    Panel 1 has no interactive affordances and ignores it.
    """
    bar_width = width - 2 * _PANEL_PAD_X
    bar_inner_width = bar_width - 2 * _BAR_PAD_X

    style = render_style("case_input_styles.css") if css else ""
    identity = _render_identity(case)
    section_label = (
        f'  <text class="section-label" x="{_PANEL_PAD_X}" y="{_SECTION_LABEL_Y}">AI risk score</text>'
    )
    score_label = _render_score_label(case, width, bar_inner_width)
    bar = render_interval_bar(case, width=bar_width, height=56, css=False)
    bar_translated = f'  <g transform="translate({_PANEL_PAD_X}, {_BAR_TOP_Y})">\n{bar}\n  </g>'
    threshold_label = _render_threshold_label(case, bar_inner_width)
    description = _render_description(case, width)

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" class="case-input" xmlns="http://www.w3.org/2000/svg">
  {style}
{identity}
{section_label}
{score_label}
{bar_translated}
{threshold_label}
{description}
</svg>'''
