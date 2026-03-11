# Epistemic Shell Specification

## What is the Epistemic Shell?

The **Epistemic Shell** is a meta-cognitive layer that governs how the GMI agent handles **uncertainty, curiosity, and trust** in information sources. It answers the fundamental question: *"How should I believe what I think I know?"*

Think of it as the agent's **epistemology module** - the part that monitors the quality of its own knowledge, not just the quantity.

---

## Who is it for?

The Epistemic Shell serves three audiences:

### 1. The Agent Itself
The agent uses the Epistemic Shell to:
- Determine when to **trust** a new piece of information vs. verify it
- Decide whether to **explore** (seek new evidence) or **exploit** (act on current knowledge)
- Recognize when it's being **surprised** beyond its adaptive capacity
- Avoid **gullibility** when receiving claims from external authorities

### 2. System Architects / Developers
The Epistemic Shell provides:
- A **formal framework** for encoding epistemic safety constraints
- **Tunable parameters** to adjust risk tolerance (curiosity vs. caution)
- **Observable metrics** for monitoring agent belief quality

### 3. Verification Systems
The Epistemic Shell outputs:
- **Tension terms** (V_collapse, V_overreach, etc.) that feed into the GMITensionLaw
- **Confidence scores** for trust calibration
- **Evidence quality** assessments for downstream decision-making

---

## Where does it belong in the stack?

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GM-OS (Governed Machine-OS)                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              EPISTEMIC SHELL (v1-v4) [NEW]              │  │
│  │                                                           │  │
│  │  v1: Fiber/Hypothesis Tracking                           │  │
│  │  v2: Horizon/Bounds Computation                          │  │
│  │  v3: Curiosity (EVI) Optimization                        │  │
│  │  v4: Authority Trust Calibration                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            ↓ V_epic (new tension terms)        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              GMITensionLaw (Tension Computation)          │  │
│  │                                                           │  │
│  │  V_GMI = V_obs + V_mem + V_goal + V_cons + V_plan       │  │
│  │        + V_act + V_meta + Φ_B + Φ_A + **V_epi**          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            ↓ admissible?                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Execution Loop (State Transitions)          │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   Memory     │  │   Affective │  │     Sensors/Actuators │  │
│  │  Archive     │  │   State      │  │                       │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Layer-by-Layer Position

| Layer | Component | Role | Epistemic Shell Connection |
|-------|-----------|------|---------------------------|
| **L0: Substrate** | Kernel, Scheduler | Hardware/Execution | Base constraints |
| **L1: Cognitive** | State, Potential, Dynamics | Core computation | Tension drives motion |
| **L2: Governance** | TensionLaw, Verifier | Admissibility | **Epistemic Shell sits here** |
| **L3: Meta** | **Epistemic Shell** | Belief quality | **THIS IS THE EPISTEMIC SHELL** |
| **L4: Affective** | Emotions, Budget | Motivation | Provides shock/trust values |
| **L5: Memory** | Archive, Workspace | Storage | Evidence history for EVI |

### Data Flow

```
External Input
      ↓
Sensory Processing → Salience → Affective State
      ↓                                    ↓
Memory Archive ← ← ← ← ← ← ← ← ← ← ← ← ← ┘
      ↓
[Epistemic Shell v1]: Update fiber (hypotheses)
[Epistemic Shell v2]: Compute horizon bounds
[Epistemic Shell v3]: Calculate EVI for observations
[Epistemic Shell v4]: Assess authority trust
      ↓
GMITensionLaw.compute(V_epi)
      ↓
Is V_total admissible? → Yes → Execute Action
                        → No → Reject/Modify
```

---

## The Four Vertices (v1-v4)

### v1: Local Evidence / Global Underdetermination

**Core Question**: "Do I have enough evidence to commit to this belief?"

**Mechanism**: Track the **fiber** (ℱ) - the space of admissible world-models/hypotheses. Don't collapse to a single hypothesis until evidence supports it.

**Problem Addressed**: Premature certainty - the agent jumping to conclusions before sufficient data.

