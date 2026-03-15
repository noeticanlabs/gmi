#!/usr/bin/env python3
"""
Phase 3 Repeated-Seed Evaluation

Runs evaluation across multiple seeds to compute statistical significance.
"""

import random
import importlib.util
import os
import json
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
adaptation = load_module("adaptation", 
    GMOS_SRC / "gmos" / "agents" / "gmi" / "adaptation.py")
task_dataset = load_module("task_dataset", 
    BENCHMARKS / "phase2" / "task_dataset.py")
task_b = load_module("task_b_dataset", 
    BENCHMARKS / "phase3" / "task_b" / "dataset.py")


class DiagnosisWithEnhancedMemory:
    """Diagnosis system with enhanced memory."""
    
    def __init__(self, diagnoses, diagnosis_symptoms, budget_limit=10, use_memory=True):
        self.diagnoses = diagnoses
        self.diagnosis_symptoms = diagnosis_symptoms
        self.budget_limit = budget_limit
        self.use_memory = use_memory
        
        self.retrieval_engine = enhanced_retrieval.create_retrieval_engine("diagnosis")
        self.mode_machine = mode_machine.create_mode_machine(enable_safehold=False)
        self.memory_cases = []
        
    def add_memory(self, case):
        self.memory_cases.append(case)
    
    def diagnose(self, symptoms, memory=None):
        memory_cases = memory if memory is not None else self.memory_cases
        budget = self.budget_limit
        spent = 0
        
        self.mode_machine.reset()
        
        RuntimeMode = mode_machine.RuntimeMode
        TransitionReason = mode_machine.TransitionReason
        self.mode_machine.transition(RuntimeMode.RECALL, TransitionReason.PERCEPT_COMPLETE)
        
        retrieved_memory = []
        if self.use_memory and memory_cases:
            symptom_dict = {f"symptom_{i}": bool(s) for i, s in enumerate(symptoms)}
            query = {"symptoms": symptom_dict}
            results = self.retrieval_engine.retrieve(memory_cases, query, top_k=5)
            retrieved_memory = [r.episode for r in results]
        
        self.mode_machine.transition(RuntimeMode.DELIBERATE, TransitionReason.MEMORY_RETRIEVED)
        
        scores = {}
        for diagnosis in self.diagnoses:
            base_symptoms = self.diagnosis_symptoms.get(diagnosis, [])
            base_score = sum(1 for s in base_symptoms if symptoms[s])
            
            memory_bonus = 0
            if retrieved_memory:
                for mem in retrieved_memory:
                    mem_diag = mem.get("diagnosis", "")
                    if mem_diag == diagnosis:
                        outcome = mem.get("outcome", "")
                        if outcome in ["correct", "resolved", "success"]:
                            memory_bonus += 0.3
                        elif outcome in ["incorrect", "failed"]:
                            memory_bonus -= 0.2
            
            scores[diagnosis] = base_score + memory_bonus
        
        predicted = max(scores, key=scores.get)
        confidence = min(0.5 + scores[predicted] / 10.0, 0.95)
        
        return {
            "predicted": predicted,
            "confidence": confidence,
            "spent": 2 if retrieved_memory else 1,
            "memory_used": bool(retrieved_memory),
        }


class TriageWithEnhancedMemory:
    """Triage system with SafeHold disabled (based on analysis)."""
    
    ACTIONS = [
        "INSPECT_LOCAL", "CONTINUE_MONITOR", "GATHER_EVIDENCE",
        "REPLACE_COMPONENT", "SHUT_DOWN", "ESCALATE_SPECIALIST", "SAFEHOLD_ABSTAIN"
    ]
    
    def __init__(self, budget_limit=8, use_memory=True):
        self.budget_limit = budget_limit
        self.use_memory = use_memory
        
        self.retrieval_engine = enhanced_retrieval.create_retrieval_engine("triage")
        self.mode_machine = mode_machine.create_mode_machine(enable_safehold=False)  # Disabled
        self.memory_cases = []
        
    def add_memory(self, case):
        self.memory_cases.append(case)
    
    def triage(self, symptoms, context, severity, memory=None):
        memory_cases = memory if memory is not None else self.memory_cases
        budget = self.budget_limit
        spent = 0
        
        self.mode_machine.reset()
        
        RuntimeMode = mode_machine.RuntimeMode
        TransitionReason = mode_machine.TransitionReason
        self.mode_machine.transition(RuntimeMode.RECALL, TransitionReason.PERCEPT_COMPLETE)
        
        retrieved_memory = []
        if self.use_memory and memory_cases:
            query = {"symptoms": symptoms, "context": context}
            results = self.retrieval_engine.retrieve(memory_cases, query, top_k=5)
            retrieved_memory = [r.episode for r in results]
        
        self.mode_machine.transition(RuntimeMode.DELIBERATE, TransitionReason.MEMORY_RETRIEVED)
        
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


