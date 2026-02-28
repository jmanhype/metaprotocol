"""Negotiation engine and state machine."""

from .engine import NegotiationEngine
from .state_machine import validate_transition, can_accept, can_reject, can_counter
from .escrow import create_escrow, release_escrow, refund_escrow, freeze_escrow
from .multiparty import track_acceptance, track_rejection, get_acceptance_status
from .expiration import check_expiry, mark_expired, set_expiry

__all__ = [
    "NegotiationEngine",
    "validate_transition",
    "can_accept",
    "can_reject",
    "can_counter",
    "create_escrow",
    "release_escrow",
    "refund_escrow",
    "freeze_escrow",
    "track_acceptance",
    "track_rejection",
    "get_acceptance_status",
    "check_expiry",
    "mark_expired",
    "set_expiry",
]
