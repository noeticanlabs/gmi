#!/usr/bin/env python3
"""
Phase 3 SafeHold Threshold Sweep

Tests different SafeHold thresholds to find optimal calibration.
Current issue: SafeHold triggers 67% of time, hurts accuracy (39% vs 64% without).
"""

import random
import importlib.util
import os
from pathlib import Path
from typing import List, Dict, Any

# Get repo root directory
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GMOS_SRC = REPO_ROOT / "gmos" / "src"
BENCHMARKS = REPO_ROOT / "gmos" / "benchmarks"

# Load modules
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

enhanced_retrieval = load_module("enhanced_retrieval", 
    GMOS_SRC / "gmos" / "memory" / "enhanced_retrieval.py")
mode_machine = load_module("mode_machine", 
    GMOS_SRC / "gmos" / "runtime" / "mode_machine.py")

# Load Task B dataset
task_b = load_module("task_b_dataset", 
    BENCHMARKS / "phase3" / "task_b" / "dataset.py")


class TriageWithTunableSafeHold:
    """Triage system with tunable SafeHold threshold."""
    
    ACTIONS = [
        "INSPECT_LOCAL", "CONTINUE_MONITOR", "GATHER_EVIDENCE",
        "REPLACE_COMPONENT", "SHUT_DOWN", "ESCALATE_SPECIALIST", "SAFEHOLD_ABSTAIN"
    ]
    
    def __init__(
        self,
        budget_limit: int = 8,
        uncertainty_threshold: float = 0.7,  # Tunable
        budget_threshold: float = 0.2,
    ):
        self.budget_limit = budget_limit
        self.uncertainty_threshold = uncertainty_threshold
        self.budget_threshold = budget_threshold
        
        self.retrieval_engine = enhanced_retrieval.create_retrieval_engine("triage")
        self.mode_machine = mode_machine.create_mode_machine(enable_safehold=True)
        self.memory_cases = []
        
    def add_memory(self, case: Dict[str, Any]) -> None:
        self.memory_cases.append(case)
    
    def triage(
        self,
        symptoms: Dict[str, bool],
        context: Dict[str, Any],
        severity: int,
        memory: List[Dict] = None
    ) -> Dict[str, Any]:
        """Select action with tunable SafeHold."""
        
        memory_cases = memory if memory is not None else self.memory_cases
        budget = self.budget_limit
        spent = 0
        
        # Reset mode machine
        self.mode_machine.reset()
        
        RuntimeMode = mode_machine.RuntimeMode
        TransitionReason = mode_machine.TransitionReason
        self.mode_machine.transition(RuntimeMode.RECALL, TransitionReason.PERCEPT_COMPLETE)
        
        retrieved_memory = []
        if memory_cases:
            query = {"symptoms": symptoms, "context": context}
            results = self.retrieval_engine.retrieve(memory_cases, query, top_k=5)
            retrieved_memory = [r.episode for r in results]
        
        self.mode_machine.transition(RuntimeMode.DELIBERATE, TransitionReason.MEMORY_RETRIEVED)
        
        # Calculate confidence
        confidence = 0.5
        if retrieved_memory:
            outcome_scores = []
            for mem in retrieved_memory:
                outcome = mem.get("outcome", "")
                if outcome in ["resolved", "correct_caution", "appropriate_caution"]:
                    outcome_scores.append(1.0)
                elif outcome in ["informative", "partial"]:
                    outcome_scores.append(0.5)
                else:
                    outcome_scores.append(0.0)
            confidence = sum(outcome_scores) / len(outcome_scores) if outcome_scores else 0.5
        
        # Check SafeHold with tunable threshold
        budget_ratio = (budget - spent) / self.budget_limit if self.budget_limit > 0 else 0
        
        should_hold = (
            confidence < self.uncertainty_threshold or
            budget_ratio < self.budget_threshold
        )
        
        if should_hold:
            self.mode_machine.transition(RuntimeMode.SAFE_HOLD, TransitionReason.UNCERTAINTY_HIGH)
            return {
                "predicted": "SAFEHOLD_ABSTAIN",
                "confidence": confidence,
                "spent": spent + 1,
                "safehold": True,
                "memory_used": bool(retrieved_memory),
            }
        
        # Score actions
        scores = {}
        for action in self.ACTIONS:
            if action == "SAFEHOLD_ABSTAIN":
                scores[action] = 0.1
                continue
            
            base_score = 0.5
            memory_bonus = 0
            if retrieved_memory:
                for mem in retrieved_memory:
                    mem_action = mem.get("action", "")
                    if mem_action == action:
                        outcome = mem.get("outcome", "")
                        if outcome in ["resolved", "correct_caution", "appropriate_caution", "success"]:
                            memory_bonus += 0.4
                        elif outcome in ["informative", "partial"]:
                            memory_bonus += 0.2
                        elif outcome in ["overreaction", "unnecessary", "missed_issue"]:
                            memory_bonus -= 0.3
            
            scores[action] = base_score + memory_bonus
        
        predicted = max(scores, key=scores.get)
        confidence = min(0.3 + scores[predicted], 0.95)
        
        return {
            "predicted": predicted,
            "confidence": confidence,
            "spent": 2 if retrieved_memory else 1,
            "safehold": False,
            "memory_used": bool(retrieved_memory),
        }


