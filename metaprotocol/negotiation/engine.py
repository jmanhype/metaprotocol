from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from ..exceptions import NegotiationStateError
from ..types import (
    EscrowContract,
    EscrowStatus,
    MultiPartyProposal,
    NegotiationProposal,
    NegotiationStatus,
)
from ..store import SQLiteStore


class NegotiationEngine:
    def __init__(self, store: SQLiteStore, max_counter_offers: int = 5, default_ttl_hours: int = 24) -> None:
        self.store = store
        self.max_counter_offers = max_counter_offers
        self.default_ttl_hours = default_ttl_hours

    def _save_payload(self, proposal_id: str, payload: dict[str, Any]) -> None:
        self.store.execute(
            """
            INSERT INTO negotiations(proposal_id, payload_json) VALUES (?, ?)
            ON CONFLICT(proposal_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (proposal_id, self.store.dumps_json(payload)),
        )

    def _save_proposal(self, proposal: NegotiationProposal) -> None:
        self._save_payload(proposal.proposal_id, proposal.model_dump(mode="json"))

    def _save_multi_proposal(self, proposal: MultiPartyProposal) -> None:
        self._save_payload(proposal.proposal_id, proposal.model_dump(mode="json"))

    def _save_escrow(self, escrow: EscrowContract) -> None:
        self.store.execute(
            """
            INSERT INTO escrow_contracts(escrow_contract_id, proposal_id, payload_json) VALUES (?, ?, ?)
            ON CONFLICT(escrow_contract_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (escrow.escrow_contract_id, escrow.proposal_id, self.store.dumps_json(escrow.model_dump(mode="json"))),
        )

    def get_proposal(self, proposal_id: str) -> NegotiationProposal:
        rows = self.store.query("SELECT payload_json FROM negotiations WHERE proposal_id = ?", (proposal_id,))
        if not rows:
            raise NegotiationStateError(f"proposal not found: {proposal_id}")
        return NegotiationProposal.model_validate(self.store.loads_json(rows[0]["payload_json"]))

    def get_multi_proposal(self, proposal_id: str) -> MultiPartyProposal:
        rows = self.store.query("SELECT payload_json FROM negotiations WHERE proposal_id = ?", (proposal_id,))
        if not rows:
            raise NegotiationStateError(f"proposal not found: {proposal_id}")
        return MultiPartyProposal.model_validate(self.store.loads_json(rows[0]["payload_json"]))

    def get_escrow(self, proposal_id: str) -> EscrowContract | None:
        rows = self.store.query("SELECT payload_json FROM escrow_contracts WHERE proposal_id = ?", (proposal_id,))
        if not rows:
            return None
        return EscrowContract.model_validate(self.store.loads_json(rows[0]["payload_json"]))

    def _ensure_not_expired(self, proposal: NegotiationProposal | MultiPartyProposal) -> None:
        if proposal.expires_at is None:
            return
        expires_at = proposal.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            proposal.status = NegotiationStatus.EXPIRED
            self._save_payload(proposal.proposal_id, proposal.model_dump(mode="json"))
            raise NegotiationStateError("proposal expired")

    def propose(
        self,
        proposer_agent_id: str,
        responder_agent_id: str,
        task_id: str,
        required_skills: list[str],
        offered_compensation: float,
        escrow: bool = True,
        terms: dict | None = None,
        expires_at: datetime | None = None,
        deadline: datetime | None = None,
    ) -> NegotiationProposal:
        if expires_at is None:
            expires_at = datetime.now(UTC) + timedelta(hours=self.default_ttl_hours)
        proposal = NegotiationProposal(
            proposer_agent_id=proposer_agent_id,
            responder_agent_id=responder_agent_id,
            task_id=task_id,
            required_skills=required_skills,
            offered_compensation=offered_compensation,
            escrow=escrow,
            terms=terms or {},
            expires_at=expires_at,
            deadline=deadline,
        )
        self._save_proposal(proposal)
        return proposal

    def accept(self, proposal_id: str, agent_id: str) -> NegotiationProposal:
        proposal = self.get_proposal(proposal_id)
        self._ensure_not_expired(proposal)
        if agent_id != proposal.responder_agent_id:
            raise NegotiationStateError("only responder may accept proposal")
        if proposal.status not in {NegotiationStatus.PROPOSED, NegotiationStatus.COUNTERED}:
            raise NegotiationStateError(f"cannot accept from state {proposal.status.value}")

        proposal.status = NegotiationStatus.IN_ESCROW if proposal.escrow else NegotiationStatus.ACCEPTED
        self._save_proposal(proposal)

        if proposal.escrow:
            escrow = EscrowContract(proposal_id=proposal.proposal_id, amount=proposal.offered_compensation)
            self._save_escrow(escrow)
        return proposal

    def reject(self, proposal_id: str, agent_id: str) -> NegotiationProposal:
        proposal = self.get_proposal(proposal_id)
        if agent_id != proposal.responder_agent_id:
            raise NegotiationStateError("only responder may reject proposal")
        if proposal.status in {NegotiationStatus.COMPLETED, NegotiationStatus.REJECTED}:
            raise NegotiationStateError(f"cannot reject from state {proposal.status.value}")
        proposal.status = NegotiationStatus.REJECTED
        self._save_proposal(proposal)
        return proposal

    def counter(
        self,
        proposal_id: str,
        agent_id: str,
        revised_compensation: float | None = None,
        message: str | None = None,
        revised_terms: dict | None = None,
    ) -> NegotiationProposal:
        proposal = self.get_proposal(proposal_id)
        self._ensure_not_expired(proposal)
        if agent_id not in {proposal.proposer_agent_id, proposal.responder_agent_id}:
            raise NegotiationStateError("countering agent not in negotiation")
        if len(proposal.counter_offers) >= self.max_counter_offers:
            raise NegotiationStateError("max counter offers exceeded")
        if proposal.status not in {NegotiationStatus.PROPOSED, NegotiationStatus.COUNTERED}:
            raise NegotiationStateError(f"cannot counter from state {proposal.status.value}")

        if revised_compensation is not None:
            proposal.offered_compensation = revised_compensation
        proposal.counter_offers.append(
            {
                "agent_id": agent_id,
                "revised_compensation": revised_compensation,
                "revised_terms": revised_terms or {},
                "message": message,
            }
        )
        proposal.terms.update(revised_terms or {})
        proposal.status = NegotiationStatus.COUNTERED
        proposal.expires_at = datetime.now(UTC) + timedelta(hours=self.default_ttl_hours)
        self._save_proposal(proposal)
        return proposal

    def complete(self, proposal_id: str, success: bool = True) -> NegotiationProposal:
        proposal = self.get_proposal(proposal_id)
        if proposal.status not in {
            NegotiationStatus.IN_ESCROW,
            NegotiationStatus.ACCEPTED,
            NegotiationStatus.EXECUTING,
        }:
            raise NegotiationStateError(f"cannot complete from state {proposal.status.value}")
        proposal.status = NegotiationStatus.COMPLETED if success else NegotiationStatus.DISPUTED
        self._save_proposal(proposal)

        escrow = self.get_escrow(proposal_id)
        if escrow:
            escrow.status = EscrowStatus.RELEASED if success else EscrowStatus.REFUNDED
            escrow.updated_at = datetime.now(UTC)
            self._save_escrow(escrow)

        return proposal

    def propose_multi(
        self,
        proposer_agent_id: str,
        participant_agent_ids: list[str],
        task_id: str,
        required_skills: list[str],
        offered_compensation: float,
        escrow: bool = True,
        terms: dict | None = None,
        compensation_by_agent: dict[str, float] | None = None,
        expires_at: datetime | None = None,
        deadline: datetime | None = None,
    ) -> MultiPartyProposal:
        if expires_at is None:
            expires_at = datetime.now(UTC) + timedelta(hours=self.default_ttl_hours)
        proposal = MultiPartyProposal(
            proposer_agent_id=proposer_agent_id,
            participant_agent_ids=participant_agent_ids,
            task_id=task_id,
            required_skills=required_skills,
            offered_compensation=offered_compensation,
            escrow=escrow,
            terms=terms or {},
            compensation_by_agent=compensation_by_agent or {},
            expires_at=expires_at,
            deadline=deadline,
        )
        self._save_multi_proposal(proposal)
        return proposal

    def accept_multi(self, proposal_id: str, agent_id: str) -> MultiPartyProposal:
        proposal = self.get_multi_proposal(proposal_id)
        self._ensure_not_expired(proposal)
        if agent_id not in proposal.participant_agent_ids:
            raise NegotiationStateError("only participants may accept proposal")
        if proposal.status not in {NegotiationStatus.PROPOSED, NegotiationStatus.COUNTERED}:
            raise NegotiationStateError(f"cannot accept from state {proposal.status.value}")
        if agent_id in proposal.rejected_agent_ids:
            raise NegotiationStateError("rejected participant cannot accept proposal")

        if agent_id not in proposal.accepted_agent_ids:
            proposal.accepted_agent_ids.append(agent_id)

        all_participants_accepted = all(
            participant in set(proposal.accepted_agent_ids) for participant in proposal.participant_agent_ids
        )
        if all_participants_accepted:
            proposal.status = NegotiationStatus.IN_ESCROW if proposal.escrow else NegotiationStatus.ACCEPTED
            if proposal.escrow:
                escrow = EscrowContract(proposal_id=proposal.proposal_id, amount=proposal.offered_compensation)
                self._save_escrow(escrow)
        self._save_multi_proposal(proposal)
        return proposal

    def reject_multi(self, proposal_id: str, agent_id: str) -> MultiPartyProposal:
        proposal = self.get_multi_proposal(proposal_id)
        if agent_id not in proposal.participant_agent_ids:
            raise NegotiationStateError("only participants may reject proposal")
        if proposal.status in {NegotiationStatus.COMPLETED, NegotiationStatus.REJECTED}:
            raise NegotiationStateError(f"cannot reject from state {proposal.status.value}")

        if agent_id not in proposal.rejected_agent_ids:
            proposal.rejected_agent_ids.append(agent_id)
        proposal.status = NegotiationStatus.REJECTED
        self._save_multi_proposal(proposal)
        return proposal

    def counter_multi(
        self,
        proposal_id: str,
        agent_id: str,
        revised_compensation: float | None = None,
        message: str | None = None,
        revised_terms: dict | None = None,
    ) -> MultiPartyProposal:
        proposal = self.get_multi_proposal(proposal_id)
        self._ensure_not_expired(proposal)
        valid_agents = set(proposal.participant_agent_ids) | {proposal.proposer_agent_id}
        if agent_id not in valid_agents:
            raise NegotiationStateError("countering agent not in negotiation")
        if len(proposal.counter_offers) >= self.max_counter_offers:
            raise NegotiationStateError("max counter offers exceeded")
        if proposal.status not in {NegotiationStatus.PROPOSED, NegotiationStatus.COUNTERED}:
            raise NegotiationStateError(f"cannot counter from state {proposal.status.value}")

        if revised_compensation is not None:
            proposal.offered_compensation = revised_compensation
        proposal.counter_offers.append(
            {
                "agent_id": agent_id,
                "revised_compensation": revised_compensation,
                "revised_terms": revised_terms or {},
                "message": message,
            }
        )
        proposal.terms.update(revised_terms or {})
        proposal.status = NegotiationStatus.COUNTERED
        proposal.accepted_agent_ids = []
        proposal.rejected_agent_ids = []
        proposal.expires_at = datetime.now(UTC) + timedelta(hours=self.default_ttl_hours)
        self._save_multi_proposal(proposal)
        return proposal

    def complete_multi(self, proposal_id: str, success: bool = True) -> MultiPartyProposal:
        proposal = self.get_multi_proposal(proposal_id)
        if proposal.status not in {
            NegotiationStatus.IN_ESCROW,
            NegotiationStatus.ACCEPTED,
            NegotiationStatus.EXECUTING,
        }:
            raise NegotiationStateError(f"cannot complete from state {proposal.status.value}")
        proposal.status = NegotiationStatus.COMPLETED if success else NegotiationStatus.DISPUTED
        self._save_multi_proposal(proposal)

        escrow = self.get_escrow(proposal_id)
        if escrow:
            escrow.status = EscrowStatus.RELEASED if success else EscrowStatus.REFUNDED
            escrow.updated_at = datetime.now(UTC)
            self._save_escrow(escrow)

        return proposal
