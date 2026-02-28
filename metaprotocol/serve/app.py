"""FastAPI application factory for MetaProtocol."""

from __future__ import annotations

from fastapi import FastAPI

from ..store.base import AbstractProtocolStore


def create_server(title: str = "MetaProtocol", version: str = "0.2.0") -> FastAPI:
    """Create and configure FastAPI application."""
    return FastAPI(
        title=title,
        description="Coordination protocol for autonomous agents",
        version=version,
    )
