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
# Optional serve import
try:
    from .serve import create_app
except ImportError:
    create_app = None

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
    # CLI and Server
    "cli_app",
    "create_app",
    # Version
    "__version__",
]
