from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class DisputeStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    AUTO_RESOLVED = "auto_resolved"


class ComplexityLevel(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class AgentCapability(BaseModel):
    skill_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    name: str
    description: Optional[str] = None
    complexity_level: ComplexityLevel
    success_rate: float = 0.0
    cost_per_use: float = 0.0
    embedding: Optional[list[float]] = None
    metadata: dict = Field(default_factory=dict)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("success_rate")
    @classmethod
    def validate_success_rate(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("success_rate must be between 0 and 1")
        return value

    @field_validator("cost_per_use")
    @classmethod
    def validate_cost_per_use(cls, value: float) -> float:
        if value < 0.0:
            raise ValueError("cost_per_use must be non-negative")
        return value


class DiscoveryMatch(BaseModel):
    agent_id: str
    skill_id: str
    name: str
    complexity_level: ComplexityLevel
    cost_per_use: float
    success_rate: float
    relevance_score: float
    freshness_score: float
    reputation_score: float = 0.5
    overall_score: float


class DiscoveryResult(BaseModel):
    matches: list[DiscoveryMatch] = Field(default_factory=list)


class CollaborationRating(BaseModel):
    rater_agent_id: str
    rated_agent_id: str
    collaboration_id: str
    score: float
    comment: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("score")
    @classmethod
    def validate_score(cls, value: float) -> float:
        if not 0.0 <= value <= 5.0:
            raise ValueError("score must be between 0 and 5")
        return value


class ReputationSnapshot(BaseModel):
    score: float
    timestamp: datetime
    event: str


class ReputationRecord(BaseModel):
    agent_id: str
    reputation_score: float = 50.0
    total_collaborations: int = 0
    successful_collaborations: int = 0
    disputed_collaborations: int = 0
    partners: list[str] = Field(default_factory=list)
    success_rate: float = 0.0
    avg_partner_satisfaction: float = 0.0
    recent_ratings: list[CollaborationRating] = Field(default_factory=list)
    reputation_history: list[ReputationSnapshot] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_verified: bool = False


class NegotiationStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTERED = "countered"
    EXPIRED = "expired"
    IN_ESCROW = "in_escrow"
    EXECUTING = "executing"
    COMPLETED = "completed"
    DISPUTED = "disputed"


class CounterOffer(BaseModel):
    counter_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    revised_compensation: Optional[float] = None
    revised_deadline: Optional[datetime] = None
    revised_terms: dict = Field(default_factory=dict)
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MultiPartyProposal(BaseModel):
    """A proposal from one agent to multiple agents for a task."""
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    proposer_agent_id: str
    responder_agent_ids: list[str]
    task_id: str
    required_skills: list[str]
    offered_compensation: float
    deadline: Optional[datetime] = None
    escrow: bool = True
    terms: dict = Field(default_factory=dict)
    status: NegotiationStatus = NegotiationStatus.PROPOSED
    responder_acceptance: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = None


class NegotiationProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    proposer_agent_id: str
    responder_agent_id: str
    task_id: str
    required_skills: list[str]
    offered_compensation: float
    deadline: Optional[datetime] = None
    escrow: bool = True
    terms: dict = Field(default_factory=dict)
    status: NegotiationStatus = NegotiationStatus.PROPOSED
    counter_offers: list[CounterOffer] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = None

    @field_validator("offered_compensation")
    @classmethod
    def validate_offered_compensation(cls, value: float) -> float:
        if value < 0.0:
            raise ValueError("offered_compensation must be non-negative")
        return value


class MultiPartyProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    proposer_agent_id: str
    participant_agent_ids: list[str]
    task_id: str
    required_skills: list[str]
    offered_compensation: float
    compensation_by_agent: dict[str, float] = Field(default_factory=dict)
    deadline: Optional[datetime] = None
    escrow: bool = True
    terms: dict = Field(default_factory=dict)
    status: NegotiationStatus = NegotiationStatus.PROPOSED
    counter_offers: list[CounterOffer] = Field(default_factory=list)
    accepted_agent_ids: list[str] = Field(default_factory=list)
    rejected_agent_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = None

    @field_validator("participant_agent_ids")
    @classmethod
    def validate_participants(cls, value: list[str]) -> list[str]:
        unique = list(dict.fromkeys(value))
        if not unique:
            raise ValueError("participant_agent_ids must include at least one agent")
        return unique

    @field_validator("offered_compensation")
    @classmethod
    def validate_total_offered_compensation(cls, value: float) -> float:
        if value < 0.0:
            raise ValueError("offered_compensation must be non-negative")
        return value

    @field_validator("compensation_by_agent")
    @classmethod
    def validate_compensation_by_agent(cls, value: dict[str, float]) -> dict[str, float]:
        for amount in value.values():
            if amount < 0.0:
                raise ValueError("compensation_by_agent values must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_party_shape(self) -> "MultiPartyProposal":
        if self.proposer_agent_id in self.participant_agent_ids:
            raise ValueError("proposer_agent_id must not be in participant_agent_ids")
        if 1 + len(self.participant_agent_ids) < 2:
            raise ValueError("multi-party proposals require at least two parties")
        unknown = set(self.compensation_by_agent) - set(self.participant_agent_ids) - {self.proposer_agent_id}
        if unknown:
            raise ValueError("compensation_by_agent contains unknown agent_ids")
        return self


class EscrowStatus(str, Enum):
    LOCKED = "locked"
    RELEASED = "released"
    REFUNDED = "refunded"


class Dispute(BaseModel):
    dispute_id: str = Field(default_factory=lambda: str(uuid4()))
    proposal_id: str
    agent_id: str
    reason: str
    description: Optional[str] = None
    evidence: dict = Field(default_factory=dict)
    status: DisputeStatus = DisputeStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    auto_resolve_deadline: Optional[datetime] = None


class EscrowContract(BaseModel):
    escrow_contract_id: str = Field(default_factory=lambda: str(uuid4()))
    proposal_id: str
    amount: float
    status: EscrowStatus = EscrowStatus.LOCKED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TeamStatus(str, Enum):
    FORMING = "forming"
    ACTIVE = "active"
    EXECUTING = "executing"
    COMPLETED = "completed"
    DISSOLVED = "dissolved"


class TeamInteraction(BaseModel):
    agent_id: str
    action: str
    payload: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Team(BaseModel):
    team_id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    agent_ids: list[str]
    role_assignments: dict[str, str] = Field(default_factory=dict)
    required_skills: list[str]
    skill_coverage: dict[str, str] = Field(default_factory=dict)
    shared_state: dict = Field(default_factory=dict)
    interaction_history: list[TeamInteraction] = Field(default_factory=list)
    agreed_terms: dict = Field(default_factory=dict)
    escrow_contract_id: Optional[str] = None
    total_budget: float = 0.0
    status: TeamStatus = TeamStatus.FORMING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None


class TeamAssignment(BaseModel):
    team: Team
    total_cost: float
    optimization_score: float


class TeamFormationError(Exception):
    pass


class NegotiationStateError(Exception):
    pass
