# GMOS Full Functionality Plan

## Executive Summary
The GMOS (GMI Management and Operating System) codebase has 174+ classes but suffers from import/configuration issues. The goal is to make GMOS fully functional so GMI can run inside it.

## Current Status

### Working Components
- Legacy GMI (core/, memory/, ledger/, runtime/) - Fully functional
- 174+ classes defined across GMOS modules
- Test suite passes for legacy GMI

### Broken Components
1. **Import Issues**: Circular imports between kernel modules
2. **Missing Aliases**: Some expected classes not exported
3. **Configuration Gaps**: Incomplete module initialization

---

## Phase 1: Fix Import Issues (Priority: Critical)

### Issue 1.1: AffectiveBudgetManager Missing
**Location**: `gmos/src/gmos/agents/gmi/hosted_agent.py` line 37
**Problem**: Imports `AffectiveBudgetManager` but only `AffectiveBudgetLaw` and `AffectiveBudgetCalculator` exist
**Fix**: Add alias to `affective_budget.py`

```python
# In affective_budget.py, add:
AffectiveBudgetManager = AffectiveBudgetCalculator  # Alias for compatibility
```

### Issue 1.2: HostedAgent Class Mismatch
**Location**: `gmos/src/gmos/agents/gmi/hosted_agent.py` line 64
**Problem**: Class is `HostedGMIAgent` but code expects `HostedAgent`
**Fix**: Add alias in hosted_agent.py

### Issue 1.3: Kernel Import Chain
**Location**: `gmos/src/gmos/kernel/substrate_state.py` line 37
**Problem**: Imports `KernelScheduler` which may not be ready
**Fix**: Already partially fixed with lazy import pattern

---

## Phase 2: Module Exports (Priority: High)

### 2.1 Fix gmos/__init__.py
The main __init__.py should expose working modules. Current issue: tries to import everything at startup.

**Current**: 
```python
from gmos.kernel import state_host, scheduler, ...
from gmos.agents.gmi import hosted_agent
```

**Fix**: Use lazy imports or expose only working submodules

### 2.2 Fix agents/__init__.py
**Fix**: Ensure GMIAgent is properly exported

### 2.3 Fix agents/gmi/__init__.py
**Status**: Already partially fixed - needs testing

---

## Phase 3: Core Functionality (Priority: High)

### 3.1 GMI Execution Loop
**Location**: `gmos/src/gmos/agents/gmi/execution_loop.py`
**Function**: `run_gmi_engine()`
**Test**: Verify it runs and produces receipts

### 3.2 GMI Evolution Loop
**Location**: `gmos/src/gmos/agents/gmi/evolution_loop.py`
**Function**: `run_gmi_evolution()`
**Test**: Verify policy evolution works

### 3.3 Hosted Agent
**Location**: `gmos/src/gmos/agents/gmi/hosted_agent.py`
**Class**: `HostedGMIAgent`
**Test**: Verify agent can process steps

---

## Phase 4: Kernel Integration (Priority: Medium)

### 4.1 Scheduler
**File**: `gmos/src/gmos/kernel/scheduler.py`
**Status**: Class `KernelScheduler` exists - needs verification

### 4.2 Budget Router
**File**: `gmos/src/gmos/kernel/budget_router.py`
**Status**: Class `BudgetRouter` exists - needs verification

### 4.3 Receipt Engine
**File**: `gmos/src/gmos/kernel/receipt_engine.py`
**Status**: Class `ReceiptEngine` exists - needs verification

### 4.4 Verifier
**File**: `gmos/src/gmos/kernel/verifier.py`
**Status**: Class `OplaxVerifier` exists - needs verification

---

## Phase 5: Testing & Validation (Priority: High)

### 5.1 Unit Tests for Each Module
Create tests for:
- [ ] agents/gmi/execution_loop.py
- [ ] agents/gmi/evolution_loop.py
- [ ] agents/gmi/hosted_agent.py
- [ ] kernel/scheduler.py
- [ ] kernel/budget_router.py
- [ ] kernel/verifier.py

### 5.2 Integration Tests
- [ ] GMI inside GMOS full loop
- [ ] Receipt generation
- [ ] Budget enforcement
- [ ] State persistence

### 5.3 Test Files to Update
- `tests/test_gmi_in_gmos.py` - Enable skipped tests

---

## Implementation Order

```
Week 1: Phase 1 (Import Fixes)
├── Fix affective_budget.py export
├── Fix hosted_agent.py class name
└── Test basic imports

Week 2: Phase 2 (Module Exports)
├── Fix gmos/__init__.py
├── Fix agents/__init__.py
└── Test module discovery

Week 3: Phase 3 (Core Functionality)
├── Verify execution_loop.py
├── Verify evolution_loop.py
└── Verify hosted_agent.py

Week 4: Phase 4 (Kernel)
├── Test scheduler
├── Test budget router
└── Test receipt engine

Week 5: Phase 5 (Testing)
├── Enable test_gmi_in_gmos.py
├── Add integration tests
└── Full system validation
```

---

## Dependencies

### External Dependencies
- numpy >= 1.24.0
- pytest >= 7.0.0

### Internal Dependencies (GMOS → Legacy)
- core/state.py (State, Instruction)
- core/potential.py (GMIPotential)
- ledger/receipt.py (Receipt)
- memory/workspace.py (Workspace)

---

## Success Criteria

1. ✅ `from gmos.agents.gmi import execution_loop` works
2. ✅ `run_gmi_engine()` executes without errors
3. ✅ Receipts are generated
4. ✅ All 14 skipped tests in test_gmi_in_gmos.py pass
5. ✅ No circular import errors on startup

---

## Files to Modify

| File | Change Type | Priority |
|------|-------------|----------|
| gmos/src/gmos/agents/gmi/affective_budget.py | Add alias | Critical |
| gmos/src/gmos/agents/gmi/hosted_agent.py | Add alias | Critical |
| gmos/src/gmos/__init__.py | Lazy imports | High |
| gmos/src/gmos/agents/__init__.py | Fix exports | High |
| tests/test_gmi_in_gmos.py | Enable tests | Medium |

---

## Notes

- The codebase has significant implementation - the issues are primarily around module organization and exports
- Legacy GMI (core/, memory/, etc.) is fully working and should remain as the reference implementation
- GMOS is meant to be a higher-level orchestration layer
