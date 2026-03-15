# Phase 4 Objective

## Mission

**Make GM-OS selectively intelligent about its own internal capabilities.**

The system should decide, per episode and per state:
- When to use memory
- When to ignore memory
- When to trigger SafeHold
- When to request more evidence
- When to attempt repair
- When to adapt thresholds or policies
- When a simpler route is better

---

## Phase 4 Objective Statement

By the end of Phase 4, the project should be able to say:

> GM-OS hosts calibrated GMI processes that selectively use memory, SafeHold, repair, and evidence-gathering under governance, improving robustness and guardrails across at least three task regimes without unacceptable accuracy loss or complexity debt.

---

## What Phase 4 Must Prove

### 1. Selective feature use beats always-on feature use

- Gated memory > always-on memory
- Calibrated SafeHold > blunt SafeHold
- Targeted repair > generic repair or no repair

### 2. Uncertainty is handled intelligently

- Estimate confidence
- Estimate downside risk
- Abstain or gather evidence when appropriate
- Commit when confidence is sufficient

### 3. The substrate generalizes beyond two tasks

Add one more task or shifted regime (Task C).

### 4. New complexity earns its keep

Every feature must answer:
- What metric improved?
- What guardrail improved?
- What latency/cost increased?
- Is the trade worth it?

### 5. Decision policy is explicit

The system should behave like:
> "These mechanisms activate under these conditions."

Not:
> "All knobs on, good luck."

---

## Phase 2-3 Summary

| Phase | What Was Proven |
|-------|-----------------|
| Phase 2 | Governance adds measurable value (+12%) |
| Phase 3 | Substrate supports two tasks; Memory helps Task B (+53%), not Task A (0%) |

### Phase 3 Limitations Carried Forward
- Memory is not universally helpful
- SafeHold can hurt accuracy when overused
- Adaptation and repair exist but are not value-demonstrated

---

## Phase 4 Completion Criteria

### Minimum Completion
- [ ] Gated memory outperforms always-on memory in at least one regime
- [ ] Calibrated SafeHold reduces harmful overuse
- [ ] Task C or shifted regime is operational
- [ ] Repeated-seed evaluation supports selective-policy benefit

### Strong Completion
- [ ] Selective substrate beats always-on on combined utility
- [ ] Evidence-request mode adds measurable value
- [ ] Repair becomes useful on at least one failure class
- [ ] Memory harm rate drops materially

### Exceptional Completion
- [ ] Selective policy improves both performance and guardrails
- [ ] Calibration is demonstrably good
- [ ] System chooses right internal behavior under different conditions

---

## Key Insight

**Phase 4 is where the project learns restraint.**

The big lesson from Phases 2-3:
> A capability existing is not the same as a capability being useful.

The next breakthrough is not "more features."
It's:
> The substrate learns when NOT to use its own features.
