"""
Phase 3 Task B Dataset Generator

Generates synthetic maintenance triage cases for evaluation.
Memory has stronger action-outcome correlation than Task A.
"""

import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from enum import Enum


class Action(Enum):
    """Available maintenance actions."""
    INSPECT_LOCAL = "INSPECT_LOCAL"
    CONTINUE_MONITOR = "CONTINUE_MONITOR"
    GATHER_EVIDENCE = "GATHER_EVIDENCE"
    REPLACE_COMPONENT = "REPLACE_COMPONENT"
    SHUT_DOWN = "SHUT_DOWN"
    ESCALATE_SPECIALIST = "ESCALATE_SPECIALIST"
    SAFEHOLD_ABSTAIN = "SAFEHOLD_ABSTAIN"
    
    @classmethod
    def from_string(cls, s: str) -> "Action":
        for a in cls:
            if a.value == s:
                return a
        return cls.SAFEHOLD_ABSTAIN


class AmbiguityLevel(Enum):
    """Level of ambiguity in the case."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SeverityLevel(Enum):
    """Urgency level of the issue."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class Criticality(Enum):
    """Equipment criticality level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SAFETY_CRITICAL = "safety_critical"


class OperationalState(Enum):
    """Current operational state."""
    RUNNING = "running"
    IDLE = "idle"
    STARTING = "starting"
    STOPPING = "stopping"
    MAINTENANCE = "maintenance"


@dataclass
class TriageCase:
    """A single triage case."""
    case_id: str
    symptoms: Dict[str, bool]  # Symptom name -> present
    context: Dict[str, Any]   # Equipment context
    severity: int              # 1-5
    ambiguity_level: str        # none/low/medium/high
    correct_action: str        # The correct action
    difficulty: float          # 0-1 scale
    memory_relevance: float    # How much memory should help (0-1)


class TriageDatasetGenerator:
    """Generate synthetic triage dataset for Phase 3."""
    
    # Define symptom patterns that map to actions
    ACTION_SYMPTOMS = {
        "INSPECT_LOCAL": [
            "unusual_noise", "minor_vibration", "slight_temperature_rise",
            "minor_error_code", " cosmetic_damage"
        ],
        "CONTINUE_MONITOR": [
            "stable_reading", "within_tolerance", "normal_operation",
            "expected_behavior", "no_change_detected"
        ],
        "GATHER_EVIDENCE": [
            "intermittent_fault", "unclear_symptoms", "multiple_error_codes",
            "sensor_disagreement", "inconsistent_reading"
        ],
        "REPLACE_COMPONENT": [
            "persistent_failure", "degraded_performance", "excessive_wear",
            "component_age_high", "recurring_error"
        ],
        "SHUT_DOWN": [
            "safety_alarm", "critical_error", "overheating", "pressure_warning",
            "imminent_failure", "emergency_signal"
        ],
        "ESCALATE_SPECIALIST": [
            "complex_fault", "unknown_error", "specialized_equipment",
            "requires_expertise", "unusual_pattern"
        ],
        "SAFEHOLD_ABSTAIN": [
            "insufficient_data", "conflicting_signals", "unknown_symptoms",
            "inconclusive_reading", "requires_observation"
        ]
    }
    
    EQUIPMENT_TYPES = [
        "pump_assembly", "motor_unit", "valve_array", "sensor_cluster",
        "controller_board", "power_supply", "cooling_system", "hydraulic_line"
    ]
    
    def __init__(
        self,
        n_actions: int = 7,
        n_symptoms_per_action: int = 5,
        seed: int = 42
    ):
        self.n_actions = n_actions
        self.n_symptoms = n_actions * n_symptoms_per_action
        self.rng = random.Random(seed)
        
        self.actions = list(Action)
        self.symptom_names = []
        for action, symptoms in self.ACTION_SYMPTOMS.items():
            self.symptom_names.extend(symptoms)
        
        # Create action -> base symptom mapping
        self.action_symptom_map = {}
        idx = 0
        for action, symptoms in self.ACTION_SYMPTOMS.items():
            self.action_symptom_map[action] = list(range(idx, idx + len(symptoms)))
            idx += len(symptoms)
    
    def _symptom_name_to_idx(self, name: str) -> int:
        """Map symptom name to index."""
        return self.symptom_names.index(name)
    
    def _idx_to_symptom_name(self, idx: int) -> str:
        """Map index to symptom name."""
        return self.symptom_names[idx]
    
    def generate_case(
        self,
        difficulty: float = 0.5,
        force_action: Optional[str] = None,
        force_ambiguity: Optional[str] = None
    ) -> TriageCase:
        """Generate a single triage case."""
        
        # Determine action
        if force_action:
            action = force_action
        else:
            action = self.rng.choice(self.actions).value
        
        # Determine ambiguity
        if force_ambiguity:
            ambiguity = force_ambiguity
        else:
            # 40% clear, 35% ambiguous, 25% safehold-appropriate
            roll = self.rng.random()
            if roll < 0.4:
                ambiguity = "none"
            elif roll < 0.75:
                ambiguity = self.rng.choice(["low", "medium"])
            else:
                ambiguity = "high"
        
        # Generate symptoms based on action
        symptoms = {}
        
        if action == "SAFEHOLD_ABSTAIN" or ambiguity == "high":
            # High ambiguity: mixed/conflicting symptoms
            all_symptom_names = list(self.ACTION_SYMPTOMS.values())
            flat_symptoms = [s for sublist in all_symptom_names for s in sublist]
            
            # Sample random symptoms (conflicting signals)
            n_symptoms = self.rng.randint(5, 10)
            chosen = self.rng.sample(flat_symptoms, n_symptoms)
            for s in chosen:
                symptoms[s] = self.rng.choice([True, False])
        else:
            # Clearer signal based on action
            base_symptoms = self.ACTION_SYMPTOMS.get(action, [])
            
            # Add true symptoms (action-specific)
            for s in base_symptoms:
                # Higher difficulty = chance to miss symptom
                if self.rng.random() > difficulty * 0.3:
                    symptoms[s] = True
            
            # Add noise (wrong-action symptoms)
            if difficulty > 0.2:
                n_noise = int(difficulty * 3)
                other_actions = [a for a in self.ACTION_SYMPTOMS.keys() if a != action]
                for _ in range(n_noise):
                    noise_action = self.rng.choice(other_actions)
                    noise_symptom = self.rng.choice(self.ACTION_SYMPTOMS[noise_action])
                    symptoms[noise_symptom] = self.rng.random() < 0.3
        
        # Determine severity based on action
        if action == "SHUT_DOWN":
            severity = self.rng.choice([4, 5])
        elif action == "REPLACE_COMPONENT":
            severity = self.rng.choice([3, 4])
        elif action == "GATHER_EVIDENCE":
            severity = self.rng.choice([2, 3])
        elif action == "ESCALATE_SPECIALIST":
            severity = self.rng.choice([2, 3, 4])
        else:
            severity = self.rng.choice([1, 2])
        
        # Determine context
        context = {
            "equipment_type": self.rng.choice(self.EQUIPMENT_TYPES),
            "criticality": self.rng.choice(["low", "medium", "high"]),
            "operational_state": self.rng.choice(["running", "idle", "starting"]),
            "age_hours": self.rng.randint(100, 10000),
            "last_maintenance": self.rng.randint(0, 365)  # days ago
        }
        
        # Memory relevance: how much memory should help
        # Task B has higher memory relevance than Task A
        if action in ["INSPECT_LOCAL", "CONTINUE_MONITOR", "GATHER_EVIDENCE"]:
            memory_relevance = 0.7 + 0.2 * (1 - difficulty)  # 0.7-0.9
        elif action in ["SHUT_DOWN", "REPLACE_COMPONENT"]:
            memory_relevance = 0.6 + 0.25 * (1 - difficulty)  # 0.6-0.85
        else:
            memory_relevance = 0.5 + 0.3 * (1 - difficulty)  # 0.5-0.8
        
        return TriageCase(
            case_id=f"triage_{self.rng.randint(10000, 99999)}",
            symptoms=symptoms,
            context=context,
            severity=severity,
            ambiguity_level=ambiguity,
            correct_action=action,
            difficulty=difficulty,
            memory_relevance=memory_relevance
        )
    
    def generate_memory_case(self, action: Optional[str] = None) -> Dict[str, Any]:
        """Generate a memory case (past action + outcome)."""
        
        if action is None:
            action = self.rng.choice(self.actions).value
        
        # Generate symptoms for this action
        symptoms = {}
        base_symptoms = self.ACTION_SYMPTOMS.get(action, [])
        
        # Add symptoms with high probability (memory has cleaner signal)
        for s in base_symptoms:
            if self.rng.random() < 0.8:
                symptoms[s] = True
        
        # Add some noise but less than test cases
        if self.rng.random() < 0.2:
            other_actions = [a for a in self.ACTION_SYMPTOMS.keys() if a != action]
            noise_action = self.rng.choice(other_actions)
            noise_symptom = self.rng.choice(self.ACTION_SYMPTOMS[noise_action])
            symptoms[noise_symptom] = True
        
        # Determine outcome based on action
        if action == "SHUT_DOWN":
            outcome = "correct_caution" if self.rng.random() < 0.9 else "overreaction"
        elif action == "SAFEHOLD_ABSTAIN":
            outcome = "appropriate_caution" if self.rng.random() < 0.85 else "missed_issue"
        elif action == "REPLACE_COMPONENT":
            outcome = "resolved" if self.rng.random() < 0.8 else "unnecessary"
        elif action == "GATHER_EVIDENCE":
            outcome = "informative" if self.rng.random() < 0.75 else "inconclusive"
        else:
            outcome = self.rng.choice(["success", "partial", "inconclusive"])
        
        return {
            "symptoms": symptoms,
            "context": {
                "equipment_type": self.rng.choice(self.EQUIPMENT_TYPES),
                "criticality": self.rng.choice(["low", "medium", "high"]),
            },
            "action": action,
            "outcome": outcome,
            "success": outcome in ["resolved", "correct_caution", "appropriate_caution", "success"]
        }
    
    def generate_dataset(
        self,
        n_train: int = 500,
        n_test: int = 200,
        difficulty_range: tuple = (0.3, 0.7)
    ) -> Dict[str, Any]:
        """Generate complete dataset."""
        
        # Generate training (memory) cases
        memory_cases = [self.generate_memory_case() for _ in range(n_train)]
        
        # Generate test cases with difficulty distribution
        test_cases = []
        
        # 40% clear-cut (difficulty 0.2-0.4)
        # 35% ambiguous (difficulty 0.4-0.6)
        # 25% SafeHold-appropriate (difficulty 0.6-0.8)
        
        n_clear = int(n_test * 0.4)
        n_ambiguous = int(n_test * 0.35)
        n_safehold = n_test - n_clear - n_ambiguous
        
        for _ in range(n_clear):
            difficulty = self.rng.uniform(0.2, 0.4)
            case = self.generate_case(difficulty=difficulty, force_ambiguity="none")
            test_cases.append(case)
        
        for _ in range(n_ambiguous):
            difficulty = self.rng.uniform(0.4, 0.6)
            case = self.generate_case(difficulty=difficulty, force_ambiguity="medium")
            test_cases.append(case)
        
        for _ in range(n_safehold):
            difficulty = self.rng.uniform(0.6, 0.8)
            case = self.generate_case(difficulty=difficulty, force_ambiguity="high")
            test_cases.append(case)
        
        # Shuffle test cases
        self.rng.shuffle(test_cases)
        
        return {
            "memory": memory_cases,
            "test": [asdict(c) for c in test_cases],
            "metadata": {
                "n_memory": n_train,
                "n_test": n_test,
                "actions": [a.value for a in self.actions],
                "symptom_names": self.symptom_names,
                "difficulty_distribution": {
                    "clear": n_clear,
                    "ambiguous": n_ambiguous,
                    "safehold_appropriate": n_safehold
                }
            }
        }
    
    def to_json_compatible(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        """Convert dataset to JSON-compatible format."""
        return dataset


def generate_dataset(
    n_train: int = 500,
    n_test: int = 200,
    seed: int = 42
) -> Dict[str, Any]:
    """Convenience function to generate dataset."""
    generator = TriageDatasetGenerator(seed=seed)
    return generator.generate_dataset(n_train=n_train, n_test=n_test)


if __name__ == "__main__":
    import json
    
    # Generate dataset
    dataset = generate_dataset(n_train=500, n_test=200, seed=42)
    
    # Save to JSON
    with open("gmos/benchmarks/phase3/task_b/dataset.json", "w") as f:
        json.dump(dataset, f, indent=2)
    
    print(f"Generated {len(dataset['memory'])} memory cases")
    print(f"Generated {len(dataset['test'])} test cases")
    print(f"Actions: {dataset['metadata']['actions']}")
    print(f"Difficulty distribution: {dataset['metadata']['difficulty_distribution']}")
