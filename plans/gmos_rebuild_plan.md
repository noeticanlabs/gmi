# GM-OS Rebuild Plan

Based on the GM-OS Architecture Doc Spine and the migration checklist.

## Target Location
- New repo: `/home/user/gmi/gmos/` (subdirectory of current workspace)

## Architecture Overview

```
gmos/
├── kernel/          # Operating substrate (ledger, scheduling, budgets)
├── sensory/        # Perceptual manifold (placeholders for now)
├── memory/         # Temporal fabric (archive, workspace, replay)
├── symbolic/       # Glyph/semantic layer (placeholders)
├── agents/         # Hosted processes
│   └── gmi/        # GMI cognitive agent
├── action/         # Commitment interface (placeholders)
├── docs/           # Architecture documentation
├── tests/          # Test suite
└── experiments/   # Experiments
```

## Phased Implementation Plan

### Phase 1: Skeleton (per checklist steps 1-2)
- [ ] Create directory structure
- [ ] Add `README.md`, `pyproject.toml`, `src/gmos/__init__.py`

### Phase 2: Kernel Layer (per checklist step 4 + architecture)
- [ ] Copy from `ledger/`: hash_chain.py, receipt.py, oplax_verifier.py → verifier.py
- [ ] Add: state_host.py, scheduler.py, budget_router.py, constraint_engine.py
- [ ] Add: receipt_engine.py, macro_verifier.py, process_table.py

### Phase 3: Memory Fabric (per checklist step 5)
- [ ] Copy from `memory/`: archive.py, episode.py, workspace.py
- [ ] Copy and rename: replay_engine.py → replay.py, memory_receipts.py → receipts.py
- [ ] Copy: comparator.py, consolidation.py, operators.py, budget_costs.py

### Phase 4: Sensory Manifold (placeholders, per step 13)
- [ ] Create: manifold.py, projection.py, fusion.py, salience.py, anchors.py
- [ ] Note: Full implementation deferred

### Phase 5: Symbolic Layer (placeholders, per step 13)
- [ ] Create: glyph_space.py, semantic_manifold.py, binding.py

### Phase 6: GMI Agent (per checklist step 6)
- [ ] Copy from `core/`: state.py, potential.py, constraints.py, affective_state.py
- [ ] Copy: affective_budget.py, threat_modulation.py
- [ ] Copy from `runtime/`: policy_selection.py, evolution_loop.py
- [ ] Copy: execution_loop.py, semantic_loop.py
- [ ] Create: gmi_agent.py (main orchestrator)

### Phase 7: Action Layer (placeholders)
- [ ] Create: commitment.py, external_io.py, replenishment.py

### Phase 8: Fix Imports (per checklist step 7)
- [ ] Update all migrated files to use `gmos.*` imports

### Phase 9: Tests and Experiments (per checklist steps 9-10)
- [ ] Create test structure: tests/kernel/, tests/memory/, tests/agents/gmi/
- [ ] Copy relevant tests and fix imports
- [ ] Create experiments/gmi/ and copy experiments

### Phase 10: Install and Verify (per checklist steps 11-12)
- [ ] Run `pip install -e .`
- [ ] Verify tests pass
- [ ] Verify stress tests run
- [ ] Verify reserve law behavior
- [ ] Verify hash chain and memory replay

### Phase 11: Clean Commits (per checklist steps 14-15)
- [ ] Commit: init repo skeleton
- [ ] Commit: add kernel
- [ ] Commit: add memory
- [ ] Commit: add GMI agent
- [ ] Commit: add tests and experiments

## Key Design Decisions

1. **Move first, improve later** - Follow the checklist exactly
2. **Placeholders for deferred items** - sensory, symbolic, action modules are empty stubs
3. **Copy, don't move** - Files remain in gmi-main, copies go to gmos
4. **Import fix as separate phase** - Clean up imports after all files are copied

## Deferred Items (per checklist step 13)
- Full sensory manifold implementation
- Symbolic/glyph runtime
- GR / NS agents
- Multi-agent scheduler
- Replenishment logic beyond stubs

## Success Criteria
- GM-OS repo exists at `/home/user/gmi/gmos/`
- GMI runs inside it as a hosted agent
- Behavior matches current repo
- No major logic changed during migration
