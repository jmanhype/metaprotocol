from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .storage import SQLiteStore


class DisputeStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    AUTO_RESOLVED = "auto_resolved"


class Dispute(BaseModel):
    dispute_id: str = Field(default_factory=lambda: str(uuid4()))
    proposal_id: str
    agent_id: str
    reason: str
    description: str | None = None
    evidence: dict = Field(default_factory=dict)
    status: DisputeStatus = DisputeStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    resolution: str | None = None
    auto_resolve_deadline: datetime | None = None


class DisputeResolver:
    """Handles dispute lifecycle including auto-resolution."""

    def __init__(
        self,
        store: SQLiteStore,
        auto_resolve_days: int = 7,
        favor_higher_reputation: bool = True,
    ) -> None:
        self.store = store
        self.auto_resolve_days = auto_resolve_days
        self.favor_higher_reputation = favor_higher_reputation

    def open_dispute(
        self,
        proposal_id: str,
        agent_id: str,
        reason: str,
        description: str | None = None,
        evidence: dict | None = None,
    ) -> Dispute:
        """Open a dispute on a proposal."""
        from .reputation import ReputationSystem
        from .negotiation import NegotiationEngine

        neg = NegotiationEngine(self.store)
        rep = ReputationSystem(self.store)

        proposal = neg.get_proposal(proposal_id)

        if proposal.status.value not in {"in_escrow", "executing", "completed"}:
            raise ValueError(f"Cannot dispute proposal in state {proposal.status.value}")

        if agent_id not in {proposal.proposer_agent_id, proposal.responder_agent_id}:
            raise ValueError("Dispute must be opened by proposal participant")

        existing = self.store.query(
            "SELECT payload_json FROM disputes WHERE proposal_id = ? AND status = ?",
            (proposal_id, DisputeStatus.OPEN.value),
        )
        if existing:
            raise ValueError("An open dispute already exists for this proposal")

        deadline = datetime.now(UTC) + timedelta(days=self.auto_resolve_days)
        dispute = Dispute(
            proposal_id=proposal_id,
            agent_id=agent_id,
            reason=reason,
            description=description,
            evidence=evidence or {},
            auto_resolve_deadline=deadline,
        )

        self.store.execute(
            """
            INSERT INTO disputes(dispute_id, proposal_id, payload_json) VALUES (?, ?, ?)
            ON CONFLICT(dispute_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (dispute.dispute_id, dispute.proposal_id, self.store.dumps_json(dispute.model_dump(mode="json"))),
        )

        return dispute

    def resolve_dispute(
        self,
        dispute_id: str,
        resolution: str,
        in_favor_of: str | None = None,
    ) -> Dispute:
        """Manually resolve a dispute."""
        rows = self.store.query("SELECT payload_json FROM disputes WHERE dispute_id = ?", (dispute_id,))
        if not rows:
            raise ValueError(f"Dispute not found: {dispute_id}")

        dispute = Dispute.model_validate(self.store.loads_json(rows[0]["payload_json"]))

        if dispute.status in {DisputeStatus.RESOLVED, DisputeStatus.AUTO_RESOLVED}:
            raise ValueError(f"Dispute already resolved: {dispute_id}")

        dispute.status = DisputeStatus.RESOLVED
        dispute.resolution = f"{resolution} (in favor of: {in_favor_of})" if in_favor_of else resolution
        dispute.resolved_at = datetime.now(UTC)

        self.store.execute(
            """
            INSERT INTO disputes(dispute_id, proposal_id, payload_json) VALUES (?, ?, ?)
            ON CONFLICT(dispute_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (dispute.dispute_id, dispute.proposal_id, self.store.dumps_json(dispute.model_dump(mode="json"))),
        )

        return dispute

    def auto_resolve_expired_disputes(self) -> list[Dispute]:
        """Auto-resolve disputes that have exceeded their deadline."""
        rows = self.store.query(
            "SELECT payload_json FROM disputes WHERE status = ?",
            (DisputeStatus.OPEN.value,),
        )

        resolved: list[Dispute] = []
        now = datetime.now(UTC)

        for row in rows:
            dispute = Dispute.model_validate(self.store.loads_json(row["payload_json"]))

            if dispute.auto_resolve_deadline and dispute.auto_resolve_deadline <= now:
                if self.favor_higher_reputation:
                    resolved_dispute = self._auto_resolve_by_reputation(dispute)
                else:
                    resolved_dispute = self._auto_resolve_neutral(dispute)

                resolved.append(resolved_dispute)

        return resolved

    def _auto_resolve_by_reputation(self, dispute: Dispute) -> Dispute:
        """Auto-resolve by favoring the party with higher reputation."""
        from .negotiation import NegotiationEngine
        from .reputation import ReputationSystem

        neg = NegotiationEngine(self.store)
        rep = ReputationSystem(self.store)

        proposal = neg.get_proposal(dispute.proposal_id)
        proposer_rep = rep.get_profile(proposal.proposer_agent_id)
        responder_rep = rep.get_profile(proposal.responder_agent_id)

        if proposer_rep.reputation_score >= responder_rep.reputation_score:
            in_favor_of = proposal.proposer_agent_id
            resolution = f"Auto-resolved in favor of proposer (higher reputation: {proposer_rep.reputation_score:.2f} vs {responder_rep.reputation_score:.2f})"
        else:
            in_favor_of = proposal.responder_agent_id
            resolution = f"Auto-resolved in favor of responder (higher reputation: {responder_rep.reputation_score:.2f} vs {proposer_rep.reputation_score:.2f})"

        dispute.status = DisputeStatus.AUTO_RESOLVED
        dispute.resolution = resolution
        dispute.resolved_at = datetime.now(UTC)

        self.store.execute(
            """
            INSERT INTO disputes(dispute_id, proposal_id, payload_json) VALUES (?, ?, ?)
            ON CONFLICT(dispute_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (dispute.dispute_id, dispute.proposal_id, self.store.dumps_json(dispute.model_dump(mode="json"))),
        )

        return dispute

    def _auto_resolve_neutral(self, dispute: Dispute) -> Dispute:
        """Auto-resolve neutrally without favoring either party."""
        dispute.status = DisputeStatus.AUTO_RESOLVED
        dispute.resolution = "Auto-resolved neutrally due to expired deadline"
        dispute.resolved_at = datetime.now(UTC)

        self.store.execute(
            """
            INSERT INTO disputes(dispute_id, proposal_id, payload_json) VALUES (?, ?, ?)
            ON CONFLICT(dispute_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (dispute.dispute_id, dispute.proposal_id, self.store.dumps_json(dispute.model_dump(mode="json"))),
        )

        return dispute

    def get_dispute(self, dispute_id: str) -> Dispute:
        """Get a dispute by ID."""
        rows = self.store.query("SELECT payload_json FROM disputes WHERE dispute_id = ?", (dispute_id,))
        if not rows:
            raise ValueError(f"Dispute not found: {dispute_id}")
        return Dispute.model_validate(self.store.loads_json(rows[0]["payload_json"]))

    def list_disputes_for_proposal(self, proposal_id: str) -> list[Dispute]:
        """List all disputes for a proposal."""
        rows = self.store.query("SELECT payload_json FROM disputes WHERE proposal_id = ?", (proposal_id,))
        return [Dispute.model_validate(self.store.loads_json(row["payload_json"])) for row in rows]

    def list_open_disputes(self) -> list[Dispute]:
        """List all open disputes."""
        rows = self.store.query(
            "SELECT payload_json FROM disputes WHERE status = ?",
            (DisputeStatus.OPEN.value,),
        )
        return [Dispute.model_validate(self.store.loads_json(row["payload_json"])) for row in rows]
