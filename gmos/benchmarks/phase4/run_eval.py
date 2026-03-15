#!/usr/bin/env python3
"""
Phase 4 Evaluation Harness

Compares gated vs always-on configurations across Tasks A, B, and C.
Measures whether selective feature use improves utility.
"""

import os
import sys
import random
import json
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional

# BASE_DIR is /home/user/gmi/gmos/benchmarks/phase4
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Add paths
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "benchmarks" / "phase3"))

# Load Phase 3 components
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Load Phase 3 run_eval
phase3_path = BASE_DIR / "benchmarks" / "phase3" / "run_eval.py"
phase3 = load_module("phase3_run_eval", str(phase3_path))

# Load Phase 4 gating components
gating_path = BASE_DIR / "src" / "gmos" / "agents" / "gmi" / "gating.py"
gating_context_path = BASE_DIR / "src" / "gmos" / "agents" / "gmi" / "gating_context.py"
gating = load_module("gating", str(gating_path))
gating_context = load_module("gating_context", str(gating_context_path))

# Import context classes
PerceptContext = gating_context.PerceptContext
MemoryContext = gating_context.MemoryContext
BudgetContext = gating_context.BudgetContext
RiskContext = gating_context.RiskContext
VerifierContext = gating_context.VerifierContext
HistoryContext = gating_context.HistoryContext
TaskType = gating_context.TaskType
GatingContext = gating_context.GatingContext

# Load Phase 4 Task C dataset
task_c_path = BASE_DIR / "benchmarks" / "phase4" / "task_c" / "dataset.py"
task_c = load_module("task_c_dataset", str(task_c_path))


class GatedDiagnosisSystem:
    """Diagnosis system with gated features."""
    
    def __init__(
        self,
        diagnoses: List[str],
        diagnosis_symptoms: Dict[str, List[int]],
        use_memory: bool = True,
        use_gating: bool = False,
    ):
        self.diagnoses = diagnoses
        self.diagnosis_symptoms = diagnosis_symptoms
        self.use_memory = use_memory
        self.use_gating = use_gating
        
        # Create components
        self.retrieval_engine = phase3.create_retrieval_engine("diagnosis")
        self.mode_machine = phase3.create_mode_machine(enable_safehold=False)
        self.adaptation_tracker = None
        
        # Gating policy
        if use_gating:
            self.gating_policy = gating.create_gating_policy(
                task_name="diagnosis",
                enable_gating=True
            )
        else:
            self.gating_policy = None
    
    def diagnose(self, symptoms: List[int]) -> str:
        """Run diagnosis with optional gating."""
        # Get gating decision if enabled
        if self.use_gating and self.gating_policy:
            context = self._build_context(symptoms)
            gating_decision = self.gating_policy.compute_gating(context)
            
            use_memory = gating_decision.memory.use_memory
            top_k = gating_decision.memory.top_k
        else:
            use_memory = self.use_memory
            top_k = 5
        
        # Reset mode machine
        self.mode_machine.reset()
        
        # Retrieve memory if gated memory says to use it
        memory_context = []
        if use_memory:
            # Simple memory retrieval
            memory_context = self._retrieve_memory(symptoms, top_k)
        
        # Generate candidates (simplified)
        candidates = self._generate_candidates(symptoms)
        
        # Score candidates
        scores = self._score_candidates(candidates, symptoms, memory_context)
        
        # Return best diagnosis
        best = max(scores.items(), key=lambda x: x[1])
        return best[0]
    
    def _build_context(self, symptoms: List[int]) -> Any:
        """Build gating context from symptoms."""
        # Estimate confidence based on symptom clarity
        confidence = min(1.0, len([s for s in symptoms if s > 0]) / 5.0)
        
        return GatingContext(
            episode_id=f"diag_{random.randint(1000, 9999)}",
            task_type=TaskType.DIAGNOSIS,
            task_name="diagnosis",
            percept=PerceptContext(confidence=confidence, ambiguity=1.0 - confidence),
            memory=MemoryContext(relevance=0.5, confidence=0.5, count=0),
            budget=BudgetContext(ratio=0.8, reserve_proximity=0.1),
            risk=RiskContext(severity=0.3, reversibility=0.7),
            verifier=VerifierContext(score=confidence, passed=True),
            history=HistoryContext(recent_failures=0, total_episodes=10),
        )
    
    def _retrieve_memory(self, symptoms: List[int], top_k: int) -> List[Dict]:
        """Retrieve relevant memories."""
        # Simplified - would use actual retrieval engine
        return []
    
    def _generate_candidates(self, symptoms: List[int]) -> List[str]:
        """Generate diagnosis candidates."""
        return self.diagnoses[:5]
    
    def _score_candidates(
        self,
        candidates: List[str],
        symptoms: List[int],
        memory: List[Dict]
    ) -> Dict[str, float]:
        """Score diagnosis candidates."""
        scores = {}
        for candidate in candidates:
            score = 0.5
            if candidate in self.diagnosis_symptoms:
                for symptom in self.diagnosis_symptoms[candidate]:
                    if symptom in symptoms:
                        score += 0.1
            scores[candidate] = min(1.0, score)
        return scores


