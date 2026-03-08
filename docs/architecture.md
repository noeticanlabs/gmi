# GMI Architecture

## Overview

Governed Metabolic Intelligence (GMI) is a computational framework that treats cognitive processes as thermodynamic systems. The core insight is that valid cognitive operations must satisfy energy conservation constraints similar to physical thermodynamic laws.

## Section I — Continuous Core and Geometric Governance

> **Canonical Reference**: [`docs/section_i_continuous_core.md`](docs/section_i_continuous_core.md)

The mathematical foundation of GMI is defined in **Section I**, which establishes:

- **Admissible State Space**: Extended state $z = (x, b) \in \mathcal H \times \mathbb R_{\ge 0}$
- **Violation Functional**: $V: \mathcal H \to \mathbb R$ (proper, lsc, convex)
- **Safe Region**: $\mathcal C = \{x: V(x) \le \Theta\}$
- **Governed Dynamics**: $\dot z \in \mathcal F(z) - N_{\mathcal K}(z)$ (Moreau sweeping)
- **Budget Spend Law**: $\dot b = -\kappa (dV/dt)_+$
- **Root-Clock**: $d\tau/dt = \sqrt{b + \alpha \mathcal D_a}$

### Theorem Stack Summary

| Theorem | Statement | Status |
|---------|-----------|--------|
| Theorem 5.1 | Forward invariance: $z(0) \in K \Rightarrow z(t) \in K$ | [PROVED] |
| Theorem 7.1 | Budget boundary collapse: $b=0 \Rightarrow dV/dt \le 0$ | [PROVED] |
| Proposition 8.1 | Monotonicity: $d/dt(b + \kappa V) \le 0$ | [PROVED] |
| Theorem 9.1 | Governance damping: $\|u(t)\| \le e^{-\beta^2/\lambda_{max}t}\|u(0)\|$ | [PROVED] |
| Theorem 10.1 | Minkowski interval: $d\tau^2 = dt^2 - dx^2/c^2$ | [PROVED] |
| Theorem 11.1 | Horizon freezing: $\Lambda=0 \Rightarrow d\tau/dt=0$ | [PROVED] |
| Theorem 12.1 | ADM lapse bridge: $N = \sqrt{b + \alpha \mathcal D_a}$ | [LEMMA-NEEDED] |

### Tag Legend

- **[AXIOM]** — Foundational definitions and assumptions
- **[POLICY]** — Governing laws and dynamics
- **[PROVED]** — Theorems with implementation verification
- **[LEMMA-NEEDED]** — Items requiring additional proof work

See [`core/section_i_theorems.py`](core/section_i_theorems.py) for formal theorem implementations.

## Section II — Discrete Governance and the Oplax Ledger

> **Canonical Reference**: [`docs/section_ii_discrete_governance.md`](docs/section_ii_discrete_governance.md)

Section II converts the continuous viability law into a deterministic, receipt-verifiable algebra:

