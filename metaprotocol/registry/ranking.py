"""Ranking and composite score calculation for discovery results."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import DiscoveryMatch


def compute_composite_score(
    match: "DiscoveryMatch",
    weights: dict[str, float] | None = None,
) -> float:
    """Compute composite score from discovery match components."""
    weights = weights or {
        "relevance": 0.4,
        "reputation": 0.3,
        "success_rate": 0.2,
        "cost": 0.1,
    }

    relevance = match.relevance_score * weights.get("relevance", 0.4)
    reputation = match.reputation_score * weights.get("reputation", 0.3)
    success = match.success_rate * weights.get("success_rate", 0.2)

    max_cost = 5.0
    cost_component = 1.0 / (1.0 + match.cost_per_use / max_cost)
    cost = cost_component * weights.get("cost", 0.1)

    return relevance + reputation + success + cost


def rank_matches(matches: list["DiscoveryMatch"], weights: dict[str, float] | None = None) -> list["DiscoveryMatch"]:
    """Rank matches by composite score."""
    for match in matches:
        match.overall_score = compute_composite_score(match, weights)

    return sorted(matches, key=lambda m: m.overall_score, reverse=True)
