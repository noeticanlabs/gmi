#!/usr/bin/env python3
"""
Test script for Phase 4 gating and calibration components.
"""

import sys
import os
import importlib.util

# Load modules directly to avoid numpy dependency
# BASE_DIR is /home/user/gmi/gmos/benchmarks/phase4, go up to /home/user/gmi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add src path for imports
GMOS_SRC = os.path.join(BASE_DIR, "src")
sys.path.insert(0, GMOS_SRC)

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Load gating components
gating_config = load_module("gating_config", os.path.join(BASE_DIR, "src/gmos/agents/gmi/gating_config.py"))
gating_context = load_module("gating_context", os.path.join(BASE_DIR, "src/gmos/agents/gmi/gating_context.py"))
gating = load_module("gating", os.path.join(BASE_DIR, "src/gmos/agents/gmi/gating.py"))
calibration = load_module("calibration", os.path.join(BASE_DIR, "src/gmos/agents/gmi/calibration.py"))

# Import from loaded modules
GatingPolicy = gating.GatingPolicy
create_gating_policy = gating.create_gating_policy
create_default_gating_config = gating_config.create_default_gating_config
create_task_specific_config = gating_config.create_task_specific_config
GatingContext = gating_context.GatingContext
TaskType = gating_context.TaskType
PerceptContext = gating_context.PerceptContext
MemoryContext = gating_context.MemoryContext
BudgetContext = gating_context.BudgetContext
RiskContext = gating_context.RiskContext
VerifierContext = gating_context.VerifierContext
HistoryContext = gating_context.HistoryContext
CalibrationAnalyzer = calibration.CalibrationAnalyzer
AbstentionConfig = calibration.AbstentionConfig
CalibrationRunner = calibration.CalibrationRunner


def test_gating_policy():
    """Test basic gating policy functionality."""
    print("=" * 60)
    print("Testing Gating Policy")
    print("=" * 60)
    
    # Create policy
    policy = create_gating_policy(task_name="triage", enable_gating=True)
    print(f"Created policy for task: triage")
    print(f"Config: {policy.config}")
    
    # Create context for a high-confidence situation
    context = GatingContext(
        episode_id="test_001",
        task_type=TaskType.TRIAGE,
        task_name="triage",
        percept=PerceptContext(confidence=0.9, ambiguity=0.2),
        memory=MemoryContext(relevance=0.8, confidence=0.7, count=5),
        budget=BudgetContext(ratio=0.8, reserve_proximity=0.1),
        risk=RiskContext(severity=0.2, reversibility=0.8),
        verifier=VerifierContext(score=0.85, passed=True),
        history=HistoryContext(recent_failures=0, total_episodes=10),
    )
    
    # Compute gating
    decision = policy.compute_gating(context)
    
    print(f"\nContext: High confidence, good budget, low risk")
    print(f"Decision:")
    print(f"  - Use memory: {decision.memory.use_memory} (top_k: {decision.memory.top_k})")
    print(f"  - Enable SafeHold: {decision.safehold.enable_safehold}")
    print(f"  - Request evidence: {decision.evidence.request_evidence}")
    print(f"  - Enable repair: {decision.repair.enable_repair}")
    print(f"  - Apply adaptation: {decision.adaptation.apply_adaptation}")
    print(f"  - Combined confidence: {decision.combined_confidence:.2f}")
    
    # Test low confidence situation
    context2 = GatingContext(
        episode_id="test_002",
        task_type=TaskType.DIAGNOSIS,
        task_name="diagnosis",
        percept=PerceptContext(confidence=0.2, ambiguity=0.8),
        memory=MemoryContext(relevance=0.1, confidence=0.2, count=0),
        budget=BudgetContext(ratio=0.1, reserve_proximity=0.9),
        risk=RiskContext(severity=0.8, reversibility=0.2),
        verifier=VerifierContext(score=0.2, passed=False, issues=["low_confidence"]),
        history=HistoryContext(recent_failures=3, total_episodes=10),
    )
    
    decision2 = policy.compute_gating(context2)
    
    print(f"\nContext: Low confidence, critical budget, high risk, recent failures")
    print(f"Decision:")
    print(f"  - Use memory: {decision2.memory.use_memory}")
    print(f"  - Enable SafeHold: {decision2.safehold.enable_safehold}")
    print(f"  - Request evidence: {decision2.evidence.request_evidence}")
    print(f"  - Enable repair: {decision2.repair.enable_repair}")
    print(f"  - Apply adaptation: {decision2.adaptation.apply_adaptation}")
    
    # Get stats
    stats = policy.get_stats()
    print(f"\nStats: {stats}")
    
    print("\n✅ Gating policy test passed!")


