# Repository Canonical Structure

This document explains the canonical source of truth in this repository.

## Decision: GM-OS is Canonical

The **GM-OS package** (`gmos/src/gmos/`) is the **only shipped package**.
All legacy directories are **archive-only** and should not be used for new development.

## End-State Statement

As of this decision, `gmos/src/gmos/` is the canonical package. The following directories
are **ARCHIVE ONLY** and will be removed in a future cleanup:

## Legacy Directories (Archive Only)

> ⚠️ **DO NOT USE** - These directories contain deprecated prototype code

| Directory | Status | Notes |
|-----------|--------|-------|
| `core/` | Archive Only | Legacy core implementation |
| `memory/` | Archive Only | Legacy memory implementation |
| `ledger/` | Archive Only | Legacy ledger implementation |
| `runtime/` | Archive Only | Legacy runtime implementation |
| `adapters/` | Archive Only | Legacy adapter prototypes |
| `experiments/` | Archive Only | Legacy experiment prototypes |
| `tests/` (root) | Archive Only | Legacy tests for prototype code |

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
