from __future__ import annotations

from pathlib import Path

from metaprotocol.models import AgentCapability, ComplexityLevel, NegotiationStatus
from metaprotocol.protocol import MetaProtocol


def test_register_discover_and_negotiate(tmp_path: Path) -> None:
    protocol = MetaProtocol(db_path=tmp_path / "test.db")

    protocol.registry.register(
        AgentCapability(
            agent_id="coder",
            name="code_gen",
            complexity_level=ComplexityLevel.ADVANCED,
            cost_per_use=0.15,
            success_rate=0.9,
        )
    )
    protocol.registry.register(
        AgentCapability(
            agent_id="analyst",
            name="data_analysis",
            complexity_level=ComplexityLevel.INTERMEDIATE,
            cost_per_use=0.2,
            success_rate=0.8,
        )
    )

    result = protocol.registry.discover(required_skills=["code_gen", "data_analysis"])
    assert len(result.matches) == 2

    proposal = protocol.negotiation.propose(
        proposer_agent_id="client",
        responder_agent_id="coder",
        task_id="task-1",
        required_skills=["code_gen"],
        offered_compensation=1.0,
    )
    accepted = protocol.negotiation.accept(proposal.proposal_id, "coder")
    assert accepted.status == NegotiationStatus.IN_ESCROW

    completed = protocol.negotiation.complete(proposal.proposal_id, success=True)
    assert completed.status == NegotiationStatus.COMPLETED


def test_team_formation(tmp_path: Path) -> None:
    protocol = MetaProtocol(db_path=tmp_path / "test2.db")
    protocol.registry.register(
        AgentCapability(
            agent_id="a",
            name="code_gen",
            complexity_level=ComplexityLevel.ADVANCED,
            cost_per_use=0.2,
            success_rate=0.95,
        )
    )
    protocol.registry.register(
        AgentCapability(
            agent_id="b",
            name="data_analysis",
            complexity_level=ComplexityLevel.INTERMEDIATE,
            cost_per_use=0.2,
            success_rate=0.85,
        )
    )

    candidates = protocol.registry.discover(required_skills=["code_gen", "data_analysis"]).matches
    assignment = protocol.formation.form_team(
        task_id="task-2",
        required_skills=["code_gen", "data_analysis"],
        candidates=candidates,
        budget=1.0,
    )

    assert set(assignment.team.skill_coverage.keys()) == {"code_gen", "data_analysis"}
    assert assignment.total_cost <= 1.0
