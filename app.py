import streamlit as st

from cases.cross_domain import CASE_CR, CASE_DR
from cases.healthcare import CASE_A, CASE_B, CASE_C, CASE_D, CASE_E
from ui.case_input import render as render_case_input_panel
from ui.comparison import render as render_comparison
from ui.composition import render as render_composition_panel
from ui.rule_table import render as render_rule_table
from ui.signals import render as render_signals_panel

st.set_page_config(page_title="ActionCue", layout="wide")

ALL_CASES = (CASE_A, CASE_B, CASE_C, CASE_D, CASE_E, CASE_CR, CASE_DR)
CASE_BY_ID = {c.id: c for c in ALL_CASES}

with st.sidebar:
    st.header("ActionCue")
    mode = st.radio(
        "View",
        options=["ActionCue (full)", "Three-way comparison"],
    )
    case_id = st.selectbox(
        "Case",
        options=[c.id for c in ALL_CASES],
        index=2,
        format_func=lambda cid: f"{cid} — {CASE_BY_ID[cid].domain}",
    )

case = CASE_BY_ID[case_id]

if mode == "ActionCue (full)":
    _, top_left, top_right, _ = st.columns([1, 2, 2, 1])
    with top_left:
        render_case_input_panel(case)
    with top_right:
        render_signals_panel(case)
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        render_composition_panel(case)
else:
    render_comparison(case)

with st.expander("Rules registry", expanded=False):
    render_rule_table()
