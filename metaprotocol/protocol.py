from __future__ import annotations

from pathlib import Path

from .negotiation import NegotiationEngine
from .registry import SkillRegistry
from .reputation import ReputationSystem
from .storage import SQLiteStore
from .team import TeamFormationEngine, TeamMemory


class MetaProtocol:
    def __init__(self, db_path: str | Path = ".metaprotocol.db") -> None:
        self.store = SQLiteStore(db_path=db_path)
        self.registry = SkillRegistry(self.store)
        self.negotiation = NegotiationEngine(self.store)
        self.reputation = ReputationSystem(self.store)
        self.formation = TeamFormationEngine(self.store)
        self.memory = TeamMemory(self.store)
