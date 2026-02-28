"""Custom exceptions for MetaProtocol."""


class ProtocolError(Exception):
    """Base exception for all protocol errors."""
    pass


class NegotiationStateError(ProtocolError):
    """Invalid negotiation state transition attempted."""
    pass


class TeamFormationError(ProtocolError):
    """Error during team formation."""
    pass


class DisputeError(ProtocolError):
    """Error during dispute operations."""
    pass


class MarketError(ProtocolError):
    """Error during market rate operations."""
    pass


class StorageError(ProtocolError):
    """Error during storage operations."""
    pass
