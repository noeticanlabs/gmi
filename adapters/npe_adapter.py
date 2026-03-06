"""
NPE Adapter - Bridge between NPE proposals and GMI verification

This adapter translates between the NPE's proposal format and GMI's
thermodynamic verification system.

Key components:
1. NPEAdapter: Converts NPE proposals → GMI Proposals
2. GMIToNPEFeedback: Sends GMI verification results → NPE

References:
- nsc/npe_v2_0.py (NPE implementation)
- core/state.py (GMI Proposal, Instruction)
- ledger/oplax_verifier.py (GMI verification)
"""

from __future__ import annotations

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Protocol

# GMI imports
from core.state import State, Instruction, Proposal
from ledger.oplax_verifier import OplaxVerifier
from ledger.receipt import Receipt


class NPEInterface(Protocol):
    """Protocol for NPE - allows swapping implementations"""
    def propose(self, context: Any) -> List[Any]: ...


class CoherenceMetrics:
    """Placeholder for NPE's coherence metrics"""
    def __init__(
        self,
        r_phys: float = 0.0,
        r_cons: float = 0.0,
        r_num: float = 0.0,
        r_ref: float = 0.0,
        r_stale: float = 0.0,
        r_conflict: float = 0.0
    ):
        self.r_phys = r_phys
        self.r_cons = r_cons
        self.r_num = r_num
        self.r_ref = r_ref
        self.r_stale = r_stale
        self.r_conflict = r_conflict


class NPEProposal:
    """
    Wrapper for NPE proposals.
    
    NPE generates proposals with coherence metrics. This wrapper
    translates them into GMI-compatible format.
    """
    def __init__(
        self,
        module_id: str,
        transform_fn,
        coherence: Optional[CoherenceMetrics] = None,
        sigma: float = 1.0,
        kappa: float = 1.0,
        novelty: float = 0.0
    ):
        self.module_id = module_id
        self.transform_fn = transform_fn  # Function x → x'
        self.coherence = coherence
        self.sigma = sigma
        self.kappa = kappa
        self.novelty = novelty


class NPEAdapter:
    """
    Bridge between NPE proposals and GMI verification.
    
    This adapter:
    1. Receives proposals from NPE (with coherence metrics)
    2. Converts them to GMI Proposals with precomputed x_prime
    3. Sends to GMI verifier
    4. Returns results
    
    The key insight: NPE provides the imagination, GMI provides governance.
    """
    
    def __init__(
        self,
        npe: NPEInterface,
        verifier: OplaxVerifier,
        embedder = None  # For text → vector
    ):
        self.npe = npe
        self.verifier = verifier
        self.embedder = embedder
    
    def generate_proposals(
        self,
        state: State,
        context: Any,
        n_proposals: int = 3
    ) -> List[Proposal]:
        """
        Generate proposals from NPE and convert to GMI format.
        
        Args:
            state: Current GMI state
            context: NPE proposal context
            n_proposals: Number of proposals to generate
        
        Returns:
            List of GMI Proposals with precomputed x_prime
        """
        # Get proposals from NPE
        npe_proposals = self.npe.propose(context)
        
        gmi_proposals = []
        for npe_prop in npe_proposals[:n_proposals]:
            # Convert NPE proposal to GMI format
            gmi_prop = self._convert_proposal(npe_prop, state)
            if gmi_prop:
                gmi_proposals.append(gmi_prop)
        
        return gmi_proposals
    
    def _convert_proposal(
        self,
        npe_proposal,
        state: State
    ) -> Optional[Proposal]:
        """Convert NPE proposal to GMI Proposal"""
        
        # Extract coherence metrics if available
        coherence = getattr(npe_proposal, 'coherence', None)
        
        # Convert coherence → sigma/kappa bounds
        sigma, kappa = self._coherence_to_bounds(coherence)
        
        # Get novelty from NPE (or calculate)
        novelty = getattr(npe_proposal, 'novelty', 0.0)
        
        # Compute x_prime (precomputed - no re-evaluation)
        try:
            x_prime = npe_proposal.transform_fn(state.x)
        except Exception:
            return None  # Skip invalid proposals
        
        # Create GMI Instruction
        instr = Instruction(
            op_code=getattr(npe_proposal, 'module_id', 'NPE_PROPOSAL'),
            pi_func=lambda x, fn=npe_proposal.transform_fn: fn(x),  # Fallback
            sigma=sigma,
            kappa=kappa
        )
        
        # Add novelty metadata to instruction
        instr.novelty = novelty
        instr.coherence = coherence
        
        return Proposal(instruction=instr, x_prime=x_prime)
    
    def _coherence_to_bounds(
        self,
        coherence: Optional[CoherenceMetrics]
    ) -> Tuple[float, float]:
        """
        Convert NPE coherence metrics to thermodynamic bounds.
        
        Translation:
        - r_phys (physics defect) → kappa (allowed defect)
        - r_num (numerical stability) → sigma (energy cost)
        - r_cons (constraint) → impacts both
        """
        if coherence is None:
            return 1.0, 1.0  # Default bounds
        
        # Higher defects require higher allowances
        sigma = 1.0 + coherence.r_num * 10 + coherence.r_cons * 5
        kappa = coherence.r_phys * 5 + coherence.r_cons * 3
        
        # Ensure minimum values
        sigma = max(sigma, 0.1)
        kappa = max(kappa, 0.1)
        
        return sigma, kappa
    
    def verify_proposal(
        self,
        step_idx: int,
        state: State,
        proposal: Proposal
    ) -> Tuple[bool, State, Receipt]:
        """
        Verify a proposal using GMI's thermodynamic constraints.
        
        This is the core governance mechanism - NPE imagines,
        GMI verifies.
        """
        return self.verifier.check(
            step_idx=step_idx,
            state=state,
            instr=proposal,
            precomputed_x_prime=proposal.x_prime
        )


