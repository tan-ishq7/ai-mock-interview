"""
Factual accuracy scorer for Phase 4.

Scores are based on LLM-judged evaluation of each answer against
ground truth, with partial credit.
"""

from dataclasses import dataclass


@dataclass
class FactualScore:
    correct: int
    partial: int
    incorrect: int
    total: int
    accuracy_pct: float  # 0-100, with partial credit


def compute_factual_score(
    evaluations: list[dict],
) -> FactualScore:
    """Compute factual accuracy from per-question evaluations.

    Each evaluation dict has an 'accuracy_score' (0-10) from the LLM judge.

    Scoring:
        >= 7: correct (full credit)
        >= 4: partial (half credit)
        < 4: incorrect (no credit)
    """
    correct = 0
    partial = 0
    incorrect = 0
    total = len(evaluations)

    for ev in evaluations:
        score = ev.get("accuracy_score", 0)
        if score >= 7:
            correct += 1
        elif score >= 4:
            partial += 1
        else:
            incorrect += 1

    # Accuracy with partial credit: correct=1, partial=0.5, incorrect=0
    if total > 0:
        accuracy = ((correct + partial * 0.5) / total) * 100
    else:
        accuracy = 0.0

    return FactualScore(
        correct=correct,
        partial=partial,
        incorrect=incorrect,
        total=total,
        accuracy_pct=round(accuracy, 1),
    )
