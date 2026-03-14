"""
GM-OS Minimal Runtime Loop

This module implements the minimal executable law - the smallest lawful
end-to-end loop that proves the doctrine is not just markdown furniture.

This implements the canonical transition:
[
V(x_{t+1}) + σ ≤ V(x_t) + κ + r
]

Where:
- V = coherence functional
- σ = spend
- κ = defect tolerance
- r = reserve slack

Status: Canonical - Phase 1 Executable Proof
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from gmos.contracts.types import (
    State,
    BudgetState,
    Proposal,
    ProposalType,
    VerifierResult,
    Receipt,
    Verdict,
    create_initial_state,
    create_initial_budget,
    compute_residual,
    check_verifier_inequality,
)

from gmos.contracts.receipts import (
    create_accept_receipt,
    create_reject_receipt,
    create_repair_receipt,
    create_abstain_receipt,
)


# =============================================================================
# Minimal Verifier
# =============================================================================


class MinimalVerifier:
    """
    Minimal verifier implementing the core governance law.
    
    Verifier rules (stricter interpretation):
    1. Reserve law: spend must NOT violate reserve floor (independent check)
    2. Coherence law: proposals that worsen coherence beyond defect tolerance are REJECTED
    3. Only proposals that slightly worsen coherence within tolerance can be repaired
    
    Inequality: V(x_{t+1}) + σ ≤ V(x_t) + κ + r
    """
    
    def __init__(self, defect_tolerance: float = 10.0):
        self.defect_tolerance = defect_tolerance
    
    def verify(
        self,
        current_state: State,
        proposed_state: State,
        budget: BudgetState,
        spend: float,
    ) -> VerifierResult:
        """
        Verify a proposal against the coherence law.
        
        Returns ACCEPT, REPAIR, or REJECT.
        """
        coherence_before = current_state.coherence
        coherence_after = proposed_state.coherence
        
        # Compute residual
        residual = compute_residual(coherence_before, coherence_after)
        
        # Get reserve slack (total available minus floor)
        reserve_slack = sum(budget.reserve_slack.values())
        
        # RULE 1: Check reserve floor independently FIRST
        # If spend would violate reserve floor, REJECT immediately
        if not self._can_spend_within_reserve(budget, spend):
            return VerifierResult(
                verdict=Verdict.REJECT,
                residual=residual,
                spend=spend,
                defect=self.defect_tolerance,
                reserve_slack=reserve_slack,
                coherence_before=coherence_before,
                coherence_after=coherence_after,
                reasons=["reserve_floor_violation"],
                repair_notes="spend would violate reserve floor"
            )
        
        # RULE 2: Check if proposal worsens coherence significantly
        # If coherence_after > coherence_before + defect_tolerance, REJECT (not repair)
        # This prevents proposals that significantly degrade state from slipping through
        coherence_worsening = coherence_after - coherence_before
        if coherence_worsening > self.defect_tolerance:
            # Proposal significantly worsens coherence - REJECT
            return VerifierResult(
                verdict=Verdict.REJECT,
                residual=residual,
                spend=spend,
                defect=coherence_worsening,
                reserve_slack=reserve_slack,
                coherence_before=coherence_before,
                coherence_after=coherence_after,
                reasons=["coherence_worsens_beyond_tolerance"],
                repair_notes="coherence worsens by more than defect tolerance"
            )
        
        # RULE 3: Check verifier inequality
        is_admissible = check_verifier_inequality(
            coherence_before=coherence_before,
            coherence_after=coherence_after,
            spend=spend,
            defect=self.defect_tolerance,
            reserve_slack=reserve_slack
        )
        
        if is_admissible:
            # ACCEPT - all checks pass
            return VerifierResult(
                verdict=Verdict.ACCEPT,
                residual=residual,
                spend=spend,
                defect=0.0,  # No defect if accepted
                reserve_slack=reserve_slack,
                coherence_before=coherence_before,
                coherence_after=coherence_after,
                reasons=["verifier_inequality_satisfied"]
            )
        
        # RULE 4: Only proposals that slightly worsen coherence can be repaired
        # If coherence_worsening is positive but within tolerance, try repair
        if coherence_worsening > 0 and coherence_worsening <= self.defect_tolerance:
            # Repair: reduce the coherence impact
            repaired_coherence = coherence_before  # Restore to original
            repaired_residual = compute_residual(coherence_before, repaired_coherence)
            
            return VerifierResult(
                verdict=Verdict.REPAIR,
                residual=repaired_residual,
                spend=spend,
                defect=coherence_worsening,
                reserve_slack=reserve_slack,
                coherence_before=coherence_before,
                coherence_after=repaired_coherence,
                repair_notes="coherence restored to original level",
                reasons=["proposal_repaired"]
            )
        
        # Default: REJECT
        return VerifierResult(
            verdict=Verdict.REJECT,
            residual=residual,
            spend=spend,
            defect=self.defect_tolerance,
            reserve_slack=reserve_slack,
            coherence_before=coherence_before,
            coherence_after=coherence_after,
            reasons=["verifier_inequality_violated"],
            repair_notes="cannot repair to admissible state"
        )
    
    def _can_spend_within_reserve(self, budget: BudgetState, spend: float) -> bool:
        """Check if spend would violate reserve floor."""
        # Check each channel's reserve floor
        for channel, floor in budget.reserve_floors.items():
            current_reserve = budget.reserves.get(channel, 0)
            reserve_after = current_reserve - spend
            if reserve_after < floor:
                return False
        
        # Also check total available doesn't go below zero
        return budget.available - spend >= 0


# =============================================================================
# Minimal Memory (Stub)
# =============================================================================


@dataclass
class MinimalMemory:
    """Minimal memory placeholder."""
    episodes: list = field(default_factory=list)
    
    def store(self, content: Any) -> str:
        episode_id = str(uuid.uuid4())
        self.episodes.append({"id": episode_id, "content": content})
        return episode_id
    
    def retrieve(self, query: Any = None) -> list:
        return self.episodes[-5:] if self.episodes else []


# =============================================================================
# Minimal Percept (Stub)
# =============================================================================


@dataclass
class MinimalPercept:
    """Minimal percept placeholder."""
    raw_input: Any
    percept_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    salience: float = 0.5


# =============================================================================
# Minimal Budget Manager
# =============================================================================


class MinimalBudgetManager:
    """Minimal budget manager with reserve enforcement.
    
    The reserve floor is a HARD constraint - spending that would violate
    the reserve floor is always rejected.
    """
    
    def __init__(self, total: float = 100.0, reserve_floor: float = 10.0):
        self.total = total
        self.available = total
        self.reserve_floor = reserve_floor
        self.spent = 0.0
    
    def get_budget(self) -> BudgetState:
        return BudgetState(
            total=self.total,
            available=self.available,
            spent=self.spent,
            reserves={"default": max(0, self.available - self.reserve_floor)},
            reserve_floors={"default": self.reserve_floor},
            defect_allowance=10.0
        )
    
    def can_spend(self, amount: float) -> bool:
        """
        Check if amount can be spent without violating reserve floor.
        
        HARD constraint: available - amount >= reserve_floor
        """
        return self.available - amount >= self.reserve_floor
    
    def spend(self, amount: float) -> bool:
        """Execute spend if it doesn't violate reserve floor."""
        if self.can_spend(amount):
            self.available -= amount
            self.spent += amount
            return True
        return False
    
    def reset_spent(self):
        """Reset spent counter for new step."""
        self.spent = 0.0


