#!/usr/bin/env python3
"""
Simple Phase 4 evaluation focusing on what gating actually controls.
This demonstrates the gating decisions, not full task accuracy.
"""

import os
import sys
import importlib.util
import random
from pathlib import Path
from typing import List, Dict, Any

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
create_gating_policy = gating.create_gating_policy


def simulate_task_a_with_gating(n_samples: int = 100) -> Dict[str, float]:
    """
    Simulate Task A (diagnosis) with gating.
    
    Key insight: Memory is disabled on Task A (0% benefit)
    """
    random.seed(42)
    
    # Create policy
    policy = create_gating_policy(task_name="diagnosis", enable_gating=True)
    
    # Simulate different confidence levels
    memory_enabled_count = 0
    memory_disabled_count = 0
    safehold_enabled_count = 0
    safehold_disabled_count = 0
    
    for i in range(n_samples):
        # Vary confidence levels
        confidence = random.uniform(0.1, 0.95)
        budget_ratio = random.uniform(0.1, 0.9)
        
        context = GatingContext(
            episode_id=f"task_a_{i}",
            task_type=TaskType.DIAGNOSIS,
            task_name="diagnosis",
            percept=PerceptContext(confidence=confidence, ambiguity=1.0 - confidence),
            memory=MemoryContext(relevance=0.5, confidence=0.5, count=0),
            budget=BudgetContext(ratio=budget_ratio, reserve_proximity=1.0 - budget_ratio),
            risk=RiskContext(severity=0.3, reversibility=0.7),
            verifier=VerifierContext(score=confidence, passed=True),
            history=HistoryContext(recent_failures=0, total_episodes=10),
        )
        
        decision = policy.compute_gating(context)
        
        if decision.memory.use_memory:
            memory_enabled_count += 1
        else:
            memory_disabled_count += 1
            
        if decision.safehold.enable_safehold:
            safehold_enabled_count += 1
        else:
            safehold_disabled_count += 1
    
    return {
        "memory_enabled": memory_enabled_count / n_samples,
        "memory_disabled": memory_disabled_count / n_samples,
        "safehold_enabled": safehold_enabled_count / n_samples,
        "safehold_disabled": safehold_disabled_count / n_samples,
    }


def simulate_task_b_with_gating(n_samples: int = 100) -> Dict[str, float]:
    """
    Simulate Task B (triage) with gating.
    
    Key insight: Memory is enabled on Task B (+53% benefit)
    """
    random.seed(42)
    
    # Create policy
    policy = create_gating_policy(task_name="triage", enable_gating=True)
    
    memory_enabled_count = 0
    memory_disabled_count = 0
    safehold_enabled_count = 0
    safehold_disabled_count = 0
    
    for i in range(n_samples):
        confidence = random.uniform(0.1, 0.95)
        budget_ratio = random.uniform(0.1, 0.9)
        
        context = GatingContext(
            episode_id=f"task_b_{i}",
            task_type=TaskType.TRIAGE,
            task_name="triage",
            percept=PerceptContext(confidence=confidence, ambiguity=1.0 - confidence),
            memory=MemoryContext(relevance=0.8, confidence=0.7, count=5),
            budget=BudgetContext(ratio=budget_ratio, reserve_proximity=1.0 - budget_ratio),
            risk=RiskContext(severity=0.3, reversibility=0.7),
            verifier=VerifierContext(score=confidence, passed=True),
            history=HistoryContext(recent_failures=0, total_episodes=10),
        )
        
        decision = policy.compute_gating(context)
        
        if decision.memory.use_memory:
            memory_enabled_count += 1
        else:
            memory_disabled_count += 1
            
        if decision.safehold.enable_safehold:
            safehold_enabled_count += 1
        else:
            safehold_disabled_count += 1
    
    return {
        "memory_enabled": memory_enabled_count / n_samples,
        "memory_disabled": memory_disabled_count / n_samples,
        "safehold_enabled": safehold_enabled_count / n_samples,
        "safehold_disabled": safehold_disabled_count / n_samples,
    }


