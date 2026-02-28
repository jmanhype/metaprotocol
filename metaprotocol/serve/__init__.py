"""FastAPI server."""

try:
    from .routes import create_app
    _create_app = create_app
    from .app import create_server
    _create_server = create_server
except ImportError:
    _create_app = None
    _create_server = None

__all__ = ["create_app", "create_server"]

def create_app(*args, **kwargs):
    """Wrapper for create_app with import check."""
    if _create_app is None:
        raise ImportError(
            "FastAPI is required for server mode. "
            "Install with: pip install metaprotocol[serve]"
        )
    return _create_app(*args, **kwargs)

def create_server(*args, **kwargs):
    """Wrapper for create_server with import check."""
    if _create_server is None:
        raise ImportError(
            "FastAPI is required for server mode. "
            "Install with: pip install metaprotocol[serve]"
        )
    return _create_server(*args, **kwargs)