# =============================================================================
# Minimal State Host
# =============================================================================


class MinimalStateHost:
    """Minimal state host."""
    
    def __init__(self, initial_state: State | None = None):
        self._state = initial_state or create_initial_state()
    
    def get_state(self) -> State:
        return self._state
    
    def update_state(self, state: State) -> None:
        self._state = state


# =============================================================================
# Minimal Receipt Store
# =============================================================================


class MinimalReceiptStore:
    """Minimal receipt storage."""
    
    def __init__(self):
        self.receipts: list[Receipt] = []
        self._step = 0
    
    def write(self, receipt: Receipt) -> str:
        self.receipts.append(receipt)
        return receipt.receipt_id
    
    def get_all(self) -> list[Receipt]:
        return self.receipts
    
    def get_step(self) -> int:
        return self._step
    
    def increment_step(self):
        self._step += 1


# =============================================================================
# Minimal Runtime Loop
# =============================================================================


@dataclass
class MinimalLoopResult:
    """Result of a minimal loop execution."""
    step: int
    verdict: Verdict
    state_before: State
    state_after: State
    budget_before: BudgetState
    budget_after: BudgetState
    spend: float
    residual: float
    receipt: Receipt


class MinimalRuntimeLoop:
    """
    Minimal executable runtime loop.
    
    Implements the canonical step sequence:
    1. OBSERVE (get input)
    2. ANCHOR (create percept)
    3. RETRIEVE (get memory)
    4. PROPOSE (generate proposal)
    5. EVALUATE (compute residual/budget)
    6. VERIFY (check inequality)
    7. REPAIR/REJECT if needed
    8. COMMIT (update state)
    9. RECEIPT (write record)
    10. UPDATE (prepare next step)
    """
    
    def __init__(
        self,
        initial_coherence: float = 50.0,
        initial_budget: float = 100.0,
        reserve_floor: float = 10.0,
        defect_tolerance: float = 10.0,
    ):
        self.state_host = MinimalStateHost(
            create_initial_state(coherence=initial_coherence)
        )
        self.budget_manager = MinimalBudgetManager(
            total=initial_budget,
            reserve_floor=reserve_floor
        )
        self.verifier = MinimalVerifier(defect_tolerance=defect_tolerance)
        self.memory = MinimalMemory()
        self.receipt_store = MinimalReceiptStore()
        self.step_count = 0
    
    def step(
        self,
        raw_input: Any = None,
        proposed_coherence_change: float = -5.0,  # Negative = improve coherence
        proposed_spend: float = 5.0,
    ) -> MinimalLoopResult:
        """
        Execute one step of the minimal loop.
        
        Args:
            raw_input: Raw sensory input (optional)
            proposed_coherence_change: Proposed change to V(x) (negative = improve)
            proposed_spend: Proposed budget spend
            
        Returns:
            MinimalLoopResult with verdict and receipt
        """
        # 1. OBSERVE
        # (In minimal version, raw_input is optional)
        
        # 2. ANCHOR - create percept
        percept = MinimalPercept(raw_input=raw_input or "default_input")
        
        # 3. RETRIEVE - get memory
        memory_refs = self.memory.retrieve()
        
        # Get current state
        state_before = self.state_host.get_state()
        budget_before = self.budget_manager.get_budget()
        
        # 4. PROPOSE - create proposal
        proposal_id = str(uuid.uuid4())
        
        # 5. EVALUATE - compute expected coherence
        coherence_after = state_before.coherence + proposed_coherence_change
        
        proposed_state = State(
            state_id=str(uuid.uuid4()),
            step=self.step_count,
            coherence=coherence_after,
            data={"proposal": proposal_id}
        )
        
        # 6. VERIFY - check inequality
        verifier_result = self.verifier.verify(
            current_state=state_before,
            proposed_state=proposed_state,
            budget=budget_before,
            spend=proposed_spend,
        )
        
        state_after = state_before
        budget_after = budget_before
        spend = proposed_spend
        residual = verifier_result.residual
        
        # 7. REPAIR/REJECT - handle verdict
        if verifier_result.verdict == Verdict.ACCEPT:
            # 8. COMMIT - update state
            if self.budget_manager.spend(proposed_spend):
                state_after = proposed_state
                budget_after = self.budget_manager.get_budget()
            
            # 9. RECEIPT - write accept receipt
            receipt = create_accept_receipt(
                receipt_id=str(uuid.uuid4()),
                step=self.step_count,
                proposal_id=proposal_id,
                coherence_before=state_before.coherence,
                coherence_after=state_after.coherence,
                spend=spend,
                defect=0.0,
                reserve_slack=sum(budget_after.reserve_slack.values()),
                percept_refs=[percept.percept_id],
                memory_refs=[m["id"] for m in memory_refs]
            )
            
        elif verifier_result.verdict == Verdict.REPAIR:
            # Commit with repaired state
            if self.budget_manager.spend(proposed_spend):
                # Apply repair: use the coherence_before + small improvement
                repaired_coherence = state_before.coherence - 1.0  # Minimal improvement
                state_after = State(
                    state_id=str(uuid.uuid4()),
                    step=self.step_count,
                    coherence=repaired_coherence,
                    data={"proposal": proposal_id, "repaired": True}
                )
                budget_after = self.budget_manager.get_budget()
                residual = repaired_coherence - state_before.coherence
            
            receipt = create_repair_receipt(
                receipt_id=str(uuid.uuid4()),
                step=self.step_count,
                proposal_id=proposal_id,
                coherence_before=state_before.coherence,
                coherence_after=state_after.coherence,
                spend=spend,
                defect=self.verifier.defect_tolerance,
                reserve_slack=sum(budget_after.reserve_slack.values()),
                repair_notes=verifier_result.repair_notes or "repaired",
                percept_refs=[percept.percept_id],
                memory_refs=[m["id"] for m in memory_refs]
            )
            
        else:  # REJECT or ABSTAIN
            # No state change
            spend = 0.0
            residual = 0.0
            
            receipt = create_reject_receipt(
                receipt_id=str(uuid.uuid4()),
                step=self.step_count,
                proposal_id=proposal_id,
                reason=verifier_result.repair_notes or "rejected",
                coherence_before=state_before.coherence,
                spend=proposed_spend,
            )
        
        # Write receipt
        self.receipt_store.write(receipt)
        
        # Update state host
        self.state_host.update_state(state_after)
        
        # 10. UPDATE - prepare for next step
        self.step_count += 1
        self.budget_manager.reset_spent()
        
        return MinimalLoopResult(
            step=self.step_count - 1,
            verdict=verifier_result.verdict,
            state_before=state_before,
            state_after=state_after,
            budget_before=budget_before,
            budget_after=budget_after,
            spend=spend,
            residual=residual,
            receipt=receipt
        )
    
    def run_sequence(
        self,
        num_steps: int = 5,
        coherence_changes: list[float] | None = None,
        spends: list[float] | None = None,
    ) -> list[MinimalLoopResult]:
        """
        Run a sequence of steps.
        
        Args:
            num_steps: Number of steps to run
            coherence_changes: List of proposed coherence changes (one per step)
            spends: List of proposed spends (one per step)
            
        Returns:
            List of results
        """
        results = []
        
        changes = coherence_changes or [-5.0] * num_steps
        spend_list = spends or [5.0] * num_steps
        
        for i in range(num_steps):
            result = self.step(
                raw_input=f"input_{i}",
                proposed_coherence_change=changes[i] if i < len(changes) else -5.0,
                proposed_spend=spend_list[i] if i < len(spend_list) else 5.0,
            )
            results.append(result)
        
        return results


