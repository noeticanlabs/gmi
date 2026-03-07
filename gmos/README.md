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
├── sensory/        # Perceptual manifold (fusion, salience, anchors)
├── memory/         # Temporal fabric (archive, workspace, replay)
├── symbolic/       # Glyph/semantic layer (binding, semantic_manifold)
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

This is Phase 1 of GM-OS reconstruction. Current status:

### ✅ Complete (Phase 1-4)
- **Kernel layer**: Core modules implemented + verified
  - state_host.py - Process state management
  - scheduler.py - Process scheduling with halt/torpor/wake support
  - budget_router.py - Budget routing and reserve enforcement
  - process_table.py - Process metadata registry
  - receipt_engine.py - Kernel event receipts
  - macro_verifier.py - Slab verification
  - verifier.py - Reserve law and velocity constraints

- **Sensory layer**: Implemented
  - manifold.py - SensoryState, ExternalChart, InternalChart
  - projection.py - World/internal state projection
  - fusion.py - Confidence-weighted multi-source fusion
  - salience.py - Novelty, relevance, surprise scoring
  - anchors.py - External validation tagging

- **Symbolic layer**: Implemented
  - glyph_space.py - Glyph coordinates and embeddings
  - semantic_manifold.py - Relation bundles, composition
  - binding.py - State-symbol grounding

- **Memory layer**: Migrated from GMI repo
- **Tests**: 19 tests passing

### ⏳ Pending (Phase 5-7)
- Phase 5: Connect one hosted GMI process natively
- Phase 6: Clean up old repo / split responsibility
- Phase 7: Test hygiene

## Installation

### Prerequisites
```bash
# Create virtual environment (recommended)
python3 -m venv gmos-env
source gmos-env/bin/activate

# Install dependencies
pip install numpy pytest
```

### Install GM-OS
```bash
cd gmos
pip install -e .
```

### Run Tests
```bash
cd gmos
PYTHONPATH=$PWD/src pytest -q tests
# Or with venv active:
pytest -q tests
```

## Development

The architecture is defined in `plans/gmos_file_creation_checklist.md`.

For the phased implementation plan, see the parent directory's documentation.

## Quick Start

```python
from gmos.kernel import StateHost, KernelScheduler, OplaxVerifier
from gmos.sensory import fusion, salience
from gmos.symbolic import semantic_manifold

# Initialize kernel components
state_host = StateHost()
scheduler = KernelScheduler()
verifier = OplaxVerifier(reserve_floor=1.0)

# Register a process
scheduler.register_process("gmi_1", mode=scheduler.ScheduleMode.SURVIVAL_CRITICAL)

# Process sensory fusion
sources = [fusion.FusionSource("camera", 0.9, 1.0, {"objects": ["box"]})]
result = fusion.fuse_modalities(sources)

# Compute salience
sal = salience.compute_salience({"objects": [{"id": 1}]})
```

## License

MIT
