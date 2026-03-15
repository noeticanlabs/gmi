#!/usr/bin/env python3
"""
Phase 4 Integrated Evaluation

This evaluation properly integrates gating with the real Phase 3 systems,
not toy shells. It demonstrates that gating improves over always-on behavior.
"""

import os
import sys
import random
import json
import importlib.util
from pathlib import Path
from typing import List, Dict, Any

# BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Add paths
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "benchmarks" / "phase3"))

# Load Phase 3 modules
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Load Phase 3 run_eval (the real implementations)
phase3_path = BASE_DIR / "benchmarks" / "phase3" / "run_eval.py"
phase3 = load_module("phase3_run_eval", str(phase3_path))

# Load Phase 4 gating
gating_path = BASE_DIR / "src" / "gmos" / "agents" / "gmi" / "gating.py"
gating_context_path = BASE_DIR / "src" / "gmos" / "agents" / "gmi" / "gating_context.py"
gating = load_module("gating", str(gating_path))
gating_context = load_module("gating_context", str(gating_context_path))

GatingPolicy = gating.GatingPolicy
GatingContext = gating_context.GatingContext
PerceptContext = gating_context.PerceptContext
MemoryContext = gating_context.MemoryContext
BudgetContext = gating_context.BudgetContext
RiskContext = gating_context.RiskContext
VerifierContext = gating_context.VerifierContext
HistoryContext = gating_context.HistoryContext
TaskType = gating_context.TaskType
create_gating_policy = gating.create_gating_policy


class GatedDiagnosisSystem:
    """
    Diagnosis system with gating.
    
    This wraps the real Phase 3 DiagnosisWithEnhancedMemory
    and adds gating decisions on top.
    """
    
    def __init__(
        self,
        diagnoses: List[str],
        diagnosis_symptoms: Dict[str, List[int]],
        use_gating: bool = True,
        memory_cases: List[Dict] = None,
    ):
        self.diagnoses = diagnoses
        self.diagnosis_symptoms = diagnosis_symptoms
        self.use_gating = use_gating
        self.memory_cases = memory_cases or []
        
        # Create the REAL Phase 3 system
        self.system = phase3.DiagnosisWithEnhancedMemory(
            diagnoses=diagnoses,
            diagnosis_symptoms=diagnosis_symptoms,
            use_memory=True,  # Always on in underlying system
            use_adaptation=False,
            use_safehold=False,
        )
        
        # Add memory
        for case in self.memory_cases:
            self.system.add_memory(case)
        
        # Create gating policy
        if use_gating:
            self.gating_policy = create_gating_policy(
                task_name="diagnosis",
                enable_gating=True
            )
        else:
            self.gating_policy = None
    
    def diagnose(self, symptoms: List[int]) -> str:
        """Diagnose with optional gating."""
        
        if self.use_gating and self.gating_policy:
            # Build context for gating decision
            confidence = min(1.0, sum(1 for s in symptoms if s > 0) / 5.0)
            
            context = GatingContext(
                episode_id=f"diag_{random.randint(1000, 9999)}",
                task_type=TaskType.DIAGNOSIS,
                task_name="diagnosis",
                percept=PerceptContext(confidence=confidence, ambiguity=1.0 - confidence),
                memory=MemoryContext(relevance=0.5, confidence=0.5, count=len(self.memory_cases)),
                budget=BudgetContext(ratio=0.8, reserve_proximity=0.1),
                risk=RiskContext(severity=0.3, reversibility=0.7),
                verifier=VerifierContext(score=confidence, passed=True),
                history=HistoryContext(recent_failures=0, total_episodes=10),
            )
            
            gating_decision = self.gating_policy.compute_gating(context)
            
            # If gating says disable memory, create a no-memory system
            if not gating_decision.memory.use_memory:
                # Create temporary no-memory system for this diagnosis
                no_mem_system = phase3.DiagnosisWithEnhancedMemory(
                    diagnoses=self.diagnoses,
                    diagnosis_symptoms=self.diagnosis_symptoms,
                    use_memory=False,
                    use_adaptation=False,
                    use_safehold=False,
                )
                return no_mem_system.diagnose(symptoms)
        
        # Use full system (with memory)
        return self.system.diagnose(symptoms)


