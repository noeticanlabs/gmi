# Canonical Architecture Specification

**Canonical ID:** `gmos.architecture_spec.v1`  
**Version:** `1.0.0`  
**Status:** Canonical - Phase 1 Foundation Document

This is the engineering structure document. It defines the package map, public API surface, internal modules, dependency rules, and status map.

---

## A. Package Map

The canonical package tree for Phase 1:

```
gmos/
├── src/gmos/
│   ├── __init__.py              # Package root
│   │
│   ├── core/                    # DEPRECATED - use kernel/*
│   │   └── (legacy modules)
│   │
│   ├── kernel/                  # Canonical substrate runtime
│   │   ├── __init__.py
│   │   ├── substrate_state.py  # FullSubstrateState
│   │   ├── budget_router.py     # Budget routing with reserves
│   │   ├── verifier.py         # Verification logic
│   │   ├── receipt.py           # Receipt data structure
│   │   ├── receipt_engine.py    # Receipt chain management
│   │   ├── scheduler.py         # Execution scheduling
│   │   ├── state_host.py        # Hosted process management
│   │   ├── continuous_dynamics.py # Moreau-projected dynamics
│   │   ├── cohil_evaluator.py   # Coherence functional V(x)
│   │   ├── thermodynamic_cost.py # Cost computation
│   │   ├── operating_cost.py    # Operating cost analysis
│   │   ├── repair_controller.py # Repair/projection logic
│   │   ├── reject_codes.py      # Rejection reason codes
│   │   ├── hash_chain.py        # Cryptographic chain
│   │   ├── identity_kernel.py   # Identity management
│   │   ├── process_table.py      # Process registry
│   │   ├── mediator.py          # Component mediation
│   │   ├── checkpoint.py        # State snapshots
│   │   ├── reconfiguration.py   # Runtime reconfiguration
│   │   ├── danger.py             # Danger detection
│   │   ├── integrity_scorer.py   # Integrity metrics
│   │   ├── macro_verifier.py     # Macro-scale verification
│   │   ├── repair_verifier.py    # Repair verification
│   │   ├── theorems.py           # Core theorems
│   │   └── unified_persistence.py # Persistence layer
│   │
│   ├── memory/                  # Canonical memory management
│   │   ├── __init__.py
│   │   ├── workspace.py         # Working memory M_W
│   │   ├── archive.py           # Episodic archive M_E
│   │   ├── episode.py           # Memory episode structure
│   │   ├── consolidation.py     # Memory consolidation
│   │   ├── replay.py             # Memory replay
│   │   ├── operators.py          # Memory operators
│   │   ├── budget_costs.py      # Memory operation costs
│   │   ├── relevance.py          # Relevance scoring
│   │   ├── comparator.py         # Memory comparison
│   │   ├── receipts.py           # Memory-specific receipts
│   │   └── memory_connector.py   # Kernel-memory interface
│   │
│   ├── sensory/                 # Percept anchoring
│   │   ├── __init__.py
│   │   ├── manifold.py          # Sensory state manifold
│   │   ├── anchors.py           # Sensory anchoring
│   │   ├── fusion.py            # Multi-sensory fusion
│   │   ├── salience.py           # Salience computation
│   │   ├── tension_bounds.py    # Tension boundaries
│   │   ├── curvature.py          # Sensory curvature
│   │   ├── trauma.py             # Trauma detection
│   │   ├── conflict.py           # Sensory conflict
│   │   ├── projection.py         # Sensory projection
│   │   ├── operators.py          # Sensory operators
│   │   ├── cost_law.py           # Sensory cost law
│   │   ├── verifier.py           # Sensory verification
│   │   ├── receipts.py           # Sensory receipts
│   │   └── sensory_connector.py  # Kernel-sensory interface
│   │
│   ├── action/                  # Action commitment
│   │   ├── __init__.py
│   │   ├── commitment.py         # Action commit (χ operator)
│   │   ├── external_io.py         # External I/O
│   │   └── replenishment.py      # Budget replenishment
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   │
│   │   ├── gmi/                 # Canonical hosted intelligence
│   │   │   ├── __init__.py
│   │   │   ├── gmi_agent.py     # Main GMI agent
│   │   │   ├── hosted_agent.py  # Hosted process interface
│   │   │   ├── state.py         # GMI cognitive state
│   │   │   ├── tension_law.py   # Tension/coherence law
│   │   │   ├── potential.py     # GMI potential function
│   │   │   ├── affective_state.py # Affective state
│   │   │   ├── affective_budget.py # Affective budgets
│   │   │   ├── constraints.py   # Constraint definitions
│   │   │   ├── execution_loop.py # Main execution loop
│   │   │   ├── evolution_loop.py # Evolution loop
│   │   │   ├── semantic_loop.py  # Semantic loop
│   │   │   ├── policy_selection.py # Policy π
│   │   │   ├── memory_adapter.py  # Memory interface
│   │   │   ├── persistence_integration.py # Persistence
│   │   │   ├── character_shell.py # Character shell
│   │   │   ├── ear_operator.py   # Auditory processing
│   │   │   ├── voice_operator.py  # Vocal processing
│   │   │   ├── threat_modulation.py # Threat response
│   │   │   ├── full_dynamics.py   # Full dynamics
│   │   │   ├── quantum_coh.py     # Quantum coherence bridge
│   │   │   ├── resonant_field.py  # Resonant field
│   │   │   ├── triad_resonance.py  # Triad resonance
│   │   │   ├── twelve_block_state.py # Twelve-block state
│   │   │   ├── viscosity_law.py    # Viscosity law
│   │   │   │
│   │   │   ├── environments/     # Test environments
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py       # Base environment
│   │   │   │   ├── maze.py       # Maze environment
│   │   │   │   └── key_door.py   # Key-door environment
│   │   │   │
│   │   │   └── planning/        # Planning submodules
│   │   │       ├── __init__.py
│   │   │       ├── goal_representation.py
│   │   │       └── greedy_planner.py
│   │   │
│   │   └── (stub agents moved to experimental/)
│   │
│   ├── symbolic/               # Extension - symbolic reasoning
│   │   ├── __init__.py
│   │   ├── binding.py
│   │   ├── glyph_embedder.py
│   │   ├── glyph_space.py
│   │   ├── semantic_manifold.py
│   │   └── symbolic_connector.py
│   │
│   └── experimental/           # Experimental/speculative code
│       ├── __init__.py
│       └── agents/
│           └── (experimental agents)
│
├── tests/
│   ├── test_doc_correspondence.py
│   ├── test_imports.py
│   ├── agents/
│   │   └── gmi/
│   │       ├── test_gmi.py
│   │       ├── test_perception_verification.py
│   │       ├── test_vision.py
│   │       ├── test_hearing.py
│   │       └── benchmark_suite.py
│   ├── kernel/
│   │   ├── test_kernel.py
│   │   ├── test_budget_reserves.py
│   │   └── test_receipts.py
│   └── sensory/
│       ├── test_dual_use_pipeline.py
│       ├── test_maze_trauma.py
│       └── test_world_weld.py
│
└── docs/
    ├── coh_gmos_gmi_doctrine.md    # Canonical doctrine
    ├── definition_ledger.md        # Term definitions
    ├── architecture_spec.md         # This file
    ├── substrate_contract.md        # Substrate contract
    ├── hosted_agent_contract.md    # GMI contract
    ├── phase1_status_matrix.md      # Phase 1 status
    ├── gmos_canon_spec.md          # GM-OS spec
    ├── gmi_canon_spec.md           # GMI spec
    ├── canon_spec_index.md         # Spec index
    └── repo_status_matrix.md       # Implementation status
```

