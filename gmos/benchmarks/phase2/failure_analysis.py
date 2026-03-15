#!/usr/bin/env python3
"""
Failure Analysis for Phase 2

Analyzes failure cases to create error taxonomy and understand
where governance adds value.
"""

import json
import sys
import os
from collections import Counter, defaultdict
from typing import List, Dict, Any

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../../src")

# Import from same directory
from task_dataset import DiagnosisDatasetGenerator
from baselines import BaselineA, BaselineB, FullGMI, run_evaluation


def analyze_failures(
    test_cases: List[Dict],
    predictions_a: List[str],
    predictions_b: List[str],
    predictions_c: List[str],
    diagnoses: List[str]
) -> Dict[str, Any]:
    """Analyze failure patterns across all systems."""
    
    results = {
        'total_cases': len(test_cases),
        'correct_by_system': {
            'A': 0,
            'B': 0,
            'C': 0
        },
        'error_taxonomy': defaultdict(lambda: defaultdict(int)),
        'confusion_matrices': {
            'A': defaultdict(lambda: defaultdict(int)),
            'B': defaultdict(lambda: defaultdict(int)),
            'C': defaultdict(lambda: defaultdict(int))
        },
        'difficulty_analysis': defaultdict(lambda: {
            'total': 0,
            'correct_A': 0,
            'correct_B': 0,
            'correct_C': 0
        })
    }
    
    for i, case in enumerate(test_cases):
        true_diagnosis = case['diagnosis']
        difficulty = case.get('difficulty', 0.5)
        symptoms = case['symptoms']
        
        # Track difficulty
        results['difficulty_analysis'][f"{int(difficulty*100)}%"]['total'] += 1
        
        # Check each system
        for system_name, pred in [('A', predictions_a[i]), ('B', predictions_b[i]), ('C', predictions_c[i])]:
            is_correct = pred == true_diagnosis
            if is_correct:
                results['correct_by_system'][system_name] += 1
                results['difficulty_analysis'][f"{int(difficulty*100)}%"][f'correct_{system_name}'] += 1
            else:
                # Build confusion matrix
                results['confusion_matrices'][system_name][true_diagnosis][pred] += 1
                
                # Categorize error
                error_type = categorize_error(true_diagnosis, pred, symptoms, diagnoses)
                results['error_taxonomy'][system_name][error_type] += 1
    
    # Calculate error rates by difficulty
    for diff_level, stats in results['difficulty_analysis'].items():
        if stats['total'] > 0:
            stats['error_rate_A'] = 1 - (stats['correct_A'] / stats['total'])
            stats['error_rate_B'] = 1 - (stats['correct_B'] / stats['total'])
            stats['error_rate_C'] = 1 - (stats['correct_C'] / stats['total'])
    
    return dict(results)


def categorize_error(
    true_diagnosis: str,
    pred_diagnosis: str,
    symptoms: List[int],
    diagnoses: List[str]
) -> str:
    """Categorize the type of error."""
    
    if true_diagnosis == pred_diagnosis:
        return "correct"
    
    # Check if predictions are from same symptom cluster
    # (similar symptom overlap)
    true_idx = diagnoses.index(true_diagnosis)
    pred_idx = diagnoses.index(pred_diagnosis)
    
    # Simple heuristic: diagnoses with similar indices might share symptoms
    # In a real system, we'd use the actual symptom overlap
    idx_diff = abs(true_idx - pred_idx)
    
    if idx_diff <= 1:
        return "near_miss"  # Very close to correct
    elif idx_diff <= 3:
        return "confusable"  # Plausible but wrong
    elif idx_diff <= 5:
        return "moderate_error"  # Clearly wrong but not random
    else:
        return "random_error"  # Completely wrong


