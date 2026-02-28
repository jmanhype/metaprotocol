# MetaAgent-Protocol

**Coordination protocol for autonomous agents.**

Agents that discover, negotiate, and form teams dynamically — without human coordination.

## What It Is

MetaAgent-Protocol is not an agent framework and not a platform. It's a **coordination protocol**. It doesn't run agents or host them — it provides the communication and economic infrastructure that lets agents self-organize into teams, negotiate fair compensation, and build trust over time.

Think of it as the labor market where agents:
- Post resumes (register skills)
- Find gigs (discover partners)
- Form project teams
- Get rated (reputation)

All fully automated, at machine speed.

## Key Features

- **Skill Registry** — Agents declare capabilities with metadata; discover via keyword or semantic search
- **Reputation System** — Trust scores derived from actual collaboration outcomes, with decay to prevent inflation
- **Negotiation Engine** — Structured proposal-accept-execute-verify lifecycle with escrow contracts
- **Team Formation** — Constraint-based optimizer forms optimal teams given requirements and budget
- **Team Memory** — Shared collaborative context across team members

## Quickstart

```bash
# Install
pip install metaprotocol

# Register a skill
meta-protocol register \
  --agent-id agent-001 \
  --skill code_generation \
  --complexity advanced \
  --cost-per-use 0.15 \
  --success-rate 0.87

# Discover collaborators
meta-protocol discover \
  --skills code_generation,data_analysis \
  --format json

# Propose collaboration
meta-protocol propose \
  --from agent-001 \
  --to agent-002 \
  --task-id task-xyz \
  --skills data_analysis \
  --compensation 0.50

# Accept proposal (as agent-002)
meta-protocol respond \
  --proposal-id <proposal-id> \
  --action accept

# Form team for multi-agent task
meta-protocol form-team \
  --task-id task-xyz \
  --skills code_generation,data_analysis,code_review \
  --budget 2.00
```

## Architecture

```
Agent Systems (VAOS, LangChain, CrewAI, AutoGen, custom)
  ↓ 3 API calls
MetaAgent-Protocol
  ├─ Skill Registry (register, discover)
  ├─ Negotiation Engine (propose, accept, complete)
  ├─ Reputation System (record outcomes, query profiles)
  ├─ Team Formation (form optimal teams)
  └─ Team Memory (shared state)
  ↓
Storage: SQLite (default) / Postgres / In-memory
```

## Data Model

All protocol operations consume and produce strict Pydantic types:

- `AgentCapability` — What an agent can do
- `ReputationRecord` — Trust profile with history
- `NegotiationProposal` — Collaboration terms with state machine
- `Team` — Formed collaboration unit with shared state
- `DiscoveryResult` — Ranked matches from discovery

See `metaprotocol.models` for full definitions.

## CLI Commands

| Command | Purpose |
|----------|---------|
| `register` | Register agent skills |
| `discover` | Find collaborators by skill or query |
| `propose` | Create collaboration proposal |
| `respond` | Accept/reject/counter a proposal |
| `complete` | Mark proposal complete (triggers escrow) |
| `reputation` | Query agent reputation profile |
| `form-team` | Auto-form optimal team for task |

## Python API

```python
from metaprotocol import MetaProtocol

# Initialize protocol
protocol = MetaProtocol(db_path=".metaprotocol.db")

# Register skill
protocol.registry.register(
    AgentCapability(
        agent_id="agent-001",
        name="code_generation",
        complexity_level="advanced",
        cost_per_use=0.15,
        success_rate=0.87,
    )
)

# Discover partners
results = protocol.registry.discover(
    required_skills=["code_generation", "data_analysis"],
    complexity_min="intermediate",
    max_cost_per_use=0.50,
)

# Propose work
proposal = protocol.negotiation.propose(
    proposer_agent_id="client",
    responder_agent_id="agent-001",
    task_id="task-1",
    required_skills=["code_generation"],
    offered_compensation=0.50,
)

# Form team
assignment = protocol.formation.form_team(
    task_id="task-1",
    required_skills=["code_generation", "data_analysis"],
    candidates=results.matches,
    budget=2.00,
)
```

## Implementation Status (Phase 1 MVP ✅)

- ✅ All Pydantic models with validation
- ✅ Skill registry with keyword discovery and composite ranking
- ✅ Reputation system with weighted scoring and decay
- ✅ 1:1 negotiation engine with full state machine
- ✅ Escrow contract lifecycle
- ✅ SQLite storage backend
- ✅ Greedy team formation optimizer
- ✅ Team memory with shared state
- ✅ Full CLI (register, discover, propose, respond, reputation, form-team)
- ✅ Test suite covering end-to-end lifecycle

## Roadmap (Future Phases)

**Phase 2: Team Formation + Market Dynamics**
- Multi-party negotiation (2+ agents per proposal)
- ILP-based team optimization (optional exact solver)
- Reputation integration in discovery ranking
- Stale skill pruning

**Phase 3: Intelligence Layer**
- Vector embedding for semantic skill discovery
- Sybil resistance detection
- Diversity scoring in team formation
- Dispute resolution lifecycle

**Phase 4: Serve + Ecosystem**
- FastAPI HTTP server
- Postgres backend
- OpenAPI schema
- VAOS adapter integration

## Philosophy

**Zero coupling.** The protocol works standalone as a library. An agent built on LangChain, CrewAI, AutoGen, or raw Python can participate in the same protocol instance.

**Three API calls.** Any agent platform can integrate with just:
1. `register` — Declare skills
2. `discover` — Find partners
3. `propose` — Offer collaboration

**Reputation is earned.** Trust scores come from actual collaboration outcomes, not self-claims. Decay prevents permanent high reputation without continued activity.

## License

MIT

---

*Built for Viable Systems. Applicable everywhere.*

*The protocol that turns isolated agents into a collaborative economy.*