---

## B. Public API Surface

The following modules are public in Phase 1 and constitute the stable API:

### Kernel (Substrate) Public API

| Module | Public Exports |
|--------|----------------|
| `gmos.kernel.substrate_state` | `FullSubstrateState`, `OperationalMode` |
| `gmos.kernel.budget_router` | `BudgetRouter`, `BudgetState` |
| `gmos.kernel.verifier` | `Verifier`, `VerifierResult`, `verify()` |
| `gmos.kernel.receipt` | `Receipt`, `ReceiptData` |
| `gmos.kernel.receipt_engine` | `ReceiptEngine`, `write_receipt()` |
| `gmos.kernel.scheduler` | `KernelScheduler`, `schedule_step()` |
| `gmos.kernel.state_host` | `StateHost`, `register_process()` |
| `gmos.kernel.cohil_evaluator` | `CohilEvaluator`, `evaluate_coherence()` |

### Memory Public API

| Module | Public Exports |
|--------|----------------|
| `gmos.memory.workspace` | `Workspace`, `get_working_memory()` |
| `gmos.memory.archive` | `EpisodicArchive`, `store_episode()`, `retrieve()` |
| `gmos.memory.episode` | `MemoryEpisode`, `EpisodeData` |

### Sensory Public API

| Module | Public Exports |
|--------|----------------|
| `gmos.sensory.anchors` | `Anchor`, `anchor_percept()` |
| `gmos.sensory.manifold` | `SensoryState`, `SensoryManifold` |

