"""Public API for MetaProtocol."""

from .types import (
    AgentCapability,
    ComplexityLevel,
    DiscoveryResult,
    DiscoveryMatch,
    Dispute,
    DisputeStatus,
    EscrowContract,
    EscrowStatus,
    MultiPartyProposal,
    NegotiationProposal,
    NegotiationStatus,
    ReputationRecord,
    Team,
    TeamAssignment,
    TeamStatus,
    TeamInteraction,
    CollaborationRating,
    ReputationSnapshot,
    CounterOffer,
)
from .exceptions import (
    ProtocolError,
    NegotiationStateError,
    TeamFormationError,
    DisputeError,
    MarketError,
    StorageError,
)
from .registry import SkillRegistry, EmbeddingEngine
from .reputation import ReputationSystem, DisputeResolver
from .negotiation import NegotiationEngine
from .team import TeamFormationEngine, TeamMemory
from .store import AbstractProtocolStore, SQLiteStore, MemoryStore
from .cli import app as cli_app
from .serve import create_app, create_server
from .protocol import MetaProtocol
from .market import MarketRates
from .vaos_adapter import VAOSAdapter
from .utils import (
    generate_id,
    parse_id,
    now_utc,
    from_iso,
    to_iso,
    hours_from_now,
    days_from_now,
    days_ago,
    seconds_between,
)

__version__ = "0.2.0"

__all__ = [
    # Types
    "AgentCapability",
    "ComplexityLevel",
    "DiscoveryResult",
    "DiscoveryMatch",
    "Dispute",
    "DisputeStatus",
    "EscrowContract",
    "EscrowStatus",
    "MultiPartyProposal",
    "NegotiationProposal",
    "NegotiationStatus",
    "ReputationRecord",
    "Team",
    "TeamAssignment",
    "TeamStatus",
    "TeamInteraction",
    "CollaborationRating",
    "ReputationSnapshot",
    "CounterOffer",
    # Exceptions
    "ProtocolError",
    "NegotiationStateError",
    "TeamFormationError",
    "DisputeError",
    "MarketError",
    "StorageError",
    # Core components
    "SkillRegistry",
    "EmbeddingEngine",
    "ReputationSystem",
    "DisputeResolver",
    "NegotiationEngine",
    "TeamFormationEngine",
    "TeamMemory",
    # Storage
    "AbstractProtocolStore",
    "SQLiteStore",
    "MemoryStore",
    # Additional components
    "MetaProtocol",
    "MarketRates",
    "VAOSAdapter",
    # CLI and Server
    "cli_app",
    "create_app",
    "create_server",
    # Utils
    "generate_id",
    "parse_id",
    "now_utc",
    "from_iso",
    "to_iso",
    "hours_from_now",
    "days_from_now",
    "days_ago",
    "seconds_between",
    # Version
    "__version__",
]
