"""MetaProtocol main orchestration class."""

from __future__ import annotations

from pathlib import Path

from .store import SQLiteStore
from .registry import SkillRegistry, EmbeddingEngine
from .reputation import ReputationSystem, DisputeResolver
from .negotiation import NegotiationEngine
from .team import TeamFormationEngine, TeamMemory
from .market import MarketRates
from .vaos_adapter import VAOSAdapter


class MetaProtocol:
    """Main MetaProtocol orchestration class."""

    def __init__(
        self,
        db_path: str | Path = ".metaprotocol.db",
        strategy: str = "greedy",
        max_team_size: int = 10,
        enable_embeddings: bool = False,
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.store = SQLiteStore(db_path=db_path)

        # Initialize embedding engine if enabled
        embedding_engine = None
        if enable_embeddings:
            embedding_engine = EmbeddingEngine(model_name=embedding_model)

        # Initialize components
        self.registry = SkillRegistry(
            self.store,
            enable_vector_search=enable_embeddings,
            embedding_engine=embedding_engine,
        )
        self.reputation = ReputationSystem(self.store)
        self.negotiation = NegotiationEngine(self.store)
        self.formation = TeamFormationEngine(
            self.store,
            strategy=strategy,
            max_team_size=max_team_size,
        )
        self.memory = TeamMemory(self.store)
        self.disputes = DisputeResolver(self.store)
        self.market = MarketRates(self.store)

    @property
    def db_path(self) -> str:
        """Get the database path."""
        return self.store.db_path

    def create_vaos_adapter(self, vaos_db_path: str) -> VAOSAdapter:
        """Create a VAOS adapter for this protocol instance."""
        return VAOSAdapter(self, vaos_db_path=vaos_db_path)
