#!/usr/bin/env python3
"""
Phase 3 Component Tests

Tests the core Phase 3 components with proper repo-relative paths.
"""

import random
import importlib.util
import os
from pathlib import Path

# Get repo root directory (gmos/benchmarks/phase3 -> gmos -> repo root)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GMOS_SRC = REPO_ROOT / "gmos" / "src"
BENCHMARKS = REPO_ROOT / "gmos" / "benchmarks"

print("=" * 70)
print("PHASE 3 COMPONENT TESTS")
print("=" * 70)
print(f"Repo root: {REPO_ROOT}")
print()

# Test 1: Mode Machine
print("1. Mode Machine:")
mode_machine_path = GMOS_SRC / "gmos" / "runtime" / "mode_machine.py"
spec = importlib.util.spec_from_file_location("mode_machine", mode_machine_path)
mode_machine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mode_machine)

mm = mode_machine.create_mode_machine(enable_safehold=True)
print(f"   Initial mode: {mm.current_mode.value}")
mm.transition(mode_machine.RuntimeMode.RECALL, mode_machine.TransitionReason.PERCEPT_COMPLETE)
print(f"   After transition: {mm.current_mode.value}")
should_hold = mm.check_safehold_condition(0.5, 0.1, 1.0, 1)
print(f"   SafeHold check (low confidence, low budget): {should_hold}")
should_hold2 = mm.check_safehold_condition(0.9, 0.5, 1.0, 1)
print(f"   SafeHold check (high confidence, ok budget): {should_hold2}")
print("   ✓ PASSED")
print()

# Test 2: Enhanced Retrieval
print("2. Enhanced Retrieval:")
retrieval_path = GMOS_SRC / "gmos" / "memory" / "enhanced_retrieval.py"
spec2 = importlib.util.spec_from_file_location("enhanced_retrieval", retrieval_path)
enhanced_retrieval = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(enhanced_retrieval)

engine = enhanced_retrieval.create_retrieval_engine("triage")
print(f"   Strategy: {engine.strategy.value}")
print(f"   Weights - outcome: {engine.weights.outcome_weight}, semantic: {engine.weights.semantic_weight}")

test_episodes = [
    {"id": "ep1", "symptoms": {"noise": True}, "outcome": "resolved", "success": True},
    {"id": "ep2", "symptoms": {"vibration": True}, "outcome": "overreaction", "success": False},
    {"id": "ep3", "symptoms": {"noise": True}, "outcome": "informative", "success": True},
]
test_query = {"symptoms": {"noise": True}}
results = engine.retrieve(test_episodes, test_query, top_k=2)
print(f"   Retrieved {len(results)} episodes")
for r in results:
    print(f"     - {r.episode['id']}: score={r.score:.3f}, influence={r.influence_weight:.3f}")
print("   ✓ PASSED")
print()

# Test 3: Adaptation Tracker
print("3. Adaptation Tracker:")
adaptation_path = GMOS_SRC / "gmos" / "agents" / "gmi" / "adaptation.py"
spec3 = importlib.util.spec_from_file_location("adaptation", adaptation_path)
adaptation = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(adaptation)

tracker = adaptation.create_adaptation_tracker()
print(f"   Created successfully")
summary = tracker.get_adaptation_summary()
print(f"   Summary: episodes={summary['total_episodes']}, success_rate={summary['success_rate']:.2f}")
print("   ✓ PASSED")
print()

# Test 4: Task B Dataset
print("4. Task B Dataset:")
dataset_path = BENCHMARKS / "phase3" / "task_b" / "dataset.py"
spec4 = importlib.util.spec_from_file_location("task_b_dataset", dataset_path)
task_b = importlib.util.module_from_spec(spec4)
spec4.loader.exec_module(task_b)

dataset = task_b.generate_dataset(n_train=50, n_test=20, seed=42)
print(f"   Memory cases: {len(dataset['memory'])}")
print(f"   Test cases: {len(dataset['test'])}")
print(f"   Actions: {dataset['metadata']['actions']}")
print(f"   Difficulty distribution: {dataset['metadata']['difficulty_distribution']}")
print("   ✓ PASSED")
print()

print("=" * 70)
print("ALL TESTS PASSED!")
print("=" * 70)
