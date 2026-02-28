"""Multi-party negotiation coordination."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import MultiPartyProposal, NegotiationStatus


def track_acceptance(proposal: "MultiPartyProposal", agent_id: str) -> "MultiPartyProposal":
    """Track acceptance from a participant."""
    if agent_id not in proposal.participant_agent_ids:
        from ..exceptions import NegotiationStateError
        raise NegotiationStateError("Agent is not a participant")

    if agent_id in proposal.accepted_agent_ids:
        return proposal

    proposal.accepted_agent_ids.append(agent_id)

    all_accepted = all(
        pid in proposal.accepted_agent_ids for pid in proposal.participant_agent_ids
    )

    if all_accepted:
        proposal.status = NegotiationStatus.IN_ESCROW if proposal.escrow else NegotiationStatus.ACCEPTED

    return proposal


def track_rejection(proposal: "MultiPartyProposal", agent_id: str) -> "MultiPartyProposal":
    """Track rejection from a participant."""
    from ..types import NegotiationStatus

    if agent_id not in proposal.participant_agent_ids:
        from ..exceptions import NegotiationStateError
        raise NegotiationStateError("Agent is not a participant")

    if agent_id not in proposal.rejected_agent_ids:
        proposal.rejected_agent_ids.append(agent_id)

    proposal.status = NegotiationStatus.REJECTED
    return proposal


def get_acceptance_status(proposal: "MultiPartyProposal") -> dict[str, int]:
    """Get acceptance statistics for a multi-party proposal."""
    return {
        "accepted": len(proposal.accepted_agent_ids),
        "rejected": len(proposal.rejected_agent_ids),
        "pending": len(proposal.participant_agent_ids) - len(proposal.accepted_agent_ids) - len(proposal.rejected_agent_ids),
    }