# =============================================================================
# Demo / Test
# =============================================================================


def demo():
    """Run a demo of the minimal loop."""
    print("=" * 60)
    print("GM-OS Minimal Runtime Loop Demo")
    print("=" * 60)
    
    # Create loop
    loop = MinimalRuntimeLoop(
        initial_coherence=50.0,
        initial_budget=100.0,
        reserve_floor=10.0,
        defect_tolerance=10.0,
    )
    
    print(f"\nInitial state: coherence={loop.state_host.get_state().coherence}")
    print(f"Initial budget: {loop.budget_manager.get_budget()}")
    
    # Run sequence
    results = loop.run_sequence(
        num_steps=5,
        coherence_changes=[-5.0, -3.0, -2.0, -1.0, -1.0],  # Improving coherence
        spends=[10.0, 8.0, 6.0, 4.0, 2.0],  # Decreasing spend
    )
    
    print("\n" + "-" * 60)
    print("Step Results:")
    print("-" * 60)
    
    for result in results:
        print(f"\nStep {result.step}:")
        print(f"  Verdict: {result.verdict.value}")
        print(f"  Coherence: {result.state_before.coherence:.2f} → {result.state_after.coherence:.2f}")
        print(f"  Residual: {result.residual:.2f}")
        print(f"  Spend: {result.spend:.2f}")
    
    print("\n" + "=" * 60)
    print(f"Final coherence: {loop.state_host.get_state().coherence:.2f}")
    print(f"Final budget available: {loop.budget_manager.get_budget().available:.2f}")
    print(f"Total receipts: {len(loop.receipt_store.get_all())}")
    print("=" * 60)


if __name__ == "__main__":
    demo()
