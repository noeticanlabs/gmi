# GMI Architecture

## Overview

Governed Metabolic Intelligence (GMI) is a computational framework that treats cognitive processes as thermodynamic systems. The core insight is that valid cognitive operations must satisfy energy conservation constraints similar to physical thermodynamic laws.

## Core Components

### 1. State Model (`core/state.py`)

The fundamental unit of computation is the **Governed State**:

```
z(t) = (x(t), b(t))
```

Where:
- `x(t)`: Continuous cognition coordinates in PhaseLoom space (n-dimensional real vector)
- `b(t)`: Thermodynamic budget (non-negative real number)

#### State Properties

- **Deterministic Hashing**: SHA-256 hash of rounded state values for ledger integrity
- **Potential Function**: `V_PL(x) = Σ(x_i²)` represents cognitive tension
- **Immutable**: State objects are immutable; transitions produce new states

### 2. Instructions (`core/state.py`)

Instructions are transition operators with thermodynamic costs:

```python
Instruction(op_code, pi_func, sigma, kappa)
```

- `op_code`: Human-readable operation name
- `pi_func`: Transition function x → x'
- `σ` (sigma): Energy cost of computation
- `κ` (kappa): Allowed defect budget (how much inequality violation is tolerated)

#### Instruction Types

1. **Primitive Instructions**: Single operators (EXPLORE, INFER)
2. **Composite Instructions**: Chained operators with Oplax algebra rules

### 3. Potential Functions

The potential function `V(x)` defines the "cognitive landscape":

- **Base Potential**: `V_PL(x) = Σ(x_i²)` - simple quadratic bowl
- **Memory-Augmented**: `V(x) + curvature_penalty` - includes memory scars
- **Custom**: Any callable that maps x → scalar

### 4. Oplax Verifier (`ledger/oplax_verifier.py`)

The verifier enforces three constraint systems:

#### A. Thermodynamic Inequality

```
V(x') + σ ≤ V(x) + κ + b
```

Where:
- `V(x)`: Current potential
- `V(x')`: Proposed potential
- `σ`: Instruction cost
- `κ`: Defect allowance
- `b`: Remaining budget

If satisfied → ACCEPT
If violated → REJECT

#### B. Reserve Law (Anti-Greed Mechanism)

```
b' ≥ b_reserve
```

Where:
- `b' = b - σ` (budget after action)
- `b_reserve` = protected minimum budget (default: 1.0)

This prevents "locally rational but strategically suicidal" moves that exhaust budget for immediate gain but destroy future viability.

If violated → REJECT with "Reserve Law Violation"

#### C. Oplax Operator Algebra

For composite instructions `r1 ⊙ r2`:

1. **Metabolic Honesty**: `σ_total ≥ σ₁ + σ₂` (can't undercharge)
2. **Defect Monotonicity**: `κ_total ≤ κ₁ + κ₂` (can't launder debt)

If either violated → HALT

### 5. Receipts (`ledger/receipt.py`)

Immutable proof artifacts recording every decision:

```python
Receipt(
    step_idx,      # Execution step number
    op_code,       # Operation performed
    x_hash_before,# State hash before
    x_hash_after,  # State hash after
    v_before,      # Potential before
    v_after,       # Potential after
    sigma,         # Energy cost used
    kappa,         # Defect budget used
    b_before,      # Budget before
    b_after,       # Budget after
    is_composite,  # Was this a composite operation?
    decision,      # ACCEPT, REJECT, or HALT
    message        # Human-readable reason
)
```

### 6. Embedder (`core/embedder.py`)

Translates text into PhaseLoom coordinates:

- **Vocabulary**: Maps words to 2D semantic vectors
- **Unknown Words**: Mapped to high-tension "confusion" state
- **Punctuation**: Ignored

### 7. Memory Manifold (`core/memory.py`)

Tracks cognitive history via "scars":

- **Scars**: Past high-tension regions that repel future traversals
- **Curvature**: Extra potential penalty for approaching scarred regions
- **Decay**: Scars can optionally decay over time

## Runtime Loops

### Execution Flow

```
1. Initialize State(x₀, b₀)
2. Loop while steps < max_steps and V(x) > threshold:
   a. Generate proposal instruction(s)
   b. Call verifier.check(step, state, instruction)
   c. If ACCEPT: update state, record receipt
   d. If REJECT: try fallback instruction
   e. If HALT: terminate (composition violation)
3. Output receipts to ledger
```

### Loop Variants

| Loop | Purpose | Key Feature |
|------|---------|-------------|
| `execution_loop.py` | Basic NPE | Random exploration |
| `semantic_loop.py` | Text dynamics | Word embeddings |
| `learning_loop.py` | Memory learning | Scar tracking |
| `evolution_loop.py` | Full NPE | Combined potentials |

## Dependency Injection Pattern

The verifier uses dependency injection instead of global state:

```python
# GOOD: Inject potential function
verifier = OplaxVerifier(potential_fn=custom_V)
verifier.check(state, instruction)

# BAD: Monkey-patching (deprecated)
import core.state
core.state.V_PL = custom_V
```

This ensures:
- Testability
- No hidden global state
- Explicit configuration

## Testing Strategy

### Unit Tests

- `test_state.py`: State creation, hashing, potential functions
- `test_verifier.py`: Constraint checking, composition rules

### Property Tests

- State hashing deterministic under identical inputs
- Thermodynamic inequality correctly accepts/rejects
- Budget exhaustion properly handled
- Oplax algebra enforces composition rules

## Test Suites

### Stress Tests (`experiments/stress_tests.py`)

1. **Pressure Test**: Anti-freeze logic under high constraints
2. **Laziness Test**: Discipline/commitment to costly but beneficial paths
3. **Greed Test**: Ledger blocking of catastrophic decisions

### Intellectual Tests (`experiments/intellectual_tests.py`)

1. **Compositional Reasoning**: Oplax algebra enforcement
2. **Exploration-Exploitation**: Balance between risky and safe moves
3. **Memory Consolidation**: Memory curvature effects
4. **Convergence Under Noise**: Stochastic instruction handling
5. **Multi-Step Planning**: Looking ahead for sustainable paths

### Benchmark Suite (`experiments/benchmark_suite.py`)

Compares GMI against:
- **Gradient Descent**: Standard optimization baseline
- **Simulated Annealing**: Temperature-based stochastic optimization

Results show GMI outperforms both in convergence speed, efficiency, and safety.

## File Organization

```
gmi/
├── core/           # Pure computational logic
│   ├── state.py    # State, Instruction, V_PL
│   ├── embedder.py # Text → vector
│   ├── memory.py   # Scar tracking
│   └── potential.py # GMIPotential with budget barrier
├── ledger/         # Verification & proof
│   ├── oplax_verifier.py  # Includes Reserve Law
│   ├── receipt.py
│   └── hash_chain.py
├── runtime/       # Execution loops
├── experiments/   # Research demos & tests
│   ├── stress_tests.py
│   ├── intellectual_tests.py
│   └── benchmark_suite.py
├── tests/         # Unit tests
├── plans/         # Design documents
└── docs/          # This documentation
```

## Design Principles

1. **No Global State**: All dependencies injected explicitly
2. **Immutable State**: State objects never mutate
3. **Verifiable**: Every decision produces a receipt
4. **Explicit Costs**: Thermodynamic constraints always visible
5. **Prototype vs Stable**: Clear separation between experiments and production code
