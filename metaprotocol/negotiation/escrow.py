"""Escrow contract lifecycle management."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import EscrowContract, EscrowStatus, NegotiationProposal


def create_escrow(proposal: "NegotiationProposal") -> "EscrowContract":
    """Create an escrow contract from a proposal."""
    from ..types import EscrowContract, EscrowStatus

    return EscrowContract(
        proposal_id=proposal.proposal_id,
        amount=proposal.offered_compensation,
        status=EscrowStatus.LOCKED,
    )


def release_escrow(contract: "EscrowContract") -> "EscrowContract":
    """Release funds from escrow."""
    from ..types import EscrowStatus
    from ..utils.time import now_utc

    contract.status = EscrowStatus.RELEASED
    return contract


def refund_escrow(contract: "EscrowContract") -> "EscrowContract":
    """Refund funds to proposer."""
    from ..types import EscrowStatus
    from ..utils.time import now_utc

    contract.status = EscrowStatus.REFUNDED
    return contract


def freeze_escrow(contract: "EscrowContract") -> "EscrowContract":
    """Freeze escrow during dispute."""
    from ..types import EscrowStatus

    contract.status = EscrowStatus.LOCKED
    return contract
