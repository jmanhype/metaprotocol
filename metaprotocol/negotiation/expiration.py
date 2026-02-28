"""TTL-based proposal expiration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import NegotiationProposal, NegotiationStatus


def check_expiry(proposal: "NegotiationProposal") -> bool:
    """Check if a proposal has expired."""
    from ..types import NegotiationStatus
    from ..utils.time import now_utc

    if proposal.expires_at is None:
        return False

    if proposal.status.value in {"completed", "rejected", "expired"}:
        return False

    return now_utc() > proposal.expires_at


def mark_expired(proposal: "NegotiationProposal") -> "NegotiationProposal":
    """Mark a proposal as expired."""
    from ..types import NegotiationStatus

    proposal.status = NegotiationStatus.EXPIRED
    return proposal


def set_expiry(proposal: "NegotiationProposal", hours: int) -> "NegotiationProposal":
    """Set expiration time for a proposal."""
    from ..utils.time import hours_from_now

    proposal.expires_at = hours_from_now(hours)
    return proposal
