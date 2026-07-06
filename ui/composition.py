import streamlit.components.v1 as components

from engine import compose_cue
from models import Case
from rules import RULES
from viz.cascade import render_cascade


def render(case: Case) -> None:
    cue = compose_cue(case, RULES)
    components.html(render_cascade(case, cue, responsive=True), height=560, scrolling=False)