class GatedTriageSystem:
    """Triage system with gated features."""
    
    def __init__(
        self,
        actions: List[str],
        use_memory: bool = True,
        use_gating: bool = False,
    ):
        self.actions = actions
        self.use_memory = use_memory
        self.use_gating = use_gating
        
        # Create components
        self.retrieval_engine = phase3.create_retrieval_engine("triage")
        self.mode_machine = phase3.create_mode_machine(enable_safehold=False)
        self.adaptation_tracker = None
        
        # Gating policy
        if use_gating:
            self.gating_policy = gating.create_gating_policy(
                task_name="triage",
                enable_gating=True
            )
        else:
            self.gating_policy = None
    
    def triage(self, situation: Dict[str, Any]) -> str:
        """Run triage with optional gating."""
        # Get gating decision if enabled
        if self.use_gating and self.gating_policy:
            context = self._build_context(situation)
            gating_decision = self.gating_policy.compute_gating(context)
            
            use_memory = gating_decision.memory.use_memory
            top_k = gating_decision.memory.top_k
        else:
            use_memory = self.use_memory
            top_k = 5
        
        # Reset mode machine
        self.mode_machine.reset()
        
        # Retrieve memory if gated memory says to use it
        memory_context = []
        if use_memory:
            memory_context = self._retrieve_memory(situation, top_k)
        
        # Generate candidates
        candidates = self._generate_candidates(situation)
        
        # Score candidates
        scores = self._score_candidates(candidates, situation, memory_context)
        
        # Return best action
        best = max(scores.items(), key=lambda x: x[1])
        return best[0]
    
    def _build_context(self, situation: Dict[str, Any]) -> Any:
        """Build gating context from situation."""
        # Estimate confidence
        confidence = 0.7  # Simplified
        
        return GatingContext(
            episode_id=f"triage_{random.randint(1000, 9999)}",
            task_type=TaskType.TRIAGE,
            task_name="triage",
            percept=PerceptContext(confidence=confidence, ambiguity=0.3),
            memory=MemoryContext(relevance=0.7, confidence=0.6, count=5),
            budget=BudgetContext(ratio=0.8, reserve_proximity=0.1),
            risk=RiskContext(severity=0.3, reversibility=0.7),
            verifier=VerifierContext(score=confidence, passed=True),
            history=HistoryContext(recent_failures=0, total_episodes=10),
        )
    
    def _retrieve_memory(self, situation: Dict, top_k: int) -> List[Dict]:
        return []
    
    def _generate_candidates(self, situation: Dict) -> List[str]:
        return self.actions[:5]
    
    def _score_candidates(self, candidates, situation, memory) -> Dict[str, float]:
        scores = {}
        for c in candidates:
            scores[c] = 0.5 + random.random() * 0.3
        return scores