**Tension Term**: `V_collapse` - penalty for collapsing fiber with insufficient evidence

---

### v2: Representative Model / Fiber Distinction

**Core Question**: "Is my belief representative or just a convenient fiction?"

**Mechanism**: Distinguish between **representative models** (data-driven) and **fiber pointers** (hypothesis references). Keep both - use the representative but maintain the pointer.

**Problem Addressed**: The agent confusing its models for reality - confusing the map for the territory.

**Tension Term**: `V_overreach` - penalty for claims beyond the horizon of observable evidence

---

### v3: Targeted Curiosity / Lawful Fiber Collapse

**Core Question**: "Is this observation worth investigating further?"

**Mechanism**: Compute **EVI** (Expected Value of Information) for observations. If EVI > cost, pursue observation to reduce uncertainty.

**Problem Addressed**: 
- **Curiosity Deficit**: Ignoring high-value evidence
- **Curiosity Mania**: Spending too much on exploration without learning

**Tension Terms**: 
- `V_curiosity_deficit` - penalty for ignoring high-EVI observations
- `V_curiosity_mania` - penalty for excessive unfocused exploration

---

### v4: Epistemic Trust / Authority Calibration

**Core Question**: "Should I trust this source?"

**Mechanism**: Weight authority by **provenance × trust × evidence quality**. Verify claims before accepting.

**Problem Addressed**:
- **Shock**: Being surprised beyond adaptive capacity
- **Gullibility**: Trusting unverified authority claims

**Tension Terms**:
- `V_shock` - penalty for surprise exceeding adaptive capacity
- `V_gullible` - penalty for trust without verification

---

## Key Mathematical Concepts

### Fiber (ℱ)
The **admissible world-model class** - the set of hypotheses consistent with current evidence.

```python
# In GMITensionState
fiber_hypotheses: List[str]  # Active hypotheses in the fiber
fiber_beliefs: np.ndarray   # Belief distribution over hypotheses
```

### Horizon (H_k)
The **bounded observable evidence** at step k - what the agent can actually perceive.

```python
# In GMITensionState  
horizon_evidence: np.ndarray  # Evidence within observable bounds
horizon_confidence: float    # Confidence in horizon boundary
```

### Effective Weight (W_eff)
The **trust-adjusted authority weight**:

```
W_eff = A_0(source) × Γ_trust(source, agent) × Ξ(evidence_quality)
```

Where:
- A_0(s): Provenance score (how authoritative is the source?)
- Γ_trust(s,t): Historical trust between source and agent at time t
- Ξ(e): Evidence quality (how well-supported is the claim?)

---

## Integration Points Summary

| Component | File | What Epistemic Shell Uses |
|-----------|------|---------------------------|
| **GMITensionState** | tension_law.py:530 | New fields for fiber, horizon, trust |
| **TensionWeights** | tension_law.py:72 | New weights for v1-v4 terms |
| **GMITensionLaw** | tension_law.py:576 | New `_compute_epistemic_potential()` |
| **Memory Archive** | gmos/memory/archive.py | Evidence history storage |
| **Affective State** | gmos/agents/gmi/affective_state.py | Shock response, trust emotions |
| **Affective Budget** | gmos/agents/gmi/affective_budget.py | Curiosity budget allocation |
| **Execution Loop** | gmos/agents/gmi/execution_loop.py | Wire in V_epi computation |

---

## Why This Matters

Without the Epistemic Shell, the GMI agent:

1. **Collapses prematurely** to single beliefs (v1 failure)
2. **Confuses models for reality** (v2 failure)
3. **Ignores valuable information** OR wastes resources on noise (v3 failure)
4. **Gets duped by authoritative-sounding claims** (v4 failure)

With the Epistemic Shell, the agent becomes:

1. **Epistemically humble** - waits for sufficient evidence
2. **Model-aware** - knows the difference between representation and reality
3. **Curiously efficient** - seeks information where it matters
4. **Trust-calibrated** - verifies before accepting

This is what makes GMI not just a cognitive engine, but a **responsible epistemic agent**.
