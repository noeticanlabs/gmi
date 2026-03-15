# Phase 3 Cleanup Plan

## Issues to Fix

### 1. Path Handling
- `run_eval.py` - crashes when saving results.json
- `test_components.py` - broken paths for imports

### 2. Mode Machine Integration
- Invalid transitions: `deliberate -> deliberate`, `deliberate -> recall`
- Mode machine not reset per episode

### 3. Documentation Status
- `phase3_task_b_spec.md` says "Status: Draft"
- `phase3_eval_protocol.md` says "Status: Draft"
- `phase3_status_matrix.md` says "Complete"
- Contradiction needs resolution

### 4. SafeHold Overactivity
- Full system: 39% accuracy
- No SafeHold: 64% accuracy
- SafeHold rate: 67%
- SafeHold appears to hurt accuracy significantly

### 5. Adaptation Value
- Full: 39%
- No adaptation: 39%
- No measurable value yet

## Fix Plan

### Priority 1: Path Handling (Critical)
- Use `Path(__file__).resolve().parent` for repo-relative paths
- Fix `run_eval.py` results save path
- Fix `test_components.py` import paths

### Priority 2: Mode Machine Reset
- Reset mode machine at start of each episode
- Ensure transitions follow valid state machine

### Priority 3: SafeHold Calibration
- Current threshold: 0.7 confidence
- Too aggressive - triggering on 67% of episodes
- Need threshold sweep: 0.5, 0.6, 0.7, 0.8, 0.9
- Analyze by ambiguity level

### Priority 4: Documentation Update
- Update specs to reflect actual status
- Mark what is implemented vs value-demonstrated

### Priority 5: Repeated Trials
- Run 10-seed evaluation
- Compute statistical significance
- Generate confidence intervals

## Execution Order

1. Fix `test_components.py` paths
2. Fix `run_eval.py` paths and mode machine reset
3. Run SafeHold threshold sweep
4. Update documentation status
5. Run repeated-seed evaluation
