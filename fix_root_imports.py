"""Fix market.py and vaos_adapter.py imports."""

from pathlib import Path

# Fix market.py
market_path = Path("metaprotocol/market.py")
if market_path.exists():
    content = market_path.read_text()
    content = content.replace("from ..store import", "from .store import")
    market_path.write_text(content)
    print("Fixed market.py imports")

# Fix vaos_adapter.py
vaos_path = Path("metaprotocol/vaos_adapter.py")
if vaos_path.exists():
    content = vaos_path.read_text()
    content = content.replace("from .storage import", "from .store import")
    content = content.replace("from .protocol import", "from .protocol import")
    vaos_path.write_text(content)
    print("Fixed vaos_adapter.py imports")

print("\nDone!")
