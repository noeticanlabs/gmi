# Legacy Code: Prototype Implementation

**Status**: This directory contains the original prototype implementation.

## Status

This code is **DEPRECATED**. The canonical implementation has moved to `gmos/src/gmos/memory/`.

## What to Use Instead

- **Canonical**: `gmos/src/gmos/memory/`

## Historical Context

This was the initial memory implementation before the GM-OS architecture was formalized.

## Migration Notes

The canonical implementation in `gmos/src/gmos/memory/` provides the full memory manifold with:
- Budget-aware operations
- Episode-based replay
- Workspace state management
- Consolidation operators
- Relevance scoring

See `docs/gmos_canon_spec.md` for the formal specification.