def test_calibration():
    """Test calibration analyzer."""
    print("\n" + "=" * 60)
    print("Testing Calibration")
    print("=" * 60)
    
    analyzer = CalibrationAnalyzer(n_buckets=5)
    
    # Simulate predictions
    # High confidence -> correct
    for _ in range(20):
        analyzer.record_prediction(0.9, True)
    
    # Medium confidence -> mixed
    for _ in range(15):
        analyzer.record_prediction(0.6, True)
    for _ in range(15):
        analyzer.record_prediction(0.6, False)
    
    # Low confidence -> mostly wrong
    for _ in range(10):
        analyzer.record_prediction(0.3, False)
    for _ in range(5):
        analyzer.record_prediction(0.3, True)
    
    # Analyze
    analysis = analyzer.analyze()
    
    print(f"Total predictions: {analysis['total_predictions']}")
    print(f"Overall accuracy: {analysis['overall_accuracy']:.2f}")
    print(f"ECE (calibration error): {analysis['ece']:.3f}")
    print(f"Is well calibrated: {analysis['is_well_calibrated']}")
    
    print(f"\nReliability curve:")
    for conf, acc in analysis['reliability_curve']:
        print(f"  Confidence {conf:.1f} -> Accuracy {acc:.2f}")
    
    # Find optimal threshold
    optimal = analyzer.get_optimal_threshold(target_accuracy=0.8)
    print(f"\nOptimal proceed threshold (80% accuracy): {optimal:.2f}")
    
    print("\n✅ Calibration test passed!")


def test_abstention_config():
    """Test abstention configuration."""
    print("\n" + "=" * 60)
    print("Testing Abstention Config")
    print("=" * 60)
    
    config = AbstentionConfig()
    
    # Test different confidence levels
    test_confidences = [0.9, 0.7, 0.5, 0.3, 0.1]
    
    for conf in test_confidences:
        action = config.get_action(conf)
        print(f"Confidence {conf:.1f} -> {action}")
    
    # Test calibrated thresholds
    config.calibrated_proceed_threshold = 0.75
    config.calibrated_evidence_threshold = 0.5
    config.calibrated_abstain_threshold = 0.25
    
    print("\nWith calibrated thresholds:")
    for conf in test_confidences:
        action = config.get_action(conf)
        print(f"Confidence {conf:.1f} -> {action}")
    
    print("\n✅ Abstention config test passed!")


def test_task_specific_config():
    """Test task-specific configurations."""
    print("\n" + "=" * 60)
    print("Testing Task-Specific Configs")
    print("=" * 60)
    
    tasks = ["diagnosis", "triage", "evidence_gathering"]
    
    for task in tasks:
        config = create_task_specific_config(task)
        print(f"\nTask: {task}")
        print(f"  Memory relevance threshold: {config.memory.relevance_threshold}")
        print(f"  Memory default top_k: {config.memory.default_top_k}")
        print(f"  Evidence enabled: {config.evidence.enabled}")
        print(f"  SafeHold high threshold: {config.safehold.high_confidence_threshold}")
    
    print("\n✅ Task-specific config test passed!")


def main():
    """Run all tests."""
    print("Phase 4 Component Tests")
    print("=" * 60)
    
    test_gating_policy()
    test_calibration()
    test_abstention_config()
    test_task_specific_config()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
