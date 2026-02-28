from __future__ import annotations

import json
from typing import Optional

import typer
from rich import print

from .models import AgentCapability, ComplexityLevel, NegotiationStateError, TeamFormationError
from .protocol import MetaProtocol

app = typer.Typer(help="MetaProtocol CLI")


def _protocol(
    db: str,
    strategy: str = "greedy",
    enable_embeddings: bool = False,
) -> MetaProtocol:
    return MetaProtocol(
        db_path=db,
        strategy=strategy,
        enable_embeddings=enable_embeddings,
    )


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
    decision: Optional[str] = typer.Option(None, "--decision", help="accept|reject|counter"),
    action: Optional[str] = typer.Option(None, "--action", help="accept|reject|counter"),
    revised_compensation: Optional[float] = typer.Option(None),
    message: Optional[str] = typer.Option(None),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
    choice = action or decision
    if not choice:
        raise typer.BadParameter("one of --action or --decision is required")
    try:
        if choice == "accept":
            proposal = protocol.negotiation.accept(proposal_id=proposal_id, agent_id=agent_id)
        elif choice == "reject":
            proposal = protocol.negotiation.reject(proposal_id=proposal_id, agent_id=agent_id)
        elif choice == "counter":
            proposal = protocol.negotiation.counter(
                proposal_id=proposal_id,
                agent_id=agent_id,
                revised_compensation=revised_compensation,
                message=message,
            )
        else:
            raise typer.BadParameter("action/decision must be one of: accept, reject, counter")
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


