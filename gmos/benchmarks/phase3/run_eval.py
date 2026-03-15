#!/usr/bin/env python3
"""
Phase 3 Evaluation Runner

Runs multi-task evaluation comparing:
- Task A: Constrained Diagnosis (from Phase 2)
- Task B: Constrained Maintenance Triage (new)

With ablations:
- Full system with enhanced memory
- No memory (ablation)
- No adaptation
- No SafeHold
"""

import json
import sys
import os
import random
import importlib.util
from typing import List, Dict, Any, Optional

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../../src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load Phase 2 components directly
import os
# BASE_DIR is /home/user/gmi/gmos/benchmarks/phase3, go up to /home/user/gmi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

phase2_spec = importlib.util.spec_from_file_location("phase2_task", 
    os.path.join(BASE_DIR, "benchmarks/phase2/task_dataset.py"))
phase2_task = importlib.util.module_from_spec(phase2_spec)
phase2_spec.loader.exec_module(phase2_task)
DiagnosisDatasetGenerator = phase2_task.DiagnosisDatasetGenerator

# Import Phase 3 components using direct loading
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

enhanced_retrieval = load_module("enhanced_retrieval", 
    os.path.join(BASE_DIR, "src/gmos/memory/enhanced_retrieval.py"))
mode_machine = load_module("mode_machine", 
    os.path.join(BASE_DIR, "src/gmos/runtime/mode_machine.py"))
adaptation = load_module("adaptation", 
    os.path.join(BASE_DIR, "src/gmos/agents/gmi/adaptation.py"))

create_retrieval_engine = enhanced_retrieval.create_retrieval_engine
create_mode_machine = mode_machine.create_mode_machine
create_adaptation_tracker = adaptation.create_adaptation_tracker


# =============================================================================
# Task A: Diagnosis (from Phase 2)
# =============================================================================

