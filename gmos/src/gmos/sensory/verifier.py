"""
Sensory Verifier (RV_sens) for Dual-Use Sensory Substrate.

Per spec §16: The sensory verifier must check all acceptance criteria
for sensory observation receipts.

Verification checks:
1. Schema ID validation
2. Canon profile hash validation
3. Policy hash validation
4. Chain digest linkage
5. State hash linkage
6. Source tag validity (in {ext, int, mem, sim})
7. Numeric parse validity
8. Observation cost positivity (Σ > 0)
9. Salience bounds (0 ≤ sal ≤ 1)
10. Anchor / provenance consistency

This is the deterministic verifier interface required by Coh.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import json

from gmos.sensory.receipts import (
    SensoryReceipt,
    SCHEMA_ID,
    SourceTag,
    Verdict,
    RejectCode,
)


@dataclass
class VerificationResult:
    """
    Result of sensory receipt verification.
    """
    is_valid: bool
    verdict: str
    reject_code: Optional[str] = None
    error_message: Optional[str] = None
    verified_fields: List[str] = None
    
    def __post_init__(self):
        if self.verified_fields is None:
            self.verified_fields = []


class SensoryVerifier:
    """
    Sensory verifier RV_sens per spec §16.
    
    This is the deterministic verifier interface that checks
    all acceptance criteria for sensory observation steps.
    
    Per spec: RV_sens: (H_prev, r, H_next, H_chain_prev) → {ACCEPT, REJECT(code)}
    
    Usage:
        verifier = SensoryVerifier()
        result = verifier.verify(receipt, prev_state_hash, prev_chain_digest)
    """
    
    def __init__(
        self,
        expected_schema_id: str = SCHEMA_ID,
        expected_object_id: str = "gmos.sensory.substrate.core.v1",
    ):
        """
        Initialize the sensory verifier.
        
        Args:
            expected_schema_id: Expected schema ID for validation
            expected_object_id: Expected object ID for validation
        """
        self.expected_schema_id = expected_schema_id
        self.expected_object_id = expected_object_id
        self.valid_source_tags = {s.value for s in SourceTag}
    
    def verify(
        self,
        receipt: SensoryReceipt,
        prev_state_hash: str = "",
        prev_chain_digest: str = ""
    ) -> VerificationResult:
        """
        Verify a sensory receipt.
        
        Performs all 10 verification checks per spec §16.
        
        Args:
            receipt: SensoryReceipt to verify
            prev_state_hash: Expected previous state hash
            prev_chain_digest: Expected previous chain digest
            
        Returns:
            VerificationResult with ACCEPT or REJECT
        """
        verified_fields = []
        
        # Check 1: Schema ID
        if receipt.schema_id != self.expected_schema_id:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.INVALID_SCHEMA.value,
                error_message=f"Schema ID mismatch: expected {self.expected_schema_id}, got {receipt.schema_id}",
            )
        verified_fields.append("schema_id")
        
        # Check 2: Canon profile hash (must be present if expected)
        if not receipt.canon_profile_hash:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.INVALID_HASH.value,
                error_message="Missing canon_profile_hash",
            )
        verified_fields.append("canon_profile_hash")
        
        # Check 3: Policy hash (must be present if expected)
        if not receipt.policy_hash:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.INVALID_HASH.value,
                error_message="Missing policy_hash",
            )
        verified_fields.append("policy_hash")
        
        # Check 4: Chain digest linkage
        if prev_chain_digest and receipt.chain_digest_prev != prev_chain_digest:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.INVALID_CHAIN.value,
                error_message=f"Chain digest mismatch: expected {prev_chain_digest}, got {receipt.chain_digest_prev}",
            )
        verified_fields.append("chain_digest")
        
        # Check 5: State hash linkage
        if prev_state_hash and receipt.state_hash_prev != prev_state_hash:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.INVALID_HASH.value,
                error_message=f"State hash mismatch: expected {prev_state_hash}, got {receipt.state_hash_prev}",
            )
        verified_fields.append("state_hash")
        
        # Check 6: Source tag validity
        if receipt.source_tag not in self.valid_source_tags:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.INVALID_SOURCE_TAG.value,
                error_message=f"Invalid source_tag: {receipt.source_tag}",
            )
        verified_fields.append("source_tag")
        
        # Check 7: Numeric parse validity
        numeric_error = self._validate_numeric_fields(receipt)
        if numeric_error:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.INVALID_NUMERIC.value,
                error_message=numeric_error,
            )
        verified_fields.append("numeric_fields")
        
        # Check 8: Observation cost positivity
        try:
            cost = float(receipt.observation_cost)
            if cost <= 0:
                return VerificationResult(
                    is_valid=False,
                    verdict=Verdict.REJECT.value,
                    reject_code=RejectCode.COST_NOT_POSITIVE.value,
                    error_message=f"observation_cost must be positive: {cost}",
                )
        except ValueError as e:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.INVALID_NUMERIC.value,
                error_message=f"Invalid observation_cost: {e}",
            )
        verified_fields.append("observation_cost")
        
        # Check 9: Salience bounds
        try:
            salience = float(receipt.salience_score)
            if not (0 <= salience <= 1):
                return VerificationResult(
                    is_valid=False,
                    verdict=Verdict.REJECT.value,
                    reject_code=RejectCode.SALIENCE_OUT_OF_BOUNDS.value,
                    error_message=f"salience_score out of [0,1]: {salience}",
                )
        except ValueError as e:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.INVALID_NUMERIC.value,
                error_message=f"Invalid salience_score: {e}",
            )
        verified_fields.append("salience")
        
        # Check 10: Anchor / provenance consistency
        anchor_error = self._validate_anchor_consistency(receipt)
        if anchor_error:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.ANCHOR_MISMATCH.value,
                error_message=anchor_error,
            )
        verified_fields.append("anchor_consistency")
        
        # All checks passed
        return VerificationResult(
            is_valid=True,
            verdict=Verdict.ACCEPT.value,
            verified_fields=verified_fields,
        )
    
    def _validate_numeric_fields(self, receipt: SensoryReceipt) -> Optional[str]:
        """
        Validate that all numeric fields can be parsed.
        """
        fields = [
            ("authority_weight", receipt.authority_weight),
            ("quality_score", receipt.quality_score),
            ("salience_score", receipt.salience_score),
            ("observation_cost", receipt.observation_cost),
        ]
        
        for name, value in fields:
            try:
                float(value)
            except (ValueError, TypeError):
                return f"Invalid {name}: {value}"
        
        return None
    
    def _validate_anchor_consistency(self, receipt: SensoryReceipt) -> Optional[str]:
        """
        Validate anchor and provenance consistency.
        
        Checks:
        - If source_tag is "external", authority should be high
        - If source_tag is "simulation", authority should be low
        """
        try:
            authority = float(receipt.authority_weight)
            source = receipt.source_tag
            
            # Expected authority ranges by source
            expected_ranges = {
                "ext": (0.7, 1.0),
                "int": (0.3, 0.7),
                "mem": (0.2, 0.5),
                "sim": (0.0, 0.3),
            }
            
            if source in expected_ranges:
                low, high = expected_ranges[source]
                if not (low <= authority <= high):
                    return f"Authority {authority} out of expected range [{low},{high}] for source {source}"
            
        except (ValueError, TypeError):
            return f"Cannot validate anchor: invalid authority {receipt.authority_weight}"
        
        return None
    
    def verify_batch(
        self,
        receipts: List[SensoryReceipt],
        prev_state_hash: str = "",
        prev_chain_digest: str = ""
    ) -> List[VerificationResult]:
        """
        Verify a batch of receipts.
        
        Args:
            receipts: List of SensoryReceipt to verify
            prev_state_hash: Initial previous state hash
            prev_chain_digest: Initial previous chain digest
            
        Returns:
            List of VerificationResult (one per receipt)
        """
        results = []
        current_state = prev_state_hash
        current_chain = prev_chain_digest
        
        for receipt in receipts:
            result = self.verify(receipt, current_state, current_chain)
            results.append(result)
            
            # Update hashes for chain
            if result.is_valid:
                current_state = receipt.state_hash_next
                current_chain = receipt.chain_digest_next
        
        return results
    
    def get_reject_statistics(
        self,
        results: List[VerificationResult]
    ) -> Dict[str, int]:
        """
        Get statistics on rejection reasons.
        
        Args:
            results: List of verification results
            
        Returns:
            Dictionary of reject_code -> count
        """
        stats = {}
        for result in results:
            if not result.is_valid:
                code = result.reject_code or "UNKNOWN"
                stats[code] = stats.get(code, 0) + 1
        return stats


class SensoryVerifierWithPolicy:
    """
    Sensory verifier with policy enforcement.
    
    Extends the base verifier with policy-specific checks.
    """
    
    def __init__(
        self,
        verifier: Optional[SensoryVerifier] = None,
        max_observation_cost: float = 1.0,
        min_authority_threshold: float = 0.1,
    ):
        """
        Initialize verifier with policy.
        
        Args:
            verifier: Base sensory verifier
            max_observation_cost: Maximum allowed observation cost
            min_authority_threshold: Minimum authority to accept
        """
        self.verifier = verifier or SensoryVerifier()
        self.max_observation_cost = max_observation_cost
        self.min_authority_threshold = min_authority_threshold
    
    def verify_with_policy(
        self,
        receipt: SensoryReceipt,
        prev_state_hash: str = "",
        prev_chain_digest: str = ""
    ) -> VerificationResult:
        """
        Verify with additional policy checks.
        
        Args:
            receipt: SensoryReceipt to verify
            prev_state_hash: Previous state hash
            prev_chain_digest: Previous chain digest
            
        Returns:
            VerificationResult
        """
        # First do base verification
        result = self.verifier.verify(receipt, prev_state_hash, prev_chain_digest)
        
        if not result.is_valid:
            return result
        
        # Policy checks
        try:
            # Check observation cost
            cost = float(receipt.observation_cost)
            if cost > self.max_observation_cost:
                return VerificationResult(
                    is_valid=False,
                    verdict=Verdict.REJECT.value,
                    reject_code=RejectCode.COST_NOT_POSITIVE.value,
                    error_message=f"Observation cost {cost} exceeds policy max {self.max_observation_cost}",
                    verified_fields=result.verified_fields,
                )
            
            # Check authority threshold
            authority = float(receipt.authority_weight)
            if authority < self.min_authority_threshold:
                return VerificationResult(
                    is_valid=False,
                    verdict=Verdict.REJECT.value,
                    reject_code=RejectCode.ANCHOR_MISMATCH.value,
                    error_message=f"Authority {authority} below threshold {self.min_authority_threshold}",
                    verified_fields=result.verified_fields,
                )
                
        except (ValueError, TypeError) as e:
            return VerificationResult(
                is_valid=False,
                verdict=Verdict.REJECT.value,
                reject_code=RejectCode.INVALID_NUMERIC.value,
                error_message=f"Policy check failed: {e}",
                verified_fields=result.verified_fields,
            )
        
        # Policy checks passed
        result.verified_fields.extend(["observation_cost_policy", "authority_policy"])
        return result


# === Exports ===

__all__ = [
    "VerificationResult",
    "SensoryVerifier",
    "SensoryVerifierWithPolicy",
]
