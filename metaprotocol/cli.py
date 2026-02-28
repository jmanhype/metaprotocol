from __future__ import annotations

import json
from typing import Optional

import typer
from rich import print

from .models import AgentCapability, ComplexityLevel, NegotiationStateError, TeamFormationError
from .protocol import MetaProtocol

app = typer.Typer(help="MetaProtocol CLI")


def _protocol(db: str) -> MetaProtocol:
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
    protocol.registry.register(cap)
    print(f"registered skill_id={cap.skill_id} for agent={agent_id}")


@app.command()
def discover(
    skills: list[str] = typer.Option(None, help="Repeat --skills for each required skill"),
    query: Optional[str] = typer.Option(None),
    complexity_min: Optional[ComplexityLevel] = typer.Option(None),
    max_cost_per_use: Optional[float] = typer.Option(None),
    limit: int = typer.Option(20),
    format: str = typer.Option("table", help="table|json"),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
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
def propose(
    proposer_agent_id: str = typer.Option(...),
    responder_agent_id: str = typer.Option(...),
    task_id: str = typer.Option(...),
    skills: list[str] = typer.Option(...),
    offered_compensation: float = typer.Option(...),
    escrow: bool = typer.Option(True),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
    proposal = protocol.negotiation.propose(
        proposer_agent_id=proposer_agent_id,
        responder_agent_id=responder_agent_id,
        task_id=task_id,
        required_skills=skills,
        offered_compensation=offered_compensation,
        escrow=escrow,
    )
    print(f"proposal_id={proposal.proposal_id} status={proposal.status.value}")


@app.command()
def respond(
    proposal_id: str = typer.Option(...),
    agent_id: str = typer.Option(...),
    decision: str = typer.Option(..., help="accept|reject|counter"),
    revised_compensation: Optional[float] = typer.Option(None),
    message: Optional[str] = typer.Option(None),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
    try:
        if decision == "accept":
            proposal = protocol.negotiation.accept(proposal_id=proposal_id, agent_id=agent_id)
        elif decision == "reject":
            proposal = protocol.negotiation.reject(proposal_id=proposal_id, agent_id=agent_id)
        elif decision == "counter":
            proposal = protocol.negotiation.counter(
                proposal_id=proposal_id,
                agent_id=agent_id,
                revised_compensation=revised_compensation,
                message=message,
            )
        else:
            raise typer.BadParameter("decision must be one of: accept, reject, counter")
    except NegotiationStateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    print(f"proposal_id={proposal.proposal_id} status={proposal.status.value}")


@app.command()
def complete(
    proposal_id: str = typer.Option(...),
    success: bool = typer.Option(True),
    rate_agent_id: Optional[str] = typer.Option(None),
    partner_id: Optional[str] = typer.Option(None),
    rating: Optional[float] = typer.Option(None),
    collaboration_id: Optional[str] = typer.Option(None),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
    proposal = protocol.negotiation.complete(proposal_id=proposal_id, success=success)

    if rate_agent_id and partner_id and rating is not None:
        protocol.reputation.record_outcome(
            agent_id=rate_agent_id,
            partner_id=partner_id,
            collaboration_id=collaboration_id or proposal.proposal_id,
            success=success,
            partner_rating=rating,
        )
    print(f"proposal_id={proposal.proposal_id} status={proposal.status.value}")


@app.command()
def reputation(
    agent_id: str = typer.Option(...),
    format: str = typer.Option("table", help="table|json"),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
    profile = protocol.reputation.get_profile(agent_id)
    if format == "json":
        print(json.dumps(profile.model_dump(mode="json"), indent=2))
        return

    print(
        f"agent={profile.agent_id} score={profile.reputation_score:.2f} "
        f"success_rate={profile.success_rate:.2f} total={profile.total_collaborations} "
        f"verified={profile.is_verified}"
    )


@app.command("form-team")
def form_team(
    task_id: str = typer.Option(...),
    skills: list[str] = typer.Option(...),
    budget: float = typer.Option(...),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
    discovery = protocol.registry.discover(required_skills=skills, limit=500)
    try:
        assignment = protocol.formation.form_team(
            task_id=task_id,
            required_skills=skills,
            candidates=discovery.matches,
            budget=budget,
        )
    except TeamFormationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    print(
        json.dumps(
            {
                "team_id": assignment.team.team_id,
                "agent_ids": assignment.team.agent_ids,
                "skill_coverage": assignment.team.skill_coverage,
                "total_cost": assignment.total_cost,
                "optimization_score": assignment.optimization_score,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    app()
