#!/usr/bin/env python3
"""
Simple test to verify gating decisions are being made correctly.
"""

import os
import sys
import importlib.util
from pathlib import Path

# BASE_DIR is /home/user/gmi
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load gating components
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

gating_path = BASE_DIR / "src/gmos/agents/gmi/gating.py"
gating_context_path = BASE_DIR / "src/gmos/agents/gmi/gating_context.py"
gating_config_path = BASE_DIR / "src/gmos/agents/gmi/gating_config.py"

gating = load_module("gating", str(gating_path))
gating_context = load_module("gating_context", str(gating_context_path))
gating_config = load_module("gating_config", str(gating_config_path))

# Import classes
GatingPolicy = gating.GatingPolicy
GatingContext = gating_context.GatingContext
PerceptContext = gating_context.PerceptContext
MemoryContext = gating_context.MemoryContext
BudgetContext = gating_context.BudgetContext
RiskContext = gating_context.RiskContext
VerifierContext = gating_context.VerifierContext
HistoryContext = gating_context.HistoryContext
TaskType = gating_context.TaskType
EvidenceType = gating_context.EvidenceType


def test_memory_gating():
    """Test that gating correctly decides memory use."""
    print("=" * 60)
    print("Testing Memory Gating")
    print("=" * 60)
    
    # Test 1: Task A - memory should be disabled (0% benefit)
    print("\n--- Task A (Diagnosis) ---")
    policy_a = gating.create_gating_policy(task_name="diagnosis", enable_gating=True)
    
    # High memory relevance but task has 0% benefit
    context_a = GatingContext(
        episode_id="test_a",
        task_type=TaskType.DIAGNOSIS,
        task_name="diagnosis",
        percept=PerceptContext(confidence=0.8, ambiguity=0.2),
        memory=MemoryContext(relevance=0.9, confidence=0.8, count=5),
        budget=BudgetContext(ratio=0.8, reserve_proximity=0.1),
        risk=RiskContext(severity=0.2, reversibility=0.8),
        verifier=VerifierContext(score=0.8, passed=True),
        history=HistoryContext(recent_failures=0, total_episodes=10),
    )
    
    decision_a = policy_a.compute_gating(context_a)
    print(f"Memory use: {decision_a.memory.use_memory}")
    print(f"Reasoning: {decision_a.memory.reasoning}")
    print(f"Expected: False (memory harmful on diagnosis)")
    
    # Test 2: Task B - memory should be enabled (53% benefit)
    print("\n--- Task B (Triage) ---")
    policy_b = gating.create_gating_policy(task_name="triage", enable_gating=True)
    
    context_b = GatingContext(
        episode_id="test_b",
        task_type=TaskType.TRIAGE,
        task_name="triage",
        percept=PerceptContext(confidence=0.8, ambiguity=0.2),
        memory=MemoryContext(relevance=0.9, confidence=0.8, count=5),
        budget=BudgetContext(ratio=0.8, reserve_proximity=0.1),
        risk=RiskContext(severity=0.2, reversibility=0.8),
        verifier=VerifierContext(score=0.8, passed=True),
        history=HistoryContext(recent_failures=0, total_episodes=10),
    )
    
    decision_b = policy_b.compute_gating(context_b)
    print(f"Memory use: {decision_b.memory.use_memory}")
    print(f"Reasoning: {decision_b.memory.reasoning}")
    print(f"Expected: True (memory helpful on triage)")


