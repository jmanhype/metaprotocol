"""Weighted moving average reputation scoring."""

from __future__ import annotations

from ..types import ReputationRecord


def compute_reputation_score(
    profile: ReputationRecord,
    collaboration_outcome: float,
    partner_rating: float,
    alpha: float = 0.85,
) -> float:
    """
    Compute new reputation score using weighted moving average.

    Args:
        profile: Current reputation profile
        collaboration_outcome: Normalized outcome (0-1)
        partner_rating: Partner rating (0-5)
        alpha: Weight for history (higher = more weight on history)

    Returns:
        New reputation score (0-100)
    """
    normalized_rating = (partner_rating - 2.5) / 2.5

    score_delta = 0.0
    score_delta += 3.0 if collaboration_outcome >= 0.5 else -4.0
    score_delta += normalized_rating * 1.2

    new_score = (profile.reputation_score * alpha) + (score_delta * (1 - alpha))
    return max(0.0, min(100.0, new_score))


def compute_avg_rating(ratings: list[float]) -> float:
    """Compute average rating from a list of ratings."""
    if not ratings:
        return 0.0
    return sum(ratings) / len(ratings)
