"""Cross-model validation helpers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import (
        AgentCapability,
        NegotiationProposal,
        MultiPartyProposal,
        Team,
    )


def validate_capability_not_stale(capability: "AgentCapability", max_days: int = 30) -> bool:
    """Check if a capability has been updated recently."""
    from .utils.time import now_utc, seconds_between

    age_seconds = seconds_between(capability.updated_at, now_utc())
    age_days = age_seconds / 86400.0
    return age_days < max_days


def validate_proposal_funds(proposal: "NegotiationProposal" | "MultiPartyProposal") -> bool:
    """Validate that offered compensation is positive."""
    return proposal.offered_compensation > 0


def validate_team_budget(team: "Team", budget: float) -> bool:
    """Validate that team cost doesn't exceed budget."""
    return team.total_budget <= budget


def validate_skill_coverage(team: "Team", required_skills: list[str]) -> bool:
    """Validate that all required skills are covered."""
    return all(skill in team.skill_coverage for skill in required_skills)


def validate_team_access(team: "Team", agent_id: str) -> bool:
    """Validate that an agent is allowed to access team memory."""
    return agent_id in team.agent_ids