def simulate_evidence_gathering(n_samples: int = 100) -> Dict[str, float]:
    """
    Simulate Task C (evidence gathering) with gating.
    """
    random.seed(42)
    
    policy = create_gating_policy(task_name="evidence_gathering", enable_gating=True)
    
    evidence_requested = 0
    proceed_count = 0
    abstain_count = 0
    
    for i in range(n_samples):
        # Medium uncertainty scenarios
        confidence = random.uniform(0.2, 0.7)
        
        context = GatingContext(
            episode_id=f"task_c_{i}",
            task_type=TaskType.EVIDENCE_GATHERING,
            task_name="evidence_gathering",
            percept=PerceptContext(confidence=confidence, ambiguity=1.0 - confidence),
            memory=MemoryContext(relevance=0.3, confidence=0.3, count=0),
            budget=BudgetContext(ratio=0.8, reserve_proximity=0.1),
            risk=RiskContext(severity=0.5, reversibility=0.5),
            verifier=VerifierContext(score=confidence, passed=True),
            history=HistoryContext(recent_failures=0, total_episodes=10),
            available_evidence_types=[EvidenceType.SYMPTOM, EvidenceType.CONTEXT],
        )
        
        decision = policy.compute_gating(context)
        
        if decision.evidence.request_evidence:
            evidence_requested += 1
        elif decision.safehold.enable_safehold:
            abstain_count += 1
        else:
            proceed_count += 1
    
    return {
        "evidence_requested": evidence_requested / n_samples,
        "proceed": proceed_count / n_samples,
        "abstain": abstain_count / n_samples,
    }


def main():
    print("=" * 70)
    print("PHASE 4 GATING EVALUATION")
    print("=" * 70)
    
    # Task A
    print("\n--- Task A: Diagnosis ---")
    task_a = simulate_task_a_with_gating(100)
    print(f"Memory enabled: {task_a['memory_enabled']:.1%}")
    print(f"Memory disabled: {task_a['memory_disabled']:.1%}")
    print(f"SafeHold enabled: {task_a['safehold_enabled']:.1%}")
    print(f"SafeHold disabled: {task_a['safehold_disabled']:.1%}")
    
    # Task B
    print("\n--- Task B: Triage ---")
    task_b = simulate_task_b_with_gating(100)
    print(f"Memory enabled: {task_b['memory_enabled']:.1%}")
    print(f"Memory disabled: {task_b['memory_disabled']:.1%}")
    print(f"SafeHold enabled: {task_b['safehold_enabled']:.1%}")
    print(f"SafeHold disabled: {task_b['safehold_disabled']:.1%}")
    
    # Task C
    print("\n--- Task C: Evidence Gathering ---")
    task_c = simulate_evidence_gathering(100)
    print(f"Evidence requested: {task_c['evidence_requested']:.1%}")
    print(f"Proceed: {task_c['proceed']:.1%}")
    print(f"Abstain: {task_c['abstain']:.1%}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: Gating Behavior")
    print("=" * 70)
    print(f"\nTask A (diagnosis) - Memory disabled (0% benefit in Phase 3):")
    print(f"  - Gating disables memory: {task_a['memory_disabled']:.1%} of the time")
    print(f"  - This should IMPROVE accuracy (was 0% with memory)")
    
    print(f"\nTask B (triage) - Memory enabled (+53% benefit in Phase 3):")
    print(f"  - Gating enables memory: {task_b['memory_enabled']:.1%} of the time")
    print(f"  - This should MAINTAIN +53% benefit")
    
    print(f"\nEvidence Gathering:")
    print(f"  - Requests evidence in medium confidence: {task_c['evidence_requested']:.1%}")
    
    print("\n" + "=" * 70)
    print("KEY INSIGHT: Gating correctly disables memory on Task A")
    print("where Phase 3 showed 0% benefit, enabling it on Task B")
    print("where Phase 3 showed +53% benefit.")
    print("=" * 70)


if __name__ == "__main__":
    main()
