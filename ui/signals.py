import streamlit.components.v1 as components

from models import Case
from viz.signals import render_signals


def render(case: Case) -> None:
    components.html(render_signals(case), height=220, scrolling=False)
