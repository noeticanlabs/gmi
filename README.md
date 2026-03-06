# Governed Metabolic Intelligence (GMI)

A prototype for thermodynamic cognitive computation using the PhaseLoom model.

## What is GMI?

GMI is a computational framework that treats cognitive processes as thermodynamic systems. State transitions are governed by the **Thermodynamic Inequality**:

```
V(x') + σ ≤ V(x) + κ
```

Where:
- `V(x)` is the cognitive tension (potential function)
- `σ` (sigma) is the energy cost of computation
- `κ` (kappa) is the allowed defect budget

## Project Structure

```
gmi/
├── core/                    # Core state and computation
│   ├── state.py            # State, Instruction, V_PL
│   ├── embedder.py         # Text-to-vector embedding
│   └── memory.py           # Memory manifold with scars
├── ledger/                  # Verification and receipts
│   ├── oplax_verifier.py   # Thermodynamic constraint checker
│   └── receipt.py          # Execution proof artifacts
├── runtime/                 # Execution loops
│   ├── evolution_loop.py   # NPE with memory
│   ├── execution_loop.py   # Basic execution engine
│   ├── semantic_loop.py    # Semantic dynamics
│   └── learning_loop.py    # Memory-learning dynamics
├── experiments/             # Research demos (not canonical)
├── tests/                  # Unit tests
├── outputs/                # Generated receipts (gitignored)
│   └── receipts/
├── pyproject.toml         # Package definition
└── .gitignore            # Git exclusions
```

## Installation

```bash
# Install dependencies
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Usage

### Basic Execution

```python
from runtime.execution_loop import run_gmi_engine

# Run the GMI engine
run_gmi_engine(
    initial_x=[1.0, 1.0],
    initial_budget=15.0,
    max_steps=20
)
```

### Semantic Dynamics

```python
from runtime.semantic_loop import run_semantic_engine

run_semantic_engine(
    initial_text="brainstorm",
    initial_budget=20.0,
    max_steps=15
)
```

### Memory-Learning Engine

```python
from runtime.learning_loop import run_learning_engine

run_learning_engine(
    initial_text="chaos",
    initial_budget=20.0,
    max_steps=8
)
```

## Running Tests

```bash
pytest tests/
```

## Core Concepts

### State

The cognitive state `z(t) = (x(t), b(t))` where:
- `x(t)` - continuous cognition coordinates in PhaseLoom space
- `b(t)` - thermodynamic budget (must remain non-negative)

### Instruction

Transition operators with:
- `op_code` - human-readable operation name
- `pi(x)` - transition function mapping x → x'
- `σ` (sigma) - computational energy cost
- `κ` (kappa) - allowed defect envelope

### OplaxVerifier

Enforces two constraints:
1. **Thermodynamic Inequality**: V(x') + σ ≤ V(x) + κ + b
2. **Oplax Algebra**: Composition rules for chained instructions

### Receipts

Immutable proof artifacts that record every decision:
- Hash integrity via SHA-256
- Complete state before/after
- Decision reason and messages

## Status

This is an **alpha prototype**. The architecture is stable but APIs may change.

## License

MIT
