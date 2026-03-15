# Phase 3 Task B Specification

## Memory-Informed Constrained Maintenance Triage

**Phase**: 3  
**Status**: Draft  
**Purpose**: Second task for Phase 3 multi-task evaluation — tests state-dependent action selection under constraints.

---

## Task Overview

Given observed system symptoms, equipment context, and a memory of past maintenance cases, select the appropriate next action from a finite action set, subject to budget constraints, risk assessment, and verification.

This task complements Task A (diagnosis) by testing **action selection** rather than **state interpretation**.

---

## Why This Task

This task naturally rewards:
- **Memory**: Retrieving relevant prior maintenance actions and outcomes
- **Budget-Aware Verification**: Ensuring action is cost-effective
- **SafeHold/Abstention**: Recognizing when uncertainty is too high to act
- **Risk Assessment**: Rejecting actions that could cause harm
- **Receipt-Grade Commitment**: Each action has traceable justification

**Key Difference from Task A**:
- Task A: "What is the problem?" (classification)
- Task B: "What should be done next?" (action selection with SafeHold option)

---

## Task Formalization

### Input

1. **Symptom Vector**: Binary or categorical observations (15-25 symptoms)
2. **Equipment Context**: System type, criticality level, operational state
3. **Severity Indicators**: Urgency level, safety implications, cost implications
4. **Case Memory**: Archive of (symptoms + context → action + outcome) pairs
5. **Budget Constraints**: Maximum reasoning steps, cost limits
6. **Optional Ambiguity**: Missing data, conflicting signals (tests SafeHold)

### Output

- **Selected Action**: One of the action candidates
- **Confidence Score**: How certain the agent is (0-1)
- **Risk Assessment**: Low/Medium/High risk rating
- **Rationale**: Why this action was chosen

### Action Set (7 actions)

1. **INSPECT_LOCAL** — Examine component locally (low cost, low risk)
2. **CONTINUE_MONITOR** — Keep running, watch for changes (no cost, low risk)
3. **GATHER_EVIDENCE** — Run diagnostics, collect more data (medium cost)
4. **REPLACE_COMPONENT** — Swap out suspect part (high cost, medium risk)
5. **SHUT_DOWN** — Stop operations safely (high cost, high risk)
6. **ESCALATE_SPECIALIST** — Call expert support (medium cost, low risk)
7. **SAFEHOLD_ABSTAIN** — Do not act, uncertainty too high (zero cost, zero risk)

---

## Constraints

- **Budget Limit**: Maximum 8 reasoning steps per episode
- **Reserve Floor**: Must preserve 20% budget for future episodes
- **Verification**: Action must be coherent with symptoms and context
- **Risk Constraint**: High-risk actions require higher confidence

---

## Memory Characteristics

The memory for Task B should have **different noise profile** than Task A:

- **Higher action-outcome correlation**: Past actions directly predict current best action
- **Less ambiguous outcomes**: Clear success/failure signals
- **Risk patterns**: Memory should help identify risky vs safe actions

This addresses Phase 2's finding that memory hurt on diagnosis — Task B's memory has clearer signal.

---

## Success Criteria

- **Primary**: Correct or acceptable action selection rate
- **SafeHold Utility**: SafeHold should be invoked appropriately when uncertainty is high
- **Memory Benefit**: Memory retrieval should improve action selection (vs no-memory)
- **Budget Discipline**: Mean spend < 80% of limit, no reserve violations
- **Guardrail**: Risk assessment accuracy

---

## Baseline Comparisons

### Baseline A: Simple Heuristic

- Pick action matching highest severity symptom
- No memory, no verification, no budget
- **Baseline**

### Baseline B: Ungoverned GMI

- Same architecture as full system
- Skip verification step
- Unlimited budget
- **Control**

### System C: Full GMI on GM-OS

- Complete loop: percept → memory → proposal → verify → commit → receipt
- Budget constraints enforced
- SafeHold option available
- **System Under Test**

---

## Evaluation Metrics

### Primary KPI

**Action Accuracy**: Correct/acceptable action rate on held-out test cases

### Guardrails

1. **SafeHold Appropriate Rate**: % of high-uncertainty cases where SafeHold chosen
2. **Budget Discipline**: Reserve floor violations = 0%, mean spend < 80%
3. **Risk Violation Rate**: Actions taken that verifier rejects as too risky
4. **Memory Harm Rate**: Accuracy with memory vs without (must be ≥ 0)

### Secondary Metrics

- **Latency**: Time per episode
- **Memory Utilization**: Retrieval frequency, attribution quality
- **Mode Distribution**: How often system enters SafeHold vs Commit

---

## Test Case Structure

Each test case includes:
- `symptoms`: Dict of observed indicators
- `context`: Equipment type, criticality, operational state
- `severity`: Urgency level (1-5)
- `ambiguity_level`: None/Low/Medium/High (for SafeHold testing)
- `correct_action`: Ground truth action
- `memory_cases`: Relevant prior cases (subset of full archive)

### Example Test Case

```json
{
  "case_id": "triage_001",
  "symptoms": {
    "unusual_noise": true,
    "vibration": false,
    "temperature_elevated": true,
    "error_code": "E45",
    "performance_degraded": true
  },
  "context": {
    "equipment_type": "pump_assembly",
    "criticality": "high",
    "operational_state": "running",
    "age_hours": 4500
  },
  "severity": 3,
  "ambiguity_level": "low",
  "correct_action": "GATHER_EVIDENCE",
  "memory_cases": [
    {"symptoms": {...}, "action": "INSPECT_LOCAL", "outcome": "success"},
    {"symptoms": {...}, "action": "SHUT_DOWN", "outcome": "overreaction"}
  ]
}
```

---

## Dataset Requirements

- **Training Set**: 500 cases (for memory archive)
- **Test Set**: 200 held-out cases
- **Difficulty Distribution**: 
  - 40% clear-cut (obvious correct action)
  - 35% ambiguous (multiple reasonable options)
  - 25% SafeHold-appropriate (high uncertainty)

---

## Key Design Principles

1. **Memory should help**: Task B designed so memory retrieval is beneficial (unlike Task A)
2. **SafeHold is a feature**: Not a failure — appropriate abstention is rewarded
3. **Risk is verifiable**: The verifier can check if action matches risk level
4. **Budget matters**: Limited reasoning steps force prioritization

---

## Relationship to Task A

| Aspect | Task A (Diagnosis) | Task B (Triage) |
|--------|-------------------|-----------------|
| Output | Classification | Action selection |
| Memory signal | Weaker (noisy) | Stronger (action-outcome) |
| Abstention | Not available | SafeHold available |
| Verification focus | Coherence | Risk + coherence |
| Phase 2 result | Memory hurt by 9% | Memory should help |

Together, these tasks provide a comprehensive test of substrate value beyond governance alone.
