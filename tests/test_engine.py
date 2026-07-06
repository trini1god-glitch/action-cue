import pytest
from models import Rule, Case
from rules import RULES
from engine import compose_cue, CONSTRAINT_MATRIX
from cases.healthcare import CASE_A, CASE_B, CASE_C, CASE_D, CASE_E
from cases.cross_domain import CASE_CR, CASE_DR


# ---------- Per-case behavioral tests ----------

def test_case_a_proceeds():
    cue = compose_cue(CASE_A, RULES)
    assert cue.primary_action == "proceed"
    assert cue.primary_force == "advisory"

def test_case_b_inspects():
    cue = compose_cue(CASE_B, RULES)
    assert cue.primary_action == "inspect"
    assert cue.primary_force == "strong"

def test_case_c_completes():
    cue = compose_cue(CASE_C, RULES)
    assert cue.primary_action == "complete"
    assert cue.primary_force == "mandatory"

def test_case_d_escalates():
    cue = compose_cue(CASE_D, RULES)
    assert cue.primary_action == "escalate"
    assert cue.primary_force == "mandatory"
    assert not cue.safety_modified

def test_case_e_blocks_via_safety_modifier():
    cue = compose_cue(CASE_E, RULES)
    assert cue.primary_action == "escalate"
    assert cue.primary_force == "blocking"  # raised from mandatory
    assert cue.safety_modified

def test_case_cr_validity_dominates_completion():
    cue = compose_cue(CASE_CR, RULES)
    assert cue.primary_action == "escalate"
    assert any(f.rule.rule_class == "completion" for f in cue.supporting)

def test_case_dr_safety_raises_strong_to_mandatory():
    cue = compose_cue(CASE_DR, RULES)
    assert cue.primary_firing.rule.rule_class == "sensitivity"
    assert cue.primary_force == "mandatory"
    assert cue.safety_modified


# ---------- Engine invariants ----------

def test_constraint_matrix_enforced_for_all_cases():
    """Every composed cue must satisfy the constraint matrix."""
    for case in [CASE_A, CASE_B, CASE_C, CASE_D, CASE_E, CASE_CR, CASE_DR]:
        cue = compose_cue(case, RULES)
        assert cue.primary_force in CONSTRAINT_MATRIX[cue.primary_action], (
            f"Case {case.id}: invalid combination ({cue.primary_action}, {cue.primary_force})"
        )

def test_invalid_combination_raises():
    """A rule definition that produces a forbidden pairing must raise at composition time."""
    bad_case = Case(
        id="BAD", domain="test",
        description="forces a forbidden pairing",
        risk_score=0.5, risk_interval=(0.4, 0.6),
        decision_threshold=0.5,
        is_outside_scope=True, scope_reason="test",
    )
    bad_rule = Rule(
        id="bad", rule_class="validity", precedence=1,
        description="bad", base_action="escalate",
        base_force="advisory", # forbidden
        signal_name="out_of_scope",
        trigger=lambda c: c.is_outside_scope,
        rationale=lambda c: "bad",
    )
    with pytest.raises(ValueError, match="Invalid"):
        compose_cue(bad_case, [bad_rule])


def test_within_class_plurality_raises():
    """Two rules of the same class firing simultaneously must raise."""
    case = Case(
        id="T",
        domain="test",
        description="trigger both validity rules",
        risk_score=0.5,
        risk_interval=(0.4, 0.6),
        decision_threshold=0.5,
        is_outside_scope=True,
        scope_reason="test",
    )
    r1 = Rule(
        id="v1",
        rule_class="validity",
        precedence=1,
        description="v1",
        base_action="escalate",
        base_force="mandatory",
        signal_name="out_of_scope",
        trigger=lambda c: c.is_outside_scope,
        rationale=lambda c: "v1",
    )
    r2 = Rule(
        id="v2",
        rule_class="validity",
        precedence=1,
        description="v2",
        base_action="escalate",
        base_force="mandatory",
        signal_name="out_of_scope",
        trigger=lambda c: c.is_outside_scope,
        rationale=lambda c: "v2",
    )
    with pytest.raises(AssertionError, match="plurality"):
        compose_cue(case, [r1, r2])

def test_triggering_signal_attached_to_firings():
    """Every RuleFiring must carry the triggering UncertaintySignal."""
    cue = compose_cue(CASE_CR, RULES)
    assert cue.primary_firing.triggering_signal is not None
    for f in cue.supporting:
        assert f.triggering_signal is not None
