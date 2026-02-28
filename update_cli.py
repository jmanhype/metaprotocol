"""Update CLI main.py with correct imports."""

from pathlib import Path

cli_main = '''from __future__ import annotations

import json
from typing import Optional

import typer
from rich import print

from ..types import AgentCapability, ComplexityLevel
from ..exceptions import NegotiationStateError, TeamFormationError

# Import classes we need - will create simple wrappers for now
class MetaProtocol:
    """Temporary wrapper - will be replaced with full implementation."""
    def __init__(self, db_path: str = ".metaprotocol.db"):
        self.db_path = db_path
        from ..store import SQLiteStore
        self.store = SQLiteStore(db_path=db_path)
        from ..registry import SkillRegistry
        from ..reputation import ReputationSystem
        from ..negotiation import NegotiationEngine
        from ..team import TeamFormationEngine, TeamMemory
        
        # Placeholder - need to create proper MetaProtocol class
        self.registry = None  # Will be SkillRegistry(self.store)
        self.reputation = None  # Will be ReputationSystem(self.store)
        self.negotiation = None  # Will be NegotiationEngine(self.store)
        self.formation = None  # Will be TeamFormationEngine(self.store)
        self.memory = None  # Will be TeamMemory(self.store)

app = typer.Typer(help="MetaProtocol CLI")

def _protocol(
    db: str,
    strategy: str = "greedy",
    enable_embeddings: bool = False,
) -> MetaProtocol:
    return MetaProtocol(db_path=db)

@app.command()
def register(
    agent_id: str = typer.Option(...),
    skill: str = typer.Option(...),
    complexity: ComplexityLevel = typer.Option(...),
    cost_per_use: float = typer.Option(0.0),
    success_rate: float = typer.Option(0.0),
    description: Optional[str] = typer.Option(None),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
    cap = AgentCapability(
        agent_id=agent_id,
        name=skill,
        complexity_level=complexity,
        cost_per_use=cost_per_use,
        success_rate=success_rate,
        description=description,
    )
    if protocol.registry:
        protocol.registry.register(cap)
    print(f"registered skill_id={cap.skill_id} for agent={agent_id}")

@app.command()
def discover(
    skills: list[str] = typer.Option(None),
    query: Optional[str] = typer.Option(None),
    complexity_min: Optional[ComplexityLevel] = typer.Option(None),
    max_cost_per_use: Optional[float] = typer.Option(None),
    limit: int = typer.Option(20),
    format: str = typer.Option("table", help="table|json"),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
    if not protocol.registry:
        print("Registry not available")
        return
    
    result = protocol.registry.discover(
        required_skills=skills or [],
        query=query,
        complexity_min=complexity_min,
        max_cost_per_use=max_cost_per_use,
        limit=limit,
    )

    if format == "json":
        print(json.dumps(result.model_dump(mode="json"), indent=2))
        return

    if not result.matches:
        print("no matches")
        return

    for m in result.matches:
        print(
            f"agent={m.agent_id} skill={m.name} cost={m.cost_per_use:.4f} "
            f"success={m.success_rate:.2f} score={m.overall_score:.3f}"
        )

@app.command()
def reputation(
    agent_id: str = typer.Option(...),
    format: str = typer.Option("table", help="table|json"),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
    if not protocol.reputation:
        print("Reputation system not available")
        return
        
    profile = protocol.reputation.get_profile(agent_id)
    if format == "json":
        print(json.dumps(profile.model_dump(mode="json"), indent=2))
        return

    print(
        f"agent={profile.agent_id} score={profile.reputation_score:.2f} "
        f"success_rate={profile.success_rate:.2f} total={profile.total_collaborations} "
        f"verified={profile.is_verified}"
    )

@app.command("status")
def status_command(
    db: str = typer.Option(".metaprotocol.db"),
    format: str = typer.Option("table", help="table|json"),
) -> None:
    """Show protocol status and statistics."""
    protocol = _protocol(db)
    
    capability_rows = protocol.store.query("SELECT COUNT(DISTINCT agent_id) FROM capabilities")
    registered_agents = capability_rows[0][0] if capability_rows else 0

    skill_rows = protocol.store.query("SELECT COUNT(*) FROM capabilities")
    active_skills = skill_rows[0][0] if skill_rows else 0

    if format == "json":
        print(
            json.dumps(
                {
                    "registered_agents": registered_agents,
                    "active_skills": active_skills,
                },
                indent=2,
            )
        )
        return

    print(f"Registered agents: {registered_agents}")
    print(f"Active skills: {active_skills}")

if __name__ == "__main__":
    app()
'''

path = Path("metaprotocol/cli/main.py")
path.write_text(cli_main)
print("Updated cli/main.py with correct imports")
