"""
Phase 2 Diagnosis Task Dataset Generator

Generates synthetic diagnosis cases for evaluation.
"""

import json
import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class DiagnosisCase:
    """A single diagnosis case."""
    case_id: str
    symptoms: List[int]  # Binary symptoms (0/1)
    diagnosis: str
    difficulty: float  # 0-1 scale


class DiagnosisDatasetGenerator:
    """Generate synthetic diagnosis dataset."""
    
    def __init__(
        self,
        n_diagnoses: int = 10,
        n_symptoms: int = 20,
        seed: int = 42
    ):
        self.n_diagnoses = n_diagnoses
        self.n_symptoms = n_symptoms
        self.rng = random.Random(seed)
        
        # Generate diagnosis names
        self.diagnoses = [
            f"diagnosis_{i}" for i in range(n_diagnoses)
        ]
        
        # Generate symptom names
        self.symptom_names = [
            f"symptom_{i}" for i in range(n_symptoms)
        ]
        
        # Generate ground truth: which symptoms each diagnosis causes
        self.diagnosis_symptoms = self._generate_diagnosis_symptoms()
    
    def _generate_diagnosis_symptoms(self) -> Dict[str, List[int]]:
        """Generate ground truth: which symptoms each diagnosis causes."""
        mapping = {}
        
        for diagnosis in self.diagnoses:
            # Each diagnosis causes 3-8 symptoms
            n_symptoms_caused = self.rng.randint(3, 8)
            caused = self.rng.sample(range(self.n_symptoms), n_symptoms_caused)
            mapping[diagnosis] = caused
        
        return mapping
    
    def generate_case(self, difficulty: float = 0.5) -> DiagnosisCase:
        """Generate a single diagnosis case."""
        # Pick a diagnosis
        diagnosis = self.rng.choice(self.diagnoses)
        
        # Get the symptoms this diagnosis causes
        caused = self.diagnosis_symptoms[diagnosis].copy()
        
        # Add noise based on difficulty
        # Higher difficulty = more noise (false positives/negatives)
        symptoms = [0] * self.n_symptoms
        
        # Add true symptoms
        for s in caused:
            if self.rng.random() > difficulty * 0.3:  # Small chance of missing
                symptoms[s] = 1
        
        # Add false positives (noise)
        if difficulty > 0.3:
            n_noise = int(difficulty * 5)
            for _ in range(n_noise):
                s = self.rng.randint(0, self.n_symptoms - 1)
                if s not in caused:
                    symptoms[s] = 1
        
        return DiagnosisCase(
            case_id=f"case_{self.rng.randint(10000, 99999)}",
            symptoms=symptoms,
            diagnosis=diagnosis,
            difficulty=difficulty
        )
    
    def generate_dataset(
        self,
        n_train: int = 1000,
        n_test: int = 200
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate full dataset (train + test)."""
        train = []
        test = []
        
        # Generate training cases (with some overlap to test memory)
        for i in range(n_train):
            case = self.generate_case(difficulty=0.3)
            train.append(asdict(case))
        
        # Generate test cases (held-out) with HIGHER difficulty
        # This simulates distribution shift - test is harder than train
        # Ungoverned systems trusting memory will fail
        # Governed systems with verification should be more robust
        for i in range(n_test):
            case = self.generate_case(difficulty=0.78)  # Find the sweet spot
            test.append(asdict(case))
        
        return {
            "train": train,
            "test": test,
            "diagnoses": self.diagnoses,
            "symptom_names": self.symptom_names,
            "diagnosis_symptoms": {
                k: v for k, v in self.diagnosis_symptoms.items()
            }
        }
    
    def save(self, filepath: str):
        """Save dataset to JSON file."""
        dataset = self.generate_dataset()
        with open(filepath, 'w') as f:
            json.dump(dataset, f, indent=2)
        print(f"Saved dataset to {filepath}")
        print(f"  Train: {len(dataset['train'])} cases")
        print(f"  Test: {len(dataset['test'])} cases")


def generate_default_dataset():
    """Generate the default dataset."""
    generator = DiagnosisDatasetGenerator(
        n_diagnoses=10,
        n_symptoms=20,
        seed=42
    )
    generator.save("gmos/benchmarks/phase2/task_dataset.jsonl")


if __name__ == "__main__":
    generate_default_dataset()
