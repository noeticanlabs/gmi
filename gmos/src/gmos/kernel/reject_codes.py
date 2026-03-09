"""
Reject Codes for GM-OS Verification

Centralized reject codes used by verifiers and receipt validators.
All verification failures use these codes for consistent error reporting.
"""

from enum import Enum


class RejectCode(Enum):
    """Canonical reject codes for GM-OS verification."""
    
    # Schema/Structure errors
    BAD_SCHEMA = "bad_schema"
    BAD_VERSION = "bad_version"
    
    # Identity errors
    BAD_OBJECT_ID = "bad_object_id"
    BAD_PROCESS_ID = "bad_process_id"
    
    # Hash/Chain errors
    BAD_STATE_HASH = "bad_state_hash"
    BAD_CHAIN_LINKAGE = "bad_chain_linkage"
    BAD_CANON_PROFILE_HASH = "bad_canon_profile_hash"
    BAD_POLICY_HASH = "bad_policy_hash"
    
    # Authority errors
    BAD_AUTHORITY = "bad_authority"
    ANCHOR_CONFLICT = "anchor_conflict"
    
    # Budget/Resource errors
    RESERVE_VIOLATION = "reserve_violation"
    INSUFFICIENT_BUDGET = "insufficient_budget"
    SPEND_MISMATCH = "spend_mismatch"
    
    # Policy errors
    DEFECT_BOUND_EXCEEDED = "defect_bound_exceeded"
    NONCANONICAL_ENCODING = "noncanonical_encoding"
    
    # Operation errors
    BAD_INSTRUCTION = "bad_instruction"
    VERIFICATION_FAILED = "verification_failed"
    
    # Generic
    UNKNOWN_ERROR = "unknown_error"


# Human-readable descriptions for each code
REJECT_DESCRIPTIONS = {
    RejectCode.BAD_SCHEMA: "Receipt schema does not match expected format",
    RejectCode.BAD_VERSION: "Receipt version is not supported",
    RejectCode.BAD_OBJECT_ID: "Object ID is invalid or missing",
    RejectCode.BAD_PROCESS_ID: "Process ID is invalid or unregistered",
    RejectCode.BAD_STATE_HASH: "State hash does not match expected value",
    RejectCode.BAD_CHAIN_LINKAGE: "Chain digest linkage is broken",
    RejectCode.BAD_CANON_PROFILE_HASH: "Canonical profile hash mismatch",
    RejectCode.BAD_POLICY_HASH: "Policy hash mismatch",
    RejectCode.BAD_AUTHORITY: "Authority level insufficient for operation",
    RejectCode.ANCHOR_CONFLICT: "Anchor/authority conflict detected",
    RejectCode.RESERVE_VIOLATION: "Budget would drop below reserve floor",
    RejectCode.INSUFFICIENT_BUDGET: "Budget insufficient for operation cost",
    RejectCode.SPEND_MISMATCH: "Spend calculation does not match",
    RejectCode.DEFECT_BOUND_EXCEEDED: "Defect would exceed allowed bound",
    RejectCode.NONCANONICAL_ENCODING: "Encoding does not match canonical form",
    RejectCode.BAD_INSTRUCTION: "Instruction is malformed or invalid",
    RejectCode.VERIFICATION_FAILED: "General verification failure",
    RejectCode.UNKNOWN_ERROR: "Unknown error occurred",
}


def get_reject_description(code: RejectCode) -> str:
    """Get human-readable description for a reject code."""
    return REJECT_DESCRIPTIONS.get(code, "No description available")


def is_recoverable(code: RejectCode) -> bool:
    """Check if a reject code indicates a potentially recoverable error."""
    recoverable = {
        RejectCode.INSUFFICIENT_BUDGET,
        RejectCode.BAD_CHAIN_LINKAGE,
        RejectCode.ANCHOR_CONFLICT,
    }
    return code in recoverable


def is_fatal(code: RejectCode) -> bool:
    """Check if a reject code indicates a fatal error."""
    fatal = {
        RejectCode.BAD_SCHEMA,
        RejectCode.BAD_VERSION,
        RejectCode.BAD_OBJECT_ID,
        RejectCode.BAD_PROCESS_ID,
        RejectCode.BAD_STATE_HASH,
        RejectCode.BAD_CANON_PROFILE_HASH,
        RejectCode.BAD_POLICY_HASH,
    }
    return code in fatal
