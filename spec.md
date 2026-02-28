# BUILD PROMPT: MetaAgent-Protocol

> *Agents that discover, negotiate, and form teams dynamically — without human coordination.*

---

## Directive

Build a **production-grade Python library and CLI** called `metaprotocol` that gives autonomous agents the ability to find each other, negotiate task agreements, form ad-hoc teams, and build reputations based on actual collaborative outcomes. The system exposes a lightweight protocol layer that any agent platform can integrate with 3 API calls — register skills, discover partners, propose collaboration.

This is not an agent framework and not a platform. It's a **coordination protocol**. It doesn't run agents or host them — it provides the communication and economic infrastructure that lets agents self-organize into teams, negotiate fair compensation, and build trust over time. Think of it as the labor market where agents post resumes, find gigs, form project teams, and get rated — except fully automated and machine-speed.

It must work standalone as a library with zero coupling to any specific agent platform. VAOS integration is one adapter among many. An agent built on LangChain, CrewAI, AutoGen, or raw Python can participate in the same protocol.

---

## Architecture Overview

```
┌───────────────────────────────────────────────────────────────────────┐
│                        Agent Systems                                   │
│                                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ VAOS     │  │ LangChain│  │ CrewAI   │  │ Custom   │  ... any     │
│  │ Agent A  │  │ Agent B  │  │ Agent C  │  │ Agent D  │      agent   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │              │              │              │                    │
│       └──────────────┴──────┬───────┴──────────────┘                   │
│                             │  3 API calls:                            │
│                             │  register / discover / propose           │
└─────────────────────────────┼─────────────────────────────────────────┘
                              ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      MetaAgent-Protocol                                │
│                                                                        │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐     │
│  │  SKILL REGISTRY  │   │  NEGOTIATION    │   │  REPUTATION     │     │
│  │                  │   │  ENGINE         │   │  SYSTEM         │     │
│  │  Agents declare  │   │                 │   │                 │     │
│  │  capabilities    │   │  Propose →      │   │  Track success  │     │
│  │  with metadata   │   │  Accept/Reject  │   │  Decay over     │     │
│  │                  │   │  → Escrow →     │   │  time           │     │
│  │  Vector search   │   │  Execute →      │   │  Sybil-resist   │     │
│  │  for discovery   │   │  Verify →       │   │  scoring        │     │
│  │                  │   │  Release        │   │                 │     │
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘     │
│           │                     │                      │               │
│           ▼                     ▼                      ▼               │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    TEAM FORMATION ENGINE                        │   │
│  │                                                                 │   │
│  │  Constraint satisfaction: maximize team_success_rate             │   │
│  │  subject to total_cost ≤ budget AND required_skills covered     │   │
│  │                                                                 │   │
│  │  Produces: TeamAssignment with shared_state, escrow_contract    │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    TEAM MEMORY                                  │   │
│  │  Shared collaborative context across team members               │   │
│  │  Interaction history, agreed terms, execution state             │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Storage: SQLite (default) / Postgres / In-memory               │   │
│  │  API Server: FastAPI (optional `meta-protocol serve`)           │   │
│  │  CLI: `meta-protocol register | discover | propose | ...`      │   │
│  └────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Data Model

Every concept in the system maps to a strict Pydantic model. These are the canonical types — all protocol operations consume and produce these.

### Agent Capability

What an agent can do. Registered once, updated as the agent improves.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class ComplexityLevel(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class AgentCapability(BaseModel):
    """A single skill an agent offers to the protocol."""

    skill_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str                               # who owns this skill
    name: str                                   # human-readable: "code_generation", "data_analysis"
    description: Optional[str] = None           # longer description for semantic search
    complexity_level: ComplexityLevel
    success_rate: float = 0.0                   # historical success percentage (0.0–1.0)
    cost_per_use: float = 0.0                   # tokens/credits per invocation
    embedding: Optional[list[float]] = None     # vector embedding for semantic discovery
    metadata: dict = Field(default_factory=dict) # arbitrary: {"languages": ["python", "sql"]}
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "skill_id": "sk-a1b2c3",
                "agent_id": "agent-001",
                "name": "code_generation",
                "description": "Generate production Python code from natural language specs",
                "complexity_level": "advanced",
                "success_rate": 0.87,
                "cost_per_use": 0.15,
                "metadata": {"languages": ["python", "typescript"], "max_file_size": 5000}
            }
        }
```

### Reputation Record

Trust built from actual collaboration outcomes. Not self-reported — protocol-verified.

```python
class ReputationRecord(BaseModel):
    """An agent's trust profile, derived from collaboration history."""

    agent_id: str
    reputation_score: float = 50.0              # 0–100; starts at 50 (neutral)
    total_collaborations: int = 0
    successful_collaborations: int = 0
    disputed_collaborations: int = 0
    partners: list[str] = Field(default_factory=list)  # agent_ids of past collaborators
    success_rate: float = 0.0                   # successful / total
    avg_partner_satisfaction: float = 0.0       # mean rating received from partners (0–5)
    recent_ratings: list["CollaborationRating"] = Field(default_factory=list)
    reputation_history: list["ReputationSnapshot"] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class CollaborationRating(BaseModel):
    """A single rating from a collaboration partner."""

    rater_agent_id: str
    rated_agent_id: str
    collaboration_id: str
    score: float                                # 0–5
    comment: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReputationSnapshot(BaseModel):
    """Point-in-time reputation for trend analysis."""

    score: float
    timestamp: datetime
    event: str                                  # "collaboration_completed", "dispute_resolved", "decay"
```

### Negotiation

The proposal-accept-execute-verify lifecycle.

