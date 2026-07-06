import streamlit.components.v1 as components

from models import Case
from viz.case_input import render_case_input


def render(case: Case) -> None:
    components.html(render_case_input(case), height=220, scrolling=False)
