"""PostgreSQL backend for production deployments."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class PostgreSQLStore:
    """PostgreSQL storage backend for MetaProtocol."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "metaprotocol",
        user: str = "postgres",
        password: str = "",
        min_size: int = 5,
        max_size: int = 10,
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self._pool = None

    @property
    def pool(self) -> Any:
        """Lazy-load connection pool."""
        if self._pool is None:
            try:
                import asyncpg
            except ImportError as e:
                raise ImportError(
                    "asyncpg is required for PostgreSQL backend. "
                    "Install with: pip install metaprotocol[sql]"
                ) from e

            self._pool = asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_size,
                max_size=self.max_size,
            )

        return self._pool

    async def _init_schema(self) -> None:
        """Initialize database schema."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS capabilities (
                    skill_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    complexity_level TEXT NOT NULL,
                    success_rate REAL NOT NULL,
                    cost_per_use REAL NOT NULL,
                    embedding_json JSONB,
                    metadata_json JSONB NOT NULL,
                    registered_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS negotiations (
                    proposal_id TEXT PRIMARY KEY,
                    payload_json JSONB NOT NULL
                );

                CREATE TABLE IF NOT EXISTS escrow_contracts (
                    escrow_contract_id TEXT PRIMARY KEY,
                    proposal_id TEXT UNIQUE NOT NULL,
                    payload_json JSONB NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reputation (
                    agent_id TEXT PRIMARY KEY,
                    payload_json JSONB NOT NULL
                );

                CREATE TABLE IF NOT EXISTS teams (
                    team_id TEXT PRIMARY KEY,
                    payload_json JSONB NOT NULL
                );

                CREATE TABLE IF NOT EXISTS team_memory (
                    team_id TEXT PRIMARY KEY,
                    payload_json JSONB NOT NULL
                );

                CREATE TABLE IF NOT EXISTS disputes (
                    dispute_id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    payload_json JSONB NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_capabilities_agent ON capabilities(agent_id);
                CREATE INDEX IF NOT EXISTS idx_capabilities_name ON capabilities(name);
                CREATE INDEX IF NOT EXISTS idx_reputation_agent ON reputation(agent_id);
                CREATE INDEX IF NOT EXISTS idx_negotiations_task ON negotiations(proposal_id);
                CREATE INDEX IF NOT EXISTS idx_teams_task ON teams(team_id);
                CREATE INDEX IF NOT EXISTS idx_disputes_proposal ON disputes(proposal_id);
                """
            )

    async def execute(self, sql: str, params: tuple[Any, ...] = ()) -> str:
        """Execute a SQL statement."""
        async with self.pool.acquire() as conn:
            return await conn.execute(sql, *params)

    async def executemany(self, sql: str, params_list: list[tuple[Any, ...]]) -> str:
        """Execute a SQL statement multiple times."""
        async with self.pool.acquire() as conn:
            return await conn.executemany(sql, params_list)

    async def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Query database."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]

    async def query_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        """Query database and return a single row."""
        rows = await self.query(sql, params)
        return rows[0] if rows else None

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()

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

    async def __aenter__(self) -> "PostgreSQLStore":
        """Async context manager entry."""
        await self._init_schema()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
