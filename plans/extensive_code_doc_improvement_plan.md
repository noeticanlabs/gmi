# Extensive Code and Documentation Improvement Plan

## Executive Summary

Based on comprehensive review of the GM-OS codebase, this plan addresses documentation and code improvements. The codebase already has **excellent docstrings** in most core modules (tension_law.py, constraints.py, verifier.py, substrate_state.py), but there are specific gaps to address.

---

## Current State Assessment

### Architecture Pillars (Already Implemented)

1. **Substrate Law: GM-OS Kernel** - WELDED
   - Ontology (`process_table.py`)
   - Metabolism (`budget_router.py`)
   - Time (`scheduler.py`)
   - Causality (step/continuous_dynamics)

2. **Inhabitant: GMI Organism** - POPULATED
   - Character shell and affective budget
   - Cognitive loops (evolution, execution, semantic)

3. **Epistemological Perimeter** - IMPLEMENTED
   - Receipt/ledger system
   - Thermodynamic inequality enforcement

4. **Physics Bridge (NS Agent)** - STUBBED/HYBRID

---

## Identified Gaps

### Gap 1: End-to-End Kernel "Breath Test"
**Status**: Missing

Per the review, need a test that:
1. Instantiates a stub `P_GMI`
2. Registers it in `ProcessTable`
3. Gives 1.0 Budget via `BudgetRouter`
4. Submits a single NOOP or basic perception proposal
5. Verifies: Scheduler picks it up → Verifier approves → Router deducts ADMIN_TICK_COST → Ledger emits receipt

**Location**: Should be in `gmos/tests/kernel/test_kernel.py`

### Gap 2: Coh-IL Evaluator
**Status**: Nascent

The notebooks call for a strictly parsed "algebra of intents" (Coh-IL). The exact parser and payload normalizer is nascent.

**Recommendation**: Create design spec in `docs/`

### Gap 3: Sensory/Memory World-Weld
**Status**: Missing external I/O hooks

`gmos/sensory/manifold.py` and `gmos/memory/archive.py` lack external I/O hooks for real sensor telemetry.

**Recommendation**: Create design spec for I/O connectors

### Gap 4: Module Cross-References
**Status**: Partial

Some `__init__.py` files could have better cross-references between modules.

---

## Task Breakdown

### Phase 1: Critical - End-to-End Test

- [ ] **T1.1**: Create `test_kernel_breath_test()` in `gmos/tests/kernel/test_kernel.py`
  - Instantiate ProcessTable
  - Register P_GMI stub
  - Register budget via BudgetRouter
  - Submit NOOP proposal
  - Verify receipt generation

### Phase 2: Documentation Enhancements

- [ ] **T2.1**: Add Breath Test documentation to `docs/kernel_testing.md`
- [ ] **T2.2**: Create Coh-IL Evaluator design spec `docs/cohil_evaluator_spec.md`
- [ ] **T2.3**: Create Sensory/Memory I/O design spec `docs/world_weld_spec.md`
- [ ] **T2.4**: Enhance kernel `__init__.py` with cross-references
- [ ] **T2.5**: Create API reference index in `docs/api/`

### Phase 3: Code Quality

- [ ] **T3.1**: Add missing type hints to any legacy code
- [ ] **T3.2**: Verify all tests pass
- [ ] **T3.3**: Check for any stub implementations that need completion

---

## Module Documentation Status

| Module | Status | Notes |
|--------|--------|-------|
| `kernel/substrate_state.py` | ✅ Excellent | Full spec references |
| `kernel/verifier.py` | ✅ Excellent | Reserve law docs |
| `kernel/continuous_dynamics.py` | ✅ Good | Projected dynamics |
| `kernel/scheduler.py` | ✅ Good | Multi-clock docs |
| `kernel/budget_router.py` | ✅ Good | Conservation laws |
| `agents/gmi/tension_law.py` | ✅ Excellent | Full residual docs |
| `agents/gmi/constraints.py` | ✅ Excellent | Projection engine |
| `memory/workspace.py` | ✅ Good | Phantom states |
| `sensory/manifold.py` | ✅ Good | Chart structures |
| `symbolic/glyph_space.py` | ✅ Good | Glyph coordinates |

---

## Implementation Priority

1. **Immediate**: Create Breath Test (validates the architecture boots)
2. **High**: Enhance cross-references in `__init__.py` files
3. **Medium**: Create design specs for gaps (Coh-IL, World-Weld)
4. **Low**: API reference documentation

---

## Notes for Implementation

- The codebase is remarkably well-documented already
- Most "missing" documentation is actually design/spec work for gaps
- The "Breath Test" is the critical validation step
- Lean 4 integration is noted but out of scope for this iteration