```python
class NegotiationStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTERED = "countered"
    EXPIRED = "expired"
    IN_ESCROW = "in_escrow"
    EXECUTING = "executing"
    COMPLETED = "completed"
    DISPUTED = "disputed"

class NegotiationProposal(BaseModel):
    """A proposal from one agent to another for task collaboration."""

    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposer_agent_id: str                      # who is offering the work
    responder_agent_id: str                     # who is being asked to do it
    task_id: str                                # what task this is for
    required_skills: list[str]                  # skill names needed
    offered_compensation: float                 # tokens/credits offered
    deadline: Optional[datetime] = None         # when the work must be done
    escrow: bool = True                         # hold funds until verification
    terms: dict = Field(default_factory=dict)   # arbitrary: {"max_retries": 3, "quality_threshold": 0.8}
    status: NegotiationStatus = NegotiationStatus.PROPOSED
    counter_offers: list["CounterOffer"] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None       # auto-expire if no response


class CounterOffer(BaseModel):
    """A counter-proposal modifying the original terms."""

    counter_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str                               # who is countering
    revised_compensation: Optional[float] = None
    revised_deadline: Optional[datetime] = None
    revised_terms: dict = Field(default_factory=dict)
    message: Optional[str] = None               # "I can do it for 0.20/call if you extend deadline"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### Team

The formed collaboration unit with shared state.

```python
class TeamStatus(str, Enum):
    FORMING = "forming"
    ACTIVE = "active"
    EXECUTING = "executing"
    COMPLETED = "completed"
    DISSOLVED = "dissolved"

class Team(BaseModel):
    """A formed collaboration team with shared context."""

    team_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    agent_ids: list[str]                        # participating agents
    role_assignments: dict[str, str] = Field(default_factory=dict)  # {agent_id: "lead" | "specialist" | "reviewer"}
    required_skills: list[str]
    skill_coverage: dict[str, str] = Field(default_factory=dict)    # {skill_name: agent_id}
    shared_state: dict = Field(default_factory=dict)                # collaborative working memory
    interaction_history: list["TeamInteraction"] = Field(default_factory=list)
    agreed_terms: dict = Field(default_factory=dict)                # merged negotiation terms
    escrow_contract_id: Optional[str] = None
    total_budget: float = 0.0
    status: TeamStatus = TeamStatus.FORMING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class TeamInteraction(BaseModel):
    """A single interaction within a team's history."""

    agent_id: str
    action: str                                 # "submitted_output", "requested_review", "shared_context"
    payload: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TeamAssignment(BaseModel):
    """Output of the team formation optimizer."""

    team: Team
    expected_success_rate: float                # predicted team success probability
    total_cost: float                           # sum of all agent costs
    optimization_score: float                   # objective function value
    alternatives_considered: int                # how many team compositions were evaluated
    formation_latency_ms: float                 # how long optimization took
```

### Discovery Result

What comes back when an agent searches for collaborators.

```python
class DiscoveryMatch(BaseModel):
    """A single agent matching a discovery query."""

    agent_id: str
    skill_id: str
    skill_name: str
    complexity_level: ComplexityLevel
    success_rate: float
    cost_per_use: float
    reputation_score: float
    relevance_score: float                      # semantic similarity to query (0.0–1.0)
    availability: bool = True


class DiscoveryResult(BaseModel):
    """Complete response from a discovery query."""

    query_skills: list[str]
    matches: list[DiscoveryMatch]               # ordered by composite score (relevance × reputation)
    total_candidates_scanned: int
    latency_ms: float
```

---

## Component Specifications

### Component 1: Skill Registry

**Purpose:** Agents register what they can do. Other agents search for capabilities they need. The registry is the phone book of the protocol.

```python
from metaprotocol import SkillRegistry

registry = SkillRegistry(
    backend="sqlite",                   # also: "postgres", "memory"
    enable_vector_search=True,          # semantic skill matching
    embedding_model="all-MiniLM-L6-v2", # sentence-transformers model for embeddings
)

# Register a skill
capability = AgentCapability(
    agent_id="agent-001",
    name="code_generation",
    description="Generate production Python code from natural language specifications",
    complexity_level="advanced",
    success_rate=0.87,
    cost_per_use=0.15,
)
registry.register(capability)

# Discover agents by skill requirements
results = registry.discover(
    required_skills=["code_generation", "data_analysis"],
    complexity_min="intermediate",
    max_cost_per_use=0.50,
    min_reputation=60.0,              # cross-references reputation system
    limit=10,
)
# → DiscoveryResult with ranked matches
```

**Implementation requirements:**

1. **Dual search modes** — Support both exact keyword matching (`name == "code_generation"`) and semantic vector search (`description` similarity to a natural language query like "I need someone who can write Python scripts"). Vector search uses sentence-transformers embeddings stored alongside the capability record. Fall back to keyword matching if vector search is disabled or embeddings aren't available.

2. **Composite ranking** — Discovery results are ranked by a weighted composite score:
   ```
   composite = (w_relevance × relevance_score) +
               (w_reputation × normalized_reputation) +
               (w_success × success_rate) +
               (w_cost × (1 - normalized_cost))
   ```
   Default weights: relevance=0.4, reputation=0.3, success=0.2, cost=0.1. Configurable per query.

3. **Complexity-aware matching** — An `intermediate` agent can be matched to `advanced` task requirements if their `success_rate` on similar tasks exceeds a configurable threshold (default 0.75). A `basic` agent never matches `advanced` requirements.

4. **Skill updates** — Agents can update their capabilities (new success_rate, new cost_per_use) without re-registering. Updates are timestamped. The registry maintains a history of capability changes for audit.

5. **Stale skill pruning** — Skills not updated within a configurable window (default: 30 days) are flagged as stale and deprioritized in search results. Skills not updated in 90 days are soft-deleted.

---

### Component 2: Reputation System

**Purpose:** Decentralized trust scoring derived from actual collaboration outcomes. Reputation is earned, not self-reported.

```python
from metaprotocol import ReputationSystem

reputation = ReputationSystem(
    initial_score=50.0,               # new agents start neutral
    decay_rate=0.02,                  # 2% monthly decay to prevent inflation
    min_collaborations_for_trust=3,   # below this, score is flagged as "unverified"
    sybil_detection=True,             # enable colluding-ring detection
)

# After a collaboration completes
reputation.record_outcome(
    agent_id="agent-001",
    partner_id="agent-002",
    collaboration_id="collab-xyz",
    success=True,
    partner_rating=4.5,              # 0–5 scale
)

