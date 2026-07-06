"""Shared helpers for all viz/ panel renderers."""

from pathlib import Path


def bool_attr(value: bool) -> str:
    """Convert a Python bool to a lowercase SVG/HTML `data-*` attribute value."""
    return "true" if value else "false"


def wrap_text(text: str, max_chars: int) -> list[str]:
    """Word-wrap a string into lines no longer than max_chars.
    Never breaks a word; if a single word exceeds max_chars it sits on its own line."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_style(filename: str) -> str:
    """Read a CSS file from viz/ and return it wrapped in <style> tags.
    Pass just the filename — e.g., 'cascade_styles.css' — not a full path."""
    css = (Path(__file__).parent / filename).read_text()
    return f'<style>{css}</style>'
