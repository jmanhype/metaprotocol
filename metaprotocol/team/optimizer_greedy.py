from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from ..exceptions import TeamFormationError
from ..types import DiscoveryMatch, Team, TeamAssignment, TeamStatus

if TYPE_CHECKING:
    from ..store import SQLiteStore


class TeamOptimizer:
    """Optimizes team formation using greedy or ILP strategies."""

    def __init__(
        self,
        strategy: str = "greedy",
        max_team_size: int = 10,
        timeout_ms: int = 1000,
    ) -> None:
        if strategy not in {"greedy", "ilp"}:
            raise ValueError(f"strategy must be 'greedy' or 'ilp', got {strategy}")
        self.strategy = strategy
        self.max_team_size = max_team_size
        self.timeout_ms = timeout_ms

    def form_team(
        self,
        task_id: str,
        required_skills: list[str],
        candidates: list[DiscoveryMatch],
        budget: float,
        weights: dict[str, float] | None = None,
        partner_history: dict[str, set[str]] | None = None,
    ) -> TeamAssignment:
        """Form an optimal team for the given task."""
        weights = weights or {"success_rate": 0.4, "reputation": 0.3, "cost": 0.2, "diversity": 0.1}

        if self.strategy == "greedy":
            return self._greedy_optimize(
                task_id=task_id,
                required_skills=required_skills,
                candidates=candidates,
                budget=budget,
                weights=weights,
                partner_history=partner_history or {},
            )
        else:
            return self._ilp_optimize(
                task_id=task_id,
                required_skills=required_skills,
                candidates=candidates,
                budget=budget,
                weights=weights,
                partner_history=partner_history or {},
            )

    def _greedy_optimize(
        self,
        task_id: str,
        required_skills: list[str],
        candidates: list[DiscoveryMatch],
        budget: float,
        weights: dict[str, float],
        partner_history: dict[str, set[str]],
    ) -> TeamAssignment:
        """Greedy heuristic: select best candidate for each skill, preferring multi-skill agents."""
        by_skill: dict[str, list[DiscoveryMatch]] = {skill: [] for skill in required_skills}
        for candidate in candidates:
            if candidate.name in by_skill:
                by_skill[candidate.name].append(candidate)

        selected_agents: dict[str, DiscoveryMatch] = {}
        coverage: dict[str, str] = {}

        unassigned_skills = list(required_skills)
        candidates_by_agent: dict[str, DiscoveryMatch] = {c.agent_id: c for c in candidates}

        while unassigned_skills:
            best_score = -np.inf
            best_agent: str | None = None
            best_skills: list[str] = []

            for agent_id, candidate in candidates_by_agent.items():
                if agent_id in selected_agents:
                    continue

                skills_covered = [s for s in unassigned_skills if candidate.name == s]
                if not skills_covered:
                    continue

                score = self._compute_score(candidate, weights, partner_history.get(agent_id, set()))
                cost = candidate.cost_per_use

                if len(selected_agents) + 1 > self.max_team_size:
                    continue

                current_cost = sum(c.cost_per_use for c in selected_agents.values()) + cost
                if current_cost > budget:
                    continue

                adjusted_score = score / (1.0 + cost * 0.5)

                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_agent = agent_id
                    best_skills = skills_covered

            if best_agent is None:
                uncovered = ", ".join(unassigned_skills)
                raise TeamFormationError(
                    f"cannot cover all skills within budget. Uncovered: {uncovered}"
                )

            selected_agents[best_agent] = candidates_by_agent[best_agent]
            for skill in best_skills:
                coverage[skill] = best_agent
                if skill in unassigned_skills:
                    unassigned_skills.remove(skill)

        total_cost = sum(c.cost_per_use for c in selected_agents.values())
        agents = list(selected_agents.keys())

        role_assignments: dict[str, str] = {}
        for idx, agent_id in enumerate(agents):
            if idx == 0:
                role_assignments[agent_id] = "lead"
            elif any(
                agent_id == coverage.get(s) for s in ["code_review", "testing", "quality_assurance"]
            ):
                role_assignments[agent_id] = "reviewer"
            else:
                role_assignments[agent_id] = "specialist"

        team = Team(
            task_id=task_id,
            agent_ids=agents,
            role_assignments=role_assignments,
            required_skills=required_skills,
            skill_coverage=coverage,
            total_budget=budget,
            status=TeamStatus.ACTIVE,
        )

        optimization_score = sum(
            self._compute_score(c, weights, partner_history.get(c.agent_id, set()))
            for c in selected_agents.values()
        ) / max(1, len(selected_agents))

        return TeamAssignment(
            team=team,
            total_cost=total_cost,
            optimization_score=round(optimization_score, 4),
        )

    def _ilp_optimize(
        self,
        task_id: str,
        required_skills: list[str],
        candidates: list[DiscoveryMatch],
        budget: float,
        weights: dict[str, float],
        partner_history: dict[str, set[str]],
    ) -> TeamAssignment:
        """ILP solver using PuLP for exact optimization."""
        try:
            import pulp
        except ImportError as e:
            raise ImportError(
                "PuLP is required for ILP optimization. "
                "Install with: pip install metaprotocol[ilp]"
            ) from e

        candidates_by_id = {c.agent_id: c for c in candidates}
        skill_to_agents: dict[str, list[str]] = {skill: [] for skill in required_skills}
        for candidate in candidates:
            if candidate.name in skill_to_agents:
                skill_to_agents[candidate.name].append(candidate.agent_id)

        problem = pulp.LpProblem("TeamFormation", pulp.LpMaximize)

        x = {agent_id: pulp.LpVariable(f"x_{agent_id}", cat="Binary") for agent_id in candidates_by_id}

        objective_terms = []
        for agent_id, candidate in candidates_by_id.items():
            score = self._compute_score(candidate, weights, partner_history.get(agent_id, set()))
            objective_terms.append(score * x[agent_id])

        problem += pulp.lpSum(objective_terms), "Total_Score"

        problem += pulp.lpSum(candidates_by_id[aid].cost_per_use * x[aid] for aid in x) <= budget, "Budget"

        for skill, agent_ids in skill_to_agents.items():
            problem += pulp.lpSum(x[aid] for aid in agent_ids) >= 1, f"Cover_{skill}"

        problem += pulp.lpSum(x[aid] for aid in x) <= self.max_team_size, "TeamSize"

        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=self.timeout_ms / 1000)
        status = problem.solve(solver)

        if status != pulp.LpStatusOptimal:
            return self._greedy_optimize(task_id, required_skills, candidates, budget, weights, partner_history)

        selected_agents = {
            aid: candidates_by_id[aid] for aid, var in x.items() if var.value() == 1
        }

        if not selected_agents:
            uncovered = ", ".join(required_skills)
            raise TeamFormationError(f"no valid team found. Uncovered: {uncovered}")

        coverage: dict[str, str] = {}
        for skill, agent_ids in skill_to_agents.items():
            for agent_id in agent_ids:
                if agent_id in selected_agents:
                    coverage[skill] = agent_id
                    break

        total_cost = sum(c.cost_per_use for c in selected_agents.values())
        agents = list(selected_agents.keys())

        role_assignments: dict[str, str] = {}
        for idx, agent_id in enumerate(agents):
            if idx == 0:
                role_assignments[agent_id] = "lead"
            elif any(
                agent_id == coverage.get(s) for s in ["code_review", "testing", "quality_assurance"]
            ):
                role_assignments[agent_id] = "reviewer"
            else:
                role_assignments[agent_id] = "specialist"

        team = Team(
            task_id=task_id,
            agent_ids=agents,
            role_assignments=role_assignments,
            required_skills=required_skills,
            skill_coverage=coverage,
            total_budget=budget,
            status=TeamStatus.ACTIVE,
        )

        optimization_score = sum(
            self._compute_score(c, weights, partner_history.get(c.agent_id, set()))
            for c in selected_agents.values()
        ) / max(1, len(selected_agents))

        return TeamAssignment(
            team=team,
            total_cost=total_cost,
            optimization_score=round(optimization_score, 4),
        )

    def _compute_score(
        self,
        candidate: DiscoveryMatch,
        weights: dict[str, float],
        past_partners: set[str],
    ) -> float:
        """Compute composite score for a candidate."""
        success_score = candidate.success_rate
        reputation_score = candidate.reputation_score

        max_cost = 5.0
        cost_score = 1.0 / (1.0 + candidate.cost_per_use / max_cost)

        diversity_weight = weights.get("diversity", 0.1)
        if diversity_weight > 0 and past_partners:
            diversity_bonus = 1.0 / (1.0 + len(past_partners) * 0.1)
        else:
            diversity_bonus = 1.0

        score = (
            weights.get("success_rate", 0.4) * success_score
            + weights.get("reputation", 0.3) * reputation_score
            + weights.get("cost", 0.2) * cost_score
            + diversity_weight * diversity_bonus
        )

        return score