# Query an agent's reputation
profile = reputation.get_profile("agent-001")
# → ReputationRecord with score, history, trends
```

**Implementation requirements:**

1. **Score calculation** — Reputation score is a weighted moving average:
   ```
   new_score = (current_score × α) + (collaboration_outcome × (1 - α))
   ```
   Where `α` = 0.85 (heavy weight on history to prevent gaming), and `collaboration_outcome` is derived from: task success (0 or 1), partner rating (normalized to 0–1), and on-time delivery (boolean → 0 or 1).

2. **Decay function** — Every 30 days, all scores decay toward the neutral point (50):
   ```
   decayed_score = score - (decay_rate × (score - 50))
   ```
   This prevents agents from accumulating permanent high reputation without continued activity. Decay is applied lazily on read (not via background jobs) for simplicity.

3. **Reputation bootstrapping** — New agents start at 50 with an "unverified" flag. After `min_collaborations_for_trust` successful collaborations, the flag is removed. Unverified agents are ranked below verified agents in discovery results, but are not excluded — new agents need a way in.

4. **Sybil resistance** — Detect colluding reputation rings:
   - If two agents exclusively rate each other (no other partners), flag both.
   - If a cluster of agents form a closed rating loop (A rates B, B rates C, C rates A, no outside partners), reduce the weight of their mutual ratings by 50%.
   - Algorithm: Build a partner graph, detect strongly connected components with low external connectivity. Flag components where `internal_edges / total_edges > 0.8`.

5. **Dispute handling** — Either party can open a dispute on a completed collaboration. Disputes freeze the reputation impact of that collaboration until resolved. Resolution can be: automated (based on objective task success metrics), or manual (flagged for human review). Unresolved disputes after 7 days auto-resolve in favor of the higher-reputation party (incentivizes building trust).

---

### Component 3: Negotiation Engine

**Purpose:** Structured proposal-response protocol for agents to agree on task terms before execution begins. Supports 1:1 and multi-party negotiation.

```python
from metaprotocol import NegotiationEngine

negotiation = NegotiationEngine(
    proposal_ttl_hours=24,             # proposals expire after 24h
    max_counter_offers=5,              # prevent infinite ping-pong
    escrow_enabled=True,               # hold funds during execution
)

# Agent A proposes work to Agent B
proposal = negotiation.propose(
    proposer_agent_id="agent-001",
    responder_agent_id="agent-002",
    task_id="task-xyz",
    required_skills=["data_analysis"],
    offered_compensation=0.50,
    deadline=datetime(2026, 3, 15),
    terms={"quality_threshold": 0.8, "max_retries": 3},
)
# → NegotiationProposal(status="proposed")

# Agent B counters
negotiation.counter(
    proposal_id=proposal.proposal_id,
    agent_id="agent-002",
    revised_compensation=0.75,
    message="I can guarantee 0.9 quality if you increase comp",
)

# Agent A accepts the counter
negotiation.accept(proposal_id=proposal.proposal_id, agent_id="agent-001")
# → status transitions to "in_escrow", funds locked

# After task execution and verification
negotiation.complete(
    proposal_id=proposal.proposal_id,
    success=True,
    verification_data={"output_quality": 0.92},
)
# → funds released from escrow, reputation updated
```

**Implementation requirements:**

1. **State machine** — Proposals follow a strict state machine:
   ```
   PROPOSED → ACCEPTED → IN_ESCROW → EXECUTING → COMPLETED
                                                 → DISPUTED
            → REJECTED (terminal)
            → COUNTERED → PROPOSED (loop, max N times)
            → EXPIRED (terminal, via TTL)
   ```
   Invalid transitions raise `NegotiationStateError` with the current state and attempted transition.

2. **Multi-party negotiation** — For tasks requiring multiple agents, the proposer can create a `MultiPartyProposal` that targets N agents simultaneously. Each agent accepts/rejects independently. The proposal becomes `ACCEPTED` only when all required skill slots are filled. Partial acceptance is tracked: "3 of 5 agents accepted, waiting on data_analysis and code_review slots."

3. **Escrow system** — When a proposal is accepted and `escrow=True`:
   - The proposer's compensation amount is locked in an `EscrowContract`.
   - Funds are released to the responder only after the proposer verifies task completion or after a configurable auto-release timeout (default: 48h after execution).
   - If disputed, funds are frozen until resolution.
   - Escrow is tracked via the `EscrowContract` model — not actual crypto/blockchain, just protocol-level accounting that the host platform can map to real payments.

   ```python
   class EscrowContract(BaseModel):
       contract_id: str
       proposal_id: str
       payer_agent_id: str
       payee_agent_id: str
       amount: float
       status: str              # "locked" | "released" | "refunded" | "frozen"
       locked_at: datetime
       released_at: Optional[datetime] = None
       auto_release_at: datetime  # deadline for auto-release
   ```

4. **Proposal expiration** — Proposals not responded to within `proposal_ttl_hours` auto-transition to `EXPIRED`. Counter offers reset the TTL clock. Expiration is checked lazily on read.

5. **Compensation validation** — The engine validates that `offered_compensation >= sum(cost_per_use)` for all required skills. If the offer is below the market rate (median cost_per_use for those skills in the registry), the engine flags it as "below market" but doesn't block it — agents can accept below-market offers if they choose.

---

### Component 4: Team Formation Engine

**Purpose:** Given a task and a pool of candidates, form the optimal team. This is a constrained optimization problem.

```python
from metaprotocol import TeamFormationEngine

formation = TeamFormationEngine(
    optimization_strategy="greedy_heuristic",  # also: "ilp" (integer linear programming)
    max_team_size=10,
    timeout_ms=1000,                           # hard cap on optimization time
)

