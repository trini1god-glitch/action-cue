import streamlit as st

from rules import RULES


def render() -> None:
    rows = [
        {
            "precedence": rule.precedence,
            "class": rule.rule_class,
            "rule id": rule.id,
            "base action": rule.base_action,
            "base force": rule.base_force,
            "signal": rule.signal_name,
            "description": rule.description,
        }
        for rule in sorted(RULES, key=lambda r: r.precedence)
    ]
    st.dataframe(
        rows,
        hide_index=True,
        use_container_width=True,
        column_config={
            "precedence": st.column_config.NumberColumn(width="small"),
            "class": st.column_config.TextColumn(width="small"),
            "rule id": st.column_config.TextColumn(width="medium"),
            "base action": st.column_config.TextColumn(width="small"),
            "base force": st.column_config.TextColumn(width="small"),
            "signal": st.column_config.TextColumn(width="medium"),
            "description": st.column_config.TextColumn(width="large"),
        },
    )
    st.caption(
        f"These four rules are read directly by the rule engine without intermediate state."
    )
