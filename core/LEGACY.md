# Legacy Code: Prototype Implementation

**Status**: This directory contains the original prototype implementation.

## Status

This code is **DEPRECATED**. The canonical implementation has moved to `gmos/src/gmos/`.

## What to Use Instead

- **Canonical**: `gmos/src/gmos/kernel/`
- **GMI Agent**: `gmos/src/gmos/agents/gmi/`
- **Memory**: `gmos/src/gmos/memory/`

## Historical Context

This was the initial implementation of Governed Manifold Intelligence (GMI) before the GM-OS (Governed Manifold Operating Substrate) architecture was formalized.

## Migration Notes

The canonical implementation in `gmos/src/gmos/` provides:
- Full substrate state with continuous dynamics
- Moreau-projected dynamics for admissible evolution
- Anchor authority for anti-hallucination
- GMI Tension Law implementation
- Hash-chained receipt verification
- Complete theorem suite

See `docs/gmos_canon_spec.md` and `docs/gmi_canon_spec.md` for the formal specification.