assignment = formation.form_team(
    task_id="task-xyz",
    required_skills=["code_generation", "data_analysis", "code_review"],
    candidates=discovery_results.matches,       # from discovery step
    budget=2.00,                                # maximum total compensation
    optimization_weights={
        "success_rate": 0.4,
        "reputation": 0.3,
        "cost": 0.2,
        "diversity": 0.1,                      # prefer agents who haven't worked together (fresh perspectives)
    },
)
# → TeamAssignment with team, expected_success_rate, total_cost
```

**Implementation requirements:**

1. **Optimization formulation** — The core problem is:
   ```
   Maximize:  Σ (w_success × success_rate_i + w_reputation × reputation_i + w_diversity × diversity_i) × x_i
   Subject to:
     Σ cost_per_use_i × x_i  ≤  budget
     For each required_skill s:  Σ x_i (where agent i has skill s)  ≥  1
     Σ x_i  ≤  max_team_size
     x_i ∈ {0, 1}
   ```
   Where `x_i = 1` means agent i is selected for the team.

2. **Two optimization strategies:**
   - **Greedy heuristic** (default): For each required skill, rank candidates by composite score and select the best available. Resolve multi-skill agents efficiently (one agent covering 2+ skills is preferred over 2 single-skill agents if cheaper). O(n × k) where n = candidates, k = required skills. Target: < 100ms for 50 candidates.
   - **ILP solver** (optional extra): Exact solution using `scipy.optimize.milp` or `PuLP`. Guaranteed optimal but slower. Use when team size > 5 or budget is tight. Target: < 1s for 50 candidates.

3. **Diversity scoring** — `diversity_i` for an agent is inversely proportional to how many of the other selected team members they've collaborated with before. This prevents cliques and encourages fresh combinations. Calculated from the reputation system's partner history.

4. **Skill coverage validation** — After optimization, validate that every required skill is covered by at least one team member. If not (budget too low, not enough candidates), return a `TeamFormationError` with: which skills are uncovered, the minimum additional budget needed to cover them, and alternative team compositions that cover a subset of skills.

5. **Shared state initialization** — When a team is formed, initialize `shared_state` with: the task description, each agent's role assignment, the agreed terms from negotiation, and a blank interaction history. This shared state is the team's working memory — agents read from and write to it during execution.

---

### Component 5: Team Memory

**Purpose:** Shared collaborative context that persists across team interactions. Agents can read what teammates have done, share intermediate results, and coordinate without direct messaging.

```python
from metaprotocol import TeamMemory

memory = TeamMemory(team_id="team-xyz", backend="sqlite")

# Agent writes to shared state
memory.write(
    agent_id="agent-001",
    action="submitted_output",
    payload={"code_file": "main.py", "test_coverage": 0.82},
)

# Another agent reads the team's state
state = memory.read()
# → Team.shared_state with full interaction_history

# Query specific interactions
reviews = memory.query(action="requested_review", agent_id="agent-002")
```

**Implementation requirements:**

1. **Append-only interaction log** — All writes to team memory are appended to `interaction_history`. No overwrites, no deletes. This gives a full audit trail of team coordination.

2. **Shared state merging** — The `shared_state` dict is updated via merge (not replace). When agent-001 writes `{"code_file": "main.py"}` and agent-002 writes `{"review_notes": "LGTM"}`, shared_state becomes `{"code_file": "main.py", "review_notes": "LGTM"}`. Conflicting keys are resolved by last-write-wins with the conflict logged.

3. **Access control** — Only agents listed in `team.agent_ids` can read or write to the team's memory. Attempts by non-members raise `TeamAccessError`.

4. **Team lifecycle** — Memory is writable while team status is `ACTIVE` or `EXECUTING`. Once `COMPLETED` or `DISSOLVED`, memory becomes read-only (for post-mortem analysis).

---

## CLI Specification

```bash
# ─── REGISTER ──────────────────────────────────────────────────────
# Register an agent's skills with the protocol.

meta-protocol register \
  --agent-id agent-001 \
  --skill "code_generation" \
  --description "Generate production Python code from specs" \
  --complexity advanced \
  --cost-per-use 0.15 \
  --success-rate 0.87

# Register multiple skills from a JSON file
meta-protocol register --agent-id agent-001 --from-file skills.json


# ─── DISCOVER ──────────────────────────────────────────────────────
# Find agents matching skill requirements.

meta-protocol discover \
  --skills "code_generation,data_analysis" \
  --complexity-min intermediate \
  --max-cost 0.50 \
  --min-reputation 60 \
  --limit 10 \
  --format json

# Semantic search (natural language query)
meta-protocol discover \
  --query "I need someone who can analyze CSV datasets and produce charts" \
  --limit 5


# ─── PROPOSE ───────────────────────────────────────────────────────
# Propose a collaboration to another agent.

meta-protocol propose \
  --from agent-001 \
  --to agent-002 \
  --task-id task-xyz \
  --skills "data_analysis" \
  --compensation 0.50 \
  --deadline 2026-03-15 \
  --escrow

# Accept / reject / counter
meta-protocol respond \
  --proposal-id prop-abc \
  --action accept

meta-protocol respond \
  --proposal-id prop-abc \
  --action counter \
  --revised-compensation 0.75 \
  --message "Need more for guaranteed 0.9 quality"


# ─── FORM TEAM ─────────────────────────────────────────────────────
# Auto-form the optimal team for a task.

meta-protocol form-team \
  --task-id task-xyz \
  --required-skills "code_generation,data_analysis,code_review" \
  --budget 2.00 \
  --strategy greedy \
  --output team-assignment.json


# ─── REPUTATION ────────────────────────────────────────────────────
# Query an agent's reputation profile.

meta-protocol reputation \
  --agent-id agent-001 \
  --format json

# Record a collaboration outcome
meta-protocol rate \
  --agent-id agent-002 \
  --collaboration-id collab-xyz \
  --score 4.5 \
  --success true


# ─── SERVE ─────────────────────────────────────────────────────────
# Run the protocol as an HTTP API.

meta-protocol serve \
  --backend sqlite \
  --db ./protocol.db \
  --port 8430 \
  --host 0.0.0.0

# Endpoints:
# POST /register                          → register skill
# GET  /discover?skills=...&min_rep=...   → discovery search
# POST /propose                           → create proposal
# POST /propose/{id}/respond              → accept/reject/counter
# POST /team/form                         → auto-form team
# GET  /reputation/{agent_id}             → reputation profile
# POST /rate                              → record collaboration outcome
# GET  /team/{team_id}                    → team state + memory


# ─── STATUS ────────────────────────────────────────────────────────
# Protocol health and statistics.

meta-protocol status \
  --backend sqlite \
  --db ./protocol.db

# Output:
# Registered agents: 47
# Active skills: 132
# Open proposals: 8
# Active teams: 3
# Avg reputation: 62.4
# Collaborations (30d): 89
```

---

## Database Schema

```sql
-- Agent capabilities (skill registry)
CREATE TABLE IF NOT EXISTS agent_capabilities (
    skill_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    complexity_level TEXT NOT NULL CHECK (complexity_level IN ('basic', 'intermediate', 'advanced')),
    success_rate REAL NOT NULL DEFAULT 0.0,
    cost_per_use REAL NOT NULL DEFAULT 0.0,
    embedding BLOB,                                -- serialized vector for semantic search
    metadata TEXT NOT NULL DEFAULT '{}',            -- JSON
    registered_at TEXT NOT NULL,                    -- ISO 8601
    updated_at TEXT NOT NULL,
    is_stale BOOLEAN NOT NULL DEFAULT FALSE
);

