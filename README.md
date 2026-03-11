# Governed Metabolic Intelligence (GMI)

> **⚠️ Important**: The canonical implementation is now in `gmos/src/gmos/`. 
> Root-level `core/`, `memory/`, `ledger/`, `runtime/` are legacy prototype code.
> See [CANONICAL.md](CANONICAL.md) for details.

A universal cognition engine with thermodynamic principles, cryptographic ledger discipline, and affective mode geometry.

## What is GMI?

GMI is a computational framework that treats cognitive processes as thermodynamic systems with:
- **Canonical Energy Law**: GMIPotential unifies base tension, memory curvature, budget barriers, and domain residuals
- **Cryptographic Ledger**: Hash-chained receipts for verifiable autobiography
- **Constraint Projection**: Active projection onto lawful tangent cone
- **Affective Geometry**: Emotion (χ) as boundary-condition generator

## Core Equation

```
V(x') + σ ≤ V(x) + κ + b_reserve
```

Where:
- `V(x)` - Cognitive tension (potential function)
- `σ` - Computational energy cost
- `κ` - Allowed defect envelope

### Reserve Law (Anti-Greed)

GMI includes a **Reserve Law** that prevents budget bankruptcy:

```
b' ≥ b_reserve
```

This ensures moves cannot exhaust the budget below a protected minimum, providing mathematical guarantees against greedy/short-sighted decisions.

**Key Features:**
- Thermodynamic inequality ensures valid cognitive operations
- Reserve Law prevents strategic suicide
- Oplax algebra enforces compositional honesty
- Hash-chained receipts provide verifiable proof

## Architecture

> **⚠️ Important**: The canonical implementation is in `gmos/src/gmos/`.
> Root-level directories (`core/`, `memory/`, `ledger/`, `runtime/`, `adapters/`) are legacy prototypes.

### Canonical Structure (GM-OS)

```
gmos/src/gmos/
├── kernel/                   # Kernel (scheduler, verifier, budget, etc.)
│   ├── substrate_state.py   # FullSubstrateState, CognitiveState
│   ├── verifier.py          # OplaxVerifier
│   ├── receipt.py           # Receipt with hash chain fields
│   ├── hash_chain.py        # HashChainLedger
│   └── ...
├── agents/gmi/              # GMI Agent implementation
│   ├── gmi_agent.py        # Main agent
│   ├── tension_law.py      # Canonical energy law
│   ├── state.py            # GMIState
│   └── ...
├── memory/                  # Memory manifold
│   ├── workspace.py        # Phantom states
│   ├── archive.py          # Episodic archive
│   ├── operators.py        # Write/Read/Replay/Compare
│   └── ...
├── sensory/                 # Sensory manifold
├── symbolic/                # Symbolic reasoning
└── action/                  # Action interfaces
```

### Legacy (Deprecated - Archive Only)

```
core/        # Legacy prototype code
memory/      # Legacy prototype code  
ledger/      # Legacy prototype code
runtime/     # Legacy prototype code
adapters/    # Legacy prototype code
```

## Installation

```bash
cd gmos && pip install -e .[dev]
```

## Testing

```bash
# Run canonical package tests
cd gmos && pytest

# Run repository integration tests
pytest tests/
```

## Usage (Canonical GM-OS)

```python
from gmos.agents.gmi.gmi_agent import GMIAgent

agent = GMIAgent(budget=100.0)
state = agent.step(initial_state)
```

### With Memory

```python
from runtime.execution_loop import run_gmi_engine_with_memory

run_gmi_engine_with_memory(
    initial_x=[1.0, 1.0],
    initial_budget=15.0,
    max_steps=20
)
```

### Hash-Chained Ledger

```python
from runtime.execution_loop import run_gmi_engine_with_hash_chain

ledger = run_gmi_engine_with_hash_chain(
    initial_x=[1.0, 1.0],
    initial_budget=15.0
)
# ledger.verify_chain()  # Verify integrity
```

### Affective Mode (Threat/Flow)

```python
from core.affective_state import AffectiveCognitiveState
from core.affective_budget import AffectiveBudgetLaw
from core.threat_modulation import ThreatModulator

# χ ∈ [0, 1]: 0=safe/expansive, 1=threat/defensive
state = AffectiveCognitiveState(rho=np.array([1.0, 2.0]), chi=0.3)  # flow

# Budget costs modulated by χ
budget = AffectiveBudgetLaw(chi=0.3)
```

## Key Concepts

### GMIPotential

The canonical energy law:

```python
V_GMI(z) = V_base(x) + V_memory(x, M) + V_budget(b) + V_domain(μ)
```

- **Base**: Cognitive tension (coherent = 0)
- **Memory**: Curvature from scars/rewards
- **Budget**: Barrier diverges as b → 0 (b=0 → no motion)
- **Domain**: Adapter-specific residuals

### Memory System

Four-layer memory architecture:
- **C**: Passive structural memory (curvature)
- **E**: Episodic archive (append-only)
- **W**: Reconstructive workspace (phantom states)
- **Ω**: Ledger anchor (auditability)

Operators: Write, Read, Replay, Compare, Prune

### Hash-Chained Ledger

Every transition creates a cryptographic chain:

```
H_{k+1} = SHA256(H_k || receipt_k)
```

Enables:
- Deterministic replay
- Slab verification
- Offline audit

### Affective Mode (χ)

The state extends to `z = (ρ, θ, C, E, W, B, Ω, χ)`

| χ | Mode | Imagination Cost | Behavior |
|---|------|-----------------|----------|
| 0.1 | Deep Safety | Low (1.2x) | Max exploration |
| 0.3 | Flow | Moderate | Optimal efficiency |
| 0.9 | Defensive | High (2.8x) | Rigid logic only |

### Policy Selection (Module 15)

Deterministic argmax selection:

```
B* = argmax_{B_i ∈ B_k} [Γ(B_i) - Σ(B_i)]
```

Commitment receipt created BEFORE action execution.

### Reality Collision

Prediction error → structural scarring:

```
Δ_err = |Γ(B*) - G_actual|
```

Manifold deforms where predictions fail.

## Testing

```bash
pytest tests/
```

## Modules

| Module | Description |
|--------|-------------|
| 1-4 | GMIPotential, Memory, Hash Chain, Projection |
| 15 | Policy Selection, Commitment, Reality Collision |
| 16 | Affective Mode Geometry, Threat/Flow |

## Status

**Beta** - Core architecture stable. APIs may evolve.

## License

MIT
