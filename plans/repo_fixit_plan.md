# Repo Fix-It Plan

Based on the audit, this is the comprehensive plan to fix the issues and converge the codebase.

---

## Phase 1: Make GM-OS Installable & Testable

### 1.1 Fix GM-OS Package Import Wiring
- [ ] Verify editable install works: `pip install -e gmos/`
- [ ] Confirm tests can import `gmos`, `gmos.kernel`, `gmos.agents.gmi`
- [ ] Fix any import errors in test setup

### 1.2 Add GM-OS Smoke Test
- [ ] Create `gmos/tests/test_smoke.py`
- [ ] Test: `import gmos`
- [ ] Test: `import gmos.kernel`
- [ ] Test: `import gmos.agents.gmi`
- [ ] Test: `import gmos.agents.gmi.tension_law`

### 1.3 Run GM-OS Tests
- [ ] Run: `cd gmos && pytest tests/`
- [ ] Fix any failing tests

---

## Phase 2: Declare Canonical Tree

### 2.1 Choose Canonical Source
- **Decision**: GM-OS package (`gmos/src/gmos/`) is canonical
- **Legacy**: Root tree (`core/`, `memory/`, `ledger/`, `runtime/`) marked as prototype

### 2.2 Create Legacy Markers
- [ ] Add `core/LEGACY.md` explaining this is the old prototype
- [ ] Add `memory/LEGACY.md`
- [ ] Add `ledger/LEGACY.md`
- [ ] Add `runtime/LEGACY.md`

### 2.3 Create Compatibility Shims (if needed)
- [ ] Add shim in `gmos/src/gmos/agents/gmi/` that imports from root if needed

---

## Phase 3: Remove/Quarantine Stubs

### 3.1 Fix Action Layer
- [ ] Review `gmos/src/gmos/action/commitment.py`
- [ ] Review `gmos/src/gmos/action/external_io.py`
- [ ] Review `gmos/src/gmos/action/replenishment.py`
- [ ] Either implement properly OR move to `gmos/src/gmos/action/experimental/`

### 3.2 Fix Secondary Agents
- [ ] Move `gmos/src/gmos/agents/ns_agent.py` → `experimental/`
- [ ] Move `gmos/src/gmos/agents/physics_agent.py` → `experimental/`
- [ ] Move `gmos/src/gmos/agents/planner_agent.py` → `experimental/`
- [ ] Move `gmos/src/gmos/agents/symbolic_agent.py` → `experimental/`

### 3.3 Fix Theorem Suite
- [ ] Implement `GMOSTheorems.verify_all()` in `gmos/src/gmos/kernel/theorems.py`
- [ ] Or remove the method if not ready

### 3.4 Fix Memory Consolidation
- [ ] Replace placeholders in `gmos/src/gmos/memory/consolidation.py`
- [ ] Replace placeholders in `gmos/src/gmos/memory/operators.py`
- [ ] Replace placeholders in `gmos/src/gmos/memory/relevance.py`

---

## Phase 4: Fix Packaging Metadata

### 4.1 Update Root pyproject.toml
- [ ] Fix packages list: include `memory` and `adapters`
- [ ] Use proper package discovery

### 4.2 Clean Cache Files
- [ ] Add `__pycache__/` to `.gitignore`
- [ ] Remove existing `.pyc` files
- [ ] Add cleanup step to workflow

---

## Phase 5: Align Docs with Implementation

### 5.1 Add Status Markers to Canon Docs
- [ ] Update `docs/gmos_canon_spec.md` with status markers
- [ ] Update `docs/gmi_canon_spec.md` with status markers

### 5.2 Create Status Matrix
- [ ] Create `docs/repo_status_matrix.md`
- Columns: Concept | Spec File | Implementation | Test | Status

---

## Phase 6: Unify Receipt/Verifier

### 6.1 Choose Canonical Receipt Stack
- **Decision**: GM-OS kernel receipt is canonical
- **Legacy**: Root `ledger/` is prototype

### 6.2 Freeze Receipt Semantics
- [ ] Document state hash rules
- [ ] Document chain digest rules
- [ ] Document reject codes
- [ ] Document serialization rules

### 6.3 Make Verifier Match Docs
- [ ] Update `gmos/src/gmos/kernel/verifier.py` to support:
  - schema/version checks
  - policy hash checks
  - chain digest linkage
  - state hash linkage
  - reserve checks
  - anchor conflict checks

---

## Phase 7: GMI Receipt Schemas

### 7.1 Create GMI Receipt Schemas
- [ ] Create `gmos/src/gmos/kernel/gmi_receipts.py`
- [ ] Define: `gmi.receipt.infer.v1`
- [ ] Define: `gmi.receipt.retrieve.v1`
- [ ] Define: `gmi.receipt.repair.v1`
- [ ] Define: `gmi.receipt.branch.v1`
- [ ] Define: `gmi.receipt.plan.v1`
- [ ] Define: `gmi.receipt.act_prepare.v1`

### 7.2 Each Receipt Includes
- schema_id, version
- process_id
- state_hash_prev, state_hash_next
- chain_digest_prev, chain_digest_next
- spend_summary, defect_summary
- anchor_summary, contradiction_summary, goal_summary
- mode, metrics, payload

---

## Phase 8: Strengthen Tests

### 8.1 GM-OS Smoke Tests
- [ ] Package import test
- [ ] Kernel import test
- [ ] GMI agent import test
- [ ] Tension law import + evaluation test

### 8.2 Receipt-Chain Roundtrip Tests
- [ ] Receipt encode/decode
- [ ] Hash-chain update determinism
- [ ] Same input => same decision
- [ ] Modified receipt => reject
- [ ] Modified digest => reject

### 8.3 Reserve-Floor Tests
- [ ] GM-OS budget reserve violation test
- [ ] GMI local reserve violation test

### 8.4 Doc-to-Code Tests
- [ ] Verify classes exist from docs
- [ ] Verify theorem methods callable
- [ ] Verify operational modes enum exists

---

## Phase 9: Simplify Repo Architecture

### 9.1 Archive Old Plans
- [ ] Move old plans to `archive/plans/`
- [ ] Keep only active roadmap in `plans/`

### 9.2 Update README
- [ ] Explain root prototype vs GM-OS package
- [ ] State which is canonical
- [ ] Give current status of each subsystem

---

## Phase 10: Release Discipline

### 10.1 Pre-Release Checklist
- [ ] Remove cache files
- [ ] Tests run in clean environment
- [ ] Export only canonical files and active docs

---

## Summary

| Phase | Priority | Items | Estimated Effort |
|-------|----------|-------|------------------|
| 1 | P0 | 3 | Low |
| 2 | P1 | 3 | Low |
| 3 | P2 | 10 | Medium |
| 4 | P1 | 3 | Low |
| 5 | P4 | 3 | Low |
| 6 | P5 | 3 | Medium |
| 7 | P6 | 7 | Medium |
| 8 | P7 | 10 | Medium |
| 9 | P8 | 2 | Low |
| 10 | P8 | 1 | Low |

**Total: 45 items**

---

## Execution Recommendation

Do phases in order. Phase 1 (making GM-OS testable) is the critical path - without it, we can't verify any other fixes.

The single most important fix: **Make GM-OS installable, importable, and test-clean, then declare it canonical.**
