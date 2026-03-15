# Phase 4 Policy Gating Specification

## Overview

This document specifies the feature gating policy layer that decides when substrate features should activate.

The key insight from Phase 3: **features that always-on can hurt performance**. Gating is the solution.

---

## Gating Philosophy

### Phase 3 Lessons
- Memory helped Task B (+53%) but not Task A (0%)
- SafeHold was overactive (67% trigger rate → accuracy drop from 64% to 39%)
- Adaptation showed no value

### Phase 4 Goal
Make the substrate **selectively intelligent** about its own capabilities.

---

## Gating Inputs

For each episode or decision step, the gating policy should consider:

| Input | Type | Description |
|-------|------|-------------|
| `percept_confidence` | float | How confident is the perception layer (0-1) |
| `ambiguity_level` | float | How ambiguous is the situation (0-1) |
| `memory_relevance` | float | Estimated relevance of memory (0-1) |
| `memory_confidence` | float | How confident are retrieved memories |
| `task_difficulty` | float | Expected difficulty of this task (0-1) |
| `budget_ratio` | float | Current budget / total budget |
| `reserve_proximity` | float | How close to reserve floor (0-1) |
| `risk_severity` | float | Estimated harm if wrong (0-1) |
| `recent_failures` | int | Consecutive failures in recent episodes |
| `verifier_score` | float | Current verifier confidence |

---

## Gating Outputs

The policy produces explicit decisions:

| Output | Type | Description |
|--------|------|-------------|
| `use_memory` | bool | Whether to retrieve memory |
| `memory_top_k` | int | How many memories to retrieve (0-10) |
| `enable_safehold` | bool | Whether to enable SafeHold pathway |
| `safehold_threshold` | float | Custom threshold for this episode |
| `enable_repair` | bool | Whether to attempt repair on failure |
| `request_evidence` | bool | Whether to request more evidence |
| `evidence_type` | str | What evidence to request |
| `apply_adaptation` | bool | Whether to update adaptation weights |

---

## Gating Policy: Memory

### When to Use Memory

**Enable memory when:**
- Task type has shown memory benefit in past (e.g., Task B)
- Memory relevance score is high (>0.6)
- Current task is similar to past successful cases
- Ambiguity is high (memory can disambiguate)

**Disable memory when:**
- Task type has shown no memory benefit (e.g., Task A)
- Memory relevance is low (<0.3)
- Retrieved memories have low confidence
- Risk of memory contamination is high

### Memory Top-K Selection

| Condition | Top-K |
|-----------|-------|
| High relevance, high confidence | 5-10 |
| Medium relevance | 3-5 |
| Low relevance | 0-2 |
| High risk of noise | 0-1 |

---

## Gating Policy: SafeHold

### When to Enable SafeHold

**Enable SafeHold when:**
- Confidence is below calibrated threshold
- Budget is low (<20%)
- Risk severity is high
- Recent failures occurred
- Evidence is conflicting

**Disable SafeHold when:**
- Confidence is high (>0.8)
- Budget is healthy (>50%)
- Risk is low
- Task is time-sensitive

### Threshold Calibration

Start with heuristic thresholds, then calibrate:

```
HIGH_CONFIDENCE_THRESHOLD = 0.8
MEDIUM_CONFIDENCE_THRESHOLD = 0.5
LOW_CONFIDENCE_THRESHOLD = 0.3

if confidence > HIGH_THRESHOLD:
    action = PROCEED
elif confidence > MEDIUM_THRESHOLD:
    action = REQUEST_EVIDENCE
else:
    action = ABSTAIN
```

Calibrate these thresholds based on:
- Accuracy when proceeding at each confidence level
- SafeHold rate vs accuracy tradeoff
- Task-specific calibration curves

---

## Gating Policy: Evidence Request

### When to Request Evidence

**Request evidence when:**
- Confidence is in medium range (0.3-0.7)
- Potential value of evidence > cost of delay
- Specific evidence type would disambiguate
- Not in time-critical situation

**Don't request evidence when:**
- Confidence is already high (>0.8)
- Evidence would not help (clear case)
- Budget is too low for additional steps
- Time pressure is critical

### Evidence Type Selection