def run_diagnosis_evaluation(system, test_cases, memory_cases, use_memory):
    correct = 0
    total = 0
    
    for case in test_cases:
        system.memory_cases = memory_cases
        result = system.diagnose(symptoms=case['symptoms'], memory=memory_cases if use_memory else None)
        if result['predicted'] == case['diagnosis']:
            correct += 1
        total += 1
    
    return correct / total if total > 0 else 0


def run_triage_evaluation(system, test_cases, memory_cases, use_memory):
    correct = 0
    total = 0
    
    for case in test_cases:
        system.memory_cases = memory_cases
        result = system.triage(
            symptoms=case['symptoms'],
            context=case['context'],
            severity=case['severity'],
            memory=memory_cases if use_memory else None
        )
        if result['predicted'] == case['correct_action']:
            correct += 1
        total += 1
    
    return correct / total if total > 0 else 0


def main():
    print("=" * 70)
    print("PHASE 3 REPEATED-SEED EVALUATION")
    print("=" * 70)
    
    N_SEEDS = 10
    results_by_seed = []
    
    for seed in range(N_SEEDS):
        print(f"\n--- Seed {seed} ---")
        random.seed(seed)
        
        # Generate Task A dataset
        gen_a = task_dataset.DiagnosisDatasetGenerator(
            n_diagnoses=10, n_symptoms=20, seed=seed
        )
        dataset_a = gen_a.generate_dataset(n_train=500, n_test=100)
        train_a = dataset_a['train']
        test_a = dataset_a['test']
        diagnoses = dataset_a['diagnoses']
        diagnosis_symptoms = dataset_a['diagnosis_symptoms']
        
        memory_a = [
            {"diagnosis": t['diagnosis'], "symptoms": t['symptoms'], "outcome": "correct"}
            for t in train_a[:100]
        ]
        
        # Generate Task B dataset
        dataset_b = task_b.generate_dataset(n_train=200, n_test=100, seed=seed)
        memory_b = dataset_b['memory']
        test_b = dataset_b['test']
        
        # Task A evaluations
        system_a_full = DiagnosisWithEnhancedMemory(diagnoses, diagnosis_symptoms, use_memory=True)
        acc_a_full = run_diagnosis_evaluation(system_a_full, test_a, memory_a, use_memory=True)
        
        system_a_no_mem = DiagnosisWithEnhancedMemory(diagnoses, diagnosis_symptoms, use_memory=False)
        acc_a_no_mem = run_diagnosis_evaluation(system_a_no_mem, test_a, memory_a, use_memory=False)
        
        # Task B evaluations
        system_b_full = TriageWithEnhancedMemory(use_memory=True)
        acc_b_full = run_triage_evaluation(system_b_full, test_b, memory_b, use_memory=True)
        
        system_b_no_mem = TriageWithEnhancedMemory(use_memory=False)
        acc_b_no_mem = run_triage_evaluation(system_b_no_mem, test_b, memory_b, use_memory=False)
        
        results_by_seed.append({
            "seed": seed,
            "task_a_full": acc_a_full,
            "task_a_no_mem": acc_a_no_mem,
            "task_b_full": acc_b_full,
            "task_b_no_mem": acc_b_no_mem,
            "memory_benefit_a": acc_a_full - acc_a_no_mem,
            "memory_benefit_b": acc_b_full - acc_b_no_mem,
        })
        
        print(f"  Task A: full={acc_a_full:.1%}, no_mem={acc_a_no_mem:.1%}, benefit={acc_a_full - acc_a_no_mem:+.1%}")
        print(f"  Task B: full={acc_b_full:.1%}, no_mem={acc_b_no_mem:.1%}, benefit={acc_b_full - acc_b_no_mem:+.1%}")
    
    # Aggregate results
    print("\n" + "=" * 70)
    print("AGGREGATED RESULTS")
    print("=" * 70)
    
    task_a_fulls = [r['task_a_full'] for r in results_by_seed]
    task_a_no_mems = [r['task_a_no_mem'] for r in results_by_seed]
    task_b_fulls = [r['task_b_full'] for r in results_by_seed]
    task_b_no_mems = [r['task_b_no_mem'] for r in results_by_seed]
    memory_benefits_a = [r['memory_benefit_a'] for r in results_by_seed]
    memory_benefits_b = [r['memory_benefit_b'] for r in results_by_seed]
    
    def mean_std(values):
        m = sum(values) / len(values)
        variance = sum((x - m) ** 2 for x in values) / len(values)
        return m, variance ** 0.5
    
    mean_a_full, std_a_full = mean_std(task_a_fulls)
    mean_a_no_mem, std_a_no_mem = mean_std(task_a_no_mems)
    mean_b_full, std_b_full = mean_std(task_b_fulls)
    mean_b_no_mem, std_b_no_mem = mean_std(task_b_no_mems)
    mean_benefit_a, std_benefit_a = mean_std(memory_benefits_a)
    mean_benefit_b, std_benefit_b = mean_std(memory_benefits_b)
    
    print(f"\nTask A (Diagnosis):")
    print(f"  Full system:     {mean_a_full*100:.1f}% ± {std_a_full*100:.1f}%")
    print(f"  No memory:       {mean_a_no_mem*100:.1f}% ± {std_a_no_mem*100:.1f}%")
    print(f"  Memory benefit: {mean_benefit_a*100:+.1f}% ± {std_benefit_a*100:.1f}%")
    
    print(f"\nTask B (Triage):")
    print(f"  Full system:     {mean_b_full*100:.1f}% ± {std_b_full*100:.1f}%")
    print(f"  No memory:       {mean_b_no_mem*100:.1f}% ± {std_b_no_mem*100:.1f}%")
    print(f"  Memory benefit: {mean_benefit_b*100:+.1f}% ± {std_benefit_b*100:.1f}%")
    
    # Compute MGSR
    mgsr = (mean_a_full + mean_b_full) / 2
    print(f"\nMulti-Task Success Rate: {mgsr*100:.1f}%")
    
    # Save results
    output = {
        "n_seeds": N_SEEDS,
        "task_a": {
            "full_mean": mean_a_full,
            "full_std": std_a_full,
            "no_mem_mean": mean_a_no_mem,
            "no_mem_std": std_a_no_mem,
        },
        "task_b": {
            "full_mean": mean_b_full,
            "full_std": std_b_full,
            "no_mem_mean": mean_b_no_mem,
            "no_mem_std": std_b_no_mem,
        },
        "memory_benefit_a": mean_benefit_a,
        "memory_benefit_b": mean_benefit_b,
        "mgsr": mgsr,
        "seeds": results_by_seed,
    }
    
    output_path = Path(__file__).resolve().parent / "repeated_seeds_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    # Final verdict
    print("\n" + "=" * 70)
    print("PHASE 3 VERDICT")
    print("=" * 70)
    
    if mean_benefit_b > 0:
        print(f"✓ Memory helps Task B: +{mean_benefit_b*100:.1f}%")
    else:
        print(f"✗ Memory does NOT help Task B: {mean_benefit_b*100:.1f}%")
    
    if mean_benefit_a > 0:
        print(f"✓ Memory helps Task A: +{mean_benefit_a*100:.1f}%")
    else:
        print(f"✗ Memory does NOT help Task A: {mean_benefit_a*100:.1f}%")
    
    if mean_benefit_b > 0 and mgsr > 0.5:
        print("\n→ Phase 3 MINIMUM COMPLETION: ACHIEVED")
    else:
        print("\n→ Phase 3: More work needed")


if __name__ == "__main__":
    main()
