from __future__ import annotations

from datetime import UTC, datetime

from .models import DiscoveryMatch, Team, TeamAssignment, TeamFormationError, TeamInteraction, TeamStatus
from .storage import SQLiteStore


class TeamFormationEngine:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def form_team(
        self,
        task_id: str,
        required_skills: list[str],
        candidates: list[DiscoveryMatch],
        budget: float,
    ) -> TeamAssignment:
        by_skill: dict[str, list[DiscoveryMatch]] = {skill: [] for skill in required_skills}
        for candidate in candidates:
            if candidate.name in by_skill:
                by_skill[candidate.name].append(candidate)

        coverage: dict[str, str] = {}
        selected_agents: dict[str, DiscoveryMatch] = {}
        for skill in required_skills:
            options = sorted(by_skill.get(skill, []), key=lambda m: (-m.overall_score, m.cost_per_use))
            if not options:
                raise TeamFormationError(f"missing required skill: {skill}")
            pick = options[0]
            coverage[skill] = pick.agent_id
            selected_agents[pick.agent_id] = pick

        total_cost = sum(match.cost_per_use for match in selected_agents.values())
        if total_cost > budget:
            raise TeamFormationError(f"budget exceeded: {total_cost:.4f} > {budget:.4f}")

        agents = list(selected_agents.keys())
        role_assignments: dict[str, str] = {}
        for idx, agent_id in enumerate(agents):
            role_assignments[agent_id] = "lead" if idx == 0 else "specialist"

        team = Team(
            task_id=task_id,
            agent_ids=agents,
            role_assignments=role_assignments,
            required_skills=required_skills,
            skill_coverage=coverage,
            total_budget=budget,
            status=TeamStatus.ACTIVE,
        )
        self.store.execute(
            """
            INSERT INTO teams(team_id, payload_json) VALUES (?, ?)
            ON CONFLICT(team_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (team.team_id, self.store.dumps_json(team.model_dump(mode="json"))),
        )

        score = sum(m.overall_score for m in selected_agents.values()) / max(1, len(selected_agents))
        return TeamAssignment(team=team, total_cost=total_cost, optimization_score=round(score, 4))


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
