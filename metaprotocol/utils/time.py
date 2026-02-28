"""Timestamp handling utilities."""

from datetime import UTC, datetime, timedelta, timezone


def now_utc() -> datetime:
    """Get current datetime in UTC."""
    return datetime.now(UTC)


def from_iso(iso_string: str) -> datetime:
    """Parse an ISO 8601 string into a datetime."""
    dt = datetime.fromisoformat(iso_string)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def to_iso(dt: datetime) -> str:
    """Convert a datetime to an ISO 8601 string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def hours_from_now(hours: int) -> datetime:
    """Get a datetime X hours from now in UTC."""
    return now_utc() + timedelta(hours=hours)


def days_from_now(days: int) -> datetime:
    """Get a datetime X days from now in UTC."""
    return now_utc() + timedelta(days=days)


def days_ago(days: int) -> datetime:
    """Get a datetime X days ago in UTC."""
    return now_utc() - timedelta(days=days)


def seconds_between(start: datetime, end: datetime) -> float:
    """Get the number of seconds between two datetimes."""
    return (end - start).total_seconds()
