# Verifier Rules Documentation

This document defines the verification rules enforced by the GM-OS verifier.

## State Hash Rules

### Rule 1: State Hash Computation
- State hash is computed as SHA256 of serialized state
- Must include: position `x`, budget `b`, step count
- Format: `SHA256(serialize(x, b, step))`

### Rule 2: State Hash Linkage
- Each receipt must include `state_hash_prev` and `state_hash_next`
- Chain is valid if `state_hash_prev` matches previous receipt's `state_hash_next`

## Chain Digest Rules

### Rule 3: Chain Digest Computation
- Chain digest is computed as: `SHA256(previous_digest || receipt_json)`
- First entry uses initial state hash as previous digest

### Rule 4: Chain Linkage
- Each receipt must include `chain_digest_prev` and `chain_digest_next`
- Chain is valid if digests form continuous sequence

## Reserve Rules

### Rule 5: Reserve Floor Preservation
- Budget after operation must be >= reserve_floor
- `b' >= reserve_floor` must hold for all accepted operations

### Rule 6: Dynamic Reserve
- Dynamic reserve: `reserve = α·pressure + β·uncertainty + γ·branch_load`
- Parameters configurable in VerifierConfig

## Reject Codes

| Code | Description | Recoverable |
|------|-------------|-------------|
| BAD_SCHEMA | Receipt schema invalid | No |
| BAD_VERSION | Version not supported | No |
| RESERVE_VIOLATION | Budget below reserve | Yes |
| INSUFFICIENT_BUDGET | Not enough budget | Yes |
| ANCHOR_CONFLICT | Anchor conflict detected | Yes |
| BAD_STATE_HASH | State hash mismatch | No |
| BAD_CHAIN_LINKAGE | Chain broken | Yes |

## Schema Validation

### Required Receipt Fields
- `schema_id`: Must match expected format (e.g., "gmi.receipt.infer.v1")
- `version`: Must be "v1"
- `process_id`: Must be registered process
- `state_hash_prev`: Must match previous state
- `state_hash_next`: Must match proposed state
- `chain_digest_prev`: Must match previous digest
- `chain_digest_next`: Must match computed digest
