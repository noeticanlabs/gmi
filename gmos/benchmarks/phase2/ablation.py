#!/usr/bin/env python3
"""
Ablation Studies for Phase 2

Tests the contribution of each governance component:
- Without repair (verify/reject only)
- Without memory (current symptoms only)
- Without budget (unlimited resources)
"""

import json
import sys
import os
import random
from typing import List, Dict, Any, Optional, Tuple

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../../src")

# Import from same directory
from task_dataset import DiagnosisDatasetGenerator
from baselines import DiagnosisResult


class GMINoRepair:
    """
    System C variant: No repair mechanism.
    
    Verifies proposals but rejects them instead of repairing.
    """
    
    def __init__(
        self,
        diagnoses: List[str],
        diagnosis_symptoms: Dict[str, List[int]],
        budget_limit: int = 100,
        reserve_floor: float = 0.15
    ):
        self.diagnoses = diagnoses
        self.diagnosis_symptoms = diagnosis_symptoms
        self.budget_limit = budget_limit
        self.reserve_floor = reserve_floor
        self.budget_used = 0
        self.verification_used = 0
        self.rejected = 0
    
    def diagnose(
        self,
        symptoms: List[int],
        memory: Optional[List[Dict]] = None
    ) -> DiagnosisResult:
        """Diagnose without repair."""
        self.budget_used = 0
        
        # Step 1: Retrieve memory
        relevant_memory = self._retrieve_memory(symptoms, memory)
        self.budget_used += 1
        
        # Step 2: Generate proposals
        candidates = self._generate_candidates(symptoms, relevant_memory)
        
        # Step 3: Score and verify (NO REPAIR)
        best = None
        best_score = -1
        
        for candidate in candidates:
            if self.budget_used >= self.budget_limit:
                break
            
            score = self._compute_coherence(candidate, symptoms, relevant_memory)
            spend = self._estimate_spend(candidate)
            
            # VERIFY - but reject if fails
            verified = self._verify(candidate, score, spend, symptoms)
            self.budget_used += 1
            
            if verified:
                self.verification_used += 1
                if score > best_score:
                    best = candidate
                    best_score = score
            else:
                self.rejected += 1  # REJECT instead of repair
        
        if best is None:
            best = self._default_diagnosis(memory)
        
        confidence = min(1.0, best_score)
        
        return DiagnosisResult(
            predicted=best,
            confidence=confidence,
            rationale=f"No repair: verified={self.verification_used}, rejected={self.rejected}",
            spend=self.budget_used,
            verified=True,
            repaired=False
        )
    
    def _retrieve_memory(self, symptoms: List[int], memory: Optional[List[Dict]]) -> List[Dict]:
        if not memory:
            return []
        relevant = []
        for case in memory:
            case_symptoms = case.get('symptoms', [])
            overlap = sum(1 for i in range(len(symptoms)) 
                        if symptoms[i] == 1 and i < len(case_symptoms) and case_symptoms[i] == 1)
            relevant.append((overlap, case))
        relevant.sort(key=lambda x: x[0], reverse=True)
        return [case for _, case in relevant[:20]]
    
    def _generate_candidates(self, symptoms: List[int], memory: List[Dict]) -> List[str]:
        candidates = set()
        for case in memory[:20]:
            candidates.add(case.get('diagnosis', ''))
        candidates.update(random.sample(self.diagnoses, min(5, len(self.diagnoses))))
        candidates.update(self.diagnoses)
        return list(candidates)[:15]
    
    def _compute_coherence(self, candidate: str, symptoms: List[int], memory: List[Dict]) -> float:
        cause_symptoms = self.diagnosis_symptoms.get(candidate, [])
        if not cause_symptoms:
            return 0.0
        match = sum(1 for s in cause_symptoms if symptoms[s] == 1)
        symptom_score = match / len(cause_symptoms)
        memory_score = 0.0
        for case in memory:
            if case.get('diagnosis') == candidate:
                memory_score += 0.1
        return min(1.0, symptom_score + memory_score)
    
    def _estimate_spend(self, candidate: str) -> int:
        return 2
    
    def _verify(self, candidate: str, score: float, spend: int, symptoms: List[int]) -> bool:
        """Verify without repair option."""
        if self.budget_used + spend > self.budget_limit:
            return False
        remaining = self.budget_limit - self.budget_used - spend
        if remaining < self.budget_limit * self.reserve_floor:
            return False
        cause_symptoms = self.diagnosis_symptoms.get(candidate, [])
        match = sum(1 for s in cause_symptoms if symptoms[s] == 1)
        if len(cause_symptoms) > 0:
            match_ratio = match / len(cause_symptoms)
            if match_ratio < 0.01:
                return False  # REJECT - no repair option
        return True
    
    def _default_diagnosis(self, memory: Optional[List[Dict]]) -> str:
        if memory:
            counts = {}
            for case in memory:
                d = case.get('diagnosis', '')
                counts[d] = counts.get(d, 0) + 1
            if counts:
                return max(counts, key=counts.get)
        return self.diagnoses[0]