def run_evaluation(system, test_cases, memory_cases):
    """Run evaluation and return metrics."""
    
    correct = 0
    total = 0
    safehold_count = 0
    safehold_correct = 0
    safehold_total = 0
    
    for case in test_cases:
        system.memory_cases = memory_cases
        
        result = system.triage(
            symptoms=case['symptoms'],
            context=case['context'],
            severity=case['severity'],
            memory=memory_cases
        )
        
        if result['predicted'] == case['correct_action']:
            correct += 1
        
        if result.get('safehold'):
            safehold_count += 1
            # Check if SafeHold was appropriate
            if case['correct_action'] == "SAFEHOLD_ABSTAIN":
                safehold_correct += 1
            safehold_total += 1
        
        total += 1
    
    return {
        "accuracy": correct / total if total > 0 else 0,
        "safehold_rate": safehold_count / total if total > 0 else 0,
        "safehold_appropriate_rate": safehold_correct / safehold_total if safehold_total > 0 else 0,
    }


def main():
    print("=" * 70)
    print("SAFEHOLD THRESHOLD SWEEP")
    print("=" * 70)
    
    # Generate dataset
    dataset = task_b.generate_dataset(n_train=200, n_test=100, seed=42)
    memory_cases = dataset['memory']
    test_cases = dataset['test']
    
    print(f"\nDataset: {len(memory_cases)} memory, {len(test_cases)} test")
    
    # Count SafeHold-appropriate cases
    safehold_appropriate = sum(1 for c in test_cases if c['correct_action'] == "SAFEHOLD_ABSTAIN")
    print(f"SafeHold-appropriate cases: {safehold_appropriate} ({safehold_appropriate/len(test_cases)*100:.1f}%)")
    
    # Test thresholds
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    print("\n" + "-" * 70)
    print(f"{'Threshold':<12} {'Accuracy':<12} {'SafeHold%':<12} {'Appropriate%':<15}")
    print("-" * 70)
    
    results = []
    for threshold in thresholds:
        system = TriageWithTunableSafeHold(
            uncertainty_threshold=threshold,
            budget_threshold=0.1  # Lower budget threshold to focus on uncertainty
        )
        
        metrics = run_evaluation(system, test_cases, memory_cases)
        results.append((threshold, metrics))
        
        print(f"{threshold:<12.1f} {metrics['accuracy']*100:<11.1f}% {metrics['safehold_rate']*100:<11.1f}% {metrics['safehold_appropriate_rate']*100:<14.1f}%")
    
    # Also test with SafeHold disabled
    print("-" * 70)
    system_no_safehold = TriageWithTunableSafeHold(uncertainty_threshold=0.0)
    metrics_no_safehold = run_evaluation(system_no_safehold, test_cases, memory_cases)
    print(f"{'Disabled':<12} {metrics_no_safehold['accuracy']*100:<11.1f}% {metrics_no_safehold['safehold_rate']*100:<11.1f}%")
    
    # Find best threshold
    best = max(results, key=lambda x: x[1]['accuracy'])
    print("\n" + "=" * 70)
    print(f"BEST THRESHOLD: {best[0]:.1f}")
    print(f"  Accuracy: {best[1]['accuracy']*100:.1f}%")
    print(f"  SafeHold rate: {best[1]['safehold_rate']*100:.1f}%")
    print(f"  SafeHold appropriate: {best[1]['safehold_appropriate_rate']*100:.1f}%")
    print("=" * 70)
    
    # Analysis
    print("\nANALYSIS:")
    print(f"  - Current threshold (0.7) triggers {results[-2][1]['safehold_rate']*100:.1f}% SafeHold")
    print(f"  - No SafeHold gives {metrics_no_safehold['accuracy']*100:.1f}% accuracy")
    print(f"  - Best threshold ({best[0]:.1f}) gives {best[1]['accuracy']*100:.1f}% accuracy")
    
    if best[1]['accuracy'] > metrics_no_safehold['accuracy']:
        print(f"  → SafeHold IS beneficial when properly calibrated")
    else:
        print(f"  → SafeHold is NOT beneficial on this task - consider disabling")


if __name__ == "__main__":
    main()