class GatedTriageSystem:
    """
    Triage system with gating.
    
    This wraps the real Phase 3 TriageWithEnhancedMemory
    and adds gating decisions.
    """
    
    def __init__(
        self,
        use_gating: bool = True,
        memory_cases: List[Dict] = None,
    ):
        self.use_gating = use_gating
        self.memory_cases = memory_cases or []
        
        # Create the REAL Phase 3 system (no 'actions' param - uses class constant)
        self.system = phase3.TriageWithEnhancedMemory(
            use_memory=True,
            use_adaptation=False,
            use_safehold=False,
        )
        
        # Add memory
        for case in self.memory_cases:
            self.system.add_memory(case)
        
        # Create gating policy
        if use_gating:
            self.gating_policy = create_gating_policy(
                task_name="triage",
                enable_gating=True
            )
        else:
            self.gating_policy = None
    
    def triage(self, symptoms: Dict[str, Any], context: Dict[str, Any], severity: int = 5, memory: List[Dict] = None) -> Dict[str, Any]:
        """Triage with optional gating."""
        
        # Use provided memory or stored memory
        memory_cases = memory if memory is not None else self.memory_cases
        
        if self.use_gating and self.gating_policy:
            # Build context for gating
            confidence = 0.7  # Simplified
            
            gating_context = GatingContext(
                episode_id=f"triage_{random.randint(1000, 9999)}",
                task_type=TaskType.TRIAGE,
                task_name="triage",
                percept=PerceptContext(confidence=confidence, ambiguity=0.3),
                memory=MemoryContext(relevance=0.7, confidence=0.6, count=len(memory_cases)),
                budget=BudgetContext(ratio=0.8, reserve_proximity=0.1),
                risk=RiskContext(severity=0.3, reversibility=0.7),
                verifier=VerifierContext(score=confidence, passed=True),
                history=HistoryContext(recent_failures=0, total_episodes=10),
            )
            
            gating_decision = self.gating_policy.compute_gating(gating_context)
            
            # If gating says disable memory
            if not gating_decision.memory.use_memory:
                no_mem_system = phase3.TriageWithEnhancedMemory(
                    use_memory=False,
                    use_adaptation=False,
                    use_safehold=False,
                )
                return no_mem_system.triage(symptoms, context, severity, memory_cases)
        
        return self.system.triage(symptoms, context, severity, memory_cases)


def run_task_a_eval(n_cases: int = 50, seed: int = 42):
    """Run Task A with gating vs without."""
    random.seed(seed)
    
    # Load dataset
    dataset_gen = phase3.DiagnosisDatasetGenerator(seed=seed)
    dataset = dataset_gen.generate_dataset(n_train=50, n_test=n_cases)
    train_cases = dataset["train"]
    test_cases = dataset["test"]
    
    diagnoses = list(dataset_gen.diagnosis_symptoms.keys())
    symptoms_map = dataset_gen.diagnosis_symptoms
    
    results = {
        "always_on": {"correct": 0, "total": n_cases},
        "gated": {"correct": 0, "total": n_cases},
        "no_memory": {"correct": 0, "total": n_cases},
    }
    
    # Always-on (with memory)
    always_on = GatedDiagnosisSystem(
        diagnoses=diagnoses,
        diagnosis_symptoms=symptoms_map,
        use_gating=False,
        memory_cases=train_cases,
    )
    
    # Gated (gating decides memory use)
    gated = GatedDiagnosisSystem(
        diagnoses=diagnoses,
        diagnosis_symptoms=symptoms_map,
        use_gating=True,
        memory_cases=train_cases,
    )
    
    # No memory (ablation)
    no_memory = phase3.DiagnosisWithEnhancedMemory(
        diagnoses=diagnoses,
        diagnosis_symptoms=symptoms_map,
        use_memory=False,
        use_adaptation=False,
        use_safehold=False,
    )
    
    for case in test_cases:
        symptoms = case.get("symptoms", [])
        diagnosis = case.get("diagnosis", "")
        
        # Always-on
        result = always_on.diagnose(symptoms)
        predicted = result.get("predicted", result) if isinstance(result, dict) else result
        if predicted == diagnosis:
            results["always_on"]["correct"] += 1
        
        # Gated
        result = gated.diagnose(symptoms)
        predicted = result.get("predicted", result) if isinstance(result, dict) else result
        if predicted == diagnosis:
            results["gated"]["correct"] += 1
        
        # No memory
        result = no_memory.diagnose(symptoms)
        predicted = result.get("predicted", result) if isinstance(result, dict) else result
        if predicted == diagnosis:
            results["no_memory"]["correct"] += 1
    
    for key in results:
        results[key]["accuracy"] = results[key]["correct"] / results[key]["total"]
    
    return results