class GMINoMemory:
    """
    System C variant: No memory.
    
    Uses only current symptoms for diagnosis.
    """
    
    def __init__(
        self,
        diagnoses: List[str],
        diagnosis_symptoms: Dict[str, List[int]],
        budget_limit: int = 100,
        reserve_floor: float = 0.15
    ):
        self.diagnoses = diagnoses
        self.diagnosis_symptoms = diagnosis_symptoms
        self.budget_limit = budget_limit
        self.reserve_floor = reserve_floor
        self.budget_used = 0
        self.verification_used = 0
        self.repairs = 0
    
    def diagnose(
        self,
        symptoms: List[int],
        memory: Optional[List[Dict]] = None
    ) -> DiagnosisResult:
        """Diagnose without memory."""
        self.budget_used = 0
        
        # NO MEMORY - skip retrieval
        
        # Generate all diagnoses as candidates
        candidates = self.diagnoses
        
        # Score and verify
        best = None
        best_score = -1
        
        for candidate in candidates:
            if self.budget_used >= self.budget_limit:
                break
            
            score = self._compute_coherence(candidate, symptoms, [])
            spend = self._estimate_spend(candidate)
            
            verified, repair_needed = self._verify(candidate, score, spend, symptoms)
            self.budget_used += 1
            
            if verified:
                self.verification_used += 1
                if score > best_score:
                    best = candidate
                    best_score = score
            elif repair_needed:
                self.repairs += 1
                repaired_score = score * 0.9
                if repaired_score > best_score:
                    best = candidate
                    best_score = repaired_score
        
        if best is None:
            best = self.diagnoses[0]
        
        confidence = min(1.0, best_score)
        
        return DiagnosisResult(
            predicted=best,
            confidence=confidence,
            rationale=f"No memory: verified={self.verification_used}, repaired={self.repairs}",
            spend=self.budget_used,
            verified=True,
            repaired=self.repairs > 0
        )
    
    def _compute_coherence(self, candidate: str, symptoms: List[int], memory: List[Dict]) -> float:
        cause_symptoms = self.diagnosis_symptoms.get(candidate, [])
        if not cause_symptoms:
            return 0.0
        match = sum(1 for s in cause_symptoms if symptoms[s] == 1)
        return match / len(cause_symptoms)
    
    def _estimate_spend(self, candidate: str) -> int:
        return 2
    
    def _verify(self, candidate: str, score: float, spend: int, symptoms: List[int]) -> Tuple[bool, bool]:
        """Verify with repair."""
        if self.budget_used + spend > self.budget_limit:
            return False, False
        remaining = self.budget_limit - self.budget_used - spend
        if remaining < self.budget_limit * self.reserve_floor:
            return False, False
        cause_symptoms = self.diagnosis_symptoms.get(candidate, [])
        match = sum(1 for s in cause_symptoms if symptoms[s] == 1)
        if len(cause_symptoms) > 0:
            match_ratio = match / len(cause_symptoms)
            if match_ratio < 0.01:
                return False, False
        return True, False


