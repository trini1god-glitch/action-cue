from collections import Counter

from models import Case, Cue, Rule, RuleFiring
from rules import signal_for


ACTION_FAMILIES = ["proceed", "inspect", "complete", "reassess", "escalate", "abstain"]
FORCE_LEVELS = ["advisory", "strong", "mandatory", "blocking"]
RULE_CLASSES = ["validity", "completion", "sensitivity", "interpretation"]
PRECEDENCE = {"validity": 1, "completion": 2, "sensitivity": 3, "interpretation": 4}


CONSTRAINT_MATRIX: dict[str, set[str]] = {
    "proceed":  {"advisory"},
    "inspect":  {"advisory", "strong", "mandatory"},
    "complete": {"strong", "mandatory", "blocking"},
    "reassess": {"strong", "mandatory", "blocking"},
    "escalate": {"mandatory", "blocking"},
    "abstain":  {"blocking"},
}


def raise_force(force: str) -> str:
    idx = FORCE_LEVELS.index(force)
    return FORCE_LEVELS[min(idx + 1, len(FORCE_LEVELS) - 1)]


def validate_combination(action: str, force: str) -> None:
    if force not in CONSTRAINT_MATRIX[action]:
        raise ValueError(
            f"Invalid (action, force) combination: ({action}, {force}). "
            f"Allowed forces for {action!r}: {sorted(CONSTRAINT_MATRIX[action])}."
        )


def compose_cue(case: Case, rules: list[Rule]) -> Cue:
    # 1. Detect firings
    firings = [
        RuleFiring(
            rule=r,
            rendered_rationale=r.rationale(case),
            base_action=r.base_action,
            base_force=r.base_force,
            triggering_signal=signal_for(case, r.signal_name),
        )
        for r in rules if r.trigger(case)
    ]

    # 2. Within-class plurality assertion (Layer 2 invariant)
    class_counts = Counter(f.rule.rule_class for f in firings)
    duplicates = [cls for cls, count in class_counts.items() if count > 1]
    if duplicates:
        raise AssertionError(
            f"Within-class plurality detected in classes {duplicates}. "
            f"The framework defers within-class plurality to future work; "
            f"the demo cases must fire at most one rule per class."
        )

    # 3. No firings: proceed
    if not firings:
        cue = Cue(
            primary_action="proceed",
            primary_force="advisory",
            primary_rationale="No uncertainty conditions of decision concern detected.",
            primary_actor=case.expected_actor,
        )
        validate_combination(cue.primary_action, cue.primary_force)
        return cue

    # 4. Sort by precedence (lower = higher priority)
    firings.sort(key=lambda f: f.rule.precedence)

    # 5. Primary = highest-precedence firing; rest become supporting stack
    primary = firings[0]
    cue = Cue(
        primary_action=primary.base_action,
        primary_force=primary.base_force,
        primary_rationale=primary.rendered_rationale,
        primary_actor=case.expected_actor,
        supporting=firings[1:],
        primary_firing=primary,
    )

    # 6. Apply safety modifier
    if case.is_high_harm or case.is_low_reversibility:
        cue.primary_force = raise_force(cue.primary_force)
        cue.safety_modified = True
        reasons = []
        if case.is_high_harm:
            reasons.append("high harm")
        if case.is_low_reversibility:
            reasons.append("low reversibility")
        cue.safety_reason = " and ".join(reasons)

    # 7. Constraint matrix validation (Layer 2 invariant)
    validate_combination(cue.primary_action, cue.primary_force)

    return cue