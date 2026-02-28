"""SQLite storage backend."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .base import AbstractProtocolStore


class SQLiteStore(AbstractProtocolStore):
    """SQLite-based storage backend for MetaProtocol."""

    def __init__(self, db_path: str | Path = ".metaprotocol.db") -> None:
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS capabilities (
                skill_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                complexity_level TEXT NOT NULL,
                success_rate REAL NOT NULL,
                cost_per_use REAL NOT NULL,
                embedding_json TEXT,
                metadata_json TEXT NOT NULL,
                registered_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS negotiations (
                proposal_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS escrow_contracts (
                escrow_contract_id TEXT PRIMARY KEY,
                proposal_id TEXT UNIQUE NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reputation (
                agent_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS teams (
                team_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS disputes (
                dispute_id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_capabilities_agent ON capabilities(agent_id);
            CREATE INDEX IF NOT EXISTS idx_capabilities_name ON capabilities(name);
            CREATE INDEX IF NOT EXISTS idx_reputation_agent ON reputation(agent_id);
            CREATE INDEX IF NOT EXISTS idx_negotiations_task ON negotiations(proposal_id);
            CREATE INDEX IF NOT EXISTS idx_teams_task ON teams(team_id);
            CREATE INDEX IF NOT EXISTS idx_disputes_proposal ON disputes(proposal_id);
            """
        )
        self.conn.commit()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def executemany(self, sql: str, rows: list[tuple[Any, ...]]) -> None:
        cur = self.conn.cursor()
        cur.executemany(sql, rows)
        self.conn.commit()

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def query_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
