"""Negotiation proposal state machine and validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import NegotiationProposal, NegotiationStatus


def validate_transition(
    proposal: "NegotiationProposal",
    new_status: "NegotiationStatus",
) -> bool:
    """Validate a state machine transition."""
    valid_transitions = {
        "proposed": ["accepted", "rejected", "countered", "expired"],
        "countered": ["accepted", "rejected", "countered", "expired"],
        "accepted": ["in_escrow", "executing", "completed", "disputed"],
        "in_escrow": ["executing", "completed", "disputed"],
        "executing": ["completed", "disputed"],
        "rejected": [],
        "expired": [],
        "completed": [],
        "disputed": ["completed"],
    }

    current = proposal.status.value
    return new_status.value in valid_transitions.get(current, [])


def can_accept(proposal: "NegotiationProposal") -> bool:
    """Check if proposal can be accepted."""
    return proposal.status.value in {"proposed", "countered"}


def can_reject(proposal: "NegotiationProposal") -> bool:
    """Check if proposal can be rejected."""
    return proposal.status.value not in {"completed", "rejected", "expired"}


def can_counter(proposal: "NegotiationProposal", max_counter_offers: int) -> bool:
    """Check if proposal can be countered."""
    return (
        proposal.status.value in {"proposed", "countered"}
        and len(proposal.counter_offers) < max_counter_offers
    )