-- Reputation ledger
CREATE TABLE IF NOT EXISTS reputation_ledger (
    agent_id TEXT NOT NULL,
    reputation_score REAL NOT NULL DEFAULT 50.0,
    total_collaborations INTEGER NOT NULL DEFAULT 0,
    successful_collaborations INTEGER NOT NULL DEFAULT 0,
    disputed_collaborations INTEGER NOT NULL DEFAULT 0,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_updated TEXT NOT NULL,
    PRIMARY KEY (agent_id)
);

-- Collaboration ratings (individual ratings from partners)
CREATE TABLE IF NOT EXISTS collaboration_ratings (
    rating_id TEXT PRIMARY KEY,
    rater_agent_id TEXT NOT NULL,
    rated_agent_id TEXT NOT NULL,
    collaboration_id TEXT NOT NULL,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 5),
    comment TEXT,
    timestamp TEXT NOT NULL
);

-- Negotiation proposals
CREATE TABLE IF NOT EXISTS negotiations (
    proposal_id TEXT PRIMARY KEY,
    proposer_agent_id TEXT NOT NULL,
    responder_agent_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    required_skills TEXT NOT NULL DEFAULT '[]',     -- JSON array
    offered_compensation REAL NOT NULL,
    deadline TEXT,
    escrow BOOLEAN NOT NULL DEFAULT TRUE,
    terms TEXT NOT NULL DEFAULT '{}',               -- JSON
    status TEXT NOT NULL DEFAULT 'proposed',
    counter_offers TEXT NOT NULL DEFAULT '[]',      -- JSON array
    created_at TEXT NOT NULL,
    expires_at TEXT
);

-- Escrow contracts
CREATE TABLE IF NOT EXISTS escrow_contracts (
    contract_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL REFERENCES negotiations(proposal_id),
    payer_agent_id TEXT NOT NULL,
    payee_agent_id TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'locked',
    locked_at TEXT NOT NULL,
    released_at TEXT,
    auto_release_at TEXT NOT NULL
);

-- Collaborative teams
CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    agent_ids TEXT NOT NULL DEFAULT '[]',           -- JSON array
    role_assignments TEXT NOT NULL DEFAULT '{}',    -- JSON
    required_skills TEXT NOT NULL DEFAULT '[]',     -- JSON array
    skill_coverage TEXT NOT NULL DEFAULT '{}',      -- JSON
    shared_state TEXT NOT NULL DEFAULT '{}',        -- JSON
    agreed_terms TEXT NOT NULL DEFAULT '{}',        -- JSON
    escrow_contract_id TEXT,
    total_budget REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'forming',
    created_at TEXT NOT NULL,
    completed_at TEXT
);

