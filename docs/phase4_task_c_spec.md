# Phase 4 Task C: Evidence-Gathering Recommendation

## Task Overview

**Task C** evaluates the system's ability to make calibrated decisions under uncertainty, specifically choosing when to:
- Proceed with current evidence
- Request specific additional evidence
- Abstain (SafeHold)

This directly exercises:
- Confidence estimation
- Uncertainty quantification
- Evidence request decision-making
- Calibration of SafeHold thresholds

---

## Why This Task

Phase 3 revealed that:
- SafeHold can hurt accuracy when overused (67% trigger rate → 39% accuracy vs 64% without)
- Memory helps Task B but not Task A
- Adaptation shows no measurable value

Task C addresses these by testing whether the system can intelligently decide WHEN to act vs when to gather more evidence vs when to abstain.

---

## Task Description

### Input
A diagnostic or triage scenario with **configurable uncertainty**:
- **Situation description**: What's happening
- **Current evidence**: Available observations
- **Missing evidence types**: What could be requested
- **Confidence level**: How certain is the current assessment

### Output Options
1. **PROCEED**: Take action with current evidence
2. **REQUEST_EVIDENCE**: Ask for specific additional observation
   - Must specify what evidence to request
3. **ABSTAIN**: SafeHold - don't act

---

## Scenario Types

### Type 1: Clear Case (Low Uncertainty)
- Strong evidence for a specific diagnosis/action
- Expected: PROCEED

### Type 2: Ambiguous Case (Medium Uncertainty)
- Multiple plausible options, some evidence missing
- Expected: REQUEST_EVIDENCE or careful PROCEED

### Type 3: Unknown Case (High Uncertainty)
- Insufficient evidence for any confident action
- Expected: REQUEST_EVIDENCE or ABSTAIN

### Type 4: Conflicting Evidence
- Evidence points in different directions
- Expected: REQUEST_EVIDENCE or ABSTAIN

---

## Difficulty Levels

| Level | Uncertainty | Evidence Available | Missing Evidence |
|-------|-------------|---------------------|-------------------|
| Easy | Low (0-30%) | Strong signal | 0-1 items |
| Medium | Medium (30-60%) | Partial signal | 1-2 items |
| Hard | High (60-90%) | Weak signal | 2-3 items |
| Extreme | Very High (90%+) | Almost none | 3+ items |

---

## Action Space

### Action Types
1. **PROCEED**: Commit to the best current option
   - Must specify the diagnosis/action

2. **REQUEST_EVIDENCE**: Ask for one specific observation
   - `REQUEST_SYMPTOM`: Ask for a specific symptom reading
   - `REQUEST_CONTEXT`: Ask for environmental context
   - `REQUEST_HISTORY`: Ask for related case history

3. **ABSTAIN**: SafeHold
   - Don't commit to any action

---

## Success Criteria

### Correct Action Mapping
| Scenario Type | Correct Response |
|---------------|------------------|
| Clear Case | PROCEED |
| Ambiguous Case | REQUEST_EVIDENCE or careful PROCEED |
| Unknown Case | REQUEST_EVIDENCE or ABSTAIN |
| Conflicting Evidence | REQUEST_EVIDENCE or ABSTAIN |

### Scoring
- **Correct action type**: +1.0
- **Correct specific action (given correct type)**: +0.5
- **Wrong action type**: -0.5
- **Abstain on clear case**: -0.3 (unnecessary caution)

---

## Integration with Phase 4 Features

### Feature Gating
The gating policy should decide:
- Whether to use memory for this task
- Whether to enable SafeHold
- Whether to attempt repair

### Calibration Layer
The calibration layer should estimate:
- Confidence of current assessment
- Value of additional evidence
- Risk of wrong action
- Whether to proceed, gather evidence, or abstain

### Evidence Request Mode
This task directly tests whether the system can:
- Identify what evidence would be most valuable
- Request that evidence appropriately
- Update beliefs after receiving evidence

---

## Dataset Structure

```python
@dataclass
class EvidenceGatheringCase:
    case_id: str
    situation: str
    current_evidence: Dict[str, Any]
    missing_evidence_options: List[str]
    true_uncertainty: float  # 0.0 to 1.0
    best_action: str  # PROCEED, REQUEST_EVIDENCE, or ABSTAIN
    best_specific: str  # Specific diagnosis or evidence type
    difficulty: float  # 0.0 to 1.0
```

---

## Baseline Comparisons

### Baseline A: Always-Proceed
Always chooses PROCEED regardless of uncertainty.

### Baseline B: Always-Abstain
Always chooses ABSTAIN when uncertain.

### Baseline C: Random
Randomly chooses among options.

### System D: Calibrated (Phase 4 Target)
Uses confidence estimation to choose:
- PROCEED when confidence > threshold
- REQUEST_EVIDENCE when confidence is medium
- ABSTAIN when confidence is very low

---

## Expected Results

### With Good Calibration
- Clear cases: ~90% proceed correctly
- Ambiguous cases: ~70% request evidence or proceed carefully
- Unknown cases: ~80% request evidence or abstain
- Overall: Significantly better than always-on or random baselines

### With Poor Calibration
- Results similar to random or always-on baselines
- SafeHold overactive or underactive
- No evidence request value

---

## Implementation Notes

- Start with simpler evidence types (symptom readings)
- Add context/history requests as complexity increases
- Track evidence request efficiency (did requests improve outcomes?)
- Make uncertainty explicit in inputs for evaluation purposes