class GMIToNPEFeedback:
    """
    Feedback loop from GMI to NPE.
    
    When GMI rejects a proposal, we send that information back
    to NPE so it can learn and improve future proposals.
    
    This creates the closed-loop learning system:
    NPE (imagine) → GMI (verify) → feedback → NPE (learn)
    """
    
    def __init__(self, npe: NPEInterface):
        self.npe = npe
        self.rejection_history: List[Dict[str, Any]] = []
        self.acceptance_history: List[Dict[str, Any]] = []
    
    def report_rejection(
        self,
        proposal: Proposal,
        receipt: Receipt
    ) -> None:
        """
        Report a rejected proposal to NPE for learning.
        
        Args:
            proposal: The proposal that was rejected
            receipt: The verification receipt with failure reason
        """
        rejection_info = {
            "module_id": proposal.instruction.op_code,
            "v_before": receipt.v_before,
            "v_after": receipt.v_after,
            "sigma": receipt.sigma,
            "kappa": receipt.kappa,
            "reason": receipt.message,
            "novelty": getattr(proposal.instruction, 'novelty', 0.0)
        }
        
        self.rejection_history.append(rejection_info)
        
        # In a real implementation, this would update NPE's model
        # self.npe.learn_from_rejection(rejection_info)
    
    def report_acceptance(
        self,
        proposal: Proposal,
        receipt: Receipt
    ) -> None:
        """
        Report an accepted proposal to NPE for learning.
        
        Args:
            proposal: The proposal that was accepted
            receipt: The verification receipt
        """
        acceptance_info = {
            "module_id": proposal.instruction.op_code,
            "v_before": receipt.v_before,
            "v_after": receipt.v_after,
            "sigma": receipt.sigma,
            "kappa": receipt.kappa,
            "novelty": getattr(proposal.instruction, 'novelty', 0.0)
        }
        
        self.acceptance_history.append(acceptance_info)
        
        # In a real implementation:
        # self.npe.learn_from_acceptance(acceptance_info)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return feedback statistics"""
        total = len(self.acceptance_history) + len(self.rejection_history)
        return {
            "accepted": len(self.acceptance_history),
            "rejected": len(self.rejection_history),
            "acceptance_rate": (
                len(self.acceptance_history) / max(1, total)
            )
        }


class CombinedRuntime:
    """
    Combined NPE + GMI execution loop.
    
    This is the "wild imagination + strict governance" architecture:
    1. NPE generates proposals (potentially wild/hallucinated)
    2. GMI verifies them against thermodynamic constraints
    3. Feedback loop enables learning
    
    The key separation:
    - NPE = dreaming (generates anything)
    - GMI = waking (validates what's possible)
    """
    
    def __init__(
        self,
        npe: NPEInterface,
        verifier: OplaxVerifier,
        embedder = None,
        fallback_proposals: bool = True
    ):
        self.npe = npe
        self.verifier = verifier
        self.embedder = embedder
        self.fallback_proposals = fallback_proposals
        
        self.adapter = NPEAdapter(npe, verifier, embedder)
        self.feedback = GMIToNPEFeedback(npe)
    
    def run(
        self,
        initial_x,
        initial_budget: float,
        n_steps: int = 10,
        context_factory = None
    ) -> State:
        """
        Run the combined NPE + GMI loop.
        
        Args:
            initial_x: Initial state coordinates
            initial_budget: Thermodynamic budget
            n_steps: Number of execution steps
            context_factory: Function to create NPE context
        
        Returns:
            Final GMI state
        """
        state = State(initial_x, initial_budget)
        
        for step in range(n_steps):
            # Create context for NPE
            context = context_factory(step) if context_factory else {"step": step}
            
            # Generate proposals from NPE
            proposals = self.adapter.generate_proposals(state, context)
            
            # Add fallback proposals for robustness
            if self.fallback_proposals:
                proposals.extend(self._generate_fallbacks(state))
            
            # Verify each proposal
            survivors = []
            for proposal in proposals:
                accepted, next_state, receipt = self.adapter.verify_proposal(
                    step, state, proposal
                )
                
                if accepted:
                    survivors.append((proposal, next_state, receipt))
                    self.feedback.report_acceptance(proposal, receipt)
                else:
                    self.feedback.report_rejection(proposal, receipt)
            
            # Select best proposal
            if survivors:
                # Select by efficiency + novelty
                best = self._select_best(survivors)
                state = best[1]
                print(f"Step {step}: ACCEPTED {best[0].instruction.op_code}")
            else:
                print(f"Step {step}: HALT - No valid proposals")
                break
        
        return state
    
    def _generate_fallbacks(self, state: State) -> List[Proposal]:
        """Generate fallback proposals (INFER, EXPLORE)"""
        # This would use GMI's built-in proposal generators
        return []  # Placeholder
    
    def _select_best(
        self,
        survivors: List[Tuple[Proposal, State, Receipt]]
    ) -> Tuple[Proposal, State, Receipt]:
        """Select best proposal using efficiency + novelty scoring"""
        
        best = None
        best_score = float('-inf')
        
        for proposal, next_state, receipt in survivors:
            # Calculate efficiency
            descent = receipt.v_before - receipt.v_after
            efficiency = descent / max(proposal.instruction.sigma, 1e-6)
            
            # Get novelty
            novelty = getattr(proposal.instruction, 'novelty', 0.0)
            
            # Combined score
            score = 0.7 * efficiency + 0.3 * novelty
            
            if score > best_score:
                best_score = score
                best = (proposal, next_state, receipt)
        
        return best
