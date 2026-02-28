"""Create all remaining modules for the restructured metaprotocol."""

from pathlib import Path

# Registry module files
registry_init = '''"""Skill registry and discovery."""

from .skill_registry import SkillRegistry
from .embedding import EmbeddingEngine

__all__ = ["SkillRegistry", "EmbeddingEngine"]
'''

# Reputation module files
reputation_init = '''"""Reputation and dispute management."""

from .reputation_system import ReputationSystem
from .dispute import DisputeResolver

__all__ = ["ReputationSystem", "DisputeResolver"]
'''

# Negotiation module files
negotiation_init = '''"""Negotiation engine and state machine."""

from .engine import NegotiationEngine

__all__ = ["NegotiationEngine"]
'''

# Team module files
team_init = '''"""Team formation and memory management."""

from .formation import TeamFormationEngine, TeamMemory

__all__ = ["TeamFormationEngine", "TeamMemory"]
'''

# Serve module files
serve_init = '''"""FastAPI server."""

from .routes import create_app

__all__ = ["create_app"]
'''

# CLI module files
cli_init = '''"""Command-line interface."""

from .main import app

__all__ = ["app"]
'''

# Create __init__.py files
init_files = {
    "metaprotocol/registry/__init__.py": registry_init,
    "metaprotocol/reputation/__init__.py": reputation_init,
    "metaprotocol/negotiation/__init__.py": negotiation_init,
    "metaprotocol/team/__init__.py": team_init,
    "metaprotocol/serve/__init__.py": serve_init,
    "metaprotocol/cli/__init__.py": cli_init,
}

for file_path, content in init_files.items():
    path = Path(file_path)
    path.write_text(content)
    print(f"Created {file_path}")

print("\nAll __init__.py files created!")
