from dataclasses import dataclass, field
from typing import Optional, Callable


@dataclass
class Case:
    id: str  #  "A", "B", ..., "CR", "DR"
    domain: str  #  "healthcare" | "credit_risk" | "disaster"
    description: str #  human-readable case summary
    risk_score: float  #  0.0–1.0
    risk_interval: tuple[float, float] #  (low, high)
    decision_threshold: float  #  action threshold


    # Uncertainty signal (pre-computed for the demo)
    has_missing_critical: bool = False
    missing_fields: list[str] = field(default_factory=list)
    is_outside_scope: bool = False
    scope_reason: Optional[str] = None
    has_explanation_instability: bool = False
    explanation_disagreement: Optional[str] = None

    # Decision context (drives the safety modifier)
    is_high_harm: bool = False
    is_low_reversibility: bool = False

    # Workflow context
    expected_actor: str = "clinician" #  role to whom cues are addressed


@dataclass
class UncertaintySignal:
    name: str   #  "missing_critical_data" — stable identifier
    label: str #  display label
    detected: bool
    detail: Optional[str] = None  #  e.g., "oxygen saturation missing"


@dataclass
class Rule:
    id: str  #  "validity_outside_scope"
    rule_class: str #  "validity" | "completion" | "sensitivity" | "interpretation"
    precedence: int #  1=validity, 2=completion, 3=sensitivity, 4=interpretation
    description: str #  human-readable
    base_action: str #  one of the six action families
    base_force: str  #  one of the four force levels
    signal_name: str #  the UncertaintySignal name this rule binds to
    trigger: Callable[[Case], bool] #  pure function: does this rule fire for this case?
    rationale: Callable[[Case], str]  #  pure function: produce the rationale text


@dataclass
class RuleFiring:
    rule: Rule
    rendered_rationale: str
    base_action: str
    base_force: str
    triggering_signal: Optional[UncertaintySignal] = None


@dataclass
class Cue:
    primary_action: str
    primary_force: str
    primary_rationale: str
    primary_actor: str
    supporting: list[RuleFiring] = field(default_factory=list)
    safety_modified: bool = False
    safety_reason: Optional[str] = None
    primary_firing: Optional[RuleFiring] = None  #  the winning RuleFiring (None if no firings)