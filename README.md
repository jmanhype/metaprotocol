# MetaAgent-Protocol

**Coordination protocol for autonomous agents.**

Agents that discover, negotiate, and form teams dynamically — without human coordination.

## What It Is

MetaAgent-Protocol is not an agent framework and not a platform. It's a **coordination protocol**. It doesn't run agents or host them — it provides the communication and economic infrastructure that lets agents self-organize into teams, negotiate fair compensation, and build trust over time.

Think of it as a labor market where agents:
- Post resumes (register skills)
- Find gigs (discover partners)
- Form project teams
- Get rated (reputation)

All fully automated, at machine speed.

## Key Features

### Core Protocol
- **Skill Registry** — Agents declare capabilities with metadata; discover via keyword or semantic vector search
- **Reputation System** — Trust scores derived from actual collaboration outcomes, with time-based decay to prevent inflation
- **Negotiation Engine** — Structured proposal-accept-execute-verify lifecycle with escrow contracts
- **Team Formation** — Constraint-based optimizer forms optimal teams given requirements and budget (greedy or ILP)
- **Team Memory** — Shared collaborative context across team members with append-only interaction log

### Intelligence Layer (Phase 3)
- **Vector Embeddings** — Semantic skill discovery using sentence-transformers (`all-MiniLM-L6-v2`)
- **Sybil Resistance** — Colluding-ring detection via partner graph analysis
- **ILP Optimization** — Exact team formation using integer linear programming (PuLP)
- **Diversity Scoring** — Encourages fresh team combinations by penalizing past collaborations
- **Dispute Resolution** — Manual or auto-resolution with reputation-based tiebreaking
- **Market Rate Validation** — Compensation validation against median market rates

### Serve & Ecosystem (Phase 4)
- **FastAPI HTTP Server** — All protocol operations as REST endpoints with OpenAPI schema
- **PostgreSQL Backend** — Production-ready async storage with connection pooling
- **VAOS Adapter** — Sync agents and collaboration history from VAOS databases
- **Protocol Dashboard** — Health check and statistics endpoint

## Quickstart

### Installation

```bash
# Core (Python API + CLI)
pip install metaprotocol

# With FastAPI server
pip install metaprotocol[serve]

# With vector embeddings
pip install metaprotocol[vectors]

# With SQL backends (PostgreSQL)
pip install metaprotocol[sql]

# With ILP optimizer
pip install metaprotocol[ilp]

# Everything
pip install metaprotocol[all]
```

### Basic Usage

```bash
# Register a skill
meta-protocol register \
  --agent-id agent-001 \
  --skill code_generation \
  --complexity advanced \
  --cost-per-use 0.15 \
  --success-rate 0.87

# Discover collaborators (keyword search)
meta-protocol discover \
  --skills code_generation,data_analysis \
  --format json

# Discover collaborators (semantic search)
meta-protocol discover \
  --query "I need someone who can analyze CSV datasets and produce charts" \
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

# Form optimal team for a task
meta-protocol form-team \
  --task-id task-xyz \
  --skills code_generation,data_analysis,code_review \
  --budget 2.00

# Query reputation profile
meta-protocol reputation \
  --agent-id agent-001 \
  --format json

# Get market rate for a skill
meta-protocol market-rate \
  --skill code_generation \
  --complexity advanced

# Get recommended compensation
meta-protocol recommend-comp \
  --skills code_generation,data_analysis \
  --percentile 0.5

# Start HTTP API server
meta-protocol serve --port 8430

# Show protocol statistics
meta-protocol status --format json
```

## Architecture

```
Agent Systems (VAOS, LangChain, CrewAI, AutoGen, custom)
  ↓ 3 API calls: register / discover / propose
MetaAgent-Protocol
  ├─ Skill Registry (register, update, discover)
  │   ├─ Vector Embeddings (semantic search)
  │   ├─ Ranking (composite scores)
  │   └─ Pruning (stale skill cleanup)
  │
  ├─ Reputation System
  │   ├─ Scoring (weighted moving average)
  │   ├─ Decay (time-based reputation decay)
  │   ├─ Sybil (colluding-ring detection)
  │   └─ Dispute (resolution lifecycle)
  │
  ├─ Negotiation Engine
  │   ├─ State Machine (transition validation)
  │   ├─ Escrow (contract lifecycle)
  │   ├─ Multi-party (2+ agents)
  │   └─ Expiration (TTL-based)
  │
  ├─ Team Formation
  │   ├─ Optimizer Greedy (heuristic)
  │   ├─ Optimizer ILP (exact, optional)
  │   ├─ Memory (shared state)
  │   └─ Lifecycle (status transitions)
  │
  ├─ Market Rates
  │   └─ VAOS Adapter
  │
  └─ Storage
      ├─ SQLite (default)
      ├─ PostgreSQL (async, production)
      └─ In-memory (testing)
```

## File Structure

```
metaprotocol/
├── __init__.py                          # Public API surface
├── types.py                              # All Pydantic models
├── exceptions.py                          # Custom exceptions
├── protocol.py                           # Main MetaProtocol orchestration class
├── market.py                             # Market rate validation
├── vaos_adapter.py                       # VAOS integration
│
├── registry/
│   ├── skill_registry.py                  # SkillRegistry: register, update, discover
│   ├── embedding.py                      # Vector embedding generation + similarity search
│   ├── ranking.py                        # Composite score ranking
│   └── pruning.py                        # Stale skill detection and cleanup
│
├── reputation/
│   ├── reputation_system.py              # ReputationSystem: record, query, decay
│   ├── dispute.py                        # Dispute lifecycle management
│   ├── scoring.py                        # Weighted moving average calculation
│   ├── decay.py                          # Time-based reputation decay
│   └── sybil.py                          # Colluding-ring detection
│
├── negotiation/
│   ├── engine.py                         # NegotiationEngine: propose, counter, accept, reject
│   ├── state_machine.py                 # Proposal state transitions with validation
│   ├── escrow.py                         # EscrowContract lifecycle
│   ├── multiparty.py                     # Multi-agent proposal coordination
│   └── expiration.py                    # TTL-based proposal expiration
│
├── team/
│   ├── formation.py                      # TeamFormationEngine: form_team
│   ├── optimizer_greedy.py              # Greedy heuristic solver
│   ├── optimizer_ilp.py                 # Integer linear programming solver (optional)
│   ├── memory.py                         # TeamMemory: shared state read/write
│   └── lifecycle.py                     # Team status transitions
│
├── store/
│   ├── base.py                          # AbstractProtocolStore interface
│   ├── sqlite.py                        # SQLite backend (default)
│   ├── postgres.py                      # PostgreSQL backend (async)
│   └── memory.py                        # In-memory backend (testing)
│
├── serve/
│   ├── app.py                           # FastAPI application factory
│   └── routes.py                        # All HTTP endpoints
│
├── cli/
│   └── main.py                          # Typer CLI
│
└── utils/
    ├── ids.py                           # UUID generation utilities
    ├── time.py                          # Timestamp handling
    └── validation.py                    # Cross-model validation helpers
```

## CLI Commands

| Command | Purpose |
|---------|---------|
| `register` | Register agent skills |
| `discover` | Find collaborators by skill, complexity, cost, or semantic query |
| `propose` | Create collaboration proposal |
| `respond` | Accept/reject/counter a proposal |
| `complete` | Mark proposal complete (triggers escrow release and reputation) |
| `reputation` | Query agent reputation profile |
| `form-team` | Auto-form optimal team for task (greedy or ILP) |
| `optimize-team` | Optimize team with custom weights and strategy |
| `market-rate` | Get market rate for a skill |
| `recommend-comp` | Get recommended compensation for skill set |
| `dispute` | Open a dispute on a proposal |
| `resolve-dispute` | Manually resolve a dispute |
| `prune-skills` | Detect/remove stale skills from registry |
| `status` | Show protocol statistics (agents, skills, proposals, teams) |
| `serve` | Start HTTP API server |
| `vaos-sync` | Sync agents and collaborations from VAOS database |

## Python API

```python
from metaprotocol import MetaProtocol, AgentCapability, ComplexityLevel

# Initialize protocol with embeddings enabled
protocol = MetaProtocol(
    db_path=".metaprotocol.db",
    strategy="greedy",  # or "ilp"
    enable_embeddings=True,  # for semantic search
    embedding_model="all-MiniLM-L6-v2",
)

# Register skill
capability = AgentCapability(
    agent_id="agent-001",
    name="code_generation",
    complexity_level=ComplexityLevel.ADVANCED,
    cost_per_use=0.15,
    success_rate=0.87,
    description="Generate production Python code from natural language specs",
)
protocol.registry.register(capability)

# Discover partners (keyword)
results = protocol.registry.discover(
    required_skills=["code_generation", "data_analysis"],
    complexity_min=ComplexityLevel.INTERMEDIATE,
    max_cost_per_use=0.50,
)

# Discover partners (semantic)
results = protocol.registry.discover(
    query="I need someone who can write Python scripts",
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

# Check reputation
profile = protocol.reputation.get_profile("agent-001")
print(f"Score: {profile.reputation_score}, Verified: {profile.is_verified}")

# Detect sybil rings
flagged = protocol.reputation.detect_sybil(min_mutual_collaborations=5)

# Validate compensation
validation = protocol.market.validate_compensation(
    required_skills=["code_generation"],
    offered_compensation=0.50,
)
print(f"Is below market: {validation['is_below_market']}")

# Use VAOS adapter
vaos = protocol.create_vaos_adapter(vaos_db_path="vaos.db")
synced = vaos.sync_agents_from_vaos()
imported = vaos.import_collaborations_to_reputation()
```

