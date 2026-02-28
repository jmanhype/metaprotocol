from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..types import AgentCapability, ComplexityLevel, DiscoveryMatch, DiscoveryResult
from ..store import SQLiteStore


_COMPLEXITY_ORDER = {
    ComplexityLevel.BASIC.value: 1,
    ComplexityLevel.INTERMEDIATE.value: 2,
    ComplexityLevel.ADVANCED.value: 3,
}


class SkillRegistry:
    def __init__(
        self,
        store: SQLiteStore,
        enable_vector_search: bool = False,
        embedding_engine=None,
    ) -> None:
        self.store = store
        self.enable_vector_search = enable_vector_search
        self.embedding_engine = embedding_engine

    def register(self, capability: AgentCapability) -> AgentCapability:
        if self.enable_vector_search and self.embedding_engine and capability.embedding is None:
            capability.embedding = self.embedding_engine.encode_skill(
                name=capability.name,
                description=capability.description,
            )

        self.store.execute(
            """
            INSERT INTO capabilities (
                skill_id, agent_id, name, description, complexity_level, success_rate,
                cost_per_use, embedding_json, metadata_json, registered_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(skill_id) DO UPDATE SET
                agent_id=excluded.agent_id,
                name=excluded.name,
                description=excluded.description,
                complexity_level=excluded.complexity_level,
                success_rate=excluded.success_rate,
                cost_per_use=excluded.cost_per_use,
                embedding_json=excluded.embedding_json,
                metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at
            """,
            (
                capability.skill_id,
                capability.agent_id,
                capability.name,
                capability.description,
                capability.complexity_level.value,
                capability.success_rate,
                capability.cost_per_use,
                self.store.dumps_json(capability.embedding) if capability.embedding is not None else None,
                self.store.dumps_json(capability.metadata),
                capability.registered_at.isoformat(),
                capability.updated_at.isoformat(),
            ),
        )
        return capability

    def discover(
        self,
        required_skills: list[str] | None = None,
        query: str | None = None,
        complexity_min: ComplexityLevel | None = None,
        max_cost_per_use: float | None = None,
        limit: int = 20,
    ) -> DiscoveryResult:
        rows = self.store.query("SELECT * FROM capabilities")
        reputation_rows = self.store.query("SELECT agent_id, payload_json FROM reputation")
        reputation_by_agent: dict[str, float] = {}
        for row in reputation_rows:
            payload = self.store.loads_json(row["payload_json"])
            score = float(payload.get("reputation_score", 50.0))
            reputation_by_agent[row["agent_id"]] = max(0.0, min(100.0, score))

        required = {skill.strip().lower() for skill in (required_skills or []) if skill.strip()}
        query_tokens = {t for t in (query or "").lower().split() if t}

        semantic_matches: set[str] = set()
        if self.enable_vector_search and self.embedding_engine and query:
            from numpy import array

            skill_embeddings: dict[str, list[float]] = {}
            skill_texts: dict[str, str] = {}

            for row in rows:
                embedding_json = row.get("embedding_json")
                if embedding_json:
                    embedding = self.store.loads_json(embedding_json)
                    skill_embeddings[row["skill_id"]] = embedding
                    skill_texts[row["skill_id"]] = f"{row['name']}: {row['description'] or ''}"

            if skill_embeddings:
                try:
                    matches = self.embedding_engine.find_best_match(
                        query=query,
                        skill_embeddings=skill_embeddings,
                        skill_texts=skill_texts,
                        top_k=limit * 2,
                    )
                    semantic_matches = {skill_id for skill_id, _ in matches}
                except Exception:
                    pass

        matches: list[DiscoveryMatch] = []

        for row in rows:
            name = row["name"]
            name_l = name.lower()
            desc = (row["description"] or "").lower()

            if required and name_l not in required:
                if not (self.enable_vector_search and row["skill_id"] in semantic_matches):
                    continue
            if complexity_min and _COMPLEXITY_ORDER[row["complexity_level"]] < _COMPLEXITY_ORDER[complexity_min.value]:
                continue
            if max_cost_per_use is not None and row["cost_per_use"] > max_cost_per_use:
                continue

            relevance = 0.6
            if query_tokens:
                text = f"{name_l} {desc}"
                overlap = sum(1 for token in query_tokens if token in text)
                relevance = min(1.0, overlap / max(1, len(query_tokens)))

            if row["skill_id"] in semantic_matches:
                relevance = max(relevance, 0.7)

            updated_at = datetime.fromisoformat(row["updated_at"])
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            age_days = max(0.0, (datetime.now(timezone.utc) - updated_at).total_seconds() / 86400.0)
            freshness = max(0.1, 1.0 - min(age_days, 90.0) / 90.0)
            success_rate = float(row["success_rate"])
            cost = float(row["cost_per_use"])
            cost_component = 1.0 / (1.0 + cost)
            reputation = reputation_by_agent.get(row["agent_id"], 50.0) / 100.0

            overall = (
                0.35 * relevance
                + 0.2 * freshness
                + 0.2 * success_rate
                + 0.1 * cost_component
                + 0.15 * reputation
            )

            matches.append(
                DiscoveryMatch(
                    agent_id=row["agent_id"],
                    skill_id=row["skill_id"],
                    name=row["name"],
                    complexity_level=ComplexityLevel(row["complexity_level"]),
                    cost_per_use=cost,
                    success_rate=success_rate,
                    relevance_score=round(relevance, 4),
                    freshness_score=round(freshness, 4),
                    reputation_score=round(reputation, 4),
                    overall_score=round(overall, 4),
                )
            )

        matches.sort(key=lambda m: m.overall_score, reverse=True)
        return DiscoveryResult(matches=matches[:limit])

    def prune_stale_skills(
        self,
        max_age_days: int = 90,
        keep_if_success_rate_at_least: float = 0.9,
        dry_run: bool = False,
    ) -> list[str]:
        if max_age_days < 0:
            raise ValueError("max_age_days must be non-negative")
        if not 0.0 <= keep_if_success_rate_at_least <= 1.0:
            raise ValueError("keep_if_success_rate_at_least must be between 0 and 1")

        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        rows = self.store.query("SELECT skill_id, updated_at, success_rate FROM capabilities")
        stale_ids: list[str] = []
        for row in rows:
            updated_at = datetime.fromisoformat(row["updated_at"])
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            is_stale = updated_at < cutoff
            is_low_confidence = float(row["success_rate"]) < keep_if_success_rate_at_least
            if is_stale and is_low_confidence:
                stale_ids.append(row["skill_id"])

        if stale_ids and not dry_run:
            placeholders = ",".join("?" for _ in stale_ids)
            self.store.execute(f"DELETE FROM capabilities WHERE skill_id IN ({placeholders})", tuple(stale_ids))
        return stale_ids
