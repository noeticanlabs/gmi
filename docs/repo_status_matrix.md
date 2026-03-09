# Repository Status Matrix

This document tracks the implementation status of GM-OS/GMI concepts against the canonical specifications.

## Status Legend

| Status | Meaning |
|--------|---------|
| ✅ Implemented | Fully implemented per spec |
| ⚠️ Partial | Implemented but needs work |
| 🔄 Experimental | Basic structure, needs full implementation |
| ❌ Missing | Not yet implemented |
| 📋 Legacy | Prototype code, deprecated |

## GM-OS Kernel

| Concept | Spec File | Implementation | Test | Status |
|---------|-----------|----------------|------|--------|
| FullSubstrateState | gmos_canon_spec.md | `gmos.kernel.substrate_state` | - | ✅ Implemented |
| OperationalMode | gmos_canon_spec.md | `gmos.kernel.substrate_state` | - | ✅ Implemented |
| Moreau-projected dynamics | gmos_canon_spec.md | `gmos.kernel.continuous_dynamics` | - | ✅ Implemented |
| AdmissibleSet | gmos_canon_spec.md | `gmos.kernel.continuous_dynamics` | - | ✅ Implemented |
| AbsorbingBoundary | gmos_canon_spec.md | `gmos.kernel.continuous_dynamics` | - | ✅ Implemented |
| BudgetRouter | gmos_canon_spec.md | `gmos.kernel.budget_router` | test_kernel.py | ✅ Implemented |
| KernelScheduler | gmos_canon_spec.md | `gmos.kernel.scheduler` | test_kernel.py | ⚠️ Partial |
| HashChainLedger | gmos_canon_spec.md | `gmos.kernel.hash_chain` | - | ✅ Implemented |
| OplaxVerifier | gmos_canon_spec.md | `gmos.kernel.verifier` | test_kernel.py | ⚠️ Partial |
| Receipt | gmos_canon_spec.md | `gmos.kernel.receipt` | - | ✅ Implemented |
| Theorem Suite | gmos_canon_spec.md | `gmos.kernel.theorems` | - | ⚠️ Partial |

## GMI Agent

| Concept | Spec File | Implementation | Test | Status |
|---------|-----------|----------------|------|--------|
| GMIPotential | gmi_canon_spec.md | `gmos.agents.gmi.potential` | test_gmi.py | ✅ Implemented |
| Tension Law | gmi_canon_spec.md | `gmos.agents.gmi.tension_law` | - | ✅ Implemented |
| CognitiveState | gmi_canon_spec.md | `gmos.agents.gmi.state` | test_gmi.py | ✅ Implemented |
| AffectiveState | gmi_canon_spec.md | `gmos.agents.gmi.affective_state` | - | ✅ Implemented |
| PolicySelection | gmi_canon_spec.md | `gmos.agents.gmi.policy_selection` | - | ⚠️ Partial |
| Execution Loop | gmi_canon_spec.md | `gmos.agents.gmi.execution_loop` | - | ✅ Implemented |
| Evolution Loop | gmi_canon_spec.md | `gmos.agents.gmi.evolution_loop` | - | ✅ Implemented |
| Semantic Loop | gmi_canon_spec.md | `gmos.agents.gmi.semantic_loop` | - | ✅ Implemented |

## Sensory Manifold

| Concept | Spec File | Implementation | Test | Status |
|---------|-----------|----------------|------|--------|
| SensoryState | gmos_canon_spec.md | `gmos.sensory.manifold` | - | ✅ Implemented |
| Anchor Authority | gmos_canon_spec.md | `gmos.sensory.anchors` | - | ✅ Implemented |
| Sensory Fusion | gmos_canon_spec.md | `gmos.sensory.fusion` | - | ⚠️ Partial |
| Salience | gmos_canon_spec.md | `gmos.sensory.salience` | - | ⚠️ Partial |

## Memory Manifold

| Concept | Spec File | Implementation | Test | Status |
|---------|-----------|----------------|------|--------|
| Workspace | gmos_canon_spec.md | `gmos.memory.workspace` | - | ✅ Implemented |
| EpisodicArchive | gmos_canon_spec.md | `gmos.memory.archive` | - | ✅ Implemented |
| Budget Costs | gmos_canon_spec.md | `gmos.memory.budget_costs` | - | ✅ Implemented |
| Consolidation | gmos_canon_spec.md | `gmos.memory.consolidation` | - | ⚠️ Partial |
| Replay | gmos_canon_spec.md | `gmos.memory.replay` | - | ⚠️ Partial |

## Action Layer

| Concept | Spec File | Implementation | Test | Status |
|---------|-----------|----------------|------|--------|
| Commitment | gmos_canon_spec.md | `gmos.action.commitment` | - | ✅ Implemented |
| External I/O | gmos_canon_spec.md | `gmos.action.external_io` | - | ✅ Implemented |
| Replenishment | gmos_canon_spec.md | `gmos.action.replenishment` | - | ✅ Implemented |

## Experimental Agents

| Agent | Status | Notes |
|-------|--------|-------|
| NSAgent | 🔄 Experimental | Navier-Stokes GMI |
| PhysicsAgent | 🔄 Experimental | Physics-based agent |
| PlannerAgent | 🔄 Experimental | Planning agent |
| SymbolicAgent | 🔄 Experimental | Symbolic reasoning |

## Repository Structure

| Directory | Status | Notes |
|-----------|--------|-------|
| `gmos/src/gmos/` | ✅ Implemented | Canonical source of truth |
| `gmos/tests/` | ⚠️ Partial | Needs more tests |
| `gmos/experiments/` | 🔄 Experimental | Basic structure |
| `core/` | 📋 Legacy | See LEGACY.md |
| `memory/` | 📋 Legacy | See LEGACY.md |
| `ledger/` | 📋 Legacy | See LEGACY.md |
| `runtime/` | 📋 Legacy | See LEGACY.md |

## Last Updated

2026-03-09 (Agent loops refactored to use canonical GM-OS imports)
