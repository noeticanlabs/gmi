# Legacy Code: Prototype Implementation

**Status**: This directory contains the original prototype implementation.

## Status

This code is **DEPRECATED**. The canonical implementation has moved to `gmos/src/gmos/agents/gmi/`.

## What to Use Instead

- **Canonical**: `gmos/src/gmos/agents/gmi/`
- **Execution Loop**: `gmos/src/gmos/agents/gmi/execution_loop.py`
- **Evolution Loop**: `gmos/src/gmos/agents/gmi/evolution_loop.py`
- **Semantic Loop**: `gmos/src/gmos/agents/gmi/semantic_loop.py`

## Historical Context

This was the initial runtime implementation before the GM-OS architecture was formalized.

## Migration Notes

The canonical implementation in `gmos/src/gmos/agents/gmi/` provides:
- GMI Agent with tension law
- Execution loop with budget management
- Evolution loop with reality collision
- Semantic loop for symbolic reasoning
- Policy selection

See `docs/gmi_canon_spec.md` for the formal specification.
