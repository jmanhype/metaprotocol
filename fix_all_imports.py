"""Fix imports across all files."""

from pathlib import Path
import re

# Read each file and fix imports
files_to_fix = {
    "metaprotocol/registry/skill_registry.py": [
        ("from .models import", "from ..types import"),
        ("from .storage import", "from ..store import"),
        ("SQLiteStore", "SQLiteStore"),
    ],
    "metaprotocol/registry/embedding.py": [
        ("from .models import", "from ..types import"),
    ],
    "metaprotocol/registry/ranking.py": [
        ("from ..models import", "from ..types import"),
    ],
    "metaprotocol/registry/pruning.py": [
        ("from ..store.base import", "from ..store.base import"),
        ("from ..utils.time import", "from ..utils.time import"),
    ],
    "metaprotocol/reputation/reputation_system.py": [
        ("from .models import", "from ..types import"),
        ("from .storage import", "from ..store import"),
    ],
    "metaprotocol/reputation/dispute.py": [
        ("from .models import", "from ..types import"),
        ("from .storage import", "from ..store import"),
    ],
    "metaprotocol/reputation/scoring.py": [
        ("from ..types import", "from ..types import"),
    ],
    "metaprotocol/reputation/decay.py": [
        ("from ..store.base import", "from ..store.base import"),
        ("from ..utils.time import", "from ..utils.time import"),
        ("from ..types import", "from ..types import"),
    ],
    "metaprotocol/reputation/sybil.py": [
        ("from ..store.base import", "from ..store.base import"),
        ("from ..types import", "from ..types import"),
    ],
    "metaprotocol/negotiation/engine.py": [
        ("from ..types import", "from ..types import"),
        ("from ..store import", "from ..store import"),
    ],
    "metaprotocol/negotiation/state_machine.py": [
        ("from ..types import", "from ..types import"),
    ],
    "metaprotocol/negotiation/escrow.py": [
        ("from ..types import", "from ..types import"),
        ("from ..utils.time import", "from ..utils.time import"),
    ],
    "metaprotocol/negotiation/multiparty.py": [
        ("from ..types import", "from ..types import"),
    ],
    "metaprotocol/negotiation/expiration.py": [
        ("from ..types import", "from ..types import"),
        ("from ..utils.time import", "from ..utils.time import"),
    ],
    "metaprotocol/team/formation.py": [
        ("from ..types import", "from ..types import"),
        ("from ..store import", "from ..store import"),
    ],
    "metaprotocol/team/optimizer_greedy.py": [
        ("from .models import", "from ..types import"),
        ("from .storage import", "from ..store import"),
    ],
    "metaprotocol/team/optimizer_ilp.py": [
        ("from ..types import", "from ..types import"),
        ("from ..store.base import", "from ..store.base import"),
    ],
    "metaprotocol/team/memory.py": [
        ("from ..types import", "from ..types import"),
        ("from ..store.base import", "from ..store.base import"),
    ],
    "metaprotocol/team/lifecycle.py": [
        ("from ..types import", "from ..types import"),
    ],
    "metaprotocol/serve/routes.py": [
        ("from .protocol import", "from ..protocol import"),
    ],
    "metaprotocol/cli/main.py": [
        ("from .models import", "from ..types import"),
        ("from .protocol import", "from ..protocol import"),
        ("from .exceptions import", "from ..exceptions import"),
    ],
    "metaprotocol/market.py": [
        ("from .storage import", "from ..store import"),
    ],
    "metaprotocol/vaos_adapter.py": [
        ("from .storage import", "from ..store import"),
    ],
    "metaprotocol/protocol.py": [
        ("from .store import", "from .store import"),
    ],
}

for file_path, replacements in files_to_fix.items():
    path = Path(file_path)
    if not path.exists():
        print(f"Skipping {file_path} (not found)")
        continue

    content = path.read_text()

    for old, new in replacements:
        content = content.replace(old, new)

    path.write_text(content)
    print(f"Fixed imports in {file_path}")

print("\nAll import fixes applied!")
