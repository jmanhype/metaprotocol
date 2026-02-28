"""Team lifecycle and state transitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import Team, TeamStatus


def transition_team_status(
    team: "Team",
    new_status: "TeamStatus",
) -> "Team":
    """Transition team to a new status with validation."""
    valid_transitions = {
        "forming": ["active", "dissolved"],
        "active": ["executing", "completed", "dissolved"],
        "executing": ["completed", "dissolved"],
        "completed": [],
        "dissolved": [],
    }

    current = team.status.value
    if new_status.value not in valid_transitions.get(current, []):
        from ..exceptions import TeamFormationError
        raise TeamFormationError(
            f"Invalid transition: {current} -> {new_status.value}"
        )

    team.status = new_status
    return team


def is_team_writable(team: "Team") -> bool:
    """Check if team memory is writable."""
    return team.status.value in {"forming", "active", "executing"}


def is_team_active(team: "Team") -> bool:
    """Check if team is currently active."""
    return team.status.value in {"active", "executing"}
