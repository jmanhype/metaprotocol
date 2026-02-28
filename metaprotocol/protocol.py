from __future__ import annotations

from pathlib import Path

from .disputes import DisputeResolver
from .market import MarketRates
from .negotiation import NegotiationEngine
from .registry import SkillRegistry
from .reputation import ReputationSystem
from .storage import SQLiteStore
from .team import TeamFormationEngine, TeamMemory
from .embedding import EmbeddingEngine


class MetaProtocol:
    def __init__(
        self,
        db_path: str | Path = ".metaprotocol.db",
        strategy: str = "greedy",
        max_team_size: int = 10,
        enable_embeddings: bool = False,
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.store = SQLiteStore(db_path=db_path)
        self.registry = SkillRegistry(self.store)
        self.negotiation = NegotiationEngine(self.store)
        self.reputation = ReputationSystem(self.store)
        self.formation = TeamFormationEngine(
            self.store,
            strategy=strategy,
            max_team_size=max_team_size,
        )
        self.memory = TeamMemory(self.store)
        self.disputes = DisputeResolver(self.store)
        self.market = MarketRates(self.store)

        self.embedding_engine: EmbeddingEngine | None = None
        if enable_embeddings:
            self.embedding_engine = EmbeddingEngine(model_name=embedding_model)
