"""Fix vaos_adapter.py models import."""

from pathlib import Path

vaos_path = Path("metaprotocol/vaos_adapter.py")
if vaos_path.exists():
    content = vaos_path.read_text()
    content = content.replace("from .models import", "from .types import")
    content = content.replace("ComplexityLevel", "ComplexityLevel")
    vaos_path.write_text(content)
    print("Fixed vaos_adapter.py models import")

# Also check protocol.py for similar issues
protocol_path = Path("metaprotocol/protocol.py")
if protocol_path.exists():
    content = protocol_path.read_text()
    content = content.replace("Complexity", "ComplexityLevel")
    protocol_path.write_text(content)
    print("Fixed protocol.py ComplexityLevel typo")

print("\nDone!")
