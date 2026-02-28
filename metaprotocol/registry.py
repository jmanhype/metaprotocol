from __future__ import annotations

from datetime import datetime, timezone

from .models import AgentCapability, ComplexityLevel, DiscoveryMatch, DiscoveryResult
from .storage import SQLiteStore


_COMPLEXITY_ORDER = {
    ComplexityLevel.BASIC.value: 1,
    ComplexityLevel.INTERMEDIATE.value: 2,
    ComplexityLevel.ADVANCED.value: 3,
}


class SkillRegistry:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def register(self, capability: AgentCapability) -> AgentCapability:
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
        required = {skill.strip().lower() for skill in (required_skills or []) if skill.strip()}
        query_tokens = {t for t in (query or "").lower().split() if t}
        matches: list[DiscoveryMatch] = []

        for row in rows:
            name = row["name"]
            name_l = name.lower()
            desc = (row["description"] or "").lower()
            if required and name_l not in required:
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

            updated_at = datetime.fromisoformat(row["updated_at"])
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            age_days = max(0.0, (datetime.now(timezone.utc) - updated_at).total_seconds() / 86400.0)
            freshness = max(0.1, 1.0 - min(age_days, 90.0) / 90.0)
            success_rate = float(row["success_rate"])
            cost = float(row["cost_per_use"])
            cost_component = 1.0 / (1.0 + cost)

            overall = 0.4 * relevance + 0.25 * freshness + 0.25 * success_rate + 0.1 * cost_component

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
                    overall_score=round(overall, 4),
                )
            )

        matches.sort(key=lambda m: m.overall_score, reverse=True)
        return DiscoveryResult(matches=matches[:limit])
