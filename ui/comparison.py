import streamlit as st
import streamlit.components.v1 as components

from engine import compose_cue
from models import Case
from rules import RULES
from viz.case_input import render_interval_bar
from viz.cascade import render_cascade


def render(case: Case) -> None:
    col_conf, col_unc, col_ac = st.columns([1, 1, 2])

    with col_conf:
        st.subheader("Confidence-only")
        st.metric("AI risk score", f"{case.risk_score:.2f}")
        st.caption(f"Decision threshold: {case.decision_threshold:.2f}")

    with col_unc:
        st.subheader("Uncertainty display only")
        st.metric("AI risk score", f"{case.risk_score:.2f}")
        components.html(render_interval_bar(case, responsive=True), height=80, scrolling=False)
        st.caption(f"Decision threshold: {case.decision_threshold:.2f}")

    with col_ac:
        st.subheader("ActionCue (process transparency)")
        cue = compose_cue(case, RULES)
        components.html(render_cascade(case, cue, responsive=True), height=560, scrolling=False)
