"""UUID generation utilities."""

from uuid import uuid4, UUID


def generate_id() -> str:
    """Generate a random UUID string."""
    return str(uuid4())


def parse_id(value: str) -> UUID:
    """Parse a string into a UUID object."""
    return UUID(value)
