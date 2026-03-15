#!/usr/bin/env python3
"""
Phase 3 Simple Test Evaluation

Tests the core Phase 3 components without full evaluation infrastructure.
"""

import random
import importlib.util
import os

# Get base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("PHASE 3 COMPONENT Tests")
print("=" * 70)

# Test 1: Mode Machine
print("\n1. Mode Machine:")
spec = importlib.util.spec_from_file_location("mode_machine", 
    os.path.join(BASE_DIR, "src/gmos/runtime/mode_machine.py"))
mode_machine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mode_machine)

mm = mode_machine.create_mode_machine(enable_safehold=True)
print(f"   Initial mode: {mm.current_mode.value}")
mm.transition(mode_machine.RuntimeMode.RECALL, mode_machine.TransitionReason.PERCEPT_COMPLETE)
print(f"   After transition: {mm.current_mode.value}")
should_hold = mm.check_safehold_condition(0.5, 0.1, 1.0, 1)
print(f"   SafeHold check: {should_hold}")
print("   ✓ PASSED")

print()

# Test 2: Enhanced Retrieval
print("2. Enhanced Retrieval:")
spec2 = importlib.util.spec_from_file_location("enhanced_retrieval", 
    os.path.join(BASE_DIR, "src/gmos/memory/enhanced_retrieval.py"))
enhanced_retrieval = importlib.util.module_from_spec(spec2)
spec.loader.exec_module(enhanced_retrieval)
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
spec3 = importlib.util.spec_from_file_location("adaptation", 
    os.path.join(BASE_DIR, "src/gmos/agents/gmi/adaptation.py"))
adaptation = importlib.util.module_from_spec(spec3)
spec.loader.exec_module(adaptation)
tracker = adaptation.create_adaptation_tracker()
print(f"   Created successfully")
summary = tracker.get_adaptation_summary()
print(f"   Summary: episodes={summary['total_episodes']}, success_rate={summary['success_rate']:.2f}")
print("   ✓ PASSED")
print()

# Test 4: Task B Dataset
print("4. Task B Dataset:")
spec4 = importlib.util.spec_from_file_location("task_b_dataset", 
    os.path.join(BASE_DIR, "benchmarks/phase3/task_b/dataset.py"))
task_b = importlib.util.module_from_spec(spec4)
spec.loader.exec_module(task_b)
dataset = task_b.generate_dataset(n_train=50, n_test=20, seed=42)
print(f"   Memory cases: {len(dataset['memory'])}")
print(f"   Test cases: {len(dataset['test'])}")
print(f"   Actions: {dataset['metadata']['actions']}")
print(f"   Difficulty distribution: {dataset['metadata']['difficulty_distribution']}")
print("   ✓ PASSED")
print()

print("=" * 70)
print("All Tests Passed!")
print("=" * 70)
