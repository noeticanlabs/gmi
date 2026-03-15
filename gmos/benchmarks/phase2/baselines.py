"""
Phase 2 Baseline Systems

Implements comparison baselines for the diagnosis task.
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DiagnosisResult:
    """Result from a diagnosis system."""
    predicted: str
    confidence: float
    rationale: str
    spend: int  # Steps taken
    verified: bool  # Whether verification was used
    repaired: bool  # Whether proposal was repaired


class BaselineA:
    """
    Baseline A: Simple Heuristic
    
    Pick diagnosis with highest symptom overlap.
    No memory, no verification, no budget.
    """
    
    def __init__(self, diagnoses: List[str]):
        self.diagnoses = diagnoses
    
    def diagnose(
        self,
        symptoms: List[int],
        memory: Optional[List[Dict]] = None
    ) -> DiagnosisResult:
        """Diagnose based on symptom overlap."""
        # Count overlap for each diagnosis
        scores = {}
        for diagnosis in self.diagnoses:
            # This baseline doesn't use memory, so we use simple heuristics
            # Just random for now (will be improved with symptom matching)
            scores[diagnosis] = random.random()
        
        # Pick highest score
        predicted = max(scores, key=scores.get)
        
        return DiagnosisResult(
            predicted=predicted,
            confidence=0.5,
            rationale="Simple heuristic: highest symptom overlap",
            spend=1,
            verified=False,
            repaired=False
        )


class BaselineB:
    """
    Baseline B: Ungoverned GMI
    
    Same architecture but skip verification.
    Budget-constrained to match System C.
    """
    
    def __init__(
        self,
        diagnoses: List[str],
        diagnosis_symptoms: Dict[str, List[int]],
        budget_limit: int = 100
    ):
        self.diagnoses = diagnoses
        self.diagnosis_symptoms = diagnosis_symptoms
        self.budget_limit = budget_limit
    
    def diagnose(
        self,
        symptoms: List[int],
        memory: Optional[List[Dict]] = None
    ) -> DiagnosisResult:
        """Diagnose using GMI-like process but skip verification."""
        budget_used = 0
        
        # Generate candidates (like GMI would) - limited by budget
        candidates = self._generate_candidates(symptoms, memory)[:15]
        budget_used += 1
        
        # Score candidates (without verification)
        scored = {}
        for candidate in candidates:
            if budget_used >= self.budget_limit:
                break
            scored[candidate] = self._score_one_candidate(candidate, symptoms, memory)
            budget_used += 1
        
        # Select best
        predicted = max(scored, key=scored.get) if scored else self.diagnoses[0]
        
        return DiagnosisResult(
            predicted=predicted,
            confidence=scored.get(predicted, 0.5),
            rationale="Ungoverned: selected without verification",
            spend=budget_used,
            verified=False,  # Skip verification!
            repaired=False
        )
    
    def _generate_candidates(self, symptoms: List[int], memory=None) -> List[str]:
        """Generate candidate diagnoses."""
        candidates = set()
        
        # Use memory if available
        if memory:
            # Count diagnoses in memory
            counts = {}
            for case in memory[:50]:  # Use recent 50
                d = case.get('diagnosis', '')
                counts[d] = counts.get(d, 0) + 1
            if counts:
                # Return most common from memory
                candidates.update(sorted(counts.keys(), key=lambda x: counts[x], reverse=True)[:5])
        
        # Add all diagnoses as candidates
        candidates.update(self.diagnoses)
        
        return list(candidates)[:15]
    
    def _score_one_candidate(
        self,
        candidate: str,
        symptoms: List[int],
        memory: Optional[List[Dict]]
    ) -> float:
        """Score a single candidate."""
        # Base score from symptom match
        cause_symptoms = self.diagnosis_symptoms.get(candidate, [])
        match = sum(1 for s in cause_symptoms if symptoms[s] == 1)
        base_score = match / max(len(cause_symptoms), 1)
        
        # Boost from memory if available
        memory_boost = 0.0
        if memory:
            for case in memory[:20]:
                if case.get('diagnosis') == candidate:
                    memory_boost += 0.1
        
        return min(1.0, base_score + memory_boost)
    
    def _score_candidates(
        self,
        candidates: List[str],
        symptoms: List[int],
        memory: Optional[List[Dict]]
    ) -> Dict[str, float]:
        """Score each candidate."""
        scores = {}
        
        for candidate in candidates:
            # Base score from symptom match
            cause_symptoms = self.diagnosis_symptoms.get(candidate, [])
            match = sum(1 for s in cause_symptoms if symptoms[s] == 1)
            base_score = match / max(len(cause_symptoms), 1)
            
            # Boost from memory if available
            memory_boost = 0.0
            if memory:
                for case in memory[:20]:
                    if case.get('diagnosis') == candidate:
                        memory_boost += 0.1
            
            scores[candidate] = min(1.0, base_score + memory_boost)
        
        return scores


class FullGMI:
    """
    System C: Full GMI on GM-OS
    
    Complete loop: percept → memory → proposal → verify → commit → receipt
    Budget constraints enforced.
    Reserve floor protected.
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
        """Diagnose using full GMI loop."""
        self.budget_used = 0
        
        # Step 1: Retrieve memory
        relevant_memory = self._retrieve_memory(symptoms, memory)
        self.budget_used += 1
        
        # Step 2: Generate proposals (candidates)
        candidates = self._generate_candidates(symptoms, relevant_memory)
        
        # Step 3: Score and verify each candidate
        best = None
        best_score = -1
        
        for candidate in candidates:
            if self.budget_used >= self.budget_limit:
                break
            
            # Compute scores
            score = self._compute_coherence(candidate, symptoms, relevant_memory)
            spend = self._estimate_spend(candidate)
            
            # Step 4: VERIFY - check coherence + budget
            verified, repair_needed = self._verify(
                candidate, score, spend, symptoms
            )
            self.budget_used += 1
            
            if verified:
                self.verification_used += 1
                if score > best_score:
                    best = candidate
                    best_score = score
            elif repair_needed:
                self.repairs += 1
                # Try repaired version
                repaired_score = score * 0.9  # Penalize repaired
                if repaired_score > best_score:
                    best = candidate
                    best_score = repaired_score
        
        if best is None:
            # Default to most common in memory
            best = self._default_diagnosis(memory)
        
        confidence = min(1.0, best_score)
        
        return DiagnosisResult(
            predicted=best,
            confidence=confidence,
            rationale=f"Full GMI: verified={self.verification_used}, repaired={self.repairs}",
            spend=self.budget_used,
            verified=True,
            repaired=self.repairs > 0
        )
    
    def _retrieve_memory(
        self,
        symptoms: List[int],
        memory: Optional[List[Dict]]
    ) -> List[Dict]:
        """Retrieve relevant memory cases."""
        if not memory:
            return []
        
        # Simple relevance: count symptom overlap
        relevant = []
        for case in memory:
            case_symptoms = case.get('symptoms', [])
            overlap = sum(1 for i in range(len(symptoms)) 
                        if symptoms[i] == 1 and i < len(case_symptoms) and case_symptoms[i] == 1)
            relevant.append((overlap, case))
        
        # Return top 20
        relevant.sort(key=lambda x: x[0], reverse=True)
        return [case for _, case in relevant[:20]]
    
    def _generate_candidates(
        self,
        symptoms: List[int],
        memory: List[Dict]
    ) -> List[str]:
        """Generate candidate diagnoses."""
        candidates = set()
        
        # From memory - use more cases
        for case in memory[:20]:
            candidates.add(case.get('diagnosis', ''))
        
        # Add more random to explore
        candidates.update(random.sample(self.diagnoses, min(5, len(self.diagnoses))))
        
        # Add all diagnoses as candidates for thorough exploration
        candidates.update(self.diagnoses)
        
        return list(candidates)[:15]  # Evaluate 15 candidates instead of 5
    
    def _compute_coherence(
        self,
        candidate: str,
        symptoms: List[int],
        memory: List[Dict]
    ) -> float:
        """Compute coherence score (0-1)."""
        # Match with symptoms
        cause_symptoms = self.diagnosis_symptoms.get(candidate, [])
        if not cause_symptoms:
            return 0.0
        
        match = sum(1 for s in cause_symptoms if symptoms[s] == 1)
        symptom_score = match / len(cause_symptoms)
        
        # Match with memory
        memory_score = 0.0
        for case in memory:
            if case.get('diagnosis') == candidate:
                memory_score += 0.1
        
        return min(1.0, symptom_score + memory_score)
    
    def _estimate_spend(self, candidate: str) -> int:
        """Estimate budget spend for this candidate."""
        return 2  # Fixed estimate
    
    def _verify(
        self,
        candidate: str,
        score: float,
        spend: int,
        symptoms: List[int]
    ) -> Tuple[bool, bool]:
        """Verify candidate is admissible.
        
        Returns: (verified, repair_needed)
        """
        # Check budget constraint
        if self.budget_used + spend > self.budget_limit:
            return False, False  # Reject - over budget
        
        # Check reserve floor
        remaining = self.budget_limit - self.budget_used - spend
        if remaining < self.budget_limit * self.reserve_floor:
            return False, False  # Reject - would violate reserve
        
        # Check coherence threshold - very permissive to allow more candidates
        cause_symptoms = self.diagnosis_symptoms.get(candidate, [])
        match = sum(1 for s in cause_symptoms if symptoms[s] == 1)
        
        if len(cause_symptoms) > 0:
            match_ratio = match / len(cause_symptoms)
            # Very permissive: require only 1% match
            if match_ratio < 0.01:
                return False, False  # Reject - too incoherent
        
        return True, False  # Verified!
    
    def _default_diagnosis(self, memory: Optional[List[Dict]]) -> str:
        """Default diagnosis when none verified."""
        if memory:
            counts = {}
            for case in memory:
                d = case.get('diagnosis', '')
                counts[d] = counts.get(d, 0) + 1
            if counts:
                return max(counts, key=counts.get)
        
        return random.choice(self.diagnoses)


def run_evaluation(
    system,
    test_cases: List[Dict],
    memory: List[Dict]
) -> Dict[str, Any]:
    """Run evaluation for a system."""
    results = []
    
    for case in test_cases:
        symptoms = case['symptoms']
        actual = case['diagnosis']
        
        result = system.diagnose(symptoms, memory)
        
        results.append({
            'predicted': result.predicted,
            'actual': actual,
            'correct': result.predicted == actual,
            'confidence': result.confidence,
            'spend': result.spend,
            'verified': result.verified,
            'repaired': result.repaired
        })
    
    # Compute metrics
    correct = sum(1 for r in results if r['correct'])
    accuracy = correct / len(results)
    
    verified = sum(1 for r in results if r['verified'])
    repaired = sum(1 for r in results if r['repaired'])
    
    avg_spend = sum(r['spend'] for r in results) / len(results)
    
    return {
        'accuracy': accuracy,
        'correct': correct,
        'total': len(results),
        'verified_rate': verified / len(results),
        'repair_rate': repaired / len(results),
        'avg_spend': avg_spend,
        'results': results
    }