class EvidenceGatheringSystem:
    """Task C: Evidence gathering with gating."""
    
    def __init__(self, use_gating: bool = False):
        self.use_gating = use_gating
        
        # Gating policy
        if use_gating:
            self.gating_policy = gating.create_gating_policy(
                task_name="evidence_gathering",
                enable_gating=True
            )
        else:
            self.gating_policy = None
    
    def evaluate_case(self, case: Any) -> str:
        """Evaluate evidence gathering case."""
        # Get gating decision
        if self.use_gating and self.gating_policy:
            context = self._build_context(case)
            gating_decision = self.gating_policy.compute_gating(context)
            
            # Use gating decision
            if gating_decision.evidence.request_evidence:
                return "REQUEST_EVIDENCE"
            elif gating_decision.safehold.enable_safehold:
                return "ABSTAIN"
            else:
                return "PROCEED"
        else:
            # Always proceed without gating
            if case.uncertainty < 0.3:
                return "PROCEED"
            elif case.uncertainty < 0.7:
                return "REQUEST_EVIDENCE"
            else:
                return "ABSTAIN"
    
    def _build_context(self, case: Any) -> Any:
        confidence = 1.0 - case.uncertainty
        
        return GatingContext(
            episode_id=case.case_id,
            task_type=TaskType.EVIDENCE_GATHERING,
            task_name="evidence_gathering",
            percept=PerceptContext(confidence=confidence, ambiguity=case.uncertainty),
            memory=MemoryContext(relevance=0.5, confidence=0.5, count=0),
            budget=BudgetContext(ratio=0.8, reserve_proximity=0.1),
            risk=RiskContext(severity=case.difficulty, reversibility=0.5),
            verifier=VerifierContext(score=confidence, passed=True),
            history=HistoryContext(recent_failures=0, total_episodes=10),
        )


def run_task_a_evaluation(n_cases: int = 50, seed: int = 42) -> Dict[str, float]:
    """Run Task A (diagnosis) evaluation."""
    random.seed(seed)
    
    # Load dataset
    dataset_gen = phase3.DiagnosisDatasetGenerator(seed=seed)
    dataset = dataset_gen.generate_dataset(n_train=0, n_test=n_cases)
    cases = dataset["test"]
    
    # Get diagnoses and symptoms
    diagnoses = list(dataset_gen.diagnosis_symptoms.keys())
    symptoms_map = dataset_gen.diagnosis_symptoms
    
    results = {
        "always_on": {"correct": 0, "total": n_cases},
        "gated": {"correct": 0, "total": n_cases},
        "no_memory": {"correct": 0, "total": n_cases},
    }
    
    # Test always-on
    system_always = GatedDiagnosisSystem(diagnoses, symptoms_map, use_memory=True, use_gating=False)
    for case in cases:
        symptoms = case.get("symptoms", case.get("symptom_vector", []))
        diagnosis = case.get("diagnosis", case.get("correct_diagnosis", ""))
        result = system_always.diagnose(symptoms)
        if result == diagnosis:
            results["always_on"]["correct"] += 1
    
    # Test gated
    system_gated = GatedDiagnosisSystem(diagnoses, symptoms_map, use_memory=True, use_gating=True)
    for case in cases:
        symptoms = case.get("symptoms", case.get("symptom_vector", []))
        diagnosis = case.get("diagnosis", case.get("correct_diagnosis", ""))
        result = system_gated.diagnose(symptoms)
        if result == diagnosis:
            results["gated"]["correct"] += 1
    
    # Test no memory
    system_no_mem = GatedDiagnosisSystem(diagnoses, symptoms_map, use_memory=False, use_gating=False)
    for case in cases:
        symptoms = case.get("symptoms", case.get("symptom_vector", []))
        diagnosis = case.get("diagnosis", case.get("correct_diagnosis", ""))
        result = system_no_mem.diagnose(symptoms)
        if result == diagnosis:
            results["no_memory"]["correct"] += 1
    
    # Compute accuracy
    for key in results:
        results[key]["accuracy"] = results[key]["correct"] / results[key]["total"]
    
    return results


def run_task_b_evaluation(n_cases: int = 50, seed: int = 42) -> Dict[str, float]:
    """Run Task B (triage) evaluation."""
    random.seed(seed)
    
    # Load dataset from Phase 3
    task_b_path = BASE_DIR / "benchmarks" / "phase3" / "task_b" / "dataset.py"
    task_b_mod = load_module("task_b_dataset", str(task_b_path))
    
    dataset_gen = task_b_mod.TriageDatasetGenerator(seed=seed)
    dataset = dataset_gen.generate_dataset(n_train=0, n_test=n_cases)
    cases = dataset["test"]
    
    actions = ["inspect", "repair", "replace", "monitor", "escalate", "SafeHold"]
    
    results = {
        "always_on": {"correct": 0, "total": n_cases},
        "gated": {"correct": 0, "total": n_cases},
        "no_memory": {"correct": 0, "total": n_cases},
    }
    
    # Test always-on
    system_always = GatedTriageSystem(actions, use_memory=True, use_gating=False)
    for case in cases:
        situation = case if isinstance(case, dict) else {"description": str(case)}
        correct_action = case.get("correct_action", case.get("action", ""))
        result = system_always.triage(situation)
        if result == correct_action:
            results["always_on"]["correct"] += 1
    
    # Test gated
    system_gated = GatedTriageSystem(actions, use_memory=True, use_gating=True)
    for case in cases:
        situation = case if isinstance(case, dict) else {"description": str(case)}
        correct_action = case.get("correct_action", case.get("action", ""))
        result = system_gated.triage(situation)
        if result == correct_action:
            results["gated"]["correct"] += 1
    
    # Test no memory
    system_no_mem = GatedTriageSystem(actions, use_memory=False, use_gating=False)
    for case in cases:
        situation = case if isinstance(case, dict) else {"description": str(case)}
        correct_action = case.get("correct_action", case.get("action", ""))
        result = system_no_mem.triage(situation)
        if result == correct_action:
            results["no_memory"]["correct"] += 1
    
    # Compute accuracy
    for key in results:
        results[key]["accuracy"] = results[key]["correct"] / results[key]["total"]
    
    return results


