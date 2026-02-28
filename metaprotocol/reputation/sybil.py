"""Sybil resistance via partner graph analysis."""

from __future__ import annotations

from ..store.base import AbstractProtocolStore
from ..types import ReputationRecord


def detect_sybil_rings(
    store: AbstractProtocolStore,
    min_mutual_collaborations: int = 5,
    exclusivity_threshold: float = 0.8,
) -> list[str]:
    """
    Detect colluding reputation rings via partner graph analysis.

    Flags agents that form closed loops with high exclusivity.

    Args:
        store: Storage backend
        min_mutual_collaborations: Minimum mutual ratings required
        exclusivity_threshold: Ratio of internal to total ratings (0-1)

    Returns:
        List of flagged agent IDs
    """
    rows = store.query("SELECT payload_json FROM reputation")
    records = [
        ReputationRecord.model_validate(store.loads_json(row["payload_json"]))
        for row in rows
    ]

    if not records:
        return []

    flagged: set[str] = set()
    records_by_id = {record.agent_id: record for record in records}

    for left in records:
        for right_id in left.partners:
            right = records_by_id.get(right_id)
            if right is None:
                continue

            if left.agent_id not in right.partners:
                continue

            left_to_right = sum(
                1 for rating in left.recent_ratings if rating.rater_agent_id == right_id
            )
            right_to_left = sum(
                1 for rating in right.recent_ratings if rating.rater_agent_id == left.agent_id
            )

            if min(left_to_right, right_to_left) < min_mutual_collaborations:
                continue

            left_exclusive = left_to_right / max(1, len(left.recent_ratings))
            right_exclusive = right_to_left / max(1, len(right.recent_ratings))

            if left_exclusive >= exclusivity_threshold and right_exclusive >= exclusivity_threshold:
                flagged.add(left.agent_id)
                flagged.add(right_id)

    return sorted(flagged)


def analyze_connectivity(
    store: AbstractProtocolStore,
    agent_id: str,
) -> dict[str, int]:
    """Analyze connectivity metrics for an agent."""
    rows = store.query("SELECT payload_json FROM reputation WHERE agent_id = ?", (agent_id,))
    if not rows:
        return {"partners": 0, "ratings_given": 0, "ratings_received": 0}

    profile = ReputationRecord.model_validate(store.loads_json(rows[0]["payload_json"]))

    return {
        "partners": len(profile.partners),
        "ratings_given": len(profile.recent_ratings),
        "ratings_received": len(
            [r for r in profile.recent_ratings if r.rated_agent_id == agent_id]
        ),
    }
