# Agent Loops Completion Plan

## Executive Summary

This plan addresses the completion of the three GMI Agent Loops (Execution, Evolution, and Semantic) which are currently marked as "Partial" or "Experimental" in the repository status matrix. The primary issue is that these loops contain legacy imports from `core/`, `memory/`, and `ledger/` directories that should be replaced with canonical GM-OS imports from `gmos/src/gmos/`.

---

## Current Status

### Legacy Import Dependencies Found

| File | Legacy Import | Canonical Replacement Needed |
|------|---------------|------------------------------|
| `gmos/agents/gmi/execution_loop.py` | `core.state`, `core.potential` | `gmos.agents.gmi.state`, `gmos.agents.gmi.potential` |
| `gmos/agents/gmi/evolution_loop.py` | `core.state`, `core.embedder`, `core.memory`, `ledger.oplax_verifier` | `gmos.agents.gmi.state`, `gmos.symbolic.glyph_space`, `gmos.memory`, `gmos.kernel.verifier` |
| `gmos/agents/gmi/state.py` | `core.potential` | `gmos.agents.gmi.potential` |
| `gmos/agents/gmi/affective_state.py` | `core.state` | `gmos.agents.gmi.state` |
| `gmos/agents/gmi/potential.py` | `core.memory` | `gmos.memory` |

### Status from repo_status_matrix.md

- Execution Loop: ⚠️ Partial
- Evolution Loop: ⚠️ Partial  
- Semantic Loop: 🔄 Experimental (essentially empty - 12 lines)

---

## Implementation Plan

### Phase 1: Create Canonical Replacements

#### 1.1 Create GlyphEmbedder in gmos/symbolic/

**Location**: `gmos/src/gmos/symbolic/glyph_embedder.py`

**Purpose**: Replace legacy `GMI_Embedder` from `core.embedder`

**Requirements**:
- Interface compatible with existing evolution_loop usage
- Use existing `glyph_space.py` structures
- Methods: `embed(text) -> np.ndarray`, `vocab` property
- Support INFER, EXPLORE, INVENT operations

#### 1.2 Create Canonical State Wrapper

**Location**: `gmos/src/gmos/agents/gmi/state.py` (update existing)

**Changes Needed**:
- Replace `from core.potential import GMIPotential` with local or gmos.kernel import
- Ensure `Instruction`, `Proposal` classes work with canonical modules
- Add factory methods for creating states

#### 1.3 Create MemoryManifold Wrapper

**Location**: `gmos/src/gmos/memory/memory_adapter.py`

**Purpose**: Provide compatible interface for evolution_loop's `memory.read_curvature()` calls

**Requirements**:
- Wrap `gmos.memory` modules with compatible interface
- Method: `read_curvature(x: np.ndarray) -> float`

### Phase 2: Refactor Execution Loop

**Location**: `gmos/src/gmos/agents/gmi/execution_loop.py`

**Changes**:
1. Replace `from core.state import State, Instruction, Proposal` → `from gmos.agents.gmi.state import State, Instruction, Proposal`
2. Replace `from core.potential import GMIPotential, create_potential` → `from gmos.agents.gmi.potential import GMIPotential, create_potential`
3. Replace `from gmos.kernel.verifier import OplaxVerifier` - already correct
4. Replace `from gmos.kernel.hash_chain import HashChainLedger` - already correct

### Phase 3: Refactor Evolution Loop

**Location**: `gmos/src/gmos/agents/gmi/evolution_loop.py`

**Changes**:
1. Replace legacy imports with canonical equivalents
2. Update `NoeticanProposalEngine` to use `gmos.symbolic.glyph_embedder`
3. Update `NoeticanValidationEngine` to use `gmos.kernel.verifier`
4. Ensure memory curvature integration works

### Phase 4: Implement Semantic Loop

**Location**: `gmos/src/gmos/agents/gmi/semantic_loop.py`

**Current State**: Only 12 lines, marked experimental

**Requirements from gmi_canon_spec.md**:
- Semantic loop operator: `σ: Z × M × S → S_sem`
- Maps latent state through memory to produce semantic representation
- Integrates with sensory manifold for grounded meaning

**Implementation**:
1. Import from canonical `gmos.symbolic.semantic_manifold`
2. Implement semantic processing pipeline
3. Connect to memory manifold for context

### Phase 5: Integration & Testing

#### 5.1 Create Integration Tests

**Location**: `gmos/tests/agents/gmi/test_loops.py`

**Tests Required**:
- Execution loop: end-to-end state transition with budget verification
- Evolution loop: proposal generation and validation
- Semantic loop: semantic processing pipeline
- Cross-loop: all three loops working together

#### 5.2 Verify Kernel Integration

- Scheduler integration
- Budget router integration  
- Verifier integration
- Hash chain ledger integration

### Phase 6: Documentation Update

**Location**: `docs/repo_status_matrix.md`

**Changes**:
- Update Execution Loop: ⚠️ Partial → ✅ Complete
- Update Evolution Loop: ⚠️ Partial → ✅ Complete
- Update Semantic Loop: 🔄 Experimental → ⚠️ Partial (or ✅ Complete)

---

## Technical Details

### GMI Loop Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GMI Agent                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ Execution   │    │ Evolution    │    │ Semantic     │ │
│  │ Loop        │    │ Loop         │    │ Loop         │ │
│  │             │    │              │    │              │ │
│  │ - Step-by-  │    │ - Proposal  │    │ - Meaning    │ │
│  │   step      │    │   generation│    │   extraction│ │
│  │ - Budget    │    │ - Selection │    │ - Grounding │ │
│  │   tracking  │    │ - Mutation   │    │ - Context    │ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘ │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             │                              │
│                      ┌──────▼───────┐                      │
│                      │   Kernel    │                       │
│                      │ - Verifier  │                       │
│                      │ - Scheduler │                       │
│                      │ - Budget    │                       │
│                      └─────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Key Interfaces

#### Instruction Class
```python
@dataclass
class Instruction:
    name: str
    apply: Callable[[np.ndarray], np.ndarray]
    sigma: float  # Energy cost
    kappa: float  # Allowed defect
```

#### Proposal Class
```python
@dataclass
class Proposal:
    instruction: Instruction
    x_prime: np.ndarray  # Precomputed result
```

---

## Dependencies

### Before
- `core.state` (legacy)
- `core.potential` (legacy)
- `core.embedder` (legacy)
- `core.memory` (legacy)
- `ledger.oplax_verifier` (legacy)

### After
- `gmos.agents.gmi.state` (canonical)
- `gmos.agents.gmi.potential` (canonical)
- `gmos.symbolic.glyph_embedder` (new)
- `gmos.symbolic.glyph_space` (existing)
- `gmos.memory` (canonical)
- `gmos.kernel.verifier` (canonical)
- `gmos.kernel.hash_chain` (canonical)

---

## Acceptance Criteria

1. ✅ All three loops use only canonical GM-OS imports
2. ✅ No dependencies on legacy `core/`, `memory/`, `ledger/` modules
3. ✅ Execution loop completes full cognitive cycle with budget tracking
4. ✅ Evolution loop generates and validates proposals correctly
5. ✅ Semantic loop extracts semantic representations from state
6. ✅ Integration tests pass for all three loops
7. ✅ Repository status matrix reflects completion

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing tests | Run full test suite after each change |
| Interface mismatches | Create adapter layer if needed |
| Missing functionality | Implement minimal viable interfaces first |

---

## Timeline Estimate

This is a multi-week effort requiring:
- Phase 1: 2-3 days (canonical replacements)
- Phase 2-3: 2-3 days (refactoring loops)
- Phase 4: 3-5 days (semantic loop implementation)
- Phase 5: 2-3 days (testing)
- Phase 6: 1 day (documentation)

**Total**: Approximately 10-15 days of development work.
