"""ILP-based team optimization using PuLP."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import DiscoveryMatch, Team, TeamAssignment
    from ..store.base import AbstractProtocolStore


def solve_ilp_team_formation(
    task_id: str,
    required_skills: list[str],
    candidates: list["DiscoveryMatch"],
    budget: float,
    weights: dict[str, float],
    partner_history: dict[str, set[str]],
    store: "AbstractProtocolStore",
    max_team_size: int = 10,
    timeout_ms: int = 1000,
) -> "TeamAssignment":
    """Solve team formation using integer linear programming."""
    try:
        import pulp
    except ImportError:
        raise ImportError(
            "PuLP is required for ILP optimization. Install with: pip install metaprotocol[ilp]"
        )

    candidates_by_id = {c.agent_id: c for c in candidates}
    skill_to_agents: dict[str, list[str]] = {skill: [] for skill in required_skills}

    for candidate in candidates:
        if candidate.name in skill_to_agents:
            skill_to_agents[candidate.name].append(candidate.agent_id)

    problem = pulp.LpProblem("TeamFormation", pulp.LpMaximize)

    x = {aid: pulp.LpVariable(f"x_{aid}", cat="Binary") for aid in candidates_by_id}

    objective_terms = []
    for aid, candidate in candidates_by_id.items():
        score = _compute_score(candidate, weights, partner_history.get(aid, set()))
        objective_terms.append(score * x[aid])

    problem += pulp.lpSum(objective_terms), "Total_Score"
    problem += pulp.lpSum(candidates_by_id[aid].cost_per_use * x[aid] for aid in x) <= budget, "Budget"

    for skill, agent_ids in skill_to_agents.items():
        problem += pulp.lpSum(x[aid] for aid in agent_ids) >= 1, f"Cover_{skill}"

    problem += pulp.lpSum(x[aid] for aid in x) <= max_team_size, "TeamSize"

    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=timeout_ms / 1000)
    problem.solve(solver)

    selected_agents = {
        aid: candidates_by_id[aid] for aid, var in x.items() if var.value() == 1
    }

    if not selected_agents:
        raise Exception("No valid team found")

    from ..utils.ids import generate_id
    from ..types import Team, TeamStatus

    coverage: dict[str, str] = {}
    for skill, agent_ids in skill_to_agents.items():
        for aid in agent_ids:
            if aid in selected_agents:
                coverage[skill] = aid
                break

    team = Team(
        task_id=task_id,
        agent_ids=list(selected_agents.keys()),
        role_assignments=_assign_roles(list(selected_agents.keys())),
        required_skills=required_skills,
        skill_coverage=coverage,
        total_budget=budget,
        status=TeamStatus.ACTIVE,
    )

    optimization_score = sum(
        _compute_score(c, weights, partner_history.get(c.agent_id, set()))
        for c in selected_agents.values()
    ) / max(1, len(selected_agents))

    total_cost = sum(c.cost_per_use for c in selected_agents.values())

    return TeamAssignment(team=team, total_cost=total_cost, optimization_score=round(optimization_score, 4))


def _compute_score(
    candidate: "DiscoveryMatch",
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


def _assign_roles(agent_ids: list[str]) -> dict[str, str]:
    """Assign roles to team agents."""
    roles = {}
    for idx, agent_id in enumerate(agent_ids):
        if idx == 0:
            roles[agent_id] = "lead"
        elif idx == len(agent_ids) - 1:
            roles[agent_id] = "reviewer"
        else:
            roles[agent_id] = "specialist"
    return roles