def run_failure_analysis():
    """Run comprehensive failure analysis."""
    print("=" * 60)
    print("FAILURE ANALYSIS: ERROR TAXONOMY")
    print("=" * 60)
    
    # Generate dataset
    print("\n[1] Generating dataset...")
    generator = DiagnosisDatasetGenerator(
        n_diagnoses=10,
        n_symptoms=20,
        seed=42
    )
    dataset = generator.generate_dataset(n_train=1000, n_test=200)
    
    train = dataset['train']
    test = dataset['test']
    diagnoses = dataset['diagnoses']
    diagnosis_symptoms = dataset['diagnosis_symptoms']
    
    print(f"  Train cases: {len(train)}")
    print(f"  Test cases: {len(test)}")
    
    # Run all systems and collect predictions
    print("\n[2] Running systems and collecting predictions...")
    
    system_a = BaselineA(diagnoses)
    predictions_a = []
    for case in test:
        result = system_a.diagnose(case['symptoms'], train)
        predictions_a.append(result.predicted)
    
    system_b = BaselineB(diagnoses, diagnosis_symptoms, budget_limit=100)
    predictions_b = []
    for case in test:
        result = system_b.diagnose(case['symptoms'], train)
        predictions_b.append(result.predicted)
    
    system_c = FullGMI(diagnoses, diagnosis_symptoms, budget_limit=100, reserve_floor=0.15)
    predictions_c = []
    for case in test:
        result = system_c.diagnose(case['symptoms'], train)
        predictions_c.append(result.predicted)
    
    # Analyze failures
    print("\n[3] Analyzing failure patterns...")
    analysis = analyze_failures(test, predictions_a, predictions_b, predictions_c, diagnoses)
    
    # Print results
    print("\n" + "=" * 60)
    print("OVERALL PERFORMANCE")
    print("=" * 60)
    for system in ['A', 'B', 'C']:
        correct = analysis['correct_by_system'][system]
        total = analysis['total_cases']
        accuracy = correct / total
        print(f"System {system}: {correct}/{total} correct ({accuracy:.1%})")
    
    # Error taxonomy
    print("\n" + "=" * 60)
    print("ERROR TAXONOMY")
    print("=" * 60)
    
    for system in ['A', 'B', 'C']:
        print(f"\nSystem {system}:")
        errors = analysis['error_taxonomy'][system]
        total_errors = sum(errors.values())
        
        if total_errors > 0:
            print(f"  Total errors: {total_errors}")
            for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
                pct = count / total_errors * 100
                print(f"    {error_type:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Difficulty analysis
    print("\n" + "=" * 60)
    print("DIFFICULTY ANALYSIS")
    print("=" * 60)
    
    for diff_level, stats in sorted(analysis['difficulty_analysis'].items()):
        print(f"\nDifficulty {diff_level}:")
        print(f"  Cases: {stats['total']}")
        print(f"  System A: {stats['correct_A']} correct ({1-stats['error_rate_A']:.1%})")
        print(f"  System B: {stats['correct_B']} correct ({1-stats['error_rate_B']:.1%})")
        print(f"  System C: {stats['correct_C']} correct ({1-stats['error_rate_C']:.1%})")
    
    # Governance value analysis
    print("\n" + "=" * 60)
    print("GOVERNANCE VALUE ANALYSIS")
    print("=" * 60)
    
    # Cases where C succeeds but B fails
    c_success_b_fail = 0
    b_success_c_fail = 0
    both_fail = 0
    both_succeed = 0
    
    for i, case in enumerate(test):
        true = case['diagnosis']
        c_correct = predictions_c[i] == true
        b_correct = predictions_b[i] == true
        
        if c_correct and not b_correct:
            c_success_b_fail += 1
        elif b_correct and not c_correct:
            b_success_c_fail += 1
        elif not c_correct and not b_correct:
            both_fail += 1
        else:
            both_succeed += 1
    
    print(f"\nCases where C succeeds but B fails: {c_success_b_fail}")
    print(f"Cases where B succeeds but C fails: {b_success_c_fail}")
    print(f"Cases where both fail: {both_fail}")
    print(f"Cases where both succeed: {both_succeed}")
    
    net_advantage = c_success_b_fail - b_success_c_fail
    print(f"\nNet governance advantage: {net_advantage:+d} cases")
    
    # Save results
    output_path = "/home/user/gmi/gmos/benchmarks/phase2/failure_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    run_failure_analysis()
