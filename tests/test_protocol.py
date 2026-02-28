from __future__ import annotations

from datetime import UTC, datetime, timedelta
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


def test_multi_party_negotiation_lifecycle(tmp_path: Path) -> None:
    protocol = MetaProtocol(db_path=tmp_path / "test3.db")
    proposal = protocol.negotiation.propose_multi(
        proposer_agent_id="client",
        participant_agent_ids=["coder", "reviewer"],
        task_id="task-3",
        required_skills=["code_gen", "code_review"],
        offered_compensation=2.0,
        escrow=True,
    )

    after_first_accept = protocol.negotiation.accept_multi(proposal.proposal_id, "coder")
    assert after_first_accept.status == NegotiationStatus.PROPOSED

    after_second_accept = protocol.negotiation.accept_multi(proposal.proposal_id, "reviewer")
    assert after_second_accept.status == NegotiationStatus.IN_ESCROW
    assert set(after_second_accept.accepted_agent_ids) == {"coder", "reviewer"}

    completed = protocol.negotiation.complete_multi(proposal.proposal_id, success=True)
    assert completed.status == NegotiationStatus.COMPLETED


def test_discovery_uses_reputation_score(tmp_path: Path) -> None:
    protocol = MetaProtocol(db_path=tmp_path / "test4.db")
    protocol.registry.register(
        AgentCapability(
            agent_id="trusted",
            name="code_gen",
            complexity_level=ComplexityLevel.ADVANCED,
            cost_per_use=0.2,
            success_rate=0.8,
        )
    )
    protocol.registry.register(
        AgentCapability(
            agent_id="newcomer",
            name="code_gen",
            complexity_level=ComplexityLevel.ADVANCED,
            cost_per_use=0.2,
            success_rate=0.8,
        )
    )

    protocol.reputation.record_outcome(
        agent_id="trusted",
        partner_id="p1",
        collaboration_id="c1",
        success=True,
        partner_rating=5.0,
    )
    protocol.reputation.record_outcome(
        agent_id="trusted",
        partner_id="p2",
        collaboration_id="c2",
        success=True,
        partner_rating=5.0,
    )
    protocol.reputation.record_outcome(
        agent_id="trusted",
        partner_id="p3",
        collaboration_id="c3",
        success=True,
        partner_rating=5.0,
    )

    result = protocol.registry.discover(required_skills=["code_gen"], limit=2)
    assert len(result.matches) == 2
    assert result.matches[0].agent_id == "trusted"
    assert result.matches[0].reputation_score > result.matches[1].reputation_score


def test_prune_stale_skills(tmp_path: Path) -> None:
    protocol = MetaProtocol(db_path=tmp_path / "test5.db")
    old_time = datetime.now(UTC) - timedelta(days=120)
    stale = AgentCapability(
        agent_id="old-agent",
        name="legacy_skill",
        complexity_level=ComplexityLevel.BASIC,
        cost_per_use=0.1,
        success_rate=0.2,
        updated_at=old_time,
        registered_at=old_time,
    )
    fresh = AgentCapability(
        agent_id="fresh-agent",
        name="fresh_skill",
        complexity_level=ComplexityLevel.BASIC,
        cost_per_use=0.1,
        success_rate=0.2,
    )
    protocol.registry.register(stale)
    protocol.registry.register(fresh)

    dry_run_ids = protocol.registry.prune_stale_skills(max_age_days=90, keep_if_success_rate_at_least=0.9, dry_run=True)
    assert stale.skill_id in dry_run_ids

    pruned_ids = protocol.registry.prune_stale_skills(max_age_days=90, keep_if_success_rate_at_least=0.9)
    assert stale.skill_id in pruned_ids
    remaining = protocol.registry.discover(required_skills=["legacy_skill", "fresh_skill"], limit=10)
    assert all(match.skill_id != stale.skill_id for match in remaining.matches)