## HTTP API

### Start Server

```bash
meta-protocol serve --host 0.0.0.0 --port 8430
```

### Endpoints

```
GET  /health              - Health check
GET  /stats               - Protocol statistics
POST /register            - Register skill capability
GET  /discover            - Discover agents (skills, query, filters)
POST /propose             - Create proposal
POST /propose/{id}/respond - Accept/reject/counter
POST /propose/{id}/complete - Complete proposal
POST /team/form           - Form team
GET  /team/{id}           - Get team details
POST /team/{id}/write     - Write to team memory
GET  /reputation/{id}     - Get reputation profile
POST /rate                - Record collaboration outcome
POST /disputes            - Open dispute
GET  /market/rates/{skill} - Get market rate
GET  /market/validate     - Validate compensation
POST /optimize/team       - Optimize team formation
```

OpenAPI schema available at `http://localhost:8430/docs`

## Implementation Status

### Phase 1: Core Protocol (MVP) ✅
- ✅ All Pydantic models finalized and tested
- ✅ Skill registry with keyword-based discovery
- ✅ Reputation ledger with weighted scoring and decay
- ✅ 1:1 negotiation engine with full state machine
- ✅ Escrow contract lifecycle
- ✅ SQLite backend
- ✅ CLI: register, discover, propose, respond, reputation, form-team

### Phase 2: Team Formation + Market Dynamics ✅
- ✅ Team formation engine with greedy heuristic optimizer
- ✅ Multi-skill agent preference (agents covering 2+ skills prioritized)
- ✅ Team memory with shared state and interaction history
- ✅ Multi-party negotiation support
- ✅ Composite ranking with reputation integration in discovery
- ✅ Stale skill pruning

### Phase 3: Intelligence Layer ✅
- ✅ Vector embeddings for semantic skill discovery (sentence-transformers)
- ✅ Sybil resistance detection via partner graph analysis
- ✅ ILP-based team optimization (optional, via PuLP)
- ✅ Diversity scoring in team formation
- ✅ Dispute resolution lifecycle with auto-resolution
- ✅ Market rate validation and compensation recommendation

### Phase 4: Serve + Ecosystem ✅
- ✅ FastAPI HTTP server with all protocol operations as endpoints
- ✅ Protocol status and health dashboard
- ✅ PostgreSQL backend for production deployments
- ✅ OpenAPI schema export
- ✅ VAOS adapter for agent syncing
- ✅ Directory structure matches specification

## Performance Targets

| Operation | Target | Note |
|-----------|--------|-------|
| Skill discovery (keyword) | < 50ms | p95 with 1,000 skills |
| Skill discovery (semantic) | < 200ms | p95 with embeddings |
| Proposal accept/reject | < 100ms | p95 including escrow |
| Team formation (greedy) | < 100ms | 50 candidates, 5 skills |
| Team formation (ILP) | < 1000ms | 50 candidates, 5 skills |
| Reputation query | < 20ms | p95 with 10k records |
| Sybil detection | < 10s | 1,000 agents |

## Philosophy

**Zero coupling.** The protocol works standalone as a library. An agent built on LangChain, CrewAI, AutoGen, or raw Python can participate in the same protocol instance.

**Three API calls.** Any agent platform can integrate with just:
1. `register` — Declare skills
2. `discover` — Find partners
3. `propose` — Offer collaboration

**Reputation is earned.** Trust scores come from actual collaboration outcomes, not self-claims. Decay prevents permanent high reputation without continued activity.

## Dependencies

### Core (always installed)
- `pydantic>=2.0` — Data models and validation
- `typer>=0.12` — CLI framework
- `rich>=13.0` — Terminal output formatting
- `numpy>=1.25` — Scoring and optimization math

### Optional extras

```bash
# FastAPI HTTP server
pip install metaprotocol[serve]  # adds fastapi>=0.115, uvicorn>=0.30

# Vector embeddings for semantic search
pip install metaprotocol[vectors]  # adds sentence-transformers>=3.0

# SQL backends (PostgreSQL, async)
pip install metaprotocol[sql]  # adds asyncpg>=0.29, aiosqlite>=0.20

# ILP optimizer for exact team formation
pip install metaprotocol[ilp]  # adds pulp>=2.8

# Everything
pip install metaprotocol[all]  # all of the above
```

## License

MIT

---

*Built for Viable Systems. Applicable everywhere.*

*The protocol that turns isolated agents into a collaborative economy.*
