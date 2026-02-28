"""Market rate validation for compensation offers."""
from __future__ import annotations

from typing import Any

from .storage import SQLiteStore


class MarketRates:
    """Computes and validates compensation rates against market data."""

    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def get_market_rate(self, skill_name: str, complexity: str | None = None) -> float:
        """Get the median market rate for a skill (cost_per_use)."""
        query = "SELECT cost_per_use, complexity_level FROM capabilities WHERE name = ?"
        rows = self.store.query(query, (skill_name,))

        if not rows:
            return 0.0

        costs = []
        for row in rows:
            if complexity is None or row["complexity_level"] == complexity:
                costs.append(row["cost_per_use"])

        if not costs:
            if complexity is None:
                return sum(row["cost_per_use"] for row in rows) / len(rows)
            return 0.0

        costs.sort()
        n = len(costs)
        if n % 2 == 0:
            median = (costs[n // 2 - 1] + costs[n // 2]) / 2
        else:
            median = costs[n // 2]

        return median

    def get_rate_percentile(self, skill_name: str, cost: float, complexity: str | None = None) -> float:
        """Get what percentile a given cost falls into for a skill."""
        query = "SELECT cost_per_use, complexity_level FROM capabilities WHERE name = ?"
        rows = self.store.query(query, (skill_name,))

        if not rows:
            return 0.5

        costs = []
        for row in rows:
            if complexity is None or row["complexity_level"] == complexity:
                costs.append(row["cost_per_use"])

        if not costs:
            costs = [row["cost_per_use"] for row in rows]

        costs.sort()
        rank = sum(1 for c in costs if c <= cost)
        return rank / max(1, len(costs))

    def validate_compensation(
        self,
        required_skills: list[str],
        offered_compensation: float,
        complexity: str | None = None,
        tolerance: float = 0.2,
    ) -> dict[str, Any]:
        """Validate if offered compensation is within market range."""
        total_market_rate = 0.0
        skill_rates: dict[str, float] = {}

        for skill in required_skills:
            rate = self.get_market_rate(skill, complexity)
            skill_rates[skill] = rate
            total_market_rate += rate

        is_below_market = offered_compensation < total_market_rate * (1.0 - tolerance)
        is_above_market = offered_compensation > total_market_rate * (1.0 + tolerance)

        return {
            "total_market_rate": total_market_rate,
            "offered_compensation": offered_compensation,
            "is_below_market": is_below_market,
            "is_above_market": is_above_market,
            "difference": offered_compensation - total_market_rate,
            "difference_percent": (offered_compensation / total_market_rate - 1.0) * 100 if total_market_rate > 0 else 0,
            "skill_rates": skill_rates,
        }

    def get_rate_trends(self, skill_name: str, days: int = 30) -> dict[str, float]:
        """Get rate trends for a skill over time."""
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        query = """
            SELECT cost_per_use, updated_at
            FROM capabilities
            WHERE name = ? AND updated_at >= ?
            ORDER BY updated_at
        """
        rows = self.store.query(query, (skill_name, cutoff.isoformat()))

        if len(rows) < 2:
            return {"trend": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0, "count": len(rows)}

        costs = [row["cost_per_use"] for row in rows]

        avg = sum(costs) / len(costs)
        min_cost = min(costs)
        max_cost = max(costs)

        if len(costs) >= 3:
            early_avg = sum(costs[: len(costs) // 2]) / (len(costs) // 2)
            late_avg = sum(costs[len(costs) // 2 :]) / (len(costs) - len(costs) // 2)
            trend = (late_avg - early_avg) / max(early_avg, 0.001)
        else:
            trend = 0.0

        return {
            "trend": trend,
            "avg": avg,
            "min": min_cost,
            "max": max_cost,
            "count": len(costs),
        }

    def recommend_compensation(
        self,
        required_skills: list[str],
        complexity: str | None = None,
        target_percentile: float = 0.5,
    ) -> dict[str, float]:
        """Recommended compensation for a set of skills at a target percentile."""
        recommendations: dict[str, float] = {}

        for skill in required_skills:
            query = "SELECT cost_per_use, complexity_level FROM capabilities WHERE name = ?"
            rows = self.store.query(query, (skill,))

            if not rows:
                recommendations[skill] = 0.0
                continue

            costs = []
            for row in rows:
                if complexity is None or row["complexity_level"] == complexity:
                    costs.append(row["cost_per_use"])

            if not costs:
                costs = [row["cost_per_use"] for row in rows]

            costs.sort()
            idx = min(len(costs) - 1, int(len(costs) * target_percentile))
            recommendations[skill] = costs[idx]

        total = sum(recommendations.values())
        recommendations["_total"] = total

        return recommendations
