"""Stale skill detection and cleanup."""

from __future__ import annotations

from datetime import timedelta, timezone

from ..store.base import AbstractProtocolStore
from ..utils.time import now_utc, seconds_between


def detect_stale_skills(
    store: AbstractProtocolStore,
    max_age_days: int = 30,
    min_success_rate: float = 0.7,
) -> list[str]:
    """Detect skills that haven't been updated recently or have low success rate."""
    cutoff = now_utc() - timedelta(days=max_age_days)
    rows = store.query("SELECT skill_id, updated_at, success_rate FROM capabilities")

    stale_ids: list[str] = []
    for row in rows:
        updated_at = row["updated_at"]
        if isinstance(updated_at, str):
            from ..utils.time import from_iso
            updated_at = from_iso(updated_at)

        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)

        is_stale = updated_at < cutoff
        is_low_confidence = row["success_rate"] < min_success_rate

        if is_stale and is_low_confidence:
            stale_ids.append(row["skill_id"])

    return stale_ids


def prune_stale_skills(
    store: AbstractProtocolStore,
    max_age_days: int = 90,
    keep_if_success_rate_at_least: float = 0.9,
    dry_run: bool = False,
) -> list[str]:
    """Remove stale skills from the registry."""
    if max_age_days < 0:
        raise ValueError("max_age_days must be non-negative")
    if not 0.0 <= keep_if_success_rate_at_least <= 1.0:
        raise ValueError("keep_if_success_rate_at_least must be between 0 and 1")

    stale_ids = detect_stale_skills(store, max_age_days, keep_if_success_rate_at_least)

    if stale_ids and not dry_run:
        placeholders = ",".join("?" for _ in stale_ids)
        store.execute(f"DELETE FROM capabilities WHERE skill_id IN ({placeholders})", tuple(stale_ids))

    return stale_ids
