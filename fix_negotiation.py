"""Fix negotiation engine.py import."""

from pathlib import Path

path = Path("metaprotocol/negotiation/engine.py")
content = path.read_text()

# Fix the import - NegotiationStateError should come from exceptions, not types
content = content.replace(
    "from ..types import (\n    CounterOffer,\n    EscrowContract,\n    EscrowStatus,\n    MultiPartyProposal,\n    NegotiationProposal,\n    NegotiationStateError,\n    NegotiationStatus,\n)",
    "from ..exceptions import NegotiationStateError\nfrom ..types import (\n    CounterOffer,\n    EscrowContract,\n    EscrowStatus,\n    MultiPartyProposal,\n    NegotiationProposal,\n    NegotiationStatus,\n)"
)

path.write_text(content)
print("Fixed negotiation/engine.py imports")
