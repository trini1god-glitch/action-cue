from models import Case




CASE_A = Case(
    id="A",
    domain="healthcare",
    description="Patient with stable vitals, complete record, profile within validated population.",
    risk_score=0.82,
    risk_interval=(0.78, 0.86),
    decision_threshold=0.60,
    expected_actor="clinician at point of care",
)
# Expected: no rules fire → proceed / advisory

CASE_B = Case(
    id="B",
    domain="healthcare",
    description="Patient with risk near the action threshold; complete record, in-scope, stable.",
    risk_score=0.62,
    risk_interval=(0.48, 0.75),
    decision_threshold=0.60,
    expected_actor="clinician at point of care",
)
# Expected: sensitivity rule fires → inspect / strong

CASE_C = Case(
    id="C",
    domain="healthcare",
    description="Patient with risk at threshold; oxygen saturation missing.",
    risk_score=0.62,
    risk_interval=(0.55, 0.69),
    decision_threshold=0.60,
    has_missing_critical=True,
    missing_fields=["oxygen saturation"],
    expected_actor="clinician at point of care",
)
# Expected: completion rule fires → complete / mandatory (sensitivity also fires; completion wins by precedence)

CASE_D = Case(
    id="D",
    domain="healthcare",
    description="Patient profile rare in training population (out of scope).",
    risk_score=0.62,
    risk_interval=(0.55, 0.69),
    decision_threshold=0.60,
    is_outside_scope=True,
    scope_reason="patient demographic underrepresented in training data",
    expected_actor="clinician at point of care",
)
# Expected: validity rule fires (sensitivity also) → escalate / mandatory

CASE_E = Case(
    id="E",
    domain="healthcare",
    description="Out-of-scope case with high harm and low reversibility.",
    risk_score=0.62,
    risk_interval=(0.55, 0.69),
    decision_threshold=0.60,
    is_outside_scope=True,
    scope_reason="patient demographic underrepresented in training data",
    is_high_harm=True,
    is_low_reversibility=True,
    expected_actor="clinician at point of care",
)