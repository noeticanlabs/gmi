# Phase 2 Task Specification

**Phase**: 2  
**Status**: Draft  
**Mission**: Build one real hosted GMI agent that performs a complete governed cognition loop on one narrow task and beats a simpler baseline.

---

## Task Choice: Constrained Action Selection under Memory + Verification

### Task Description

**Constrained Diagnosis Task**: Given a set of observed symptoms and a memory of past cases, select the correct diagnosis from a set of candidates, subject to budget constraints and verification.

### Why This Task

This task naturally rewards:
- **Perception**: Anchoring symptom observations
- **Memory**: Retrieving relevant past cases
- **Proposals**: Generating multiple candidate diagnoses
- **Verification**: Checking coherence between diagnosis and evidence
- **Budget**: Constraining the reasoning effort
- **Action**: Selecting and committing to a diagnosis

---

## Task Formalization

### Input

1. **Symptom Vector** (percept): Binary or categorical observations
2. **Case Memory**: Archive of (symptoms → diagnosis) pairs
3. **Candidate Set**: Possible diagnoses to choose from

### Output

- **Selected Diagnosis**: One of the candidates
- **Confidence Score**: How certain the agent is
- **Rationale**: Why this diagnosis was chosen

### Constraints

- **Budget Limit**: Maximum reasoning steps per episode
- **Reserve Floor**: Must preserve some budget for future episodes
- **Verification**: Diagnosis must be coherent with symptoms

---

## Evaluation Metrics

### Primary KPI

**Task Accuracy**: Correct diagnosis rate on held-out test cases

### Guardrails

1. **Coherence Violation Rate**: Rate of diagnoses rejected by verifier
2. **Budget Discipline**: Average spend per episode, reserve violations = 0

### Secondary

- **Latency**: Time per episode
- **Memory Utilization**: How often retrieved memory helps

---

## Baseline Comparisons

### Baseline A: Simple Heuristic

- Pick diagnosis that matches most symptoms directly
- No memory, no verification, no budget

### Baseline B: Ungoverned GMI

- Same architecture but skip verification step
- Unlimited budget, no reserve enforcement

### System C: Full GMI on GM-OS

- Complete loop: percept → memory → proposal → verify → commit → receipt
- Budget constraints enforced
- Reserve floor protected

---

## Success Criteria

1. **Accuracy**: GMI beats both baselines on held-out test set
2. **Verification Matters**: At least 5% of proposals are blocked/repaired by verifier
3. **Budget Matters**: Agent behaves differently when budget is tight vs unlimited
4. **Memory Matters**: Retrieval improves accuracy over no-memory baseline

---

## Implementation Path

### Step 1: Task Environment

Create a synthetic diagnosis environment with:
- 50 possible diagnoses
- 20 symptom types
- 1000 training cases (memory)
- 200 test cases (held-out)

### Step 2: Agent Loop

Implement full hosted GMI cycle in `gmos/src/gmos/agents/gmi/hosted_agent.py`

### Step 3: Proposal Engine

Generate candidate diagnoses with:
- Estimated coherence match
- Estimated spend
- Confidence score

### Step 4: Evaluation

Run benchmark harness comparing all three systems

---

## Open Questions

1. Should diagnoses be ranked or single-select?
2. How to measure "memory helped"?
3. What baseline accuracy to expect?

---

*This is a draft. Comments and refinements welcome.*
