from models import Case

CASE_CR = Case(
    id="CR",
    domain="credit_risk",
    description="Credit decision near regulatory threshold; applicant data partly stale.",
    risk_score=0.55,
    risk_interval=(0.42, 0.68),
    decision_threshold=0.50,
    has_missing_critical=True,
    missing_fields=["recent income verification"],
    is_outside_scope=True,
    scope_reason="applicant profile rare in lender's portfolio",
    expected_actor="loan officer / second reviewer",
)
# Expected: validity (out of scope) primary → escalate / mandatory;
# completion supporting; sensitivity also supporting.

CASE_DR = Case(
    id="DR",
    domain="disaster",
    description="Evacuation trigger with model disagreement under high harm conditions.",
    risk_score=0.65,
    risk_interval=(0.55, 0.79),
    decision_threshold=0.60,
    has_explanation_instability=True,
    explanation_disagreement="two ensemble models assign different risk categories",
    is_high_harm=True,
    is_low_reversibility=True,
    expected_actor="emergency operations coordinator",
)
# Expected: sensitivity (interval crosses threshold) primary → inspect / strong;
# interpretation supporting; safety modifier raises strong → mandatory.


