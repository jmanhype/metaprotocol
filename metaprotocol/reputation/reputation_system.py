from __future__ import annotations

from datetime import UTC, datetime

from ..types import CollaborationRating, ReputationRecord, ReputationSnapshot
from ..store import SQLiteStore


class ReputationSystem:
    def __init__(self, store: SQLiteStore, min_collaborations_for_trust: int = 3) -> None:
        self.store = store
        self.min_collaborations_for_trust = min_collaborations_for_trust

    def get_profile(self, agent_id: str) -> ReputationRecord:
        rows = self.store.query("SELECT payload_json FROM reputation WHERE agent_id = ?", (agent_id,))
        if not rows:
            profile = ReputationRecord(agent_id=agent_id)
            self._save(profile)
            return profile
        return ReputationRecord.model_validate(self.store.loads_json(rows[0]["payload_json"]))

    def _save(self, profile: ReputationRecord) -> None:
        self.store.execute(
            """
            INSERT INTO reputation(agent_id, payload_json) VALUES (?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (profile.agent_id, self.store.dumps_json(profile.model_dump(mode="json"))),
        )

    def record_outcome(
        self,
        agent_id: str,
        partner_id: str,
        collaboration_id: str,
        success: bool,
        partner_rating: float,
    ) -> ReputationRecord:
        profile = self.get_profile(agent_id)
        profile.total_collaborations += 1
        if success:
            profile.successful_collaborations += 1
        profile.success_rate = profile.successful_collaborations / max(1, profile.total_collaborations)

        if partner_id not in profile.partners:
            profile.partners.append(partner_id)

        rating = CollaborationRating(
            rater_agent_id=partner_id,
            rated_agent_id=agent_id,
            collaboration_id=collaboration_id,
            score=partner_rating,
        )
        profile.recent_ratings.append(rating)
        profile.recent_ratings = profile.recent_ratings[-50:]

        avg_rating = sum(r.score for r in profile.recent_ratings) / len(profile.recent_ratings)
        profile.avg_partner_satisfaction = avg_rating

        delta = 0.0
        delta += 3.0 if success else -4.0
        delta += (partner_rating - 2.5) * 1.2
        profile.reputation_score = max(0.0, min(100.0, profile.reputation_score + delta))
        profile.is_verified = profile.successful_collaborations >= self.min_collaborations_for_trust
        profile.last_updated = datetime.now(UTC)
        profile.reputation_history.append(
            ReputationSnapshot(
                score=profile.reputation_score,
                timestamp=profile.last_updated,
                event="collaboration_completed" if success else "collaboration_failed",
            )
        )

        self._save(profile)
        return profile

    def detect_sybil(
        self,
        min_mutual_collaborations: int = 5,
        exclusivity_threshold: float = 0.8,
    ) -> list[str]:
        rows = self.store.query("SELECT payload_json FROM reputation")
        records = [
            ReputationRecord.model_validate(self.store.loads_json(row["payload_json"]))
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

    def apply_decay(self, toward: float = 50.0, decay_rate: float = 0.05) -> None:
        rows = self.store.query("SELECT payload_json FROM reputation")
        for row in rows:
            profile = ReputationRecord.model_validate(self.store.loads_json(row["payload_json"]))
            profile.reputation_score += (toward - profile.reputation_score) * decay_rate
            profile.last_updated = datetime.now(UTC)
            profile.reputation_history.append(
                ReputationSnapshot(score=profile.reputation_score, timestamp=profile.last_updated, event="decay")
            )
            self._save(profile)