def test_safehold_gating():
    """Test that SafeHold gating works."""
    print("\n" + "=" * 60)
    print("Testing SafeHold Gating")
    print("=" * 60)
    
    policy = gating.create_gating_policy(task_name="diagnosis", enable_gating=True)
    
    # Test high confidence - SafeHold should be disabled
    print("\n--- High Confidence ---")
    context_high = GatingContext(
        episode_id="high_conf",
        task_type=TaskType.DIAGNOSIS,
        task_name="diagnosis",
        percept=PerceptContext(confidence=0.9, ambiguity=0.1),
        memory=MemoryContext(relevance=0.5, confidence=0.5, count=0),
        budget=BudgetContext(ratio=0.9, reserve_proximity=0.0),
        risk=RiskContext(severity=0.1, reversibility=0.9),
        verifier=VerifierContext(score=0.9, passed=True),
        history=HistoryContext(recent_failures=0, total_episodes=10),
    )
    
    decision_high = policy.compute_gating(context_high)
    print(f"SafeHold enabled: {decision_high.safehold.enable_safehold}")
    print(f"Reasoning: {decision_high.safehold.reasoning}")
    print(f"Expected: False (high confidence)")
    
    # Test low confidence - SafeHold should be enabled
    print("\n--- Low Confidence ---")
    context_low = GatingContext(
        episode_id="low_conf",
        task_type=TaskType.DIAGNOSIS,
        task_name="diagnosis",
        percept=PerceptContext(confidence=0.2, ambiguity=0.8),
        memory=MemoryContext(relevance=0.1, confidence=0.1, count=0),
        budget=BudgetContext(ratio=0.9, reserve_proximity=0.0),
        risk=RiskContext(severity=0.8, reversibility=0.2),
        verifier=VerifierContext(score=0.2, passed=True),
        history=HistoryContext(recent_failures=0, total_episodes=10),
    )
    
    decision_low = policy.compute_gating(context_low)
    print(f"SafeHold enabled: {decision_low.safehold.enable_safehold}")
    print(f"Reasoning: {decision_low.safehold.reasoning}")
    print(f"Expected: True (low confidence)")
    
    # Test critical budget - SafeHold should be enabled
    print("\n--- Critical Budget ---")
    context_budget = GatingContext(
        episode_id="budget_critical",
        task_type=TaskType.DIAGNOSIS,
        task_name="diagnosis",
        percept=PerceptContext(confidence=0.8, ambiguity=0.2),
        memory=MemoryContext(relevance=0.5, confidence=0.5, count=0),
        budget=BudgetContext(ratio=0.1, reserve_proximity=0.9),
        risk=RiskContext(severity=0.5, reversibility=0.5),
        verifier=VerifierContext(score=0.8, passed=True),
        history=HistoryContext(recent_failures=0, total_episodes=10),
    )
    
    decision_budget = policy.compute_gating(context_budget)
    print(f"SafeHold enabled: {decision_budget.safehold.enable_safehold}")
    print(f"Reasoning: {decision_budget.safehold.reasoning}")
    print(f"Expected: True (budget critical)")


def test_evidence_gating():
    """Test that evidence request gating works."""
    print("\n" + "=" * 60)
    print("Testing Evidence Request Gating")
    print("=" * 60)
    
    policy = gating.create_gating_policy(task_name="evidence_gathering", enable_gating=True)
    
    # Test medium confidence - evidence request should trigger
    print("\n--- Medium Confidence ---")
    context = GatingContext(
        episode_id="medium_conf",
        task_type=TaskType.EVIDENCE_GATHERING,
        task_name="evidence_gathering",
        percept=PerceptContext(confidence=0.5, ambiguity=0.5),
        memory=MemoryContext(relevance=0.3, confidence=0.3, count=0),
        budget=BudgetContext(ratio=0.8, reserve_proximity=0.1),
        risk=RiskContext(severity=0.5, reversibility=0.5),
        verifier=VerifierContext(score=0.5, passed=True),
        history=HistoryContext(recent_failures=0, total_episodes=10),
        available_evidence_types=[EvidenceType.SYMPTOM, EvidenceType.CONTEXT],
    )
    
    decision = policy.compute_gating(context)
    print(f"Request evidence: {decision.evidence.request_evidence}")
    print(f"Evidence type: {decision.evidence.evidence_type}")
    print(f"Reasoning: {decision.evidence.reasoning}")
    print(f"Expected: True (medium confidence)")


def main():
    print("Gating Policy Evaluation Test")
    print("=" * 60)
    
    test_memory_gating()
    test_safehold_gating()
    test_evidence_gating()
    
    print("\n" + "=" * 60)
    print("ALL GATING TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
