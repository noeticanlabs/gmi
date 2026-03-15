#!/usr/bin/env python3
"""
Repeated Trials for Phase 2

Runs 10 fixed-seed evaluations to establish statistical stability.
"""

import json
import sys
import os
import math
from pathlib import Path
from typing import List, Dict, Any

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../../src")

# Import shared utilities
try:
    from __init__ import get_results_path
except ImportError:
    from pathlib import Path
    def get_results_path(filename: str) -> Path:
        return Path(__file__).resolve().parent / filename

# Import from same directory
from task_dataset import DiagnosisDatasetGenerator
from baselines import BaselineA, BaselineB, FullGMI, run_evaluation


def run_single_trial(seed: int, n_train: int = 1000, n_test: int = 200) -> Dict[str, Any]:
    """Run a single evaluation trial."""
    generator = DiagnosisDatasetGenerator(
        n_diagnoses=10,
        n_symptoms=20,
        seed=seed
    )
    dataset = generator.generate_dataset(n_train=n_train, n_test=n_test)
    
    train = dataset['train']
    test = dataset['test']
    diagnoses = dataset['diagnoses']
    diagnosis_symptoms = dataset['diagnosis_symptoms']
    
    # Run Baseline A
    from baselines import BaselineA
    system_a = BaselineA(diagnoses)
    result_a = run_evaluation(system_a, test, train)
    
    # Run Baseline B
    from baselines import BaselineB
    system_b = BaselineB(diagnoses, diagnosis_symptoms, budget_limit=100)
    result_b = run_evaluation(system_b, test, train)
    
    # Run System C
    from baselines import FullGMI
    system_c = FullGMI(diagnoses, diagnosis_symptoms, budget_limit=100, reserve_floor=0.15)
    result_c = run_evaluation(system_c, test, train)
    
    return {
        'seed': seed,
        'accuracy_a': result_a['accuracy'],
        'accuracy_b': result_b['accuracy'],
        'accuracy_c': result_c['accuracy'],
        'advantage_c_vs_b': result_c['accuracy'] - result_b['accuracy'],
        'advantage_c_vs_a': result_c['accuracy'] - result_a['accuracy'],
        'verified_rate_c': result_c['verified_rate'],
        'repair_rate_c': result_c['repair_rate'],
    }


def run_repeated_trials(n_trials: int = 10):
    """Run multiple trials and collect statistics."""
    print("=" * 60)
    print("REPEATED TRIALS: STATISTICAL STABILITY")
    print("=" * 60)
    
    results = []
    
    # Fixed seeds for reproducibility
    base_seed = 42
    seeds = [base_seed + i * 100 for i in range(n_trials)]
    
    for i, seed in enumerate(seeds):
        print(f"\nTrial {i+1}/{n_trials} (seed={seed})...")
        result = run_single_trial(seed)
        results.append(result)
        
        print(f"  A: {result['accuracy_a']:.1%}, B: {result['accuracy_b']:.1%}, C: {result['accuracy_c']:.1%}")
        print(f"  C vs B: {result['advantage_c_vs_b']:+.1%}, C vs A: {result['advantage_c_vs_a']:+.1%}")
    
    # Calculate statistics using pure Python
    acc_a = [r['accuracy_a'] for r in results]
    acc_b = [r['accuracy_b'] for r in results]
    acc_c = [r['accuracy_c'] for r in results]
    adv_c_b = [r['advantage_c_vs_b'] for r in results]
    adv_c_a = [r['advantage_c_vs_a'] for r in results]
    
    # Helper functions
    def mean(lst):
        return sum(lst) / len(lst)
    
    def std(lst):
        m = mean(lst)
        variance = sum((x - m) ** 2 for x in lst) / len(lst)
        return math.sqrt(variance)
    
    stats = {
        'n_trials': n_trials,
        'seeds': seeds,
        'baseline_a': {
            'mean': mean(acc_a),
            'std': std(acc_a),
            'min': min(acc_a),
            'max': max(acc_a),
            'per_trial': acc_a
        },
        'baseline_b': {
            'mean': mean(acc_b),
            'std': std(acc_b),
            'min': min(acc_b),
            'max': max(acc_b),
            'per_trial': acc_b
        },
        'system_c': {
            'mean': mean(acc_c),
            'std': std(acc_c),
            'min': min(acc_c),
            'max': max(acc_c),
            'per_trial': acc_c
        },
        'advantage_c_vs_b': {
            'mean': mean(adv_c_b),
            'std': std(adv_c_b),
            'min': min(adv_c_b),
            'max': max(adv_c_b),
            'positive_count': sum(1 for x in adv_c_b if x > 0),
            'per_trial': adv_c_b
        },
        'advantage_c_vs_a': {
            'mean': mean(adv_c_a),
            'std': std(adv_c_a),
            'min': min(adv_c_a),
            'max': max(adv_c_a),
            'positive_count': sum(1 for x in adv_c_a if x > 0),
            'per_trial': adv_c_a
        },
        'c_beats_b_count': sum(1 for r in results if r['accuracy_c'] > r['accuracy_b']),
        'c_beats_a_count': sum(1 for r in results if r['accuracy_c'] > r['accuracy_a']),
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("STATISTICAL SUMMARY")
    print("=" * 60)
    
    print(f"\nBaseline A:   {stats['baseline_a']['mean']:.1%} ± {stats['baseline_a']['std']:.1%}")
    print(f"Baseline B:   {stats['baseline_b']['mean']:.1%} ± {stats['baseline_b']['std']:.1%}")
    print(f"System C:     {stats['system_c']['mean']:.1%} ± {stats['system_c']['std']:.1%}")
    
    print(f"\nC vs B:       {stats['advantage_c_vs_b']['mean']:+.1%} ± {stats['advantage_c_vs_b']['std']:.1%}")
    print(f"              [{stats['advantage_c_vs_b']['min']:+.1%}, {stats['advantage_c_vs_b']['max']:+.1%}]")
    print(f"              C beats B: {stats['c_beats_b_count']}/{n_trials} trials")
    
    print(f"\nC vs A:       {stats['advantage_c_vs_a']['mean']:+.1%} ± {stats['advantage_c_vs_a']['std']:.1%}")
    print(f"              [{stats['advantage_c_vs_a']['min']:+.1%}, {stats['advantage_c_vs_a']['max']:+.1%}]")
    print(f"              C beats A: {stats['c_beats_a_count']}/{n_trials} trials")
    
    # Confidence interval for C vs B (95%)
    mean_adv = stats['advantage_c_vs_b']['mean']
    std_adv = stats['advantage_c_vs_b']['std']
    ci_95 = 1.96 * std_adv / (n_trials ** 0.5)
    print(f"\n95% CI for C vs B: [{mean_adv - ci_95:.1%}, {mean_adv + ci_95:.1%}]")
    
    # Save results
    output_path = get_results_path("repeated_trials_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"\nResults saved to {output_path}")
    
    return stats


if __name__ == "__main__":
    run_repeated_trials(10)
