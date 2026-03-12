# GM-OS API Reference

> **Note**: This is an index to the GM-OS API. Auto-generated API docs can be built with Sphinx.

## Kernel Module (`gmos.kernel`)

### Core State & Types

| Class/Function | File | Description |
|----------------|------|-------------|
| `FullSubstrateState` | [`kernel/substrate_state.py`](kernel/substrate_state.py) | Unified state type ξ |
| `OperationalMode` | [`kernel/substrate_state.py`](kernel/substrate_state.py) | GM-OS operational modes |
| `GMOSState` | [`kernel/substrate_state.py`](kernel/substrate_state.py) | Compact state representation |

### Process Management

| Class/Function | File | Description |
|----------------|------|-------------|
| `StateHost` | [`kernel/state_host.py`](kernel/state_host.py) | Hosted process state management |
| `ProcessTable` | [`kernel/process_table.py`](kernel/process_table.py) | Process census and lifecycle |
| `KernelScheduler` | [`kernel/scheduler.py`](kernel/scheduler.py) | Multi-clock scheduling |

### Budget & Economics

| Class/Function | File | Description |
|----------------|------|-------------|
| `BudgetRouter` | [`kernel/budget_router.py`](kernel/budget_router.py) | Budget routing and reserve law |
| `BudgetSlice` | [`kernel/budget_router.py`](kernel/budget_router.py) | Individual budget allocation |
| `ReserveTier` | [`kernel/budget_router.py`](kernel/budget_router.py) | Reserve protection tiers |

### Verification & Receipts

| Class/Function | File | Description |
|----------------|------|-------------|
| `OplaxVerifier` | [`kernel/verifier.py`](kernel/verifier.py) | Thermodynamic constraint enforcement |
| `ReceiptEngine` | [`kernel/receipt_engine.py`](kernel/receipt_engine.py) | Receipt generation |
| `KernelReceipt` | [`kernel/receipt_engine.py`](kernel/receipt_engine.py) | Canonical receipt type |
| `HashChainLedger` | [`kernel/hash_chain.py`](kernel/hash_chain.py) | Immutable receipt chain |

### Dynamics

| Class/Function | File | Description |
|----------------|------|-------------|
| `ProjectedDynamicalSystem` | [`kernel/continuous_dynamics.py`](kernel/continuous_dynamics.py) | Moreau-projected dynamics |
| `AdmissibleSet` | [`kernel/continuous_dynamics.py`](kernel/continuous_dynamics.py) | Constraint manifold |

---

## GMI Agent Module (`gmos.agents.gmi`)

### Core Agent

| Class/Function | File | Description |
|----------------|------|-------------|
| `GMIState` | [`agents/gmi/state.py`](agents/gmi/state.py) | GMI internal state |
| `GMIPotential` | [`agents/gmi/potential.py`](agents/gmi/potential.py) | Canonical energy law |

### Tension & Constraints

| Class/Function | File | Description |
|----------------|------|-------------|
| `ResidualVector` | [`agents/gmi/tension_law.py`](agents/gmi/tension_law.py) | All residual components |
| `TensionWeights` | [`agents/gmi/tension_law.py`](agents/gmi/tension_law.py) | Weight coefficients |
| `ConstraintSet` | [`agents/gmi/constraints.py`](agents/gmi/constraints.py) | Lawful constraint manifold |
| `ConstraintGovernor` | [`agents/gmi/constraints.py`](agents/gmi/constraints.py) | Projection onto tangent cone |

### Affective Systems

| Class/Function | File | Description |
|----------------|------|-------------|
| `AffectiveCognitiveState` | [`agents/gmi/affective_state.py`](agents/gmi/affective_state.py) | Emotional modeling |
| `AffectiveBudgetManager` | [`agents/gmi/affective_budget.py`](agents/gmi/affective_budget.py) | Budget with affect |
| `ThreatModulator` | [`agents/gmi/threat_modulation.py`](agents/gmi/threat_modulation.py) | Threat response |

### Cognitive Loops

| Class/Function | File | Description |
|----------------|------|-------------|
| `EvolutionLoop` | [`agents/gmi/evolution_loop.py`](agents/gmi/evolution_loop.py) | Policy evolution |
| `ExecutionLoop` | [`agents/gmi/execution_loop.py`](agents/gmi/execution_loop.py) | Action execution |
| `SemanticLoop` | [`agents/gmi/semantic_loop.py`](agents/gmi/semantic_loop.py) | Semantic processing |

---

## Memory Module (`gmos.memory`)

| Class/Function | File | Description |
|----------------|------|-------------|
| `WorkspaceState` | [`memory/workspace.py`](memory/workspace.py) | Active phantom states |
| `PhantomState` | [`memory/workspace.py`](memory/workspace.py) | Reconstructed memory state |
| `ArchiveState` | [`memory/archive.py`](memory/archive.py) | Episodic storage |
| `Episode` | [`memory/episode.py`](memory/episode.py) | Individual episode |

---

## Sensory Module (`gmos.sensory`)

| Class/Function | File | Description |
|----------------|------|-------------|
| `SensoryState` | [`sensory/manifold.py`](sensory/manifold.py) | Full sensory manifold |
| `ExternalChart` | [`sensory/manifold.py`](sensory/manifold.py) | External perception |
| `SemanticChart` | [`sensory/manifold.py`](sensory/manifold.py) | Symbolic perception |
| `InternalChart` | [`sensory/manifold.py`](sensory/manifold.py) | Interoception |

---

## Symbolic Module (`gmos.symbolic`)

| Class/Function | File | Description |
|----------------|------|-------------|
| `GlyphSpace` | [`symbolic/glyph_space.py`](symbolic/glyph_space.py) | Symbolic coordinate space |
| `GlyphEmbedding` | [`symbolic/glyph_space.py`](symbolic/glyph_space.py) | Symbol with features |
| `SemanticManifold` | [`symbolic/semantic_manifold.py`](symbolic/semantic_manifold.py) | Semantic structure |

---

## Building API Docs

```bash
cd gmos
pip install -e .[docs]
sphinx-build -b html docs docs/_build/html
```

Or use Sphinx autodoc:
```bash
sphinx-apidoc -f -o docs/api/ src/gmos/
```
