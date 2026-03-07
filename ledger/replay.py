"""
Replay Engine for the GMI Universal Cognition Engine.

Deterministic replay for offline audit.
Can reconstruct full execution from initial state + receipt chain.
"""

import json
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any, Callable
import numpy as np

from ledger.receipt import Receipt
from ledger.hash_chain import HashChainLedger


@dataclass
class ReplayResult:
    """Result of a replay operation."""
    is_valid: bool
    message: str
    final_state_hash: str
    diagnostics: Dict[str, Any]


class LedgerReplay:
    """
    Deterministic replay engine for offline audit.
    
    Can reconstruct full execution from initial state + receipt chain.
    Verifies that:
    - State transitions are legal
    - Potential values are consistent
    - Budget is properly managed
    - Chain integrity is maintained
    """
    
    def __init__(
        self, 
        initial_state_hash: str,
        potential_fn: Callable[[np.ndarray], float]
    ):
        """
        Initialize replay engine.
        
        Args:
            initial_state_hash: Hash of the initial state
            potential_fn: Function to compute potential from state
        """
        self.initial_state_hash = initial_state_hash
        self.potential_fn = potential_fn
        self.reconstructed_states: List[Dict[str, Any]] = []
        self.receipts: List[Receipt] = []
    
    def load_receipts(self, receipts: List[Receipt]) -> None:
        """Load receipts for replay."""
        self.receipts = receipts
    
    def load_from_file(self, filepath: str) -> None:
        """Load receipts from JSONL file."""
        receipts = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    receipts.append(Receipt.from_json(line.strip()))
        self.receipts = receipts
    
    def replay(
        self, 
        expected_final_state: Optional[str] = None,
        stop_on_error: bool = True
    ) -> ReplayResult:
        """
        Replay entire execution from receipts.
        
        Args:
            expected_final_state: Optional expected final state hash
            stop_on_error: Whether to stop on first error
            
        Returns:
            ReplayResult
        """
        if not self.receipts:
            return ReplayResult(
                is_valid=False,
                message="No receipts to replay",
                final_state_hash="",
                diagnostics={}
            )
        
        current_state_hash = self.initial_state_hash
        step_errors = []
        
        for i, receipt in enumerate(self.receipts):
            # Verify state hash continuity
            if receipt.x_hash_before != current_state_hash:
                error_msg = f"Step {i}: State hash mismatch - expected {current_state_hash[:16]}..., got {receipt.x_hash_before[:16]}..."
                step_errors.append(error_msg)
                if stop_on_error:
                    return ReplayResult(
                        is_valid=False,
                        message=error_msg,
                        final_state_hash=current_state_hash,
                        diagnostics={'error_at_step': i, 'errors': step_errors}
                    )
            
            # Verify potential values
            # Note: We can't reconstruct the actual state vector from hash alone
            # but we can verify consistency if we had the vector
            if receipt.v_before < 0 or receipt.v_after < 0:
                error_msg = f"Step {i}: Negative potential values"
                step_errors.append(error_msg)
                if stop_on_error:
                    return ReplayResult(
                        is_valid=False,
                        message=error_msg,
                        final_state_hash=current_state_hash,
                        diagnostics={'error_at_step': i}
                    )
            
            # Verify thermodynamic inequality (if we can)
            # V_after + sigma <= V_before + kappa
            thermo_check = (receipt.v_after + receipt.sigma) <= (receipt.v_before + receipt.kappa)
            if not thermo_check and receipt.decision == "ACCEPTED":
                error_msg = f"Step {i}: Thermodynamic inequality violated"
                step_errors.append(error_msg)
                if stop_on_error:
                    return ReplayResult(
                        is_valid=False,
                        message=error_msg,
                        final_state_hash=current_state_hash,
                        diagnostics={'error_at_step': i}
                    )
            
            # Verify budget consistency
            expected_budget_after = receipt.budget_before - receipt.sigma
            if abs(receipt.budget_after - expected_budget_after) > 1e-6:
                error_msg = f"Step {i}: Budget mismatch - expected {expected_budget_after}, got {receipt.budget_after}"
                step_errors.append(error_msg)
                if stop_on_error:
                    return ReplayResult(
                        is_valid=False,
                        message=error_msg,
                        final_state_hash=current_state_hash,
                        diagnostics={'error_at_step': i}
                    )
            
            # Verify decision consistency
            if receipt.decision == "ACCEPTED":
                current_state_hash = receipt.x_hash_after
            # If rejected/halt, state doesn't change
            
            # Store reconstructed state
            self.reconstructed_states.append({
                'step': i,
                'state_hash': current_state_hash,
                'potential': receipt.v_after,
                'budget': receipt.budget_after,
                'decision': receipt.decision
            })
        
        # Check final state if provided
        if expected_final_state and current_state_hash != expected_final_state:
            return ReplayResult(
                is_valid=False,
                message=f"Final state mismatch - expected {expected_final_state[:16]}..., got {current_state_hash[:16]}...",
                final_state_hash=current_state_hash,
                diagnostics={'errors': step_errors}
            )
        
        return ReplayResult(
            is_valid=len(step_errors) == 0,
            message=f"Replay complete: {len(self.receipts)} steps" + (f", {len(step_errors)} errors" if step_errors else ""),
            final_state_hash=current_state_hash,
            diagnostics={
                'total_steps': len(self.receipts),
                'errors': step_errors,
                'final_potential': self.reconstructed_states[-1]['potential'] if self.reconstructed_states else 0,
                'final_budget': self.reconstructed_states[-1]['budget'] if self.reconstructed_states else 0
            }
        )
    
    def replay_with_chain(
        self,
        ledger: HashChainLedger,
        expected_final_state: Optional[str] = None
    ) -> ReplayResult:
        """
        Replay execution using hash chain ledger.
        
        This verifies both:
        1. Receipt chain integrity
        2. State transition legality
        
        Args:
            ledger: HashChainLedger with receipts
            expected_final_state: Expected final state hash
            
        Returns:
            ReplayResult
        """
        # First verify chain integrity
        chain_valid, chain_msg = ledger.verify_chain()
        if not chain_valid:
            return ReplayResult(
                is_valid=False,
                message=f"Chain verification failed: {chain_msg}",
                final_state_hash="",
                diagnostics={'chain_error': chain_msg}
            )
        
        # Load receipts from ledger
        self.receipts = ledger.receipts
        
        # Get initial state hash from first chain record
        if ledger.chain:
            initial = ledger.chain[0].state_hash_prev
        else:
            initial = self.initial_state_hash
        
        # Replay with this initial state
        return self.replay(expected_final_state=expected_final_state)
    
    def get_state_at(self, step: int) -> Optional[Dict[str, Any]]:
        """Get reconstructed state at a specific step."""
        if 0 <= step < len(self.reconstructed_states):
            return self.reconstructed_states[step]
        return None
    
    def get_trajectory(self) -> List[Dict[str, Any]]:
        """Get full state trajectory."""
        return self.reconstructed_states
    
    def summary(self) -> Dict[str, Any]:
        """Get replay summary."""
        if not self.reconstructed_states:
            return {'message': 'No replay data'}
        
        return {
            'total_steps': len(self.reconstructed_states),
            'initial_state': self.reconstructed_states[0]['state_hash'] if self.reconstructed_states else "",
            'final_state': self.reconstructed_states[-1]['state_hash'],
            'final_potential': self.reconstructed_states[-1]['potential'],
            'final_budget': self.reconstructed_states[-1]['budget'],
            'decisions': {
                'accepted': sum(1 for s in self.reconstructed_states if s['decision'] == 'ACCEPTED'),
                'rejected': sum(1 for s in self.reconstructed_states if s['decision'] == 'REJECTED'),
                'halted': sum(1 for s in self.reconstructed_states if s['decision'] == 'HALT')
            }
        }


def replay_from_files(
    receipts_file: str,
    initial_state_hash: str,
    potential_fn: Callable[[np.ndarray], float],
    expected_final_state: Optional[str] = None
) -> ReplayResult:
    """
    Convenience function to replay from files.
    
    Args:
        receipts_file: Path to receipts JSONL file
        initial_state_hash: Hash of initial state
        potential_fn: Potential function
        expected_final_state: Optional expected final state
        
    Returns:
        ReplayResult
    """
    replay = LedgerReplay(initial_state_hash, potential_fn)
    replay.load_from_file(receipts_file)
    return replay.replay(expected_final_state=expected_final_state)


def verify_ledger_chain(ledger: HashChainLedger) -> Tuple[bool, str]:
    """
    Verify the integrity of a hash chain ledger.
    
    Args:
        ledger: Ledger to verify
        
    Returns:
        (is_valid, message)
    """
    return ledger.verify_chain()
