"""
Socratic Depth Metric — scoring for Phases 2 and 3.

Measures how deep the candidate can go in the Russian Doll drilling
before failing to answer, plus hint recovery rate.
"""

from dataclasses import dataclass


@dataclass
class SocraticScore:
    max_depth_reached: int  # 1-5
    total_questions: int
    depth_score_pct: float  # 0-100
    hints_given: int
    hints_recovered: int
    hint_recovery_rate: float  # 0-1
    composite_score: float  # 0-100 final score


# Depth level descriptors and score weights
DEPTH_LABELS = {
    1: "Surface-level description",
    2: "Architecture / workflow explanation",
    3: "Core ML concept understanding",
    4: "Implementation tradeoffs and alternatives",
    5: "Deep theoretical + practical mastery",
}

DEPTH_SCORE_MAP = {0: 0, 1: 20, 2: 40, 3: 60, 4: 80, 5: 100}


def compute_socratic_score(
    max_depth_reached: int,
    total_questions: int,
    hints_given: int,
    hints_recovered: int,
) -> SocraticScore:
    """Compute the Socratic Depth Metric for a project deep-dive phase.

    Parameters
    ----------
    max_depth_reached:
        Highest depth level (1-5) where the candidate answered correctly.
    total_questions:
        Total number of questions asked in this phase.
    hints_given:
        Number of hints provided to the candidate.
    hints_recovered:
        Number of times the candidate answered correctly after a hint.

    Returns
    -------
    SocraticScore with all scoring components.
    """
    depth_score = DEPTH_SCORE_MAP.get(max_depth_reached, 0)
    hint_recovery_rate = (
        hints_recovered / hints_given if hints_given > 0 else 1.0
    )

    # Composite: 70% depth score + 30% hint recovery
    # If no hints were needed, that's a positive signal
    if hints_given == 0:
        composite = depth_score
    else:
        composite = (depth_score * 0.7) + (hint_recovery_rate * 100 * 0.3)

    return SocraticScore(
        max_depth_reached=max_depth_reached,
        total_questions=total_questions,
        depth_score_pct=depth_score,
        hints_given=hints_given,
        hints_recovered=hints_recovered,
        hint_recovery_rate=hint_recovery_rate,
        composite_score=round(composite, 1),
    )
