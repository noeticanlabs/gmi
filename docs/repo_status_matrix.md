# Repository Status Matrix

This document tracks the implementation status of GM-OS/GMI concepts against the canonical specifications.

## Status Legend

| Status | Meaning |
|--------|---------|
| ✅ Complete | Fully implemented per spec |
| ⚠️ Partial | Implemented but needs work |
| 🔄 Stub | Basic structure, needs full implementation |
| ❌ Missing | Not yet implemented |
| 📋 Planned | On roadmap |

## GM-OS Kernel

| Concept | Spec File | Implementation | Test | Status |
|---------|-----------|----------------|------|--------|
| FullSubstrateState | gmos_canon_spec.md | `gmos.kernel.substrate_state` | - | ✅ Complete |
| OperationalMode | gmos_canon_spec.md | `gmos.kernel.substrate_state` | - | ✅ Complete |
| Moreau-projected dynamics | gmos_canon_spec.md | `gmos.kernel.continuous_dynamics` | - | ✅ Complete |
| AdmissibleSet | gmos_canon_spec.md | `gmos.kernel.continuous_dynamics` | - | ✅ Complete |
| AbsorbingBoundary | gmos_canon_spec.md | `gmos.kernel.continuous_dynamics` | - | ✅ Complete |
| BudgetRouter | gmos_canon_spec.md | `gmos.kernel.budget_router` | test_kernel.py | ✅ Complete |
| KernelScheduler | gmos_canon_spec.md | `gmos.kernel.scheduler` | test_kernel.py | ✅ Complete |
| HashChainLedger | gmos_canon_spec.md | `gmos.kernel.hash_chain` | - | ✅ Complete |
| OplaxVerifier | gmos_canon_spec.md | `gmos.kernel.verifier` | test_kernel.py | ✅ Complete |
| Receipt | gmos_canon_spec.md | `gmos.kernel.receipt` | - | ✅ Complete |
| Theorem Suite | gmos_canon_spec.md | `gmos.kernel.theorems` | - | ✅ Complete |

## GMI Agent

| Concept | Spec File | Implementation | Test | Status |
|---------|-----------|----------------|------|--------|
| GMIPotential | gmi_canon_spec.md | `gmos.agents.gmi.potential` | - | ✅ Complete |
| Tension Law | gmi_canon_spec.md | `gmos.agents.gmi.tension_law` | - | ✅ Complete |
| CognitiveState | gmi_canon_spec.md | `gmos.agents.gmi.state` | - | ✅ Complete |
| AffectiveState | gmi_canon_spec.md | `gmos.agents.gmi.affective_state` | - | ✅ Complete |
| PolicySelection | gmi_canon_spec.md | `gmos.agents.gmi.policy_selection` | - | ✅ Complete |
| Execution Loop | gmi_canon_spec.md | `gmos.agents.gmi.execution_loop` | - | ✅ Complete |
| Evolution Loop | gmi_canon_spec.md | `gmos.agents.gmi.evolution_loop` | - | ✅ Complete |
| Semantic Loop | gmi_canon_spec.md | `gmos.agents.gmi.semantic_loop` | - | ✅ Complete |

## Sensory Manifold

| Concept | Spec File | Implementation | Test | Status |
|---------|-----------|----------------|------|--------|
| SensoryState | gmos_canon_spec.md | `gmos.sensory.manifold` | - | ✅ Complete |
| Anchor Authority | gmos_canon_spec.md | `gmos.sensory.anchors` | - | ✅ Complete |
| Sensory Fusion | gmos_canon_spec.md | `gmos.sensory.fusion` | - | ⚠️ Partial |
| Salience | gmos_canon_spec.md | `gmos.sensory.salience` | - | ⚠️ Partial |

## Memory Manifold

| Concept | Spec File | Implementation | Test | Status |
|---------|-----------|----------------|------|--------|
| Workspace | gmos_canon_spec.md | `gmos.memory.workspace` | - | ✅ Complete |
| EpisodicArchive | gmos_canon_spec.md | `gmos.memory.archive` | - | ✅ Complete |
| Budget Costs | gmos_canon_spec.md | `gmos.memory.budget_costs` | - | ✅ Complete |
| Consolidation | gmos_canon_spec.md | `gmos.memory.consolidation` | - | 🔄 Stub |
| Replay | gmos_canon_spec.md | `gmos.memory.replay` | - | ⚠️ Partial |

## Action Layer

| Concept | Spec File | Implementation | Test | Status |
|---------|-----------|----------------|------|--------|
| Commitment | gmos_canon_spec.md | `gmos.action.commitment` | - | 🔄 Stub |
| External I/O | gmos_canon_spec.md | `gmos.action.external_io` | - | 🔄 Stub |
| Replenishment | gmos_canon_spec.md | `gmos.action.replenishment` | - | 🔄 Stub |

## Experimental Agents

| Agent | Status | Notes |
|-------|--------|-------|
| NSAgent | 🔄 Stub | Navier-Stokes GMI |
| PhysicsAgent | 🔄 Stub | Physics-based agent |
| PlannerAgent | 🔄 Stub | Planning agent |
| SymbolicAgent | 🔄 Stub | Symbolic reasoning |

## Repository Structure

| Directory | Status | Notes |
|-----------|--------|-------|
| `gmos/src/gmos/` | ✅ Canonical | Source of truth |
| `gmos/tests/` | ⚠️ Partial | Needs more tests |
| `gmos/experiments/` | ⚠️ Partial | Basic structure |
| `core/` | 📋 Legacy | See LEGACY.md |
| `memory/` | 📋 Legacy | See LEGACY.md |
| `ledger/` | 📋 Legacy | See LEGACY.md |
| `runtime/` | 📋 Legacy | See LEGACY.md |

## Last Updated

2026-03-09