| Missing Information | Request Type |
|--------------------|--------------|
| Specific symptom | REQUEST_SYMPTOM |
| Environmental context | REQUEST_CONTEXT |
| Similar past case | REQUEST_HISTORY |
| Current state reading | REQUEST_SENSOR |

---

## Gating Policy: Repair

### When to Enable Repair

**Enable repair when:**
- Initial proposal failed verification
- Failure type is recoverable
- Budget allows for repair attempt
- Same failure hasn't occurred repeatedly

**Disable repair when:**
- Failure type is not recoverable
- Repair already attempted multiple times
- Budget is critical
- Failure indicates fundamental impossibility

---

## Gating Policy: Adaptation

### When to Apply Adaptation

**Apply adaptation when:**
- Episode resulted in clear failure
- Failure pattern is consistent
- Enough episodes have passed to establish pattern

**Don't apply adaptation when:**
- Few episodes have run
- Failure appears random
- Adaptation would cause oscillation

---

## Implementation Structure

### GatingPolicy Class

```python
class GatingPolicy:
    """Feature gating policy for selective substrate intelligence."""
    
    def __init__(
        self,
        memory_config: MemoryGatingConfig,
        safehold_config: SafeHoldGatingConfig,
        evidence_config: EvidenceGatingConfig,
        repair_config: RepairGatingConfig,
        adaptation_config: AdaptationGatingConfig
    ):
        ...
    
    def compute_gating(
        self,
        context: GatingContext
    ) -> GatingDecision:
        """
        Compute gating decision based on current context.
        
        Args:
            context: Current episode context (confidence, budget, etc.)
            
        Returns:
            GatingDecision with all feature enable/disable flags
        """
        ...
    
    def should_use_memory(self, context: GatingContext) -> MemoryGating:
        """Decide memory usage."""
        ...
    
    def should_enable_safehold(self, context: GatingContext) -> SafeHoldGating:
        """Decide SafeHold activation."""
        ...
    
    def should_request_evidence(self, context: GatingContext) -> EvidenceGating:
        """Decide evidence request."""
        ...
    
    def should_enable_repair(self, context: GatingContext) -> RepairGating:
        """Decide repair activation."""
        ...
    
    def should_apply_adaptation(self, context: GatingContext) -> AdaptationGating:
        """Decide adaptation application."""
        ...
```

### Configuration Classes

```python
@dataclass
class MemoryGatingConfig:
    relevance_threshold: float = 0.5
    confidence_threshold: float = 0.4
    task_benefit_map: Dict[str, float] = None  # Task -> benefit rate
    max_top_k: int = 10

@dataclass
class SafeHoldGatingConfig:
    confidence_threshold: float = 0.3
    budget_threshold: float = 0.2
    risk_threshold: float = 0.7
    max_consecutive_holds: int = 3

@dataclass
class EvidenceGatingConfig:
    min_confidence: float = 0.3
    max_confidence: float = 0.7
    evidence_value_threshold: float = 0.5

@dataclass
class RepairGatingConfig:
    max_attempts: int = 2
    failure_type_whitelist: List[str] = None
    budget_threshold: float = 0.3

@dataclass
class AdaptationGatingConfig:
    min_episodes: int = 5
    failure_threshold: float = 0.3
    learning_rate: float = 0.1
```

---

## Logging and Audit

Every gating decision should be logged:

```python
@dataclass
class GatingDecision:
    episode_id: str
    context: GatingContext
    decisions: Dict[str, bool]
    reasoning: Dict[str, str]  # Why each decision was made
    timestamp: float
```

---

## Calibration Process

1. **Initial thresholds**: Set from domain knowledge
2. **Run evaluation**: Collect accuracy vs confidence curves
3. **Adjust thresholds**: Tune to optimize utility
4. **Validate**: Test on held-out data
5. **Deploy**: Use calibrated thresholds

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Gated memory improvement | >0% over always-on |
| SafeHold rate | 10-30% (vs 67% in Phase 3) |
| Evidence request value | >0% improvement when used |
| Repair success rate | >30% when enabled |
| Overall utility | >always-on baseline |

---

## Files to Create

- `gmos/src/gmos/agents/gmi/gating.py` - Main gating policy
- `gmos/src/gmos/agents/gmi/gating_config.py` - Configuration classes
- `gmos/src/gmos/agents/gmi/gating_context.py` - Context structures
