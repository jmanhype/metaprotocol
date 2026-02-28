"""Fix imports across all moved files."""

from pathlib import Path
import re

# Import mapping for moved files
import_fixes = {
    # skill_registry.py
    "from .models import": "from ..types import",
    "from .storage import": "from ..store import",
    "ComplexityLevel": "ComplexityLevel",
    "DiscoveryMatch": "DiscoveryMatch",
    "DiscoveryResult": "DiscoveryResult",
    "AgentCapability": "AgentCapability",
    
    # reputation_system.py
    "from .models import": "from ..types import",
    "from .storage import": "from ..store import",
    "ReputationRecord": "ReputationRecord",
    
    # dispute.py
    "from .models import": "from ..types import",
    "from .storage import": "from ..store import",
    
    # engine.py (negotiation)
    "from .models import": "from ..types import",
    "from .storage import": "from ..store import",
    
    # formation.py (team)
    "from .models import": "from ..types import",
    "from .storage import": "from ..store import",
}

files_to_fix = [
    "metaprotocol/registry/skill_registry.py",
    "metaprotocol/reputation/reputation_system.py",
    "metaprotocol/reputation/dispute.py",
    "metaprotocol/negotiation/engine.py",
    "metaprotocol/team/formation.py",
]

for file_path in files_to_fix:
    path = Path(file_path)
    if not path.exists():
        print(f"Skipping {file_path} (not found)")
        continue

    content = path.read_text()

    # Fix imports
    content = re.sub(r"from \.models import", "from ..types import", content)
    content = re.sub(r"from \.storage import", "from ..store import", content)
    content = re.sub(r"SQLiteStore", "SQLiteStore", content)
    
    path.write_text(content)
    print(f"Fixed imports in {file_path}")

print("\nImport fixes complete!")
print("Note: Some files may still need manual import adjustments.")
