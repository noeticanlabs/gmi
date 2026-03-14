"""
GM-OS Receipt Contract

This module defines receipt structures and utilities for the Phase 1
executable law.

Status: Canonical - Phase 1 Foundation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from gmos.contracts.types import Receipt, ReceiptData, Verdict


# =============================================================================
# Receipt Factories
# =============================================================================


def create_receipt(
    receipt_id: str,
    data: ReceiptData,
) -> Receipt:
    """
    Create a receipt from receipt data.
    
    This is the canonical way to create receipts.
    """
    return Receipt(
        receipt_id=receipt_id,
        step=data.step,
        proposal_id=data.proposal_id,
        percept_refs=data.percept_refs,
        memory_refs=data.memory_refs,
        state_before_hash=data.state_before_hash,
        state_after_hash=data.state_after_hash,
        spend=data.spend,
        defect=data.defect,
        reserve_slack=data.reserve_slack,
        verdict=data.verdict,
        repair_notes=data.repair_notes,
        coherence_before=data.coherence_before,
        coherence_after=data.coherence_after,
        residual=data.residual,
        timestamp=datetime.now()
    )


def create_accept_receipt(
    receipt_id: str,
    step: int,
    proposal_id: str,
    coherence_before: float,
    coherence_after: float,
    spend: float,
    defect: float,
    reserve_slack: float,
    percept_refs: list[str] | None = None,
    memory_refs: list[str] | None = None,
) -> Receipt:
    """
    Create a receipt for an accepted proposal.
    """
    return create_receipt(
        receipt_id=receipt_id,
        data=ReceiptData(
            step=step,
            proposal_id=proposal_id,
            percept_refs=percept_refs or [],
            memory_refs=memory_refs or [],
            spend=spend,
            defect=defect,
            reserve_slack=reserve_slack,
            verdict=Verdict.ACCEPT,
            coherence_before=coherence_before,
            coherence_after=coherence_after,
            residual=coherence_after - coherence_before
        )
    )


def create_reject_receipt(
    receipt_id: str,
    step: int,
    proposal_id: str,
    reason: str,
    coherence_before: float,
    spend: float = 0.0,
) -> Receipt:
    """
    Create a receipt for a rejected proposal.
    """
    return create_receipt(
        receipt_id=receipt_id,
        data=ReceiptData(
            step=step,
            proposal_id=proposal_id,
            spend=spend,
            defect=0.0,
            reserve_slack=0.0,
            verdict=Verdict.REJECT,
            repair_notes=reason,
            coherence_before=coherence_before,
            coherence_after=coherence_before,
            residual=0.0
        )
    )


def create_repair_receipt(
    receipt_id: str,
    step: int,
    proposal_id: str,
    coherence_before: float,
    coherence_after: float,
    spend: float,
    defect: float,
    reserve_slack: float,
    repair_notes: str,
    percept_refs: list[str] | None = None,
    memory_refs: list[str] | None = None,
) -> Receipt:
    """
    Create a receipt for a repaired proposal.
    """
    return create_receipt(
        receipt_id=receipt_id,
        data=ReceiptData(
            step=step,
            proposal_id=proposal_id,
            percept_refs=percept_refs or [],
            memory_refs=memory_refs or [],
            spend=spend,
            defect=defect,
            reserve_slack=reserve_slack,
            verdict=Verdict.REPAIR,
            repair_notes=repair_notes,
            coherence_before=coherence_before,
            coherence_after=coherence_after,
            residual=coherence_after - coherence_before
        )
    )


def create_abstain_receipt(
    receipt_id: str,
    step: int,
    reason: str = "abstain",
    coherence_before: float = 0.0,
) -> Receipt:
    """
    Create a receipt for abstaining (no action).
    """
    return create_receipt(
        receipt_id=receipt_id,
        data=ReceiptData(
            step=step,
            proposal_id="abstain",
            spend=0.0,
            defect=0.0,
            reserve_slack=0.0,
            verdict=Verdict.ABSTAIN,
            repair_notes=reason,
            coherence_before=coherence_before,
            coherence_after=coherence_before,
            residual=0.0
        )
    )


# =============================================================================
# Receipt Validation
# =============================================================================


def validate_receipt(receipt: Receipt) -> tuple[bool, str]:
    """
    Validate a receipt for integrity.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if not receipt.receipt_id:
        return False, "receipt_id is required"
    
    if receipt.step < 0:
        return False, "step must be non-negative"
    
    if receipt.spend < 0:
        return False, "spend must be non-negative"
    
    # Check residual matches coherence difference
    expected_residual = receipt.coherence_after - receipt.coherence_before
    if abs(receipt.residual - expected_residual) > 1e-6:
        return False, f"residual mismatch: {receipt.residual} != {expected_residual}"
    
    return True, ""


