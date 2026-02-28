"""Time-based reputation decay."""

from __future__ import annotations

from ..store.base import AbstractProtocolStore
from ..utils.time import now_utc
from ..types import ReputationRecord


def apply_decay_to_profile(
    profile: ReputationRecord,
    toward: float = 50.0,
    decay_rate: float = 0.05,
) -> ReputationRecord:
    """
    Apply time-based decay to a reputation profile.

    Reputation decays toward the neutral point (50) over time.

    Args:
        profile: Reputation profile to decay
        toward: Target neutral score
        decay_rate: Rate of decay (0.05 = 5%)

    Returns:
        Updated profile
    """
    profile.reputation_score += (toward - profile.reputation_score) * decay_rate
    profile.last_updated = now_utc()

    profile.reputation_history.append({
        "score": profile.reputation_score,
        "timestamp": profile.last_updated,
        "event": "decay",
    })

    return profile


def apply_decay_all(
    store: AbstractProtocolStore,
    toward: float = 50.0,
    decay_rate: float = 0.05,
) -> int:
    """Apply decay to all reputation records in storage."""
    rows = store.query("SELECT payload_json FROM reputation")
    count = 0

    for row in rows:
        profile = ReputationRecord.model_validate(store.loads_json(row["payload_json"]))
        apply_decay_to_profile(profile, toward, decay_rate)

        store.execute(
            "INSERT OR REPLACE INTO reputation(agent_id, payload_json) VALUES (?, ?)",
            (profile.agent_id, store.dumps_json(profile.model_dump(mode="json"))),
        )
        count += 1

    return count
