from __future__ import annotations

from datetime import UTC, datetime

from .models import DiscoveryMatch, Team, TeamAssignment, TeamFormationError, TeamInteraction, TeamStatus
from .optimizer import TeamOptimizer
from .storage import SQLiteStore


class TeamFormationEngine:
    def __init__(
        self,
        store: SQLiteStore,
        strategy: str = "greedy",
        max_team_size: int = 10,
        timeout_ms: int = 1000,
    ) -> None:
        self.store = store
        self.optimizer = TeamOptimizer(
            strategy=strategy,
            max_team_size=max_team_size,
            timeout_ms=timeout_ms,
        )

    def form_team(
        self,
        task_id: str,
        required_skills: list[str],
        candidates: list[DiscoveryMatch],
        budget: float,
        weights: dict[str, float] | None = None,
    ) -> TeamAssignment:
        partner_history: dict[str, set[str]] = {}

        for candidate in candidates:
            from .reputation import ReputationSystem

            rep = ReputationSystem(self.store)
            profile = rep.get_profile(candidate.agent_id)
            partner_history[candidate.agent_id] = set(profile.partners)

        assignment = self.optimizer.form_team(
            task_id=task_id,
            required_skills=required_skills,
            candidates=candidates,
            budget=budget,
            weights=weights,
            partner_history=partner_history,
        )

        self.store.execute(
            """
            INSERT INTO teams(team_id, payload_json) VALUES (?, ?)
            ON CONFLICT(team_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (assignment.team.team_id, self.store.dumps_json(assignment.team.model_dump(mode="json"))),
        )

        return assignment



class TeamMemory:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def _get_team(self, team_id: str) -> Team:
        rows = self.store.query("SELECT payload_json FROM teams WHERE team_id = ?", (team_id,))
        if not rows:
            raise TeamFormationError(f"unknown team_id: {team_id}")
        return Team.model_validate(self.store.loads_json(rows[0]["payload_json"]))

    def _save_team(self, team: Team) -> None:
        self.store.execute(
            """
            INSERT INTO teams(team_id, payload_json) VALUES (?, ?)
            ON CONFLICT(team_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (team.team_id, self.store.dumps_json(team.model_dump(mode="json"))),
        )

    def write(self, team_id: str, agent_id: str, action: str, payload: dict | None = None) -> Team:
        team = self._get_team(team_id)
        team.interaction_history.append(
            TeamInteraction(agent_id=agent_id, action=action, payload=payload or {}, timestamp=datetime.now(UTC))
        )
        self._save_team(team)
        return team