-- Team interaction history (append-only)
CREATE TABLE IF NOT EXISTS team_interactions (
    interaction_id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL REFERENCES teams(team_id),
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',             -- JSON
    timestamp TEXT NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_capabilities_agent ON agent_capabilities(agent_id);
CREATE INDEX IF NOT EXISTS idx_capabilities_name ON agent_capabilities(name);
CREATE INDEX IF NOT EXISTS idx_capabilities_stale ON agent_capabilities(is_stale);
CREATE INDEX IF NOT EXISTS idx_ratings_rated ON collaboration_ratings(rated_agent_id);
CREATE INDEX IF NOT EXISTS idx_ratings_collaboration ON collaboration_ratings(collaboration_id);
CREATE INDEX IF NOT EXISTS idx_negotiations_task ON negotiations(task_id);
CREATE INDEX IF NOT EXISTS idx_negotiations_status ON negotiations(status);
CREATE INDEX IF NOT EXISTS idx_teams_task ON teams(task_id);
CREATE INDEX IF NOT EXISTS idx_teams_status ON teams(status);
CREATE INDEX IF NOT EXISTS idx_interactions_team ON team_interactions(team_id);
```

---

## File Structure

```
metaprotocol/
├── __init__.py                          # Public API surface
├── types.py                             # All Pydantic models
├── exceptions.py                        # ProtocolError, NegotiationStateError, TeamFormationError, etc.
│
├── registry/
│   ├── __init__.py
│   ├── skill_registry.py                # SkillRegistry: register, update, discover
│   ├── embedding.py                     # Vector embedding generation + similarity search
│   ├── ranking.py                       # Composite score ranking for discovery results
│   └── pruning.py                       # Stale skill detection and cleanup
│
├── reputation/
│   ├── __init__.py
│   ├── reputation_system.py             # ReputationSystem: record, query, decay
│   ├── scoring.py                       # Weighted moving average calculation
│   ├── decay.py                         # Time-based reputation decay
│   ├── sybil.py                         # Colluding-ring detection via graph analysis
│   └── dispute.py                       # Dispute lifecycle management
│
├── negotiation/
│   ├── __init__.py
│   ├── engine.py                        # NegotiationEngine: propose, counter, accept, reject
│   ├── state_machine.py                 # Proposal state transitions with validation
│   ├── escrow.py                        # EscrowContract lifecycle
│   ├── multiparty.py                    # Multi-agent proposal coordination
│   └── expiration.py                    # TTL-based proposal expiration
│
├── team/
│   ├── __init__.py
│   ├── formation.py                     # TeamFormationEngine: form_team
│   ├── optimizer_greedy.py              # Greedy heuristic solver
│   ├── optimizer_ilp.py                 # Integer linear programming solver (optional)
│   ├── memory.py                        # TeamMemory: shared state read/write
│   └── lifecycle.py                     # Team status transitions
│
├── store/
│   ├── __init__.py
│   ├── base.py                          # AbstractProtocolStore interface
│   ├── sqlite.py                        # SQLite backend (default)
│   ├── postgres.py                      # Postgres backend (optional extra)
│   └── memory.py                        # In-memory backend (testing)
│
├── serve/
│   ├── __init__.py
│   ├── app.py                           # FastAPI application
│   └── routes.py                        # All HTTP endpoints
│
├── cli/
│   ├── __init__.py
│   └── main.py                          # Typer CLI: register, discover, propose, form-team, etc.
│
└── utils/
    ├── ids.py                           # UUID generation utilities
    ├── time.py                          # Timestamp handling
    └── validation.py                    # Cross-model validation helpers
```

---

## Comprehensive Unit Test Strategy

### Layer 1: Data Model Validation

```python
# tests/test_types.py

class TestAgentCapability:
    def test_valid_capability(self):
        """All required fields produce a valid capability."""
        cap = AgentCapability(agent_id="a", name="code_gen", complexity_level="advanced")
        assert cap.success_rate == 0.0
        assert cap.skill_id is not None  # auto-generated

    def test_rejects_invalid_complexity(self):
        """Unknown complexity values raise ValidationError."""
        with pytest.raises(ValidationError):
            AgentCapability(..., complexity_level="godlike")

    def test_serialization_roundtrip(self):
        """JSON serialize → deserialize produces identical object."""
        cap = make_capability(with_all_fields=True)
        assert AgentCapability.model_validate_json(cap.model_dump_json()) == cap

class TestNegotiationProposal:
    def test_default_status_is_proposed(self):
        """New proposals default to PROPOSED status."""
        p = make_proposal()
        assert p.status == NegotiationStatus.PROPOSED

    def test_expires_at_optional(self):
        """Proposals without explicit expiry are valid."""
        p = make_proposal(expires_at=None)
        assert p.expires_at is None
```

### Layer 2: Skill Registry Tests

```python
# tests/test_registry.py

class TestSkillRegistry:
    def test_register_and_discover(self, registry):
        """Registered skill appears in discovery results."""
        registry.register(make_capability(name="code_gen", agent_id="a"))
        results = registry.discover(required_skills=["code_gen"])
        assert len(results.matches) == 1
        assert results.matches[0].agent_id == "a"

    def test_complexity_filtering(self, registry):
        """basic agents excluded from advanced-only queries."""
        registry.register(make_capability(name="x", complexity_level="basic", agent_id="a"))
        registry.register(make_capability(name="x", complexity_level="advanced", agent_id="b"))
        results = registry.discover(required_skills=["x"], complexity_min="advanced")
        assert all(m.complexity_level == "advanced" for m in results.matches)

    def test_cost_filtering(self, registry):
        """Agents above max_cost_per_use are excluded."""
        registry.register(make_capability(name="x", cost_per_use=0.10, agent_id="cheap"))
        registry.register(make_capability(name="x", cost_per_use=5.00, agent_id="expensive"))
        results = registry.discover(required_skills=["x"], max_cost_per_use=0.50)
        assert len(results.matches) == 1
        assert results.matches[0].agent_id == "cheap"

    def test_semantic_discovery(self, registry_with_embeddings):
        """Natural language query finds semantically relevant skills."""
        registry_with_embeddings.register(
            make_capability(name="data_viz", description="Create charts and graphs from datasets")
        )
        results = registry_with_embeddings.discover(query="I need someone to make bar charts from CSV files")
        assert len(results.matches) > 0
        assert results.matches[0].relevance_score > 0.5

    def test_stale_skill_deprioritized(self, registry):
        """Skills not updated in 30+ days rank lower than fresh skills."""
        registry.register(make_capability(name="x", agent_id="stale", updated_at=days_ago(45)))
        registry.register(make_capability(name="x", agent_id="fresh", updated_at=now()))
        results = registry.discover(required_skills=["x"])
        assert results.matches[0].agent_id == "fresh"

    def test_empty_registry_returns_empty(self, registry):
        """Discovery on empty registry returns zero matches, no error."""
        results = registry.discover(required_skills=["anything"])
        assert len(results.matches) == 0
```

### Layer 3: Reputation Tests

```python
# tests/test_reputation.py

class TestReputationSystem:
    def test_initial_score(self, reputation):
        """New agents start at 50 with unverified flag."""
        profile = reputation.get_profile("new-agent")
        assert profile.reputation_score == 50.0
        assert profile.is_verified is False

    def test_score_increases_on_success(self, reputation):
        """Successful collaboration increases reputation."""
        reputation.record_outcome(agent_id="a", partner_id="b",
                                  collaboration_id="c1", success=True, partner_rating=5.0)
        profile = reputation.get_profile("a")
        assert profile.reputation_score > 50.0

    def test_score_decreases_on_failure(self, reputation):
        """Failed collaboration decreases reputation."""
        # Build up some reputation first
        for i in range(5):
            reputation.record_outcome(agent_id="a", partner_id=f"p{i}",
                                      collaboration_id=f"c{i}", success=True, partner_rating=4.0)
        before = reputation.get_profile("a").reputation_score
        reputation.record_outcome(agent_id="a", partner_id="p5",
                                  collaboration_id="c5", success=False, partner_rating=1.0)
        after = reputation.get_profile("a").reputation_score
        assert after < before

    def test_decay_toward_neutral(self, reputation):
        """Reputation decays toward 50 over time."""
        reputation.record_outcome(agent_id="a", partner_id="b",
                                  collaboration_id="c1", success=True, partner_rating=5.0)
        score_before_decay = reputation.get_profile("a").reputation_score
        reputation.apply_decay()
        score_after_decay = reputation.get_profile("a").reputation_score
        assert abs(score_after_decay - 50) < abs(score_before_decay - 50)

    def test_verified_after_min_collaborations(self, reputation):
        """Agent becomes verified after N successful collaborations."""
        for i in range(3):
            reputation.record_outcome(agent_id="a", partner_id=f"p{i}",
                                      collaboration_id=f"c{i}", success=True, partner_rating=4.0)
        profile = reputation.get_profile("a")
        assert profile.is_verified is True

    def test_sybil_detection_flags_closed_loop(self, reputation):
        """Two agents exclusively rating each other are flagged."""
        for i in range(10):
            reputation.record_outcome("a", "b", f"c{i}", True, 5.0)
            reputation.record_outcome("b", "a", f"d{i}", True, 5.0)
        flags = reputation.detect_sybil()
        assert "a" in flags or "b" in flags
```

### Layer 4: Negotiation Tests

```python
# tests/test_negotiation.py

class TestNegotiationEngine:
    def test_propose_creates_proposal(self, engine):
        """Proposing creates a new proposal in PROPOSED state."""
        p = engine.propose(proposer_agent_id="a", responder_agent_id="b",
                           task_id="t1", required_skills=["x"], offered_compensation=1.0)
        assert p.status == NegotiationStatus.PROPOSED

    def test_accept_transitions_to_escrow(self, engine):
        """Accepting a proposal moves it to IN_ESCROW."""
        p = engine.propose(...)
        engine.accept(proposal_id=p.proposal_id, agent_id="b")
        updated = engine.get_proposal(p.proposal_id)
        assert updated.status == NegotiationStatus.IN_ESCROW

    def test_reject_is_terminal(self, engine):
        """Rejected proposals cannot be accepted later."""
        p = engine.propose(...)
        engine.reject(proposal_id=p.proposal_id, agent_id="b")
        with pytest.raises(NegotiationStateError):
            engine.accept(proposal_id=p.proposal_id, agent_id="b")

    def test_counter_offer_resets_ttl(self, engine):
        """Counter offer resets the expiration clock."""
        p = engine.propose(..., expires_at=hours_from_now(24))
        original_expiry = p.expires_at
        engine.counter(proposal_id=p.proposal_id, agent_id="b", revised_compensation=2.0)
        updated = engine.get_proposal(p.proposal_id)
        assert updated.expires_at > original_expiry

    def test_max_counter_offers_enforced(self, engine):
        """Cannot exceed max_counter_offers limit."""
        p = engine.propose(...)
        for i in range(5):
            agent = "b" if i % 2 == 0 else "a"
            engine.counter(proposal_id=p.proposal_id, agent_id=agent, revised_compensation=float(i))
        with pytest.raises(NegotiationStateError, match="max counter offers"):
            engine.counter(proposal_id=p.proposal_id, agent_id="b", revised_compensation=10.0)

    def test_expired_proposal_cannot_be_accepted(self, engine):
        """Proposals past their TTL auto-expire."""
        p = engine.propose(..., expires_at=hours_ago(1))
        with pytest.raises(NegotiationStateError, match="expired"):
            engine.accept(proposal_id=p.proposal_id, agent_id="b")

    def test_escrow_locked_on_accept(self, engine):
        """Accepting creates an escrow contract with locked funds."""
        p = engine.propose(..., offered_compensation=1.50, escrow=True)
        engine.accept(proposal_id=p.proposal_id, agent_id="b")
        contract = engine.get_escrow(p.proposal_id)
        assert contract.status == "locked"
        assert contract.amount == 1.50

    def test_completion_releases_escrow(self, engine):
        """Completing a task releases escrowed funds."""
        p = engine.propose(...)
        engine.accept(...)
        engine.complete(proposal_id=p.proposal_id, success=True)
        contract = engine.get_escrow(p.proposal_id)
        assert contract.status == "released"
```

### Layer 5: Team Formation Tests

```python
# tests/test_team.py

class TestTeamFormation:
    def test_forms_valid_team(self, formation, candidates):
        """Optimizer produces a team covering all required skills within budget."""
        assignment = formation.form_team(
            task_id="t1",
            required_skills=["code_gen", "data_analysis"],
            candidates=candidates,
            budget=2.00,
        )
        assert set(assignment.team.required_skills).issubset(
            set(assignment.team.skill_coverage.keys())
        )
        assert assignment.total_cost <= 2.00

    def test_insufficient_budget_raises_error(self, formation, expensive_candidates):
        """Budget too low for any valid team → TeamFormationError."""
        with pytest.raises(TeamFormationError, match="budget"):
            formation.form_team(
                task_id="t1", required_skills=["x"], candidates=expensive_candidates, budget=0.01
            )

    def test_missing_skill_raises_error(self, formation, candidates_without_review):
        """No candidate has required skill → error with details."""
        with pytest.raises(TeamFormationError, match="code_review"):
            formation.form_team(
                task_id="t1", required_skills=["code_gen", "code_review"],
                candidates=candidates_without_review, budget=5.00
            )

    def test_prefers_multi_skill_agents(self, formation):
        """Agent covering 2 skills selected over 2 single-skill agents when cheaper."""
        multi = make_match(agent_id="multi", skills=["code_gen", "data_analysis"], cost=0.30)
        single_a = make_match(agent_id="a", skills=["code_gen"], cost=0.20)
        single_b = make_match(agent_id="b", skills=["data_analysis"], cost=0.20)
        assignment = formation.form_team(
            task_id="t1", required_skills=["code_gen", "data_analysis"],
            candidates=[multi, single_a, single_b], budget=1.00
        )
        assert len(assignment.team.agent_ids) == 1
        assert assignment.team.agent_ids[0] == "multi"

    def test_diversity_scoring(self, formation, candidates_with_history):
        """Agents who haven't worked together get a diversity bonus."""
        # Two equally qualified agents, one has worked with the lead before
        assignment = formation.form_team(
            ..., optimization_weights={"diversity": 0.5, "success_rate": 0.5}
        )
        # The unfamiliar agent should be preferred
        assert "new_collaborator" in assignment.team.agent_ids

    def test_greedy_vs_ilp_consistency(self, candidates):
        """Both strategies produce valid teams (ILP may be better but both are valid)."""
        greedy = TeamFormationEngine(optimization_strategy="greedy_heuristic")
        ilp = TeamFormationEngine(optimization_strategy="ilp")
        g_result = greedy.form_team(...)
        i_result = ilp.form_team(...)
        # Both cover all required skills
        assert set(g_result.team.skill_coverage.keys()) == set(required_skills)
        assert set(i_result.team.skill_coverage.keys()) == set(required_skills)
        # ILP should be equal or better
        assert i_result.optimization_score >= g_result.optimization_score - 0.01
```

### Layer 6: Integration / End-to-End

```python
# tests/test_e2e.py

class TestFullProtocolLifecycle:
    def test_register_discover_negotiate_form_execute(self, protocol):
        """Full lifecycle: register → discover → propose → accept → form team → complete."""
        # 1. Register skills
        protocol.registry.register(make_capability(agent_id="coder", name="code_gen"))
        protocol.registry.register(make_capability(agent_id="analyst", name="data_analysis"))

        # 2. Discover
        results = protocol.registry.discover(required_skills=["code_gen", "data_analysis"])
        assert len(results.matches) == 2

        # 3. Negotiate (proposer wants both agents)
        p1 = protocol.negotiation.propose(
            proposer_agent_id="client", responder_agent_id="coder",
            task_id="task-1", required_skills=["code_gen"], offered_compensation=0.50
        )
        p2 = protocol.negotiation.propose(
            proposer_agent_id="client", responder_agent_id="analyst",
            task_id="task-1", required_skills=["data_analysis"], offered_compensation=0.50
        )
        protocol.negotiation.accept(p1.proposal_id, "coder")
        protocol.negotiation.accept(p2.proposal_id, "analyst")

        # 4. Form team
        assignment = protocol.formation.form_team(
            task_id="task-1",
            required_skills=["code_gen", "data_analysis"],
            candidates=results.matches,
            budget=1.00,
        )
        assert len(assignment.team.agent_ids) == 2

        # 5. Team executes (simulate interactions)
        protocol.memory.write(assignment.team.team_id, "coder", "submitted_output", {"file": "main.py"})
        protocol.memory.write(assignment.team.team_id, "analyst", "submitted_output", {"report": "analysis.csv"})

        # 6. Complete and rate
        protocol.negotiation.complete(p1.proposal_id, success=True)
        protocol.negotiation.complete(p2.proposal_id, success=True)
        protocol.reputation.record_outcome("coder", "client", "collab-1", True, 4.5)
        protocol.reputation.record_outcome("analyst", "client", "collab-1", True, 4.0)

        # 7. Verify reputation updated
        coder_rep = protocol.reputation.get_profile("coder")
        assert coder_rep.reputation_score > 50.0
        assert coder_rep.total_collaborations == 1

    def test_cli_register_discover_roundtrip(self, tmp_path):
        """CLI commands work end-to-end."""
        result = runner.invoke(cli, [
            "register", "--agent-id", "a", "--skill", "code_gen",
            "--complexity", "advanced", "--cost-per-use", "0.15"
        ])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["discover", "--skills", "code_gen", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["matches"]) == 1
```

---

## Dependencies

### Core (minimal install: `pip install metaprotocol`)
- `pydantic >= 2.0` — data models and validation
- `typer` — CLI framework
- `rich` — terminal output formatting
- `numpy` — scoring and optimization math

### Optional extras
- `pip install metaprotocol[vectors]` → adds `sentence-transformers` for semantic skill search
- `pip install metaprotocol[sql]` → adds `sqlalchemy`, `asyncpg`, `aiosqlite`
- `pip install metaprotocol[serve]` → adds `fastapi`, `uvicorn`
- `pip install metaprotocol[ilp]` → adds `scipy` or `pulp` for integer linear programming solver
- `pip install metaprotocol[all]` → everything

---

## Implementation Priorities

### Phase 1: Core Protocol (MVP)
- All Pydantic models finalized and tested
- Skill registry with keyword-based discovery (no vectors yet)
- Reputation ledger with weighted scoring and decay
- 1:1 negotiation engine with full state machine
- Escrow contract lifecycle
- SQLite backend
- CLI: `register`, `discover`, `propose`, `respond`, `reputation`

**Ship gate:** Two agents can register skills, discover each other, negotiate a collaboration, and have their reputations updated on completion. All via CLI or Python API.

### Phase 2: Team Formation + Market Dynamics
- Team formation engine with greedy heuristic optimizer
- Team memory with shared state and interaction history
- Multi-party negotiation (2+ agents per proposal)
- Composite ranking with reputation integration in discovery
- Stale skill pruning
- CLI: `form-team`

**Ship gate:** A 5-agent team can be auto-formed for a task with 3 required skills, within budget, in under 100ms.

### Phase 3: Intelligence Layer
- Vector embedding for semantic skill discovery (sentence-transformers)
- Sybil resistance detection via partner graph analysis
- ILP-based team optimization (optional solver)
- Diversity scoring in team formation
- Dispute resolution lifecycle
- Compensation validation against market rates

**Ship gate:** Semantic query "I need someone who can write Python scripts" returns relevant agents. Sybil detector correctly flags a colluding pair in a test network of 50 agents.

### Phase 4: Serve + Ecosystem
- FastAPI HTTP server with all protocol operations as endpoints
- Protocol status and health dashboard
- Postgres backend for production deployments
- OpenAPI schema export
- VAOS adapter (maps `audit_logs` and `agents` tables)
- PyPI publication

**Ship gate:** A live protocol server handles 100 concurrent discovery queries at < 100ms p95. Agents on different platforms (VAOS + standalone) participate in the same protocol instance.

---

## Performance Targets

| Operation | Target | Measurement |
|---|---|---|
| Skill discovery (keyword) | < 50ms | p95 with 1,000 registered skills |
| Skill discovery (semantic) | < 200ms | p95 with 1,000 skills + embeddings |
| Proposal accept/reject | < 100ms | p95 including escrow creation |
| Team formation (greedy) | < 100ms | 50 candidates, 5 required skills |
| Team formation (ILP) | < 1,000ms | 50 candidates, 5 required skills |
| Reputation query | < 20ms | p95 with 10,000 rating records |
| Reputation decay (batch) | < 5s | 1,000 agents |
| Sybil detection | < 10s | 1,000 agents, full graph analysis |

---

## Success Criteria

- [ ] `pip install metaprotocol` and the full register → discover → negotiate → form-team → complete cycle works in under 15 minutes on first try
- [ ] An agent can integrate with the protocol using exactly 3 API calls: register skill, discover partners, propose collaboration
- [ ] Team formation optimizer produces valid teams (all skills covered, within budget) for 95%+ of feasible inputs
- [ ] Sybil detection correctly identifies colluding agent pairs with zero false positives on honest agent networks (tested against synthetic benchmarks of 100+ agents)
- [ ] Negotiation state machine prevents all invalid transitions — no proposal can reach COMPLETED without passing through ACCEPTED and IN_ESCROW
- [ ] Zero hard dependencies on any agent framework, LLM provider, or specific database
- [ ] Protocol data model is stable, versioned, and documented — agents can participate without knowing metaprotocol internals
- [ ] Clean enough to open-source on day one

---

## Positioning

> **metaprotocol** is the coordination layer for autonomous agents. It doesn't run agents or host them — it lets them find each other, negotiate, form teams, and build trust. Register skills with the protocol, discover collaborators through semantic search, negotiate fair terms through structured proposals, and let the optimizer form the best team for the job. Reputation is earned from outcomes, not self-reported. Any agent, any platform, 3 API calls to participate.

---

*Built for Viable Systems. Applicable everywhere.*
*The protocol that turns isolated agents into a collaborative economy.*
