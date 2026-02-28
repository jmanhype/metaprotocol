"""Abstract storage interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class AbstractProtocolStore(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        """Execute a SQL statement."""
        pass

    @abstractmethod
    def executemany(self, sql: str, rows: list[tuple[Any, ...]]) -> Any:
        """Execute a SQL statement multiple times."""
        pass

    @abstractmethod
    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Query the database."""
        pass

    @abstractmethod
    def query_one(self, sql: str, params: tuple[Any, ...] = ()) -> Optional[dict[str, Any]]:
        """Query the database and return a single row."""
        pass

    @staticmethod
    def dumps_json(payload: Any) -> str:
        """Serialize to JSON."""
        import json
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)

    @staticmethod
    def loads_json(payload: str) -> Any:
        """Deserialize from JSON."""
        import json
        return json.loads(payload)
