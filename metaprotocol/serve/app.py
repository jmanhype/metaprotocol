"""FastAPI application for MetaProtocol."""

from fastapi import FastAPI

from .routes import create_app


def create_server() -> FastAPI:
    """Create and configure FastAPI application."""
    return FastAPI(
        title="MetaProtocol API",
        description="Coordination protocol for autonomous agents",
        version="0.2.0",
    )
