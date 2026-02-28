"""FastAPI server."""

try:
    from .routes import create_app
    __all__ = ["create_app"]
except ImportError:
    create_app = None
    __all__ = []
