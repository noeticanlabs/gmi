# Character Shell Specification

## What is the Character Shell?

The **Character Shell** (χ) is a **threshold modulation field** that defines how the GMI organism responds within the lawful epistemic space. It is NOT a second belief system - it is a lawful parameterization of response **style**.

Think of it as the organism's **temperament** - not what it knows, but how it tends to act on what it knows.

---

## Who is it for?

### 1. The Agent Itself
The agent uses the Character Shell to:
- Decide **how aggressively** to act under uncertainty
- Determine **how much discomfort** to tolerate before acting
- Choose **how long** to persist in the face of failure
- Calibrate **how much risk** to accept in pursuit of goals
- Balance **speed vs. thoroughness** in decision-making

### 2. System Architects / Developers
The Character Shell provides:
- **Tunable personality profiles** for different use cases
- **Formal parameterization** of behavioral tendencies
- **Stability guarantees** - character cannot override hard laws

### 3. Verification Systems
The Character Shell outputs:
- **Modulated thresholds** for action selection
- **Behavioral drift** metrics over time
- **Compliance verification** - character never overrides legality

---

## Where does it belong in the stack?

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GM-OS (Governed Machine-OS)                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              EPISTEMIC SHELL (v1-v4)                      │  │
│  │                                                           │  │
│  │  v1: Fiber/Hypothesis Tracking                            │  │
│  │  v2: Horizon/Bounds Computation                           │  │
│  │  v3: Curiosity (EVI) Optimization                         │  │
│  │  v4: Authority Trust Calibration                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            ↓ V_epi(x; Θ_χ)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              CHARACTER SHELL (χ) [NEW]                    │  │
│  │                                                           │  │
│  │  χ = (χ_courage, χ_discipline, χ_patience, χ_curiosity, │  │
│  │       χ_restraint, χ_persistence, χ_laziness, χ_humility)│  │
│  │                                                           │  │
│  │  Modulates thresholds within lawful epistemic space      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            ↓ Θ_χ = M_χ(Θ_0)                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              GMITensionLaw (Tension Computation)          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            ↓ admissible?                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Execution Loop (State Transitions)           │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   Memory     │  │   Affective │  │     Sensors/Actuators │  │
│  │  Archive     │  │   State      │  │                       │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### The Stack Order

```
Coh law → GM-OS substrate → GMI cognition → Epistemic shell v1-v4 → Character shell χ → Execution evaluator
```

**Meaning:**
1. **Coh** defines what lawful transition means
2. **GM-OS** defines the substrate and kernel
3. **GMI** defines the hosted intelligence
4. **Epistemic shell** constrains belief, uncertainty, curiosity, and trust
5. **Character shell** biases action selection within that lawful epistemic space
6. **Execution evaluator** turns the resulting intention into kernel-step proposals

---

## Why Does It Exist?

### The Problem: Behavioral Style Without Corruption

GMI needs to act in the world, but "how it acts" varies by context:
- A diagnostic system should be **careful and thorough**
- A real-time controller should be **fast and decisive**
- An explorer should be **curious and bold**
- A guard should be **suspicious and patient**

But we can't just hardcode these behaviors - that would be fragile. Instead, we parameterize them as character traits that modulate thresholds.

### Why Not Just Use Traits?

Traditional "personality" approaches have problems:
- They become vague psychology words without formal meaning
- They can override truth - "courage" becomes a license to ignore evidence
- They don't have stability guarantees

The Character Shell solves this by:
1. **Formal parameters** (χ ∈ [0,1]^m)
2. **Hard constraint** - χ cannot override legality
3. **Threshold modulation** - χ only affects how thresholds are applied, not what is legal

### The Core Principle

> **Character Shell Principle**
> 
> χ may modulate thresholds, costs, and preferences inside the lawful set, but may NOT override legality, anchor dominance, reserve floors, or deterministic verification.

In plain English:
- **Courage** may make you act sooner, but NOT on illegal evidence
- **Curiosity** may make you query more, but NOT past reserve floors
- **Laziness** may reduce exploration, but NOT justify hallucinated certainty
- **Discipline** may keep you in repair mode longer, but NOT invent evidence

---

## The Character Parameters (χ)

### Definition

Let the character shell be a parameter bundle:

```
χ = (χ_courage, χ_discipline, χ_patience, χ_curiosity, χ_restraint, χ_persistence, χ_laziness, χ_humility) ∈ [0,1]^m
```

Each parameter is a control coefficient in [0,1].

### Parameter Meanings

| Parameter | Question | Effect |
|-----------|----------|--------|
| **χ_courage** | "Can I act when it's uncertain?" | Tolerance for acting under ambiguity |
| **χ_discipline** | "Do I keep the bookkeeping straight?" | Pointer preservation, bookkeeping rigor |
| **χ_patience** | "Can I wait for better evidence?" | Tolerance for delay in learning |
| **χ_curiosity** | "Is it worth paying to learn more?" | Willingness to pay for evidence |
| **χ_restraint** | "Should I act on this alone?" | Corroboration demand before acting |
| **χ_persistence** | "Should I keep trying?" | Resistance to giving up during repair |
| **χ_laziness** | "Is this worth the effort?" | Preference for cheap representatives |
| **χ_humility** | "Am I sure enough?" | Resistance to premature fiber collapse |

---

## How χ Ties Into v1-v4

### v1: Local Evidence / Global Underdetermination

**Humility modulates collapse resistance:**

```
λ_collapse(χ) = λ_collapse^0 × (1 + α_h × χ_humility)
```

- High χ_humility: "keep alternatives alive longer" → higher collapse penalty
- Low χ_humility: "collapse faster if permitted" → lower collapse penalty

**Courage modulates ambiguity tolerance:**

```
τ_frag(χ) = τ_frag^0 + a_c × χ_courage - a_r × χ_restraint
```

- Higher courage increases tolerated fragility
- Higher restraint decreases it

### v2: Representative Model / Fiber Distinction

**Laziness modulates representative persistence:**

```
τ_refresh(χ) = τ_refresh^0 + a_l × χ_laziness - a_d × χ_discipline
```

- High laziness: continue using current representative longer
- High discipline: refresh sooner when misfit rises

**Discipline guards against overreach:**

```
λ_overreach(χ) = λ_overreach^0 × (1 + a_d × χ_discipline + a_h × χ_humility)
```

Disciplined and humble systems pay heavily for confusing the representative with truth.

### v3: Targeted Curiosity / Lawful Fiber Collapse

**Curiosity modulates EVI threshold:**

```
τ_epi(χ) = τ_epi^0 + a_q × χ_curiosity - a_l × χ_laziness
```

- High curiosity: ask more often
- High laziness: ask less often

**Patience modulates delay cost:**

```
β_delay(χ) = β_delay^0 + a_c × χ_courage + a_l × χ_laziness - a_p × χ_patience
```

- Courage reduces willingness to delay for more evidence
- Patience increases willingness to wait and learn

**Restraint vs persistence modulates mania:**

```
λ_mania(χ) = λ_mania^0 × (1 + a_r × χ_restraint - a_p × χ_persistence)
```

### v4: Epistemic Trust / Authority Calibration

**Restraint/humility demand corroboration:**

```
τ_corr(χ) = τ_corr^0 + a_r × χ_restraint + a_h × χ_humility - a_c × χ_courage
```

- Restrained and humble systems want more corroboration
- Bolder systems willing to act with less

**Courage/patience soften shock:**

```
λ_shock(χ) = λ_shock^0 × (1 - a_c × χ_courage - a_p × χ_patience + a_l × χ_laziness)
```

- Courage and patience soften model-falsification shock
- Laziness makes surprise harder to metabolize

---

## Threshold Modulation Map

A good high-level way to formalize χ:

**Definition — Threshold Field Induced by Character**

Let the epistemic shell define a baseline vector of thresholds and weights:

```
Θ_0 = (τ_frag^0, τ_epi^0, τ_corr^0, λ_collapse^0, λ_overreach^0, λ_mania^0, λ_shock^0, ...)
```

Then character induces a modulation map:

```
M_χ: Θ_0 → Θ_χ
```

So the actual operating epistemic shell is:

```
(v1, v2, v3, v4; Θ_χ)
```

This keeps:
- Epistemic law fixed
- Character-dependent response style variable

---

## Character Non-Override Constraint

**Theorem — Character Non-Override Constraint**

Let L_hard denote the hard lawful constraints of Coh/GM-OS/GMI:
- Verifier acceptance
- Reserve floors
- Anchor dominance
- Quarantine thresholds
- Deterministic receipt legality
- Admissibility bounds

Then for any character state χ:

```
χ ∉ Override(L_hard)
```

Equivalently:

> **Character may bias lawful selection, but may NOT make an unlawful act lawful.**

Without this:
- Courage becomes recklessness
- Curiosity becomes compulsion
- Patience becomes stagnation
- Laziness becomes delusion

---

## Character Profiles

| Profile | χ_courage | χ_discipline | χ_patience | χ_curiosity | χ_restraint | χ_humility | Behavior |
|---------|------------|--------------|------------|-------------|-------------|------------|----------|
| **Scientist** | 0.3 | 0.8 | 0.8 | 0.6 | 0.7 | 0.8 | Preserves larger fibers, refreshes representatives sooner, asks more corroborating questions, tolerates delayed action better |
| **Warrior** | 0.9 | 0.6 | 0.3 | 0.4 | 0.3 | 0.4 | Acts earlier under ambiguity, tolerates more fragility, seeks less corroboration, lower shock response |
| **Explorer** | 0.7 | 0.4 | 0.5 | 0.9 | 0.3 | 0.5 | High curiosity spending, moderate patience, lower restraint, balanced persistence |
| **Diplomat** | 0.5 | 0.7 | 0.6 | 0.5 | 0.8 | 0.7 | High restraint and humility, moderate courage, good discipline |

---

## The Clean Summary

```
Epistemic Shell = "what is lawful to believe, ask, and trust"
```

```
Character Shell χ = "how strongly the organism prefers caution, boldness, patience, curiosity, or cheapness inside that lawful space"
```

Or even tighter:

> **χ does NOT decide truth; it decides style of lawful pursuit of truth and action.**

---

## Full Integration Equation

Let the epistemic penalties/rewards from v1–v4 be collectively V_epi(x; Θ_χ).

Then the character-aware GMI potential becomes:

```
V_GMI(x; χ) = V_percept + V_memory + V_goal + V_cons + V_plan + V_action + V_meta + V_resource + V_epi(x; Θ_χ)
```

So χ does NOT appear as "a mood layer." It appears as a lawful modulation of the epistemic-energy landscape.

---

## Why This Matters

Without the Character Shell:
- GMI has no way to express "cautious" vs "bold" behavior
- All decisions are made with the same urgency
- No personality differentiation for different use cases

With the Character Shell:
- GMI can be configured for different roles (diagnostic, controller, explorer, guard)
- Behavior is mathematically guaranteed to stay within legal bounds
- Character adapts slowly under experience, enabling learning without instability
