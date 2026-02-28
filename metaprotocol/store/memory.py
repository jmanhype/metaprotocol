"""In-memory storage backend for testing."""

from __future__ import annotations

from typing import Any

from .base import AbstractProtocolStore


class MemoryStore(AbstractProtocolStore):
    """In-memory storage backend for testing."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {
            "capabilities": {},
            "negotiations": {},
            "escrow_contracts": {},
            "reputation": {},
            "teams": {},
            "disputes": {},
        }

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        """Execute a SQL statement (simplified in-memory implementation)."""
        return None

    def executemany(self, sql: str, rows: list[tuple[Any, ...]]) -> Any:
        """Execute a SQL statement multiple times (simplified in-memory implementation)."""
        return None

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Query the in-memory store (simplified implementation)."""
        return []

    def query_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        """Query the in-memory store for a single result (simplified)."""
        return None

    def clear(self) -> None:
        """Clear all in-memory data."""
        for key in self._data:
            self._data[key] = {}