def run_task_c_evaluation(n_cases: int = 50, seed: int = 42) -> Dict[str, float]:
    """Run Task C (evidence gathering) evaluation."""
    random.seed(seed)
    
    # Generate dataset
    dataset_gen = task_c.EvidenceGatheringDatasetGenerator(seed=seed)
    cases = dataset_gen.generate_dataset(n_cases=n_cases)
    
    results = {
        "always_on": {"correct": 0, "total": n_cases},
        "gated": {"correct": 0, "total": n_cases},
    }
    
    # Test always-on (no gating)
    system_always = EvidenceGatheringSystem(use_gating=False)
    for case in cases:
        result = system_always.evaluate_case(case)
        expected = case.correct_action.value
        if result == expected:
            results["always_on"]["correct"] += 1
    
    # Test gated
    system_gated = EvidenceGatheringSystem(use_gating=True)
    for case in cases:
        result = system_gated.evaluate_case(case)
        expected = case.correct_action.value
        if result == expected:
            results["gated"]["correct"] += 1
    
    # Compute accuracy
    for key in results:
        results[key]["accuracy"] = results[key]["correct"] / results[key]["total"]
    
    return results


def main():
    """Run Phase 4 evaluation."""
    print("=" * 70)
    print("PHASE 4 EVALUATION: GATED VS ALWAYS-ON")
    print("=" * 70)
    
    results = {}
    
    # Task A: Diagnosis
    print("\n--- Task A: Diagnosis ---")
    task_a = run_task_a_evaluation(n_cases=50, seed=42)
    print(f"Always-on: {task_a['always_on']['accuracy']:.1%}")
    print(f"Gated:     {task_a['gated']['accuracy']:.1%}")
    print(f"No memory: {task_a['no_memory']['accuracy']:.1%}")
    results["task_a"] = task_a
    
    # Task B: Triage
    print("\n--- Task B: Triage ---")
    task_b = run_task_b_evaluation(n_cases=50, seed=42)
    print(f"Always-on: {task_b['always_on']['accuracy']:.1%}")
    print(f"Gated:     {task_b['gated']['accuracy']:.1%}")
    print(f"No memory: {task_b['no_memory']['accuracy']:.1%}")
    results["task_b"] = task_b
    
    # Task C: Evidence Gathering
    print("\n--- Task C: Evidence Gathering ---")
    task_c = run_task_c_evaluation(n_cases=50, seed=42)
    print(f"Always-on: {task_c['always_on']['accuracy']:.1%}")
    print(f"Gated:     {task_c['gated']['accuracy']:.1%}")
    results["task_c"] = task_c
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    always_on_avg = (
        results["task_a"]["always_on"]["accuracy"] +
        results["task_b"]["always_on"]["accuracy"] +
        results["task_c"]["always_on"]["accuracy"]
    ) / 3
    
    gated_avg = (
        results["task_a"]["gated"]["accuracy"] +
        results["task_b"]["gated"]["accuracy"] +
        results["task_c"]["gated"]["accuracy"]
    ) / 3
    
    print(f"Always-on average: {always_on_avg:.1%}")
    print(f"Gated average:     {gated_avg:.1%}")
    print(f"Improvement:       {gated_avg - always_on_avg:+.1%}")
    
    # Save results
    output_path = BASE_DIR / "gmos" / "benchmarks" / "phase4" / "evaluation_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=float)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