### Action Public API

| Module | Public Exports |
|--------|----------------|
| `gmos.action.commitment` | `Commitment`, `commit_action()` |

### GMI Agent Public API

| Module | Public Exports |
|--------|----------------|
| `gmos.agents.gmi.gmi_agent` | `GMIAgent` |
| `gmos.agents.gmi.state` | `CognitiveState` |
| `gmos.agents.gmi.tension_law` | `TensionLaw`, `compute_tension()` |
| `gmos.agents.gmi.hosted_agent` | `HostedAgent`, `generate_proposal()` |

---

## C. Internal-Only Modules

The following modules are internal and not part of the public API:

| Module | Reason |
|--------|--------|
| `gmos.kernel.continuous_dynamics` | Internal implementation detail |
| `gmos.kernel.thermodynamic_cost` | Internal cost computation |
| `gmos.kernel.operating_cost` | Internal cost analysis |
| `gmos.kernel.repair_controller` | Internal repair logic |
| `gmos.kernel.hash_chain` | Internal cryptographic chain |
| `gmos.kernel.process_table` | Internal process registry |
| `gmos.kernel.mediator` | Internal mediation |
| `gmos.kernel.checkpoint` | Internal state snapshots |
| `gmos.kernel.reconfiguration` | Internal reconfiguration |
| `gmos.kernel.danger` | Internal danger detection |
| `gmos.kernel.integrity_scorer` | Internal integrity metrics |
| `gmos.kernel.macro_verifier` | Internal macro verification |
| `gmos.kernel.repair_verifier` | Internal repair verification |
| `gmos.kernel.theorems` | Internal theorem suite |
| `gmos.kernel.unified_persistence` | Internal persistence |
| `gmos.kernel.reject_codes` | Internal rejection codes |
| `gmos.kernel.identity_kernel` | Internal identity |
| `gmos.sensory.*` (most modules) | Internal sensory processing |
| `gmos.memory.*` (most modules) | Internal memory operations |
| `gmos.agents.gmi.*` (most modules) | Internal GMI implementation |

---

## D. Dependency Rules

### Allowed Dependencies

| Consumer | Allowed Providers |
|----------|-------------------|
| `gmos.agents.gmi` | `gmos.kernel`, `gmos.memory`, `gmos.sensory`, `gmos.action` |
| `gmos.kernel` | (core only, no cycles) |
| `gmos.memory` | `gmos.kernel` |
| `gmos.sensory` | `gmos.kernel` |
| `gmos.action` | `gmos.kernel` |

### Forbidden Dependencies

| Consumer | Forbidden Providers |
|----------|---------------------|
| `gmos.kernel` | `gmos.agents.gmi` (no cycles) |
| `gmos.kernel` | `gmos.experimental.*` |
| `gmos.agents.gmi` | `gmos.experimental.*` (except via explicit opt-in) |

### Doctrine Term Mapping

Every canonical term in [`definition_ledger.md`](definition_ledger.md) must map to exactly one code module:

| Term | Canonical Module |
|------|------------------|
| Coh | `gmos.kernel.cohil_evaluator` |
| Coherence | `gmos.kernel.cohil_evaluator` |
| Verifier | `gmos.kernel.verifier` |
| Receipt | `gmos.kernel.receipt` |
| Budget | `gmos.kernel.budget_router` |
| Reserve | `gmos.kernel.budget_router` |
| Memory Episode | `gmos.memory.episode` |
| Workspace | `gmos.memory.workspace` |
| Sensory Anchor | `gmos.sensory.anchors` |
| Action Commit | `gmos.action.commitment` |
| GMI | `gmos.agents.gmi.gmi_agent` |

---

## E. Status Map

Each major file/module is tagged with a status:

| Module/Doc | Status | Notes |
|------------|--------|-------|
| `docs/coh_gmos_gmi_doctrine.md` | **Canonical** | Phase 1 foundation |
| `docs/definition_ledger.md` | **Canonical** | Phase 1 foundation |
| `docs/architecture_spec.md` | **Canonical** | This file |
| `docs/substrate_contract.md` | **Canonical** | Phase 1 deliverable |
| `docs/hosted_agent_contract.md` | **Canonical** | Phase 1 deliverable |
| `docs/phase1_status_matrix.md` | **Canonical** | Phase 1 deliverable |
| `docs/gmos_canon_spec.md` | **Canonical** | GM-OS spec |
| `docs/gmi_canon_spec.md` | **Canonical** | GMI spec |
| `gmos.kernel.*` | **Canonical** | Production-ready substrate |
| `gmos.memory.*` | **Canonical** | Production-ready memory |
| `gmos.sensory.*` | **Canonical** | Production-ready sensory |
| `gmos.action.*` | **Canonical** | Production-ready action |
| `gmos.agents.gmi.*` | **Canonical** | Production-ready GMI |
| `gmos.symbolic.*` | **Extension** | Allowed but non-core |
| `gmos.experimental.*` | **Speculative** | Doc-only, experimental |
| `docs/quantum_coh_bridge_spec.md` | **Speculative** | Future exploration |
| `docs/character_shell_spec.md` | **Extension** | Allowed extension |
| `core/` | **Archive** | Deprecated, do not use |
| `memory/` (root) | **Archive** | Deprecated, use gmos.memory |
| `runtime/` (root) | **Archive** | Deprecated |
| `ledger/` (root) | **Archive** | Deprecated, use gmos.kernel |
| `agents/ns_agent.py` | **Archive** | Stub, move to experimental |
| `agents/physics_agent.py` | **Archive** | Stub, move to experimental |
| `agents/planner_agent.py` | **Archive** | Stub, move to experimental |
| `agents/symbolic_agent.py` | **Archive** | Stub, move to experimental |

---

## F. Installation and Build

### Canonical Development Path

```bash
# Clone and setup
cd gmos
pip install -e .[dev]

# Run tests
pytest

# Run specific test suite
pytest gmos/tests/kernel/
pytest gmos/tests/agents/gmi/
```

### Package Structure

- `gmos/src/gmos/` is the one true implementation tree
- No `sys.path.insert(...)` rituals required
- All imports should use `from gmos.kernel import ...` style

---

## G. Import Conventions

### Correct (Canonical)

```python
from gmos.kernel import FullSubstrateState, Verifier
from gmos.kernel.verifier import verify
from gmos.agents.gmi import GMIAgent
from gmos.memory import Workspace, EpisodicArchive
```

### Incorrect (Avoid)

```python
# Don't use legacy paths
from core.memory import Memory  # Wrong - use gmos.memory

# Don't use experimental directly
from gmos.experimental.agents import ExperimentalAgent  # Wrong

# Don't use internal modules
from gmos.kernel.internal import SomeInternalThing  # Wrong
```

---

## References

- [`coh_gmos_gmi_doctrine.md`](coh_gmos_gmi_doctrine.md) - Canonical doctrine
- [`definition_ledger.md`](definition_ledger.md) - Term definitions
- [`substrate_contract.md`](substrate_contract.md) - Substrate contract
- [`hosted_agent_contract.md`](hosted_agent_contract.md) - GMI contract

---

*This architecture is canonical for Phase 1. Changes require explicit versioning and Phase 1 completion.*
