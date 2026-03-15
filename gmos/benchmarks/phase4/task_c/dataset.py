"""
Phase 4 Task C: Evidence-Gathering Recommendation Dataset Generator

This task evaluates the system's ability to make calibrated decisions
under uncertainty - choosing when to proceed, request evidence, or abstain.
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ScenarioType(Enum):
    """Types of scenarios with different uncertainty levels."""
    CLEAR_CASE = "clear_case"          # Low uncertainty
    AMBIGUOUS_CASE = "ambiguous_case"  # Medium uncertainty
    UNKNOWN_CASE = "unknown_case"       # High uncertainty
    CONFLICTING_EVIDENCE = "conflicting"  # Conflicting evidence


class ActionType(Enum):
    """Possible action types."""
    PROCEED = "proceed"
    REQUEST_EVIDENCE = "request_evidence"
    ABSTAIN = "abstain"


@dataclass
class EvidenceGatheringCase:
    """A single case for evidence-gathering evaluation."""
    case_id: str
    situation: str
    current_evidence: Dict[str, Any]
    available_evidence_options: List[str]
    scenario_type: ScenarioType
    uncertainty: float  # 0.0 to 1.0
    difficulty: float   # 0.0 to 1.0
    
    # Correct answers
    correct_action: ActionType
    correct_specific: str  # Specific diagnosis or evidence type
    
    # What evidence would help
    helpful_evidence: str


class EvidenceGatheringDatasetGenerator:
    """Generate synthetic evidence-gathering dataset."""
    
    # Disease definitions for diagnosis scenarios
    DIAGNOSES = [
        "infection", "allergy", "autoimmune", "toxic_exposure",
        "nutritional_deficiency", "mechanical_issue", "genetic_disorder"
    ]
    
    # Evidence types
    EVIDENCE_TYPES = [
        "symptom_temperature",      # Body temperature reading
        "symptom_blood_pressure",    # Blood pressure
        "symptom_lab_results",        # Lab test results
        "context_environment",        # Environmental factors
        "history_family",            # Family medical history
        "history_travel",            # Recent travel
        "sensor_cardiac",            # Cardiac monitor reading
        "sensor_respiratory",        # Respiratory monitor
    ]
    
    # Symptoms mapped to diagnoses
    DIAGNOSIS_SYMPTOMS = {
        "infection": ["fever", "fatigue", "cough"],
        "allergy": ["rash", "sneezing", "itching"],
        "autoimmune": ["joint_pain", "fatigue", "fever"],
        "toxic_exposure": ["headache", "nausea", "dizziness"],
        "nutritional_deficiency": ["fatigue", "pallor", "weakness"],
        "mechanical_issue": ["pain", "limited_movement", "swelling"],
        "genetic_disorder": ["family_history", "developmental_delay"],
    }
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
    
    def generate_case(
        self,
        scenario_type: Optional[ScenarioType] = None,
        difficulty: float = 0.5,
    ) -> EvidenceGatheringCase:
        """Generate a single evidence-gathering case."""
        
        # Select scenario type if not specified
        if scenario_type is None:
            scenario_type = self._select_scenario_type()
        
        # Generate based on scenario type
        if scenario_type == ScenarioType.CLEAR_CASE:
            return self._generate_clear_case(difficulty)
        elif scenario_type == ScenarioType.AMBIGUOUS_CASE:
            return self._generate_ambiguous_case(difficulty)
        elif scenario_type == ScenarioType.UNKNOWN_CASE:
            return self._generate_unknown_case(difficulty)
        else:  # CONFLICTING_EVIDENCE
            return self._generate_conflicting_case(difficulty)
    
    def _select_scenario_type(self) -> ScenarioType:
        """Select scenario type with appropriate distribution."""
        r = random.random()
        if r < 0.25:
            return ScenarioType.CLEAR_CASE
        elif r < 0.55:
            return ScenarioType.AMBIGUOUS_CASE
        elif r < 0.80:
            return ScenarioType.UNKNOWN_CASE
        else:
            return ScenarioType.CONFLICTING_EVIDENCE
    
    def _generate_clear_case(self, difficulty: float) -> EvidenceGatheringCase:
        """Generate a clear case with low uncertainty."""
        diagnosis = random.choice(self.DIAGNOSES)
        symptoms = self.DIAGNOSIS_SYMPTOMS[diagnosis]
        
        # Strong evidence for diagnosis
        current_evidence = {
            "primary_symptom": symptoms[0],
            "secondary_symptom": symptoms[1] if len(symptoms) > 1 else None,
            "duration_days": random.randint(5, 14),
        }
        
        return EvidenceGatheringCase(
            case_id=f"clear_{random.randint(1000, 9999)}",
            situation=f"Patient presents with clear symptoms of {diagnosis}. "
                     f"Primary symptom: {symptoms[0]}.",
            current_evidence=current_evidence,
            available_evidence_options=self.EVIDENCE_TYPES,
            scenario_type=ScenarioType.CLEAR_CASE,
            uncertainty=random.uniform(0.05, 0.25),
            difficulty=difficulty * 0.3,  # Easier
            correct_action=ActionType.PROCEED,
            correct_specific=diagnosis,
            helpful_evidence="none_needed",
        )
    
    def _generate_ambiguous_case(self, difficulty: float) -> EvidenceGatheringCase:
        """Generate an ambiguous case with medium uncertainty."""
        # Two possible diagnoses
        possible = random.sample(self.DIAGNOSES, 2)
        
        current_evidence = {
            "primary_symptom": "fatigue",  # Common to many
            "secondary_symptom": "general_discomfort",
            "duration_days": random.randint(2, 7),
        }
        
        # What evidence would help
        helpful = random.choice([
            "symptom_lab_results",
            "history_family",
            "context_environment",
        ])
        
        return EvidenceGatheringCase(
            case_id=f"ambiguous_{random.randint(1000, 9999)}",
            situation=f"Patient presents with ambiguous symptoms. "
                     f"Could be {possible[0]} or {possible[1]}.",
            current_evidence=current_evidence,
            available_evidence_options=self.EVIDENCE_TYPES,
            scenario_type=ScenarioType.AMBIGUOUS_CASE,
            uncertainty=random.uniform(0.35, 0.55),
            difficulty=difficulty,
            correct_action=ActionType.REQUEST_EVIDENCE,
            correct_specific=helpful,
            helpful_evidence=helpful,
        )
    
    def _generate_unknown_case(self, difficulty: float) -> EvidenceGatheringCase:
        """Generate an unknown case with high uncertainty."""
        current_evidence = {
            "primary_symptom": None,
            "secondary_symptom": None,
            "duration_days": 1,
        }
        
        return EvidenceGatheringCase(
            case_id=f"unknown_{random.randint(1000, 9999)}",
            situation="Patient presents with vague symptoms. "
                     "Not enough information to proceed.",
            current_evidence=current_evidence,
            available_evidence_options=self.EVIDENCE_TYPES,
            scenario_type=ScenarioType.UNKNOWN_CASE,
            uncertainty=random.uniform(0.70, 0.95),
            difficulty=difficulty * 1.2,  # Harder
            correct_action=ActionType.REQUEST_EVIDENCE,
            correct_specific="symptom_lab_results",
            helpful_evidence="symptom_lab_results",
        )
    
    def _generate_conflicting_case(self, difficulty: float) -> EvidenceGatheringCase:
        """Generate a case with conflicting evidence."""
        # Evidence points in different directions
        possible = random.sample(self.DIAGNOSES, 2)
        
        current_evidence = {
            "symptom_a": self.DIAGNOSIS_SYMPTOMS[possible[0]][0],
            "symptom_b": self.DIAGNOSIS_SYMPTOMS[possible[1]][0],
            "conflict": "symptoms suggest different diagnoses",
        }
        
        return EvidenceGatheringCase(
            case_id=f"conflict_{random.randint(1000, 9999)}",
            situation=f"Patient presents with conflicting evidence. "
                     f"Some symptoms suggest {possible[0]}, "
                     f"others suggest {possible[1]}.",
            current_evidence=current_evidence,
            available_evidence_options=self.EVIDENCE_TYPES,
            scenario_type=ScenarioType.CONFLICTING_EVIDENCE,
            uncertainty=random.uniform(0.60, 0.85),
            difficulty=difficulty * 1.1,
            correct_action=ActionType.REQUEST_EVIDENCE,
            correct_specific="context_environment",
            helpful_evidence="context_environment",
        )
    
    def generate_dataset(
        self,
        n_cases: int = 100,
        difficulty: float = 0.5,
    ) -> List[EvidenceGatheringCase]:
        """Generate a full dataset."""
        cases = []
        for i in range(n_cases):
            case = self.generate_case(difficulty=difficulty)
            cases.append(case)
        return cases
    
    def score_response(
        self,
        case: EvidenceGatheringCase,
        action: ActionType,
        specific: str,
    ) -> float:
        """
        Score a response to a case.
        
        Returns:
            Score from -0.5 to 1.0
        """
        # Correct action type
        if action == case.correct_action:
            action_score = 1.0
        elif action == ActionType.ABSTAIN and case.scenario_type == ScenarioType.CLEAR_CASE:
            # Unnecessary caution on clear case
            action_score = -0.3
        else:
            action_score = -0.5
        
        # Correct specific (if action was correct)
        if action == case.correct_action:
            if specific == case.correct_specific:
                specific_score = 0.5
            elif case.correct_specific == "none_needed":
                specific_score = 0.0  # Neutral if no specific needed
            else:
                specific_score = 0.0  # Partial credit
        else:
            specific_score = 0.0
        
        return action_score + specific_score


def generate_default_dataset(
    n_cases: int = 100,
    seed: int = 42,
) -> List[EvidenceGatheringCase]:
    """Generate default dataset."""
    generator = EvidenceGatheringDatasetGenerator(seed=seed)
    return generator.generate_dataset(n_cases=n_cases)


# Example usage
if __name__ == "__main__":
    generator = EvidenceGatheringDatasetGenerator(seed=42)
    
    print("Generating 10 sample cases...")
    for i in range(10):
        case = generator.generate_case(difficulty=0.5)
        print(f"\n--- Case {i+1} ({case.scenario_type.value}) ---")
        print(f"Situation: {case.situation}")
        print(f"Uncertainty: {case.uncertainty:.2f}")
        print(f"Correct action: {case.correct_action.value}")
        print(f"Correct specific: {case.correct_specific}")
