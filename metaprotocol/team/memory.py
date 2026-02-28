"""Team memory and shared state management."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import Team, TeamInteraction
    from ..store.base import AbstractProtocolStore


class TeamMemory:
    """Manages shared team state and interaction history."""

    def __init__(self, store: "AbstractProtocolStore") -> None:
        self.store = store

    def _get_team(self, team_id: str) -> "Team":
        from ..types import Team

        rows = self.store.query("SELECT payload_json FROM teams WHERE team_id = ?", (team_id,))
        if not rows:
            from ..exceptions import TeamFormationError
            raise TeamFormationError(f"unknown team_id: {team_id}")
        return Team.model_validate(self.store.loads_json(rows[0]["payload_json"]))

    def _save_team(self, team: "Team") -> None:
        self.store.execute(
            """
            INSERT INTO teams(team_id, payload_json) VALUES (?, ?)
            ON CONFLICT(team_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (team.team_id, self.store.dumps_json(team.model_dump(mode="json"))),
        )

    def write(
        self,
        team_id: str,
        agent_id: str,
        action: str,
        payload: dict | None = None,
    ) -> "Team":
        """Write to team memory (append-only)."""
        from ..types import TeamInteraction
        from ..utils.time import now_utc

        team = self._get_team(team_id)
        team.interaction_history.append(
            TeamInteraction(
                agent_id=agent_id,
                action=action,
                payload=payload or {},
                timestamp=now_utc(),
            )
        )
        self._save_team(team)
        return team

    def read(self, team_id: str) -> "Team":
        """Read team state and interaction history."""
        return self._get_team(team_id)

    def merge_state(self, team_id: str, updates: dict) -> "Team":
        """Merge updates into team shared state."""
        team = self._get_team(team_id)
        team.shared_state.update(updates)
        self._save_team(team)
        return team

    def query(self, team_id: str, action: str | None = None, agent_id: str | None = None) -> list["TeamInteraction"]:
        """Query interaction history with filters."""
        team = self._get_team(team_id)
        interactions = team.interaction_history

        if action:
            interactions = [i for i in interactions if i.action == action]
        if agent_id:
            interactions = [i for i in interactions if i.agent_id == agent_id]

        return interactions