@app.command("prune-skills")
def prune_skills(
    max_age_days: int = typer.Option(90),
    keep_if_success_rate_at_least: float = typer.Option(0.9),
    dry_run: bool = typer.Option(False),
    format: str = typer.Option("table", help="table|json"),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    protocol = _protocol(db)
    try:
        stale_ids = protocol.registry.prune_stale_skills(
            max_age_days=max_age_days,
            keep_if_success_rate_at_least=keep_if_success_rate_at_least,
            dry_run=dry_run,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if format == "json":
        print(
            json.dumps(
                {"dry_run": dry_run, "pruned_count": len(stale_ids), "skill_ids": stale_ids},
                indent=2,
            )
        )
        return

    mode = "would prune" if dry_run else "pruned"
    print(f"{mode} {len(stale_ids)} skills")
    if stale_ids:
        for skill_id in stale_ids:
            print(f"- {skill_id}")


@app.command("dispute")
def open_dispute(
    proposal_id: str = typer.Option(...),
    agent_id: str = typer.Option(...),
    reason: str = typer.Option(...),
    description: Optional[str] = typer.Option(None),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    """Open a dispute on a proposal."""
    from .disputes import DisputeResolver

    protocol = _protocol(db)
    resolver = DisputeResolver(protocol.store)
    dispute = resolver.open_dispute(
        proposal_id=proposal_id,
        agent_id=agent_id,
        reason=reason,
        description=description,
    )
    print(f"dispute_id={dispute.dispute_id} status={dispute.status.value}")


@app.command("resolve-dispute")
def resolve_dispute(
    dispute_id: str = typer.Option(...),
    resolution: str = typer.Option(...),
    in_favor_of: Optional[str] = typer.Option(None),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    """Manually resolve a dispute."""
    from .disputes import DisputeResolver

    protocol = _protocol(db)
    resolver = DisputeResolver(protocol.store)
    dispute = resolver.resolve_dispute(
        dispute_id=dispute_id,
        resolution=resolution,
        in_favor_of=in_favor_of,
    )
    print(f"dispute_id={dispute.dispute_id} status={dispute.status.value}")


@app.command("market-rate")
def get_market_rate(
    skill: str = typer.Option(...),
    complexity: Optional[ComplexityLevel] = typer.Option(None),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    """Get market rate for a skill."""
    from .market import MarketRates

    protocol = _protocol(db)
    market = MarketRates(protocol.store)
    rate = market.get_market_rate(skill, complexity.value if complexity else None)
    print(f"skill={skill} complexity={complexity} market_rate={rate:.4f}")


@app.command("recommend-comp")
def recommend_compensation(
    skills: list[str] = typer.Option(...),
    complexity: Optional[ComplexityLevel] = typer.Option(None),
    percentile: float = typer.Option(0.5, min=0.0, max=1.0),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    """Get recommended compensation for a set of skills."""
    from .market import MarketRates

    protocol = _protocol(db)
    market = MarketRates(protocol.store)
    recommendations = market.recommend_compensation(
        required_skills=skills,
        complexity=complexity.value if complexity else None,
        target_percentile=percentile,
    )
    print(json.dumps(recommendations, indent=2))


@app.command("optimize-team")
def optimize_team_command(
    task_id: str = typer.Option(...),
    skills: list[str] = typer.Option(...),
    budget: float = typer.Option(...),
    strategy: str = typer.Option("greedy"),
    weights: str = typer.Option("{}"),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    """Optimize team formation with ILP or greedy strategy."""
    from .optimizer import TeamOptimizer

    protocol = _protocol(db, strategy=strategy)

    discovery = protocol.registry.discover(required_skills=skills, limit=500)

    optimizer = TeamOptimizer(strategy=strategy, max_team_size=10, timeout_ms=1000)

    partner_history: dict[str, set[str]] = {}
    for match in discovery.matches:
        profile = protocol.reputation.get_profile(match.agent_id)
        partner_history[match.agent_id] = set(profile.partners)

    weight_dict = json.loads(weights) if weights else None

    assignment = optimizer.form_team(
        task_id=task_id,
        required_skills=skills,
        candidates=discovery.matches,
        budget=budget,
        weights=weight_dict,
        partner_history=partner_history,
    )

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


@app.command("serve")
def serve_command(
    host: str = typer.Option("0.0.0.0"),
    port: int = typer.Option(8430),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    """Start the HTTP API server."""
    import uvicorn

    from .serve import create_app

    protocol = _protocol(db)
    app = create_app(protocol)

    print(f"Starting MetaProtocol API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


@app.command("vaos-sync")
def vaos_sync(
    vaos_db: str = typer.Option(...),
    default_complexity: ComplexityLevel = typer.Option(ComplexityLevel.INTERMEDIATE),
    import_collaborations: bool = typer.Option(True),
    db: str = typer.Option(".metaprotocol.db"),
) -> None:
    """Sync agents and collaborations from VAOS database."""
    from .vaos_adapter import VAOSAdapter

    protocol = _protocol(db)
    adapter = VAOSAdapter(protocol, vaos_db_path=vaos_db)

    print("Syncing agents from VAOS...")
    synced = adapter.sync_agents_from_vaos(default_complexity=default_complexity.value)
    print(f"Synced {len(synced)} agent capabilities")

    if import_collaborations:
        print("Importing collaboration history...")
        imported = adapter.import_collaborations_to_reputation()
        print(f"Imported {imported} collaboration records")


@app.command("status")
def status_command(
    db: str = typer.Option(".metaprotocol.db"),
    format: str = typer.Option("table", help="table|json"),
) -> None:
    """Show protocol status and statistics."""
    from .models import ReputationRecord

    protocol = _protocol(db)

    capability_rows = protocol.store.query("SELECT COUNT(DISTINCT agent_id) FROM capabilities")
    registered_agents = capability_rows[0][0] if capability_rows else 0

    skill_rows = protocol.store.query("SELECT COUNT(*) FROM capabilities")
    active_skills = skill_rows[0][0] if skill_rows else 0

    proposal_rows = protocol.store.query(
        "SELECT payload_json FROM negotiations WHERE payload_json LIKE '%\"status\": \"proposed\"%'"
    )
    open_proposals = len(proposal_rows)

    team_rows = protocol.store.query(
        "SELECT payload_json FROM teams WHERE payload_json LIKE '%\"status\": \"active\"%'"
    )
    active_teams = len(team_rows)

    rep_rows = protocol.store.query("SELECT payload_json FROM reputation")
    total_rep = 0.0
    total_collabs = 0
    for row in rep_rows:
        profile = ReputationRecord.model_validate(protocol.store.loads_json(row["payload_json"]))
        total_rep += profile.reputation_score
        total_collabs += profile.total_collaborations

    avg_reputation = total_rep / len(rep_rows) if rep_rows else 0.0

    if format == "json":
        print(
            json.dumps(
                {
                    "registered_agents": registered_agents,
                    "active_skills": active_skills,
                    "open_proposals": open_proposals,
                    "active_teams": active_teams,
                    "avg_reputation": round(avg_reputation, 2),
                    "total_collaborations": total_collabs,
                },
                indent=2,
            )
        )
        return

    print(f"Registered agents: {registered_agents}")
    print(f"Active skills: {active_skills}")
    print(f"Open proposals: {open_proposals}")
    print(f"Active teams: {active_teams}")
    print(f"Avg reputation: {avg_reputation:.2f}")
    print(f"Total collaborations: {total_collabs}")


if __name__ == "__main__":
    app()
