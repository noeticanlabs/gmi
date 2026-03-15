# Phase 4 Calibration Protocol

**Phase**: 4  
**Status**: Draft  
**Purpose**: Defines how to calibrate confidence, SafeHold thresholds, and evidence request decisions.

---

## Overview

Calibration is critical for Phase 4 because Phase 3 showed:
- SafeHold was overactive (67% trigger rate → accuracy drop from 64% to 39%)
- The system needs to know WHEN to use its features

This protocol defines how to measure and improve calibration.

---

## Calibration Metrics

### 1. Expected Calibration Error (ECE)

```
ECE = Σ (bucket_weight * |bucket_accuracy - bucket_confidence|)
```

- 10 confidence buckets (0.0-0.1, 0.1-0.2, ..., 0.9-1.0)
- Lower is better
- Target: ECE < 0.1

### 2. Reliability Curve

Plot of confidence vs accuracy per bucket:
- Perfect calibration: diagonal line
- Underconfident: curve above diagonal
- Overconfident: curve below diagonal

### 3. Threshold Sweeps

For each threshold level:
- What accuracy do we achieve?
- What is the abstention rate?
- What is the F1-like score?

---

## Calibration Process

### Step 1: Collect Predictions

For each episode, record:
- `confidence`: Estimated confidence (0-1)
- `outcome`: Whether prediction was correct (True/False)

### Step 2: Build Buckets

Group predictions into confidence buckets.

### Step 3: Compute Metrics

- ECE
- Per-bucket accuracy
- Reliability curve

### Step 4: Find Optimal Thresholds

Sweep thresholds to find:
- Proceed threshold (for action)
- Evidence threshold (for requesting more)
- Abstain threshold (for SafeHold)

---

## SafeHold Calibration

### Current Problem (Phase 3)
- SafeHold trigger rate: 67%
- Accuracy with SafeHold: 39%
- Accuracy without SafeHold: 64%

### Calibration Target
- Reduce SafeHold rate to 10-30%
- Maintain or improve accuracy
- Only trigger when truly uncertain

### Threshold Sweep

| Threshold | Accuracy | SafeHold Rate | Notes |
|-----------|----------|---------------|-------|
| 0.0 (none) | baseline | 0% | No SafeHold |
| 0.2 | ? | ? | Very permissive |
| 0.3 | ? | ? | Current low |
| 0.5 | ? | ? | Current medium |
| 0.7 | ? | ? | Conservative |
| 0.8 | ? | ? | Very conservative |

### Optimal Threshold Criteria

Find threshold that maximizes:
```
F1 = 2 * accuracy * (1 - abstention_rate) / (accuracy + (1 - abstention_rate))
```

---

## Evidence Request Calibration

### When to Request Evidence

The system should request evidence when:
- Confidence is in medium range (0.3-0.7)
- Evidence would reduce uncertainty
- Cost of delay is acceptable

### Value Estimation

```
evidence_value = ambiguity * 0.4 + risk * 0.4 + (1 - memory_confidence) * 0.2
```

If evidence_value > threshold: request evidence

### Threshold Sweep

| Evidence Threshold | Request Rate | Downstream Accuracy |
|-------------------|--------------|---------------------|
| 0.3 | ? | ? |
| 0.4 | ? | ? |
| 0.5 | ? | ? |
| 0.6 | ? | ? |
| 0.7 | ? | ? |

---

## Memory Calibration

### When Memory Helps

Phase 3 results:
- Task A: 0% benefit (memory doesn't help)
- Task B: +53% benefit (memory helps significantly)

### Memory Utility Estimation

```
memory_value = relevance * task_benefit_rate - contamination_risk
```

If memory_value > threshold: use memory

### Top-K Selection

| Relevance | Top-K |
|-----------|-------|
| > 0.8 | 8-10 |
| 0.6-0.8 | 5-7 |
| 0.4-0.6 | 3-5 |
| < 0.4 | 0-2 |

---

## Calibration Artifacts

### Per-Run Output

```json
{
  "calibration": {
    "ece": 0.085,
    "reliability_curve": [
      {"confidence": 0.3, "accuracy": 0.33},
      {"confidence": 0.6, "accuracy": 0.50},
      {"confidence": 0.9, "accuracy": 1.0}
    ],
    "optimal_thresholds": {
      "proceed": 0.8,
      "evidence": 0.5,
      "abstain": 0.3
    }
  }
}
```

---

## Completion Criteria

### Minimum
- [ ] ECE computed for each run
- [ ] Reliability curves generated
- [ ] Threshold sweeps completed

### Strong
- [ ] SafeHold rate reduced from 67%
- [ ] Evidence requests improve downstream accuracy
- [ ] Memory gating reduces harm on Task A

### Exceptional
- [ ] ECE < 0.1
- [ ] All thresholds calibrated per-task
- [ ] Calibration generalizes across seeds