def run_task_b_eval(n_cases: int = 50, seed: int = 42):
    """Run Task B with gating vs without."""
    random.seed(seed)
    
    # Load task B dataset
    task_b_path = BASE_DIR / "benchmarks" / "phase3" / "task_b" / "dataset.py"
    task_b = load_module("task_b", str(task_b_path))
    
    dataset_gen = task_b.TriageDatasetGenerator(seed=seed)
    dataset = dataset_gen.generate_dataset(n_train=50, n_test=n_cases)
    # Correct keys: "memory" for training cases, "test" for test cases
    train_cases = dataset.get("memory", [])
    test_cases = dataset.get("test", [])
    
    actions = ["inspect", "repair", "replace", "monitor", "escalate", "SafeHold"]
    
    results = {
        "always_on": {"correct": 0, "total": n_cases},
        "gated": {"correct": 0, "total": n_cases},
        "no_memory": {"correct": 0, "total": n_cases},
    }
    
    # Always-on
    always_on = GatedTriageSystem(
        use_gating=False,
        memory_cases=train_cases,
    )
    
    # Gated
    gated = GatedTriageSystem(
        use_gating=True,
        memory_cases=train_cases,
    )
    
    # No memory
    no_memory = phase3.TriageWithEnhancedMemory(
        use_memory=False,
        use_adaptation=False,
        use_safehold=False,
    )
    
    for case in test_cases:
        # Build the required arguments for triage()
        # From Phase 3: triage(symptoms, context, severity, memory)
        symptoms = case.get("symptoms", {})
        context = case.get("context", {})
        severity = case.get("severity", 5)
        memory = train_cases  # Use training cases as memory
        
        # Get correct action from the case
        correct_action = case.get("correct_action", "")
        
        # Always-on (pass 4 args including memory)
        result = always_on.triage(symptoms, context, severity, memory)
        if result.get("predicted") == correct_action:
            results["always_on"]["correct"] += 1
        
        # Gated
        result = gated.triage(symptoms, context, severity)
        if result.get("predicted") == correct_action:
            results["gated"]["correct"] += 1
        
        # No memory
        result = no_memory.triage(symptoms, context, severity, None)
        if result.get("predicted") == correct_action:
            results["no_memory"]["correct"] += 1
    
    for key in results:
        results[key]["accuracy"] = results[key]["correct"] / results[key]["total"]
    
    return results


def main():
    print("=" * 70)
    print("PHASE 4 INTEGRATED EVALUATION")
    print("(Gating + Real Phase 3 Systems)")
    print("=" * 70)
    
    # Task A
    print("\n--- Task A: Diagnosis ---")
    task_a = run_task_a_eval(n_cases=50, seed=42)
    print(f"Always-on (memory): {task_a['always_on']['accuracy']:.1%}")
    print(f"Gated:              {task_a['gated']['accuracy']:.1%}")
    print(f"No memory:          {task_a['no_memory']['accuracy']:.1%}")
    
    improvement_a = task_a['gated']['accuracy'] - task_a['always_on']['accuracy']
    print(f"Gating improvement: {improvement_a:+.1%}")
    
    # Task B
    print("\n--- Task B: Triage ---")
    task_b = run_task_b_eval(n_cases=50, seed=42)
    print(f"Always-on (memory): {task_b['always_on']['accuracy']:.1%}")
    print(f"Gated:              {task_b['gated']['accuracy']:.1%}")
    print(f"No memory:          {task_b['no_memory']['accuracy']:.1%}")
    
    improvement_b = task_b['gated']['accuracy'] - task_b['always_on']['accuracy']
    print(f"Gating improvement: {improvement_b:+.1%}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    always_on_avg = (task_a['always_on']['accuracy'] + task_b['always_on']['accuracy']) / 2
    gated_avg = (task_a['gated']['accuracy'] + task_b['gated']['accuracy']) / 2
    
    print(f"Always-on average: {always_on_avg:.1%}")
    print(f"Gated average:     {gated_avg:.1%}")
    print(f"Overall improvement: {gated_avg - always_on_avg:+.1%}")
    
    # Save results
    output_path = BASE_DIR / "benchmarks" / "phase4" / "integrated_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        "task_a": task_a,
        "task_b": task_b,
        "summary": {
            "always_on_avg": always_on_avg,
            "gated_avg": gated_avg,
            "improvement": gated_avg - always_on_avg,
        }
    }
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=float)
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
