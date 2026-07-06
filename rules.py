from models import Rule, Case, UncertaintySignal
from typing import Optional


RULES = [
    Rule(
        id="validity_outside_scope",
        rule_class="validity",
        precedence=1,
        description="Case falls outside the model's validated population or operating envelope.",
        base_action="escalate",
        base_force="mandatory",
        signal_name="out_of_scope",
        trigger=lambda c: c.is_outside_scope,
        rationale=lambda c: f"Case is outside the validated scope: {c.scope_reason}.",
    ),
    Rule(
        id="completion_missing_critical",
        rule_class="completion",
        precedence=2,
        description="A field required for the decision is missing or unreliable.",
        base_action="complete",
        base_force="mandatory",
        signal_name="missing_critical_data",
        trigger=lambda c: c.has_missing_critical,
        rationale=lambda c: f"Critical inputs missing: {', '.join(c.missing_fields)}.",
    ),
    Rule(
        id="sensitivity_threshold_crossing",
        rule_class="sensitivity",
        precedence=3,
        description="The risk interval contains the action threshold.",
        base_action="inspect",
        base_force="strong",
        signal_name="threshold_crossing",
        trigger=lambda c: c.risk_interval[0] <= c.decision_threshold <= c.risk_interval[1],
        rationale=lambda c: (
            f"Risk interval ({c.risk_interval[0]:.2f}–{c.risk_interval[1]:.2f}) "
            f"crosses the action threshold ({c.decision_threshold:.2f})."
        ),
    ),
    Rule(
        id="interpretation_explanation_instability",
        rule_class="interpretation",
        precedence=4,
        description="Explanations or models disagree across runs.",
        base_action="inspect",
        base_force="advisory",
        signal_name="explanation_instability",
        trigger=lambda c: c.has_explanation_instability,
        rationale=lambda c: f"Explanation instability detected: {c.explanation_disagreement}.",
    ),
]


def signal_for(case: Case, signal_name: str) -> Optional[UncertaintySignal]:
    if signal_name == "missing_critical_data":
        return UncertaintySignal(
            name=signal_name,
            label="Missing critical data",
            detected=case.has_missing_critical,
            detail=", ".join(case.missing_fields) if case.missing_fields else None,
        )
    if signal_name == "out_of_scope":
        return UncertaintySignal(
            name=signal_name,
            label="Out of scope",
            detected=case.is_outside_scope,
            detail=case.scope_reason,
        )
    if signal_name == "threshold_crossing":
        return UncertaintySignal(
            name=signal_name,
            label="Interval crosses threshold",
            detected=case.risk_interval[0] <= case.decision_threshold <= case.risk_interval[1],
            detail=f"interval ({case.risk_interval[0]:.2f}–{case.risk_interval[1]:.2f}) contains threshold {case.decision_threshold:.2f}",
        )
    if signal_name == "explanation_instability":
        return UncertaintySignal(
            name=signal_name,
            label="Explanation instability",
            detected=case.has_explanation_instability,
            detail=case.explanation_disagreement,
        )
    return None