# GM-OS: Glyph-Manifold Operating System

**Governed Manifold Operating Substrate for Reflective, Ledger-Bound Intelligence**

GM-OS is the operating substrate that provides:
- perceptual geometry (sensory manifold)
- state-space management (kernel)
- budget/resource scheduling
- ledger verification
- memory infrastructure
- action commitment
- inter-process coordination

## Architecture

```
gmos/
├── kernel/          # Operating substrate (ledger, scheduling, budgets)
├── sensory/        # Perceptual manifold
├── memory/         # Temporal fabric (archive, workspace, replay)
├── symbolic/       # Glyph/semantic layer
├── agents/         # Hosted processes (GMI, planners, etc.)
├── action/         # Commitment interface
├── tests/
└── experiments/
```

## Key Concepts

### GM-OS vs GMI
- **GM-OS** is the lawful substrate (like physics to biology)
- **GMI** is the governed cognitive process running on GM-OS

### Core Laws
1. **Freedom under constraint** - the only stable path
2. **Reserve preservation** - protected survival layers
3. **Oplax compositionality** - subadditive verification costs
4. **Ledger integrity** - hash-chained audit trails

## Status

This is Phase 0 of GM-OS reconstruction. Current status:
- Kernel layer: Core modules implemented
- Memory layer: Migrated from GMI repo
- Sensory layer: Placeholders (deferred)
- Symbolic layer: Placeholders (deferred)
- Agent layer: GMI integration pending

## Installation

```bash
cd gmos
pip install -e .
```

## Development

The architecture is defined in `plans/gmos_file_creation_checklist.md`.
