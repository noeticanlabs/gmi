# Repository Canonical Structure

This document explains the canonical source of truth in this repository.

## Decision: GM-OS is Canonical

The **GM-OS package** (`gmos/src/gmos/`) is the canonical implementation.

## Legacy Directories

The following directories contain **deprecated prototype code**:
- `core/` - Legacy core implementation
- `memory/` - Legacy memory implementation  
- `ledger/` - Legacy ledger implementation
- `runtime/` - Legacy runtime implementation
- `adapters/` - Legacy adapter prototypes
- `experiments/` - Legacy experiment prototypes
- `tests/` (root) - Legacy tests for prototype code

Each legacy directory has a `LEGACY.md` file explaining its status.

## Canonical Directories

### GM-OS Package
```
gmos/src/gmos/
├── kernel/          # Kernel (scheduler, substrate, budget, etc.)
├── agents/gmi/      # GMI Agent implementation
├── memory/          # Memory manifold
├── sensory/         # Sensory manifold
├── symbolic/        # Symbolic reasoning
└── action/          # Action interfaces
```

### GM-OS Tests
```
gmos/tests/
```

### GM-OS Experiments
```
gmos/experiments/
```

### Canonical Documentation
```
docs/
├── gmos_canon_spec.md    # GM-OS specification
├── gmi_canon_spec.md     # GMI specification
└── canon_spec_index.md   # Spec index
```

## Migration

All new development should occur in `gmos/src/gmos/`. Legacy directories will eventually be removed or archived.

See `docs/gmos_canon_spec.md` for the formal specification.
