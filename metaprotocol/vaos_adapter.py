"""VAOS adapter for integrating MetaProtocol with VAOS agent systems."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import AgentCapability, ComplexityLevel

if TYPE_CHECKING:
    from .protocol import MetaProtocol


class VAOSAdapter:
    """Adapter to integrate VAOS agents with MetaProtocol."""

    def __init__(self, protocol: "MetaProtocol", vaos_db_path: str) -> None:
        self.protocol = protocol
        self.vaos_db_path = vaos_db_path
        self._vaos_store: Any | None = None

    @property
    def vaos_store(self) -> Any:
        """Lazy-load VAOS storage."""
        if self._vaos_store is None:
            from .storage import SQLiteStore

            self._vaos_store = SQLiteStore(db_path=self.vaos_db_path)
        return self._vaos_store

    def sync_agents_from_vaos(self, default_complexity: str = "intermediate") -> dict[str, str]:
        """Sync agent capabilities from VAOS agents table."""
        agent_rows = self.vaos_store.query("SELECT * FROM agents")

        synced: dict[str, str] = {}

        for row in agent_rows:
            agent_id = row["agent_id"]

            try:
                name = row.get("capabilities") or row.get("name", "general")
                capabilities = name.split(",") if "," in name else [name]

                for cap_name in capabilities:
                    capability = AgentCapability(
                        agent_id=agent_id,
                        name=cap_name.strip(),
                        description=row.get("description"),
                        complexity_level=ComplexityLevel(default_complexity),
                        success_rate=float(row.get("success_rate", 0.5)),
                        cost_per_use=float(row.get("cost_per_use", 0.1)),
                        metadata={"source": "vaos", "original_agent_data": dict(row)},
                    )

                    self.protocol.registry.register(capability)
                    synced[f"{agent_id}:{cap_name}"] = capability.skill_id

            except Exception as e:
                print(f"Failed to sync agent {agent_id}: {e}")

        return synced

    def extract_collaboration_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Extract collaboration history from VAOS audit logs."""
        audit_rows = self.vaos_store.query(
            "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )

        collaborations: list[dict[str, Any]] = []
        seen = set()

        for row in audit_rows:
            event = row.get("event", "")
            if "collab" in event.lower() or "task" in event.lower():
                collab_id = row.get("collaboration_id") or row.get("task_id") or row.get("id")
                if collab_id and collab_id not in seen:
                    seen.add(collab_id)
                    collaborations.append(dict(row))

        return collaborations

    def import_collaborations_to_reputation(self, limit: int = 100) -> int:
        """Import VAOS collaboration history into reputation system."""
        collaborations = self.extract_collaboration_history(limit)
        imported = 0

        for collab in collaborations:
            try:
                agent_id = collab.get("agent_id")
                partner_id = collab.get("partner_id")

                if not agent_id or not partner_id:
                    continue

                success = str(collab.get("status", "")).lower() in {
                    "completed",
                    "success",
                    "done",
                }
                rating = float(collab.get("rating", 3.0))

                self.protocol.reputation.record_outcome(
                    agent_id=agent_id,
                    partner_id=partner_id,
                    collaboration_id=collab.get("id", "vaos-import"),
                    success=success,
                    partner_rating=rating,
                )
                imported += 1

            except Exception as e:
                print(f"Failed to import collaboration: {e}")

        return imported

    def export_team_to_vaos(self, team_id: str, vaos_task_id: str) -> dict[str, Any]:
        """Export a MetaProtocol team to VAOS as a task."""
        from .models import Team

        rows = self.protocol.store.query(
            "SELECT payload_json FROM teams WHERE team_id = ?",
            (team_id,),
        )

        if not rows:
            raise ValueError(f"Team not found: {team_id}")

        team = Team.model_validate(self.protocol.store.loads_json(rows[0]["payload_json"]))

        vaos_team_data = {
            "vaos_task_id": vaos_task_id,
            "team_id": team_id,
            "agents": team.agent_ids,
            "roles": team.role_assignments,
            "required_skills": team.required_skills,
            "skill_coverage": team.skill_coverage,
            "status": team.status.value,
            "budget": team.total_budget,
            "created_at": team.created_at.isoformat(),
        }

        self.vaos_store.execute(
            """
            INSERT INTO vaos_teams(vaos_task_id, team_id, payload_json)
            VALUES (?, ?, ?)
            ON CONFLICT(vaos_task_id) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (
                vaos_task_id,
                team_id,
                self.vaos_store.dumps_json(vaos_team_data),
            ),
        )

        return vaos_team_data

    def get_agent_vaos_data(self, agent_id: str) -> dict[str, Any] | None:
        """Get VAOS-specific data for an agent."""
        rows = self.vaos_store.query("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))

        if not rows:
            return None

        return dict(rows[0])