class DiagnosisWithEnhancedMemory:
    """
    Enhanced diagnosis system using Phase 3 memory.
    """
    
    def __init__(
        self,
        diagnoses: List[str],
        diagnosis_symptoms: Dict[str, List[int]],
        budget_limit: int = 10,
        reserve_floor: float = 0.2,
        use_memory: bool = True,
        use_adaptation: bool = True,
        use_safehold: bool = False,  # Not relevant for diagnosis
    ):
        self.diagnoses = diagnoses
        self.diagnosis_symptoms = diagnosis_symptoms
        self.budget_limit = budget_limit
        self.reserve_floor = reserve_floor
        self.use_memory = use_memory
        self.use_adaptation = use_adaptation
        
        # Phase 3 components
        self.retrieval_engine = create_retrieval_engine("diagnosis")
        RuntimeMode = mode_machine.RuntimeMode
        TransitionReason = mode_machine.TransitionReason
        self.mode_machine = create_mode_machine(enable_safehold=False)
        self.adaptation_tracker = create_adaptation_tracker() if use_adaptation else None
        
        # Memory store
        self.memory_cases = []
        
    def add_memory(self, case: Dict[str, Any]) -> None:
        """Add a memory case."""
        self.memory_cases.append(case)
    
    def diagnose(
        self,
        symptoms: List[int],
        memory: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Diagnose with optional memory."""
        
        # Use provided memory or stored memory
        memory_cases = memory if memory is not None else self.memory_cases
        
        # Track budget
        budget = self.budget_limit
        spent = 0
        
        # Mode: OBSERVE (symptoms are already given)
        RuntimeMode = mode_machine.RuntimeMode
        TransitionReason = mode_machine.TransitionReason
        self.mode_machine.transition(
            RuntimeMode.RECALL,
            TransitionReason.PERCEPT_COMPLETE
        )
        
        retrieved_memory = []
        
        # Memory retrieval (if enabled)
        if self.use_memory and memory_cases:
            # Convert symptoms to dict for retrieval
            symptom_dict = {f"symptom_{i}": bool(s) for i, s in enumerate(symptoms)}
            
            query = {"symptoms": symptom_dict}
            
            results = self.retrieval_engine.retrieve(
                memory_cases,
                query,
                top_k=5
            )
            
            retrieved_memory = [r.episode for r in results]
        
        # Mode: DELIBERATE
        self.mode_machine.transition(
            RuntimeMode.DELIBERATE,
            TransitionReason.MEMORY_RETRIEVED
        )
        
        # Score each diagnosis
        scores = {}
        for diagnosis in self.diagnoses:
            # Base score from symptom match
            base_symptoms = self.diagnosis_symptoms.get(diagnosis, [])
            base_score = sum(1 for s in base_symptoms if symptoms[s])
            
            # Memory bonus
            memory_bonus = 0
            if retrieved_memory:
                for mem in retrieved_memory:
                    mem_diag = mem.get("diagnosis", "")
                    if mem_diag == diagnosis:
                        # Check outcome
                        outcome = mem.get("outcome", "")
                        if outcome in ["correct", "resolved", "success"]:
                            memory_bonus += 0.3
                        elif outcome in ["incorrect", "failed"]:
                            memory_bonus -= 0.2
            
            scores[diagnosis] = base_score + memory_bonus
        
        # Select best
        predicted = max(scores, key=scores.get)
        confidence = min(0.5 + scores[predicted] / 10.0, 0.95)
        
        spent = 2 if retrieved_memory else 1
        
        return {
            "predicted": predicted,
            "confidence": confidence,
            "score": scores[predicted],
            "spent": spent,
            "memory_used": bool(retrieved_memory),
            "memory_retrieved": len(retrieved_memory),
        }


# =============================================================================
# Task B: Triage (new for Phase 3)
# =============================================================================

class TriageWithEnhancedMemory:
    """
    Triage system using Phase 3 memory and SafeHold.
    """
    
    ACTIONS = [
        "INSPECT_LOCAL", "CONTINUE_MONITOR", "GATHER_EVIDENCE",
        "REPLACE_COMPONENT", "SHUT_DOWN", "ESCALATE_SPECIALIST", "SAFEHOLD_ABSTAIN"
    ]
    
    def __init__(
        self,
        budget_limit: int = 8,
        reserve_floor: float = 0.2,
        use_memory: bool = True,
        use_adaptation: bool = True,
        use_safehold: bool = True,
    ):
        self.budget_limit = budget_limit
        self.reserve_floor = reserve_floor
        self.use_memory = use_memory
        self.use_adaptation = use_adaptation
        self.use_safehold = use_safehold
        
        # Phase 3 components
        self.retrieval_engine = create_retrieval_engine("triage")
        self.mode_machine = create_mode_machine(enable_safehold=use_safehold)
        self.adaptation_tracker = create_adaptation_tracker() if use_adaptation else None
        
        # Memory store
        self.memory_cases = []
        
    def add_memory(self, case: Dict[str, Any]) -> None:
        """Add a memory case."""
        self.memory_cases.append(case)
    
    def triage(
        self,
        symptoms: Dict[str, bool],
        context: Dict[str, Any],
        severity: int,
        memory: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Select action with optional memory and SafeHold."""
        
        # Use provided memory or stored memory
        memory_cases = memory if memory is not None else self.memory_cases
        
        # Track budget
        budget = self.budget_limit
        spent = 0
        
        # Mode: OBSERVE
        RuntimeMode = mode_machine.RuntimeMode
        TransitionReason = mode_machine.TransitionReason
        self.mode_machine.transition(
            RuntimeMode.RECALL,
            TransitionReason.PERCEPT_COMPLETE
        )
        
        retrieved_memory = []
        
        # Memory retrieval (if enabled)
        if self.use_memory and memory_cases:
            query = {"symptoms": symptoms, "context": context}
            
            results = self.retrieval_engine.retrieve(
                memory_cases,
                query,
                top_k=5
            )
            
            retrieved_memory = [r.episode for r in results]
        
        # Mode: DELIBERATE
        self.mode_machine.transition(
            RuntimeMode.DELIBERATE,
            TransitionReason.MEMORY_RETRIEVED
        )
        
        # Check SafeHold condition
        if self.use_safehold:
            # Calculate confidence based on memory
            confidence = 0.5
            if retrieved_memory:
                # Average outcome score
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
            
            # Check budget
            budget_ratio = (budget - spent) / self.budget_limit if self.budget_limit > 0 else 0
            
            should_hold = self.mode_machine.check_safehold_condition(
                confidence=confidence,
                budget_remaining=budget_ratio * self.budget_limit,
                budget_total=self.budget_limit,
                valid_proposals=1
            )
            
            if should_hold:
                self.mode_machine.transition(
                    RuntimeMode.SAFE_HOLD,
                    TransitionReason.UNCERTAINTY_HIGH
                )
                return {
                    "predicted": "SAFEHOLD_ABSTAIN",
                    "confidence": confidence,
                    "spent": spent + 1,
                    "safehold": True,
                    "memory_used": bool(retrieved_memory),
                }
        
        # Score each action
        scores = {}
        for action in self.ACTIONS:
            if action == "SAFEHOLD_ABSTAIN":
                scores[action] = 0.1  # Low default
                continue
            
            # Base score from symptom match (simplified)
            base_score = 0.5
            
            # Memory bonus
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
        
        # Select best
        predicted = max(scores, key=scores.get)
        confidence = min(0.3 + scores[predicted], 0.95)
        
        spent = 2 if retrieved_memory else 1
        
        return {
            "predicted": predicted,
            "confidence": confidence,
            "score": scores[predicted],
            "spent": spent,
            "safehold": False,
            "memory_used": bool(retrieved_memory),
            "memory_retrieved": len(retrieved_memory),
        }


# =============================================================================
# Evaluation Functions
# =============================================================================

def run_diagnosis_evaluation(
    system,
    test_cases: List[Dict],
    memory_cases: List[Dict],
    use_memory: bool = True
) -> Dict[str, Any]:
    """Run diagnosis evaluation."""
    
    correct = 0
    total = 0
    total_spent = 0
    memory_used_count = 0
    
    for case in test_cases:
        # Add memory to system
        if hasattr(system, 'memory_cases'):
            system.memory_cases = memory_cases
        
        result = system.diagnose(
            symptoms=case['symptoms'],
            memory=memory_cases if use_memory else None
        )
        
        if result['predicted'] == case['diagnosis']:
            correct += 1
        
        total += 1
        total_spent += result['spent']
        if result.get('memory_used'):
            memory_used_count += 1
    
    return {
        "accuracy": correct / total if total > 0 else 0,
        "total_cases": total,
        "avg_spent": total_spent / total if total > 0 else 0,
        "memory_usage_rate": memory_used_count / total if total > 0 else 0,
    }


def run_triage_evaluation(
    system,
    test_cases: List[Dict],
    memory_cases: List[Dict],
    use_memory: bool = True
) -> Dict[str, Any]:
    """Run triage evaluation."""
    
    correct = 0
    total = 0
    total_spent = 0
    memory_used_count = 0
    safehold_count = 0
    
    for case in test_cases:
        # Add memory to system
        if hasattr(system, 'memory_cases'):
            system.memory_cases = memory_cases
        
        result = system.triage(
            symptoms=case['symptoms'],
            context=case['context'],
            severity=case['severity'],
            memory=memory_cases if use_memory else None
        )
        
        if result['predicted'] == case['correct_action']:
            correct += 1
        
        if result.get('safehold'):
            safehold_count += 1
        
        total += 1
        total_spent += result['spent']
        if result.get('memory_used'):
            memory_used_count += 1
    
    return {
        "accuracy": correct / total if total > 0 else 0,
        "total_cases": total,
        "avg_spent": total_spent / total if total > 0 else 0,
        "memory_usage_rate": memory_used_count / total if total > 0 else 0,
        "safehold_rate": safehold_count / total if total > 0 else 0,
    }


def run_ablations(
    task_name: str,
    test_cases: List[Dict],
    memory_cases: List[Dict],
    create_system_fn,
    run_eval_fn,
) -> Dict[str, Any]:
    """Run all ablation variants."""
    
    results = {}
    
    # Full system
    system = create_system_fn(use_memory=True, use_adaptation=True, use_safehold=True)
    results['full'] = run_eval_fn(system, test_cases, memory_cases, use_memory=True)
    
    # No memory
    system = create_system_fn(use_memory=False, use_adaptation=False, use_safehold=True)
    results['no_memory'] = run_eval_fn(system, test_cases, memory_cases, use_memory=False)
    
    # No adaptation
    system = create_system_fn(use_memory=True, use_adaptation=False, use_safehold=True)
    results['no_adaptation'] = run_eval_fn(system, test_cases, memory_cases, use_memory=True)
    
    # No SafeHold (Task B only)
    if 'safehold_rate' in results.get('full', {}):
        system = create_system_fn(use_memory=True, use_adaptation=True, use_safehold=False)
        results['no_safehold'] = run_eval_fn(system, test_cases, memory_cases, use_memory=True)
    
    return results


def main():
    print("=" * 70)
    print("PHASE 3 EVALUATION: MULTI-TASK SUBSTRATE VALUE")
    print("=" * 70)
    
    random.seed(42)
    
    # =========================================================================
    # TASK A: Diagnosis
    # =========================================================================
    print("\n" + "=" * 70)
    print("TASK A: CONSTRAINED DIAGNOSIS")
    print("=" * 70)
    
    # Generate dataset
    print("\n[1] Generating Task A dataset...")
    gen_a = DiagnosisDatasetGenerator(n_diagnoses=10, n_symptoms=20, seed=42)
    dataset_a = gen_a.generate_dataset(n_train=500, n_test=100)
    train_a = dataset_a['train']
    test_a = dataset_a['test']
    diagnoses = dataset_a['diagnoses']
    diagnosis_symptoms = dataset_a['diagnosis_symptoms']
    
    print(f"  Train: {len(train_a)}, Test: {len(test_a)}")
    
    # Convert memory to dict format
    memory_a = [
        {"diagnosis": t['diagnosis'], "symptoms": t['symptoms'], "outcome": "correct"}
        for t in train_a[:100]
    ]
    
    # Create system factory
    def create_diagnosis_system(use_memory, use_adaptation, use_safehold):
        return DiagnosisWithEnhancedMemory(
            diagnoses=diagnoses,
            diagnosis_symptoms=diagnosis_symptoms,
            budget_limit=10,
            use_memory=use_memory,
            use_adaptation=use_adaptation,
            use_safehold=use_safehold,
        )
    
    # Run ablations
    print("\n[2] Running Task A ablations...")
    results_a = run_ablations(
        "diagnosis", test_a, memory_a,
        create_diagnosis_system, run_diagnosis_evaluation
    )
    
    print(f"\n  Full system:        {results_a['full']['accuracy']:.1%}")
    print(f"  No memory:          {results_a['no_memory']['accuracy']:.1%}")
    print(f"  No adaptation:      {results_a['no_adaptation']['accuracy']:.1%}")
    
    memory_benefit_a = results_a['full']['accuracy'] - results_a['no_memory']['accuracy']
    print(f"\n  Memory benefit:     {memory_benefit_a:+.1%}")
    
    # =========================================================================
    # TASK B: Triage
    # =========================================================================
    print("\n" + "=" * 70)
    print("TASK B: CONSTRAINED MAINTENANCE TRIAGE")
    print("=" * 70)
    
    # Generate dataset
    print("\n[3] Generating Task B dataset...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/task_b")
    from dataset import generate_dataset as generate_triage_dataset
    
    dataset_b = generate_triage_dataset(n_train=200, n_test=100, seed=42)
    memory_b = dataset_b['memory']
    test_b = dataset_b['test']
    
    print(f"  Memory: {len(memory_b)}, Test: {len(test_b)}")
    
    # Create system factory
    def create_triage_system(use_memory, use_adaptation, use_safehold):
        return TriageWithEnhancedMemory(
            budget_limit=8,
            use_memory=use_memory,
            use_adaptation=use_adaptation,
            use_safehold=use_safehold,
        )
    
    # Run ablations
    print("\n[4] Running Task B ablations...")
    results_b = run_ablations(
        "triage", test_b, memory_b,
        create_triage_system, run_triage_evaluation
    )
    
    print(f"\n  Full system:        {results_b['full']['accuracy']:.1%}")
    print(f"  No memory:          {results_b['no_memory']['accuracy']:.1%}")
    print(f"  No adaptation:      {results_b['no_adaptation']['accuracy']:.1%}")
    print(f"  No SafeHold:        {results_b['no_safehold']['accuracy']:.1%}")
    print(f"  SafeHold rate:      {results_b['full']['safehold_rate']:.1%}")
    
    memory_benefit_b = results_b['full']['accuracy'] - results_b['no_memory']['accuracy']
    print(f"\n  Memory benefit:     {memory_benefit_b:+.1%}")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    mgsr = (results_a['full']['accuracy'] + results_b['full']['accuracy']) / 2
    
    print(f"\n  Multi-Task Success Rate: {mgsr:.1%}")
    print(f"\n  Task A (Diagnosis):")
    print(f"    - Full:     {results_a['full']['accuracy']:.1%}")
    print(f"    - No mem:  {results_a['no_memory']['accuracy']:.1%}")
    print(f"    - Benefit: {memory_benefit_a:+.1%}")
    print(f"\n  Task B (Triage):")
    print(f"    - Full:     {results_b['full']['accuracy']:.1%}")
    print(f"    - No mem:  {results_b['no_memory']['accuracy']:.1%}")
    print(f"    - Benefit: {memory_benefit_b:+.1%}")
    
    # Phase 3 success criteria
    print("\n" + "-" * 70)
    print("PHASE 3 STATUS:")
    
    memory_helps = memory_benefit_a >= 0 or memory_benefit_b >= 0
    no_collapse = results_b['full']['accuracy'] > 0.1
    
    print(f"  Memory benefit ≥ 0%:     {'✓' if memory_helps else '✗'} ({memory_benefit_b:+.1%} on Task B)")
    print(f"  Task B no collapse:       {'✓' if no_collapse else '✗'} ({results_b['full']['accuracy']:.1%})")
    
    if memory_helps and no_collapse:
        print("\n  Phase 3 MINIMUM COMPLETION: ACHIEVED ✓")
    else:
        print("\n  Phase 3: More work needed")
    
    # Save results
    output = {
        "task_a": results_a,
        "task_b": results_b,
        "summary": {
            "mgsr": mgsr,
            "memory_benefit_a": memory_benefit_a,
            "memory_benefit_b": memory_benefit_b,
        }
    }
    
    with open("gmos/benchmarks/phase3/results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: gmos/benchmarks/phase3/results.json")


if __name__ == "__main__":
    main()