class GMIUnlimitedBudget:
    """
    System C variant: Unlimited budget.
    
    No budget constraints - can explore all candidates.
    """
    
    def __init__(
        self,
        diagnoses: List[str],
        diagnosis_symptoms: Dict[str, List[int]],
        reserve_floor: float = 0.0  # No reserve floor needed
    ):
        self.diagnoses = diagnoses
        self.diagnosis_symptoms = diagnosis_symptoms
        self.reserve_floor = reserve_floor
        self.budget_used = 0
        self.verification_used = 0
        self.repairs = 0
    
    def diagnose(
        self,
        symptoms: List[int],
        memory: Optional[List[Dict]] = None
    ) -> DiagnosisResult:
        """Diagnose with unlimited budget."""
        self.budget_used = 0
        
        # Retrieve memory
        relevant_memory = self._retrieve_memory(symptoms, memory)
        self.budget_used += 1
        
        # Generate ALL candidates
        candidates = self.diagnoses
        
        # Score and verify (no budget limit)
        best = None
        best_score = -1
        
        for candidate in candidates:
            score = self._compute_coherence(candidate, symptoms, relevant_memory)
            spend = self._estimate_spend(candidate)
            
            verified, repair_needed = self._verify(candidate, score, spend, symptoms)
            self.budget_used += 1
            
            if verified:
                self.verification_used += 1
                if score > best_score:
                    best = candidate
                    best_score = score
            elif repair_needed:
                self.repairs += 1
                repaired_score = score * 0.9
                if repaired_score > best_score:
                    best = candidate
                    best_score = repaired_score
        
        confidence = min(1.0, best_score)
        
        return DiagnosisResult(
            predicted=best,
            confidence=confidence,
            rationale=f"Unlimited: verified={self.verification_used}, repaired={self.repairs}",
            spend=self.budget_used,
            verified=True,
            repaired=self.repairs > 0
        )
    
    def _retrieve_memory(self, symptoms: List[int], memory: Optional[List[Dict]]) -> List[Dict]:
        if not memory:
            return []
        relevant = []
        for case in memory:
            case_symptoms = case.get('symptoms', [])
            overlap = sum(1 for i in range(len(symptoms)) 
                        if symptoms[i] == 1 and i < len(case_symptoms) and case_symptoms[i] == 1)
            relevant.append((overlap, case))
        relevant.sort(key=lambda x: x[0], reverse=True)
        return [case for _, case in relevant[:20]]
    
    def _compute_coherence(self, candidate: str, symptoms: List[int], memory: List[Dict]) -> float:
        cause_symptoms = self.diagnosis_symptoms.get(candidate, [])
        if not cause_symptoms:
            return 0.0
        match = sum(1 for s in cause_symptoms if symptoms[s] == 1)
        symptom_score = match / len(cause_symptoms)
        memory_score = 0.0
        for case in memory:
            if case.get('diagnosis') == candidate:
                memory_score += 0.1
        return min(1.0, symptom_score + memory_score)
    
    def _estimate_spend(self, candidate: str) -> int:
        return 2
    
    def _verify(self, candidate: str, score: float, spend: int, symptoms: List[int]) -> Tuple[bool, bool]:
        """Verify - no budget check."""
        cause_symptoms = self.diagnosis_symptoms.get(candidate, [])
        match = sum(1 for s in cause_symptoms if symptoms[s] == 1)
        if len(cause_symptoms) > 0:
            match_ratio = match / len(cause_symptoms)
            if match_ratio < 0.01:
                return False, False
        return True, False


def run_ablation_study():
    """Run all ablation experiments."""
    print("=" * 60)
    print("ABLATION STUDIES: GOVERNANCE COMPONENTS")
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
    
    # Import FullGMI
    from baselines import FullGMI, run_evaluation
    
    # Run ablation variants
    results = {}
    
    # 1. Full GMI (baseline)
    print("\n[2] Full GMI (baseline)...")
    system_full = FullGMI(diagnoses, diagnosis_symptoms, budget_limit=100, reserve_floor=0.15)
    results['Full GMI'] = run_evaluation(system_full, test, train)
    print(f"  Accuracy: {results['Full GMI']['accuracy']:.1%}")
    
    # 2. No Repair
    print("\n[3] GMI without Repair...")
    system_no_repair = GMINoRepair(diagnoses, diagnosis_symptoms, budget_limit=100, reserve_floor=0.15)
    results['No Repair'] = run_evaluation(system_no_repair, test, train)
    print(f"  Accuracy: {results['No Repair']['accuracy']:.1%}")
    
    # 3. No Memory
    print("\n[4] GMI without Memory...")
    system_no_memory = GMINoMemory(diagnoses, diagnosis_symptoms, budget_limit=100, reserve_floor=0.15)
    results['No Memory'] = run_evaluation(system_no_memory, test, train)
    print(f"  Accuracy: {results['No Memory']['accuracy']:.1%}")
    
    # 4. Unlimited Budget
    print("\n[5] GMI with Unlimited Budget...")
    system_unlimited = GMIUnlimitedBudget(diagnoses, diagnosis_symptoms, reserve_floor=0.0)
    results['Unlimited Budget'] = run_evaluation(system_unlimited, test, train)
    print(f"  Accuracy: {results['Unlimited Budget']['accuracy']:.1%}")
    
    # Summary
    print("\n" + "=" * 60)
    print("ABLATION SUMMARY")
    print("=" * 60)
    print(f"\n{'Variant':<20} {'Accuracy':>10} {'vs Full':>10}")
    print("-" * 60)
    
    baseline_acc = results['Full GMI']['accuracy']
    
    for name, result in results.items():
        acc = result['accuracy']
        diff = acc - baseline_acc
        diff_str = f"+{diff:.1%}" if diff > 0 else f"{diff:.1%}"
        print(f"{name:<20} {acc:>9.1%} {diff_str:>10}")
    
    print("\n" + "=" * 60)
    print("KEY INSIGHTS:")
    print("=" * 60)
    
    # Analyze contributions
    repair_value = results['Full GMI']['accuracy'] - results['No Repair']['accuracy']
    memory_value = results['Full GMI']['accuracy'] - results['No Memory']['accuracy']
    budget_value = results['Unlimited Budget']['accuracy'] - results['Full GMI']['accuracy']
    
    print(f"\nRepair value: {repair_value:+.1%}")
    print(f"Memory value: {memory_value:+.1%}")
    print(f"Budget constraint cost: {-budget_value:+.1%}")
    
    # Save results
    output_path = "/home/user/gmi/gmos/benchmarks/phase2/ablation_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    run_ablation_study()
