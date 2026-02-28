from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

if TYPE_CHECKING:
    from .protocol import MetaProtocol


app = FastAPI(
    title="MetaProtocol API",
    description="Coordination protocol for autonomous agents",
    version="0.1.0",
)


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str


class ProtocolStats(BaseModel):
    registered_agents: int
    active_skills: int
    open_proposals: int
    active_teams: int
    avg_reputation: float
    total_collaborations: int


def create_app(protocol: "MetaProtocol") -> FastAPI:
    """Create and configure the FastAPI application."""

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            database=protocol.store.db_path,
        )

    @app.get("/stats", response_model=ProtocolStats)
    async def stats() -> ProtocolStats:
        """Protocol statistics."""
        from .models import ReputationRecord

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

        return ProtocolStats(
            registered_agents=registered_agents,
            active_skills=active_skills,
            open_proposals=open_proposals,
            active_teams=active_teams,
            avg_reputation=avg_reputation,
            total_collaborations=total_collabs,
        )

    @app.post("/register")
    async def register_skill(capability: dict) -> JSONResponse:
        """Register a skill capability."""
        from .models import AgentCapability

        try:
            cap = AgentCapability(**capability)
            protocol.registry.register(cap)
            return JSONResponse({"skill_id": cap.skill_id, "status": "registered"})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/discover")
    async def discover(
        skills: list[str] = Query(None),
        query: str = Query(None),
        complexity_min: str = Query(None),
        max_cost: float = Query(None),
        limit: int = Query(20),
    ) -> dict:
        """Discover agents by skill requirements."""
        from .models import ComplexityLevel

        complexity = ComplexityLevel(complexity_min) if complexity_min else None

        result = protocol.registry.discover(
            required_skills=skills or [],
            query=query,
            complexity_min=complexity,
            max_cost_per_use=max_cost,
            limit=limit,
        )

        return result.model_dump(mode="json")

    @app.post("/propose")
    async def propose(proposal: dict) -> JSONResponse:
        """Create a collaboration proposal."""
        try:
            p = protocol.negotiation.propose(
                proposer_agent_id=proposal["proposer_agent_id"],
                responder_agent_id=proposal["responder_agent_id"],
                task_id=proposal["task_id"],
                required_skills=proposal["required_skills"],
                offered_compensation=proposal["offered_compensation"],
                escrow=proposal.get("escrow", True),
                terms=proposal.get("terms"),
            )
            return JSONResponse({"proposal_id": p.proposal_id, "status": p.status.value})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/propose/{proposal_id}/respond")
    async def respond_proposal(proposal_id: str, response: dict) -> JSONResponse:
        """Accept, reject, or counter a proposal."""
        try:
            action = response["action"]
            agent_id = response["agent_id"]

            if action == "accept":
                p = protocol.negotiation.accept(proposal_id=proposal_id, agent_id=agent_id)
            elif action == "reject":
                p = protocol.negotiation.reject(proposal_id=proposal_id, agent_id=agent_id)
            elif action == "counter":
                p = protocol.negotiation.counter(
                    proposal_id=proposal_id,
                    agent_id=agent_id,
                    revised_compensation=response.get("revised_compensation"),
                    message=response.get("message"),
                )
            else:
                raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

            return JSONResponse({"proposal_id": p.proposal_id, "status": p.status.value})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/propose/{proposal_id}/complete")
    async def complete_proposal(proposal_id: str, data: dict) -> JSONResponse:
        """Mark a proposal as completed."""
        try:
            success = data.get("success", True)
            p = protocol.negotiation.complete(proposal_id=proposal_id, success=success)

            if "rate_agent_id" in data:
                protocol.reputation.record_outcome(
                    agent_id=data["rate_agent_id"],
                    partner_id=data["partner_id"],
                    collaboration_id=data.get("collaboration_id", proposal_id),
                    success=success,
                    partner_rating=data["rating"],
                )

            return JSONResponse({"proposal_id": p.proposal_id, "status": p.status.value})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/team/form")
    async def form_team(request: dict) -> JSONResponse:
        """Form an optimal team for a task."""
        try:
            from .models import TeamFormationError

            discovery = protocol.registry.discover(
                required_skills=request["required_skills"], limit=500
            )
            assignment = protocol.formation.form_team(
                task_id=request["team_id"],
                required_skills=request["required_skills"],
                candidates=discovery.matches,
                budget=request["budget"],
                weights=request.get("weights"),
            )

            return JSONResponse(
                {
                    "team_id": assignment.team.team_id,
                    "agent_ids": assignment.team.agent_ids,
                    "skill_coverage": assignment.team.skill_coverage,
                    "total_cost": assignment.total_cost,
                    "optimization_score": assignment.optimization_score,
                }
            )
        except TeamFormationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/team/{team_id}")
    async def get_team(team_id: str) -> dict:
        """Get team details."""
        from .models import Team

        rows = protocol.store.query("SELECT payload_json FROM teams WHERE team_id = ?", (team_id,))
        if not rows:
            raise HTTPException(status_code=404, detail="Team not found")

        team = Team.model_validate(protocol.store.loads_json(rows[0]["payload_json"]))
        return team.model_dump(mode="json")

    @app.post("/team/{team_id}/write")
    async def write_team_memory(team_id: str, data: dict) -> JSONResponse:
        """Write to team memory."""
        try:
            team = protocol.memory.write(
                team_id=team_id,
                agent_id=data["agent_id"],
                action=data["action"],
                payload=data.get("payload"),
            )
            return JSONResponse({"team_id": team.team_id, "interaction_count": len(team.interaction_history)})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/reputation/{agent_id}")
    async def get_reputation(agent_id: str) -> dict:
        """Get reputation profile for an agent."""
        profile = protocol.reputation.get_profile(agent_id)
        return profile.model_dump(mode="json")

    @app.post("/rate")
    async def rate_agent(rating: dict) -> JSONResponse:
        """Record a collaboration outcome."""
        try:
            profile = protocol.reputation.record_outcome(
                agent_id=rating["agent_id"],
                partner_id=rating["partner_id"],
                collaboration_id=rating["collaboration_id"],
                success=rating["success"],
                partner_rating=rating["rating"],
            )
            return JSONResponse(
                {
                    "agent_id": profile.agent_id,
                    "new_score": profile.reputation_score,
                    "total_collaborations": profile.total_collaborations,
                }
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/disputes")
    async def open_dispute(dispute_data: dict) -> JSONResponse:
        """Open a dispute on a proposal."""
        try:
            from .disputes import DisputeResolver

            resolver = DisputeResolver(protocol.store)
            dispute = resolver.open_dispute(
                proposal_id=dispute_data["proposal_id"],
                agent_id=dispute_data["agent_id"],
                reason=dispute_data["reason"],
                description=dispute_data.get("description"),
                evidence=dispute_data.get("evidence"),
            )
            return JSONResponse({"dispute_id": dispute.dispute_id, "status": dispute.status.value})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/market/rates/{skill_name}")
    async def get_market_rate(
        skill_name: str,
        complexity: str = Query(None),
    ) -> dict:
        """Get market rate for a skill."""
        from .market import MarketRates

        market = MarketRates(protocol.store)
        rate = market.get_market_rate(skill_name, complexity)

        return {
            "skill": skill_name,
            "complexity": complexity,
            "market_rate": rate,
        }

    @app.get("/market/validate")
    async def validate_compensation(
        skills: list[str] = Query(...),
        offered: float = Query(...),
        complexity: str = Query(None),
    ) -> dict:
        """Validate compensation against market rates."""
        from .market import MarketRates

        market = MarketRates(protocol.store)
        validation = market.validate_compensation(
            required_skills=skills,
            offered_compensation=offered,
            complexity=complexity,
        )

        return validation

    @app.post("/optimize/team")
    async def optimize_team(request: dict) -> JSONResponse:
        """Optimize team formation with specified parameters."""
        try:
            from .optimizer import TeamOptimizer

            discovery = protocol.registry.discover(required_skills=request["required_skills"], limit=500)

            optimizer = TeamOptimizer(
                strategy=request.get("strategy", "greedy"),
                max_team_size=request.get("max_team_size", 10),
                timeout_ms=request.get("timeout_ms", 1000),
            )

            partner_history = {}
            for match in discovery.matches:
                profile = protocol.reputation.get_profile(match.agent_id)
                partner_history[match.agent_id] = set(profile.partners)

            assignment = optimizer.form_team(
                task_id=request["task_id"],
                required_skills=request["required_skills"],
                candidates=discovery.matches,
                budget=request["budget"],
                weights=request.get("weights"),
                partner_history=partner_history,
            )

            return JSONResponse(
                {
                    "team_id": assignment.team.team_id,
                    "agent_ids": assignment.team.agent_ids,
                    "skill_coverage": assignment.team.skill_coverage,
                    "total_cost": assignment.total_cost,
                    "optimization_score": assignment.optimization_score,
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app