def verify_receipt_chain(receipts: list[Receipt]) -> tuple[bool, str]:
    """
    Verify a chain of receipts for continuity.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not receipts:
        return True, ""
    
    # Sort by step
    sorted_receipts = sorted(receipts, key=lambda r: r.step)
    
    # Check step continuity
    expected_step = 0
    for receipt in sorted_receipts:
        if receipt.step != expected_step:
            return False, f"step discontinuity: expected {expected_step}, got {receipt.step}"
        expected_step += 1
    
    # Validate each receipt
    for receipt in sorted_receipts:
        is_valid, error = validate_receipt(receipt)
        if not is_valid:
            return False, f"invalid receipt {receipt.receipt_id}: {error}"
    
    return True, ""


# =============================================================================
# Receipt Queries
# =============================================================================


def get_receipts_by_verdict(
    receipts: list[Receipt],
    verdict: Verdict
) -> list[Receipt]:
    """Get all receipts with a specific verdict."""
    return [r for r in receipts if r.verdict == verdict]


def get_receipts_by_step(
    receipts: list[Receipt],
    step: int
) -> list[Receipt]:
    """Get all receipts for a specific step."""
    return [r for r in receipts if r.step == step]


def get_total_spend(receipts: list[Receipt]) -> float:
    """Calculate total spend across all receipts."""
    return sum(r.spend for r in receipts)


def get_total_defect(receipts: list[Receipt]) -> float:
    """Calculate total defect across all receipts."""
    return sum(r.defect for r in receipts)


def get_coherence_trajectory(receipts: list[Receipt]) -> list[float]:
    """Get coherence values over time."""
    sorted_receipts = sorted(receipts, key=lambda r: r.step)
    return [r.coherence_before for r in sorted_receipts]


# =============================================================================
# Receipt Statistics
# =============================================================================


@dataclass
class ReceiptStats:
    """Statistics about a set of receipts."""
    total_steps: int
    accepted: int
    rejected: int
    repaired: int
    abstained: int
    total_spend: float
    total_defect: float
    avg_spend: float
    avg_defect: float
    coherence_trend: str  # "improving", "stable", "degrading"


def compute_receipt_stats(receipts: list[Receipt]) -> ReceiptStats:
    """Compute statistics for a set of receipts."""
    if not receipts:
        return ReceiptStats(
            total_steps=0,
            accepted=0,
            rejected=0,
            repaired=0,
            abstained=0,
            total_spend=0.0,
            total_defect=0.0,
            avg_spend=0.0,
            avg_defect=0.0,
            coherence_trend="stable"
        )
    
    accepted = len(get_receipts_by_verdict(receipts, Verdict.ACCEPT))
    rejected = len(get_receipts_by_verdict(receipts, Verdict.REJECT))
    repaired = len(get_receipts_by_verdict(receipts, Verdict.REPAIR))
    abstained = len(get_receipts_by_verdict(receipts, Verdict.ABSTAIN))
    
    total_spend = get_total_spend(receipts)
    total_defect = get_total_defect(receipts)
    
    avg_spend = total_spend / len(receipts)
    avg_defect = total_defect / len(receipts)
    
    # Determine coherence trend
    trajectory = get_coherence_trajectory(receipts)
    if len(trajectory) >= 2:
        if trajectory[-1] < trajectory[0]:
            coherence_trend = "improving"
        elif trajectory[-1] > trajectory[0]:
            coherence_trend = "degrading"
        else:
            coherence_trend = "stable"
    else:
        coherence_trend = "stable"
    
    return ReceiptStats(
        total_steps=len(receipts),
        accepted=accepted,
        rejected=rejected,
        repaired=repaired,
        abstained=abstained,
        total_spend=total_spend,
        total_defect=total_defect,
        avg_spend=avg_spend,
        avg_defect=avg_defect,
        coherence_trend=coherence_trend
    )
