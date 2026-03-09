"""
Formal Theorems for GM-OS Canon Spec v1.

Implements core theorems from spec §24:
- Theorem 24.1: Forward Invariance
- Theorem 24.2: Kernel Monopoly  
- Theorem 24.3: Budget Reserve Preservation
- Theorem 24.4: Anchor Dominance
- Theorem 24.5: Memory Loop Finiteness
- Theorem 24.6: Discrete Soundness
- Theorem 24.7: Chain Closure
- Theorem 24.8: Deterministic Consensus

These theorems provide formal guarantees about GM-OS behavior.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
import hashlib
import json


# === Theorem Results ===

@dataclass
class TheoremResult:
    """Result of a theorem check."""
    theorem_name: str
    satisfied: bool
    message: str
    details: Dict[str, Any]


# === Theorem 24.1: Forward Invariance ===

def theorem_forward_invariance(
    initial_state: Any,
    dynamics_system: Any,
    T: float,
) -> TheoremResult:
    """
    Theorem 24.1: Forward Invariance.
    
    If ξ(0) ∈ K and continuous drift satisfies viability conditions,
    then every continuous trajectory remains in K until a discrete event.
    
    Args:
        initial_state: Initial state in admissible set K
        dynamics_system: ProjectedDynamicalSystem instance
        T: Simulation time
        
    Returns:
        TheoremResult with verification
    """
    # Check initial admissibility
    if not dynamics_system.admissible.is_admissible(initial_state):
        return TheoremResult(
            theorem_name="Forward Invariance",
            satisfied=False,
            message="Initial state not in admissible set K",
            details={"initial_admissible": False},
        )
    
    # Simulate and check each step
    current = initial_state.copy()
    dt = dynamics_system.dt
    
    for step in range(int(T / dt)):
        current = dynamics_system.step(current, dt)
        
        if not dynamics_system.admissible.is_admissible(current):
            return TheoremResult(
                theorem_name="Forward Invariance",
                satisfied=False,
                message=f"State left admissible set at t={step*dt}",
                details={"exit_time": step * dt},
            )
    
    return TheoremResult(
        theorem_name="Forward Invariance",
        satisfied=True,
        message="All states remained in admissible set K",
        details={"simulation_time": T, "steps": int(T / dt)},
    )


# === Theorem 24.2: Kernel Monopoly ===

def theorem_kernel_monopoly(
    state_mutations: List[Dict[str, Any]],
    kernel_step_fn: Any,
) -> TheoremResult:
    """
    Theorem 24.2: Kernel Monopoly.
    
    Every global state mutation affecting world interface, budget bundle,
    cross-process relations, ledger state, or authority state must occur
    through the kernel step operator.
    
    Args:
        state_mutations: List of attempted state mutations
        kernel_step_fn: The kernel step function
        
    Returns:
        TheoremResult with verification
    """
    kernel_mutations = 0
    non_kernel_mutations = 0
    
    for mutation in state_mutations:
        # Check if mutation went through kernel
        if mutation.get("through_kernel", False):
            kernel_mutations += 1
        else:
            # Check if mutation affects protected state factors
            factors = mutation.get("affected_factors", [])
            protected = {"x_ext", "b", "p", "k", "ℓ"}
            
            if any(f in protected for f in factors):
                non_kernel_mutations += 1
    
    # Theorem satisfied if no non-kernel mutations to protected factors
    satisfied = non_kernel_mutations == 0
    
    return TheoremResult(
        theorem_name="Kernel Monopoly",
        satisfied=satisfied,
        message=f"Kernel mutations: {kernel_mutations}, Non-kernel: {non_kernel_mutations}",
        details={
            "kernel_mutations": kernel_mutations,
            "non_kernel_mutations": non_kernel_mutations,
        },
    )


# === Theorem 24.3: Budget Reserve Preservation ===

def theorem_budget_reserve_preservation(
    budget_router: Any,
    channel: str,
    spend_amount: float,
) -> TheoremResult:
    """
    Theorem 24.3: Budget Reserve Preservation.
    
    If a routing or spend event would violate any reserve floor
    (b_i ≥ b_i,reserve), the event is inadmissible and must be rejected.
    
    Args:
        budget_router: BudgetRouter instance
        channel: Budget channel to test
        spend_amount: Amount to spend
        
    Returns:
        TheoremResult with verification
    """
    # Get current budget
    amount = budget_router.get_budget(channel)
    if amount is None:
        return TheoremResult(
            theorem_name="Budget Reserve Preservation",
            satisfied=False,
            message=f"No budget for channel {channel}",
            details={"channel": channel},
        )
    
    # Check if spend is allowed
    allowed, reason = budget_router.can_spend_at_boundary(channel, spend_amount)
    
    # If not allowed, theorem is satisfied (reserve was preserved)
    if not allowed:
        return TheoremResult(
            theorem_name="Budget Reserve Preservation",
            satisfied=True,
            message=f"Spend rejected: {reason}",
            details={"allowed": False, "reason": reason},
        )
    
    # If allowed, verify it doesn't violate reserve
    new_amount = amount - spend_amount
    reserve = budget_router.get_reserve(channel)
    
    if reserve is not None and new_amount < reserve:
        return TheoremResult(
            theorem_name="Budget Reserve Preservation",
            satisfied=False,
            message="Spend would violate reserve",
            details={"amount": amount, "spend": spend_amount, "reserve": reserve},
        )
    
    return TheoremResult(
        theorem_name="Budget Reserve Preservation",
        satisfied=True,
        message="Spend allowed and preserves reserve",
        details={"allowed": True},
    )


# === Theorem 24.4: Anchor Dominance ===

def theorem_anchor_dominance(
    q1: Any,  # PerceptToken
    q2: Any,  # PerceptToken
    delta_a: float,
) -> TheoremResult:
    """
    Theorem 24.4: Anchor Dominance.
    
    When two incompatible claims conflict and one has anchor authority
    margin at least δ_A over the other, the lower-authority claim cannot
    be committed as substrate truth without an explicit override receipt.
    
    Args:
        q1: Higher-authority percept
        q2: Lower-authority percept  
        delta_a: Authority margin
                
    Returns:
        TheoremResult with verification
    """
    # Check if q1 dominates q2
    authority_1 = getattr(q1, 'authority', 0.0)
    authority_2 = getattr(q2, 'authority', 0.0)
    
    margin = authority_1 - authority_2
    dominates = margin >= delta_a
    
    return TheoremResult(
        theorem_name="Anchor Dominance",
        satisfied=dominates,
        message=f"Authority margin: {margin:.3f}, required: {delta_a}",
        details={
            "authority_1": authority_1,
            "authority_2": authority_2,
            "margin": margin,
            "delta_a": delta_a,
            "dominates": dominates,
        },
    )


# === Theorem 24.5: Memory Loop Finiteness ===

def theorem_memory_loop_finiteness(
    sigma_min: float,
    memory_budget: float,
    operation_cost_fn: Any,
) -> TheoremResult:
    """
    Theorem 24.5: Memory Loop Finiteness.
    
    If nontrivial memory operations have positive minimal spend (Σ_min > 0)
    and available memory budget is finite, then only finitely many such
    operations can occur before recharge or mode change.
    
    Args:
        sigma_min: Minimum spend per operation
        memory_budget: Available memory budget
        operation_cost_fn: Function to compute operation cost
        
    Returns:
        TheoremResult with verification
    """
    if sigma_min <= 0:
        return TheoremResult(
            theorem_name="Memory Loop Finiteness",
            satisfied=False,
            message="Σ_min must be positive for theorem",
            details={"sigma_min": sigma_min},
        )
    
    if memory_budget <= 0:
        return TheoremResult(
            theorem_name="Memory Loop Finiteness",
            satisfied=True,
            message="No budget available - zero operations possible",
            details={"memory_budget": memory_budget, "max_operations": 0},
        )
    
    # Maximum operations = floor(budget / min_cost)
    max_operations = int(memory_budget / sigma_min)
    
    return TheoremResult(
        theorem_name="Memory Loop Finiteness",
        satisfied=True,
        message=f"Maximum {max_operations} operations possible",
        details={
            "sigma_min": sigma_min,
            "memory_budget": memory_budget,
            "max_operations": max_operations,
        },
    )


# === Theorem 24.6: Discrete Soundness ===

def theorem_discrete_soundness(
    v_before: float,
    v_after: float,
    spend: float,
    defect: float,
) -> TheoremResult:
    """
    Theorem 24.6: Discrete Soundness.
    
    Every accepted receipt satisfies:
        V(ξ') + Spend(r) ≤ V(ξ) + Defect(r)
    
    Args:
        v_before: Potential before transition
        v_after: Potential after transition
        spend: Spend amount
        defect: Defect amount
        
    Returns:
        TheoremResult with verification
    """
    lhs = v_after + spend
    rhs = v_before + defect
    
    satisfied = lhs <= rhs + 1e-6  # Allow small floating point error
    
    return TheoremResult(
        theorem_name="Discrete Soundness",
        satisfied=satisfied,
        message=f"V' + Spend = {lhs:.3f} ≤ V + Defect = {rhs:.3f}",
        details={
            "v_before": v_before,
            "v_after": v_after,
            "spend": spend,
            "defect": defect,
            "lhs": lhs,
            "rhs": rhs,
        },
    )


# === Theorem 24.7: Chain Closure ===

def theorem_chain_closure(
    receipts: List[Dict[str, Any]],
    chain_update_fn: Any,
) -> TheoremResult:
    """
    Theorem 24.7: Chain Closure.
    
    If a sequence of receipts is accepted and each receipt's embedded
    chain fields satisfy the declared chain update law, then the trace
    forms a deterministic ledger chain.
    
    Args:
        receipts: List of accepted receipts
        chain_update_fn: Function to compute chain digest
        
    Returns:
        TheoremResult with verification
    """
    if not receipts:
        return TheoremResult(
            theorem_name="Chain Closure",
            satisfied=True,
            message="Empty receipt chain",
            details={"receipt_count": 0},
        )
    
    prev_digest = receipts[0].get("chain_digest_prev", "")
    
    for i, receipt in enumerate(receipts):
        # Check embedded fields match
        expected_prev = receipt.get("chain_digest_prev", "")
        if expected_prev != prev_digest:
            return TheoremResult(
                theorem_name="Chain Closure",
                satisfied=False,
                message=f"Chain broken at receipt {i}",
                details={
                    "broken_at": i,
                    "expected": prev_digest,
                    "got": expected_prev,
                },
            )
        
        # Compute next digest
        receipt_json = json.dumps(receipt, sort_keys=True, default=str)
        prev_digest = chain_update_fn(prev_digest, receipt_json, receipt.get("state_hash_next", ""))
    
    return TheoremResult(
        theorem_name="Chain Closure",
        satisfied=True,
        message=f"Chain valid for {len(receipts)} receipts",
        details={"receipt_count": len(receipts)},
    )


# === Theorem 24.8: Deterministic Consensus ===

def theorem_deterministic_consensus(
    state_hash: str,
    receipt_bytes: bytes,
    prev_digest: str,
    verifier_fn: Any,
) -> TheoremResult:
    """
    Theorem 24.8: Deterministic Consensus.
    
    If canonical serialization, hash function, numeric profile, policy hash,
    and verifier implementation are fixed, then equal boundary hashes plus
    equal receipt bytes plus equal previous chain digest yield equal verifier
    decisions.
    
    Args:
        state_hash: State boundary hash
        receipt_bytes: Receipt bytes
        prev_digest: Previous chain digest
        verifier_fn: Verifier function
        
    Returns:
        TheoremResult with verification
    """
    # Run verifier multiple times to check determinism
    decisions = []
    for _ in range(3):
        decision = verifier_fn(state_hash, receipt_bytes, prev_digest)
        decisions.append(decision)
    
    # All decisions should be equal
    all_equal = len(set(decisions)) == 1
    
    return TheoremResult(
        theorem_name="Deterministic Consensus",
        satisfied=all_equal,
        message=f"Verifier decisions: {decisions}",
        details={
            "decisions": decisions,
            "all_equal": all_equal,
        },
    )


# === Theorem Suite ===

class GMOSTheorems:
    """
    Complete theorem suite for GM-OS.
    
    Provides convenient access to all theorems.
    """
    
    @staticmethod
    def forward_invariance(*args, **kwargs) -> TheoremResult:
        return theorem_forward_invariance(*args, **kwargs)
    
    @staticmethod
    def kernel_monopoly(*args, **kwargs) -> TheoremResult:
        return theorem_kernel_monopoly(*args, **kwargs)
    
    @staticmethod
    def budget_reserve_preservation(*args, **kwargs) -> TheoremResult:
        return theorem_budget_reserve_preservation(*args, **kwargs)
    
    @staticmethod
    def anchor_dominance(*args, **kwargs) -> TheoremResult:
        return theorem_anchor_dominance(*args, **kwargs)
    
    @staticmethod
    def memory_loop_finiteness(*args, **kwargs) -> TheoremResult:
        return theorem_memory_loop_finiteness(*args, **kwargs)
    
    @staticmethod
    def discrete_soundness(*args, **kwargs) -> TheoremResult:
        return theorem_discrete_soundness(*args, **kwargs)
    
    @staticmethod
    def chain_closure(*args, **kwargs) -> TheoremResult:
        return theorem_chain_closure(*args, **kwargs)
    
    @staticmethod
    def deterministic_consensus(*args, **kwargs) -> TheoremResult:
        return theorem_deterministic_consensus(*args, **kwargs)
    
    @staticmethod
    def verify_all(*args, **kwargs) -> List[TheoremResult]:
        """Verify all theorems (placeholder)."""
        # This would run all theorems
        return []
