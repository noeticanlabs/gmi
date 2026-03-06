import numpy as np
import hashlib
import json
from dataclasses import dataclass

@dataclass
class Proposal:
    """
    A materialized proposal for state transition.
    Typed wrapper around instruction + precomputed result.
    
    Using a dataclass instead of dict prevents:
    - Key typos
    - Missing fields
    - Unclear field meanings
    """
    instruction: 'Instruction'
    x_prime: np.ndarray

class State:
    """
    The cognitive state mapped as a coordinate in the PhaseLoom space.
    z(t) = (x(t), b(t)) representing cognitive coordinates and thermodynamic budget.
    """
    def __init__(self, x: list[float], budget: float):
        self.x = np.array(x, dtype=float)  # Continuous cognition state
        self.b = float(budget)             # Thermodynamic budget b >= 0

    def hash(self) -> str:
        """Deterministic hash for ledger chain integrity."""
        state_str = json.dumps({
            "x": self.x.round(6).tolist(), 
            "b": round(self.b, 6)
        }, sort_keys=True)
        return hashlib.sha256(state_str.encode('utf-8')).hexdigest()

def V_PL(x: np.ndarray) -> float:
    """
    PhaseLoom Potential: V_{PL}(x).
    Represents total cognitive tension. Bounded below, coercive.
    """
    return float(np.sum(x**2))

class Instruction:
    """Base Coh-IL Transition Operator."""
    def __init__(self, op_code: str, pi_func, sigma: float, kappa: float):
        self.op_code = op_code  # Generator choice (INFER, EXPLORE, etc.)
        self.pi = pi_func       # Untrusted heuristic proposal 
        self.sigma = sigma      # Metabolic work / Spend
        self.kappa = kappa      # Allowed defect / Positive-variation dominance

class CompositeInstruction(Instruction):
    """Represents r2 ⊙ r1. Enforces Oplax operator algebra."""
    def __init__(self, r1: Instruction, r2: Instruction, claimed_sigma: float, claimed_kappa: float):
        super().__init__(
            op_code=f"({r2.op_code} ⊙ {r1.op_code})",
            pi_func=lambda x: r2.pi(r1.pi(x)),
            sigma=claimed_sigma,
            kappa=claimed_kappa
        )
        self.r1 = r1
        self.r2 = r2