- **PDES Projection**: Many-to-one projection $\Pi: \mathcal X \to \mathcal Y$ with hidden fiber
- **Canonical Envelope**: $\widehat W(R) = \sup_{\xi \in \mathcal F_R} W(\xi)$
- **Oplax Subadditivity**: $\widehat W(R_2 \odot R_1) \le \widehat W(R_1) + \widehat W(R_2)$
- **Discrete Descent Law**: $V(x') + \text{Spend}(r) \le V(x) + \text{Defect}(r)$
- **Budget Update**: $B_{k+1} = B_k - \kappa \widehat{\mathcal D}_k - \tau_k \ge 0$
- **Canon Profile**: $H_{n+1} = \text{SHA256}(\text{tag} | H_n | \text{JCS}(r_n))$

### Theorem Stack Summary

| Theorem | Statement | Status |
|---------|-----------|--------|
| Oplax Subadditivity | $\widehat W(R_2 \odot R_1) \le \widehat W(R_1) + \widehat W(R_2)$ | [PROVED] |
| Descent Consequence | $\text{Defect}(r) \le \text{Spend}(r) \Rightarrow V(x') \le V(x)$ | [PROVED] |
| Positive Variation | $V(T) - V(0) \le \int_0^T (dV/dt)_+ dt$ | [PROVED] |
| Finite Budget Bound | $\sum (\kappa \widehat{\mathcal D}_k + \tau_k) \le B_0$ | [PROVED] |
| Oplax Morphism | $B.V(f(x')) + B.\text{Spend}(f(r)) \le B.V(f(x)) + B.\text{Defect}(f(r)) + \Delta_f$ | [DEFINITION] |
| Pos-Enrichment | $f \le g \iff \Delta_f \le \Delta_g$ | [ORDER] |

See [`core/section_ii_theorems.py`](core/section_ii_theorems.py) for formal theorem implementations.

### Tag Legend

- **[AXIOM]** — Foundational definitions and assumptions
- **[POLICY]** — Governing laws and dynamics
- **[DEFINITION]** — Formal definitions
- **[PROVED]** — Theorems with implementation verification
- **[ORDER]** — Ordering relations
- **[CONTRACT]** — Interface contract requirements
- **[LEMMA-NEEDED]** — Items requiring additional proof work
- **[INSTANTIATION]** — Domain-specific solver theories
- **[HYPOTHESIS]** — Assumptions requiring verification
- **[CONSTITUTIVE BRIDGE]** — Structural identifications
- **[WEAK-FIELD BRIDGE]** — Approximate relations

## Section III — Domain Instantiations and Verified Solver Theories

> **Canonical Reference**: [`docs/section_iii_domain_instantiations.md`](docs/section_iii_domain_instantiations.md)

Section III shows how the abstract Coh machinery becomes domain-specific mathematics:

- **NS-PCM**: Navier–Stokes instantiation with vorticity, enstrophy balance, boundary bleed
- **Relativistic**: Half-log barrier → Minkowski interval → Lorentz dynamics
- **GR Bridge**: Lawfulness power → ADM lapse → Scalar budget gravity

### Theorem Stack Summary

| Theorem | Statement | Status |
|---------|-----------|--------|
| Domain Coh Object | $S_{dom} = (X, V, Spend, Defect, RV, P)$ | [DEFINITION] |
| Enstrophy Balance | $(1/2)d/dt\|\omega\|^2 + \nu\|\nabla\omega\|^2 = \int(S\omega)\cdot\omega$ | [PROVED] |
| Millennium Gate | $\mathcal Q_\delta(t) < 1$ | [DIAGNOSTIC] |
| Minkowski Interval | $d\tau^2 = dt^2 - dx^2/c^2$ | [PROVED] |
| Relativistic Momentum | $p = \gamma_v m v$ | [PROVED] |
| Lorentz Force | $dP/dt = q(E + v \times B)$ | [PROVED] |
| Gravitational Lapse | $N = \sqrt{b + \alpha\mathcal D_a}$ | [CONSTITUTIVE BRIDGE] |
| Scalar Budget Gravity | $b \approx 1 - 2GM/(rc^2)$ | [WEAK-FIELD BRIDGE] |

See [`core/section_iii_theorems.py`](core/section_iii_theorems.py) for formal theorem implementations.

## Section IV — Formal Verification, Implementation Contract, and System Realization

> **Canonical Reference**: [`docs/section_iv_verification_contract.md`](docs/section_iv_verification_contract.md)

Section IV defines the engineering standard for canon-admissible modules:

- **Determinism Canon**: Same bytes → Same decision
- **Chain Digest Law**: $H_{n+1} = \text{hash}(\text{tag} | H_n | \text{JCS}(r_n))$
- **Trace Closure**: Legal steps compose into legal histories
- **Reject-Code Algebra**: Typed diagnostic failures

### Theorem Stack Summary

| Theorem | Statement | Status |
|---------|-----------|--------|
| Canon Module | $M = (X, V, \Sigma, RV, C)$ | [DEFINITION] |
| Determinism | Same bytes ⇒ Same decision | [AXIOM] |
| Chain Digest | $H_{n+1} = \text{hash}(\text{tag} \| H_n \| \text{JCS}(r_n))$ | [DEFINITION] |
| Trace Closure | Legal steps ⇒ Legal history | [PROVED] |
| Reject Codes | Decision = ACCEPT ∪ {REJECT(c)} | [DEFINITION] |
| Canon-Admissibility | $\text{CanonOK}(M) = \wedge P_i(M)$ | [CONTRACT] |
| Lifecycle | $S_0 \to S_1 \to \cdots \to S_8$ | [REALIZATION] |

See [`core/section_iv_theorems.py`](core/section_iv_theorems.py) for formal theorem implementations.

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
