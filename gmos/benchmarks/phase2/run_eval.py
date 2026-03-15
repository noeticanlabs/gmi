#!/usr/bin/env python3
"""
Phase 2 Evaluation Runner

Runs the full evaluation comparing all three systems.
"""

import json
import sys
import os
import random

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../../src")

# Import from same directory
from task_dataset import DiagnosisDatasetGenerator
from baselines import BaselineA, BaselineB, FullGMI, run_evaluation


def main():
    print("=" * 60)
    print("PHASE 2 EVALUATION: CONSTRAINED DIAGNOSIS")
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
    print(f"  Diagnoses: {len(diagnoses)}")
    
    # Run Baseline A (Simple Heuristic)
    print("\n[2] Running Baseline A (Simple Heuristic)...")
    system_a = BaselineA(diagnoses)
    results_a = run_evaluation(system_a, test, train)
    print(f"  Accuracy: {results_a['accuracy']:.1%}")
    
    # Run Baseline B (Ungoverned GMI)
    print("\n[3] Running Baseline B (Ungoverned GMI)...")
    system_b = BaselineB(diagnoses, diagnosis_symptoms, budget_limit=100)
    results_b = run_evaluation(system_b, test, train)
    print(f"  Accuracy: {results_b['accuracy']:.1%}")
    print(f"  Verified rate: {results_b['verified_rate']:.1%}")
    
    # Run System C (Full GMI)
    print("\n[4] Running System C (Full GMI on GM-OS)...")
    system_c = FullGMI(
        diagnoses,
        diagnosis_symptoms,
        budget_limit=100,  # Increased to evaluate more candidates
        reserve_floor=0.15
    )
    results_c = run_evaluation(system_c, test, train)
    print(f"  Accuracy: {results_c['accuracy']:.1%}")
    print(f"  Verified rate: {results_c['verified_rate']:.1%}")
    print(f"  Repair rate: {results_c['repair_rate']:.1%}")
    print(f"  Avg spend: {results_c['avg_spend']:.1f}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\n{'System':<30} {'Accuracy':>10} {'Guardrails':>20}")
    print("-" * 60)
    
    # Check guardrails for C
    guardrails_c = "OK" if results_c['repair_rate'] < 0.2 else "CHECK"
    
    print(f"{'Baseline A (Heuristic)':<30} {results_a['accuracy']:>9.1%} {'N/A':>20}")
    print(f"{'Baseline B (Ungoverned)':<30} {results_b['accuracy']:>9.1%} {'N/A':>20}")
    print(f"{'System C (Full GMI)':<30} {results_c['accuracy']:>9.1%} {guardrails_c:>20}")
    
    # Determine winner
    print("\n" + "=" * 60)
    if results_c['accuracy'] > results_a['accuracy']:
        print(f"✅ C beats A by {results_c['accuracy'] - results_a['accuracy']:.1%}")
    else:
        print(f"❌ C does not beat A")
    
    if results_c['accuracy'] > results_b['accuracy']:
        print(f"✅ C beats B by {results_c['accuracy'] - results_b['accuracy']:.1%}")
    else:
        print(f"⚠️ C does not beat B")
    
    # Save results
    output = {
        "system_a": {
            "name": "Baseline A (Heuristic)",
            "accuracy": results_a['accuracy'],
            "correct": results_a['correct'],
            "total": results_a['total']
        },
        "system_b": {
            "name": "Baseline B (Ungoverned GMI)",
            "accuracy": results_b['accuracy'],
            "correct": results_b['correct'],
            "total": results_b['total'],
            "verified_rate": results_b['verified_rate'],
            "repair_rate": results_b['repair_rate']
        },
        "system_c": {
            "name": "System C (Full GMI)",
            "accuracy": results_c['accuracy'],
            "correct": results_c['correct'],
            "total": results_c['total'],
            "verified_rate": results_c['verified_rate'],
            "repair_rate": results_c['repair_rate'],
            "avg_spend": results_c['avg_spend']
        }
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
