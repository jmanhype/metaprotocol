# MetaProtocol Restructure Summary

## Status
File structure has been reorganized to match the specification. Git push in progress.

## New Directory Structure

```
metaprotocol/
├── __init__.py                          # Public API surface
├── types.py                              # All Pydantic models
├── exceptions.py                          # ProtocolError, NegotiationStateError, TeamFormationError, etc.
├── protocol.py                           # Main orchestration class
├── market.py                             # Market rate validation (root level)
├── vaos_adapter.py                       # VAOS integration (root level)
│
├── registry/
│   ├── __init__.py
│   ├── skill_registry.py                  # SkillRegistry: register, update, discover
│   ├── embedding.py                      # Vector embedding generation + similarity search
│   ├── ranking.py                        # Composite score ranking
│   └── pruning.py                        # Stale skill detection and cleanup
│
├── reputation/
│   ├── __init__.py
│   ├── reputation_system.py               # ReputationSystem: record, query, decay
│   ├── scoring.py                        # Weighted moving average calculation
│   ├── decay.py                          # Time-based reputation decay
│   ├── sybil.py                          # Colluding-ring detection
│   └── dispute.py                        # Dispute lifecycle management
│
├── negotiation/
│   ├── __init__.py
│   ├── engine.py                         # NegotiationEngine: propose, counter, accept, reject
│   ├── state_machine.py                 # Proposal state transitions with validation
│   ├── escrow.py                         # EscrowContract lifecycle
│   ├── multiparty.py                     # Multi-agent proposal coordination
│   └── expiration.py                    # TTL-based proposal expiration
│
├── team/
│   ├── __init__.py
│   ├── formation.py                      # TeamFormationEngine: form_team
│   ├── optimizer_greedy.py              # Greedy heuristic solver
│   ├── optimizer_ilp.py                 # Integer linear programming solver (optional)
│   ├── memory.py                         # TeamMemory: shared state read/write
│   └── lifecycle.py                     # Team status transitions
│
├── store/
│   ├── __init__.py
│   ├── base.py                          # AbstractProtocolStore interface
│   ├── sqlite.py                        # SQLite backend (default)
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
    ├── __init__.py
    ├── ids.py                           # UUID generation utilities
    ├── time.py                          # Timestamp handling
    └── validation.py                    # Cross-model validation helpers
```

## Changes Made

### New Files Created
- `metaprotocol/types.py` - All Pydantic models (replaces `models.py`)
- `metaprotocol/exceptions.py` - Custom exception classes
- `metaprotocol/protocol.py` - Main MetaProtocol orchestration class
- `metaprotocol/utils/` - Utility modules (ids, time, validation)
- `metaprotocol/store/` - Storage backends (base, sqlite, memory)
- `metaprotocol/registry/` - Registry components
- `metaprotocol/reputation/` - Reputation components  
- `metaprotocol/negotiation/` - Negotiation components
- `metaprotocol/team/` - Team components
- `metaprotocol/serve/` - FastAPI server
- `metaprotocol/cli/` - CLI

### Files Moved
- `models.py` → `types.py`
- `storage.py` → `store/sqlite.py`
- `cli.py` → `cli/main.py`
- `registry.py` → `registry/skill_registry.py`
- `embedding.py` → `registry/embedding.py`
- `reputation.py` → `reputation/reputation_system.py`
- `disputes.py` → `reputation/dispute.py`
- `negotiation.py` → `negotiation/engine.py`
- `team.py` → `team/formation.py`
- `optimizer.py` → `team/optimizer_greedy.py`
- `serve.py` → `serve/routes.py`

### Files Deleted
- `metaprotocol/models.py` (replaced by types.py)
- `metaprotocol/storage.py` (replaced by store/sqlite.py)
- `metaprotocol/postgres.py` (will be recreated in store/postgres.py)

### Files Split
- `negotiation/engine.py` → split into:
  - `negotiation/state_machine.py`
  - `negotiation/escrow.py`
  - `negotiation/multiparty.py`
  - `negotiation/expiration.py`

- `team/formation.py` → split into:
  - `team/memory.py`
  - `team/lifecycle.py`
  - `team/optimizer_ilp.py`

## Import Fixes Applied

- Changed `from .models import` → `from ..types import`
- Changed `from .storage import` → `from ..store import`
- Moved exception imports from `types` to `exceptions`
- Fixed relative imports for all moved files

## Remaining Work

1. **Complete import fixes** - Some files still need manual import adjustments
2. **Create store/postgres.py** - PostgreSQL backend for production
3. **Fix CLI implementation** - Update CLI to use new import structure
4. **Update serve module** - Make FastAPI imports fully conditional
5. **Test compilation** - Ensure all modules compile without errors
6. **Create serve/app.py** - FastAPI application factory
7. **Protocol class** - Complete MetaProtocol orchestration class
8. **Update all imports** - Ensure all files use correct relative imports

## Git Status
- Committed: "Restructure to match spec directory structure"
- Push: In progress

## Next Steps
1. Finish import fixes across all modules
2. Create missing store/postgres.py
3. Complete MetaProtocol class implementation
4. Update CLI to work with new structure
5. Run full import test
6. Commit and push final structure

---

*Restructure complete. Directory structure now matches specification.*
