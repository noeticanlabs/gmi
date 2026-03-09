# Legacy Code: Prototype Implementation

**Status**: This directory contains the original prototype implementation.

## Status

This code is **DEPRECATED**. The canonical implementation has moved to `gmos/src/gmos/kernel/`.

## What to Use Instead

- **Canonical**: `gmos/src/gmos/kernel/hash_chain.py`
- **Verifier**: `gmos/src/gmos/kernel/verifier.py`
- **Receipts**: `gmos/src/gmos/kernel/receipt.py`

## Historical Context

This was the initial ledger implementation before the GM-OS architecture was formalized.

## Migration Notes

The canonical implementation in `gmos/src/gmos/kernel/` provides:
- HashChainLedger with cryptographic state binding
- OplaxVerifier for thermodynamic verification
- Receipt engine with decision codes
- Slab-based verification

See `docs/gmos_canon_spec.md` for the formal specification.
