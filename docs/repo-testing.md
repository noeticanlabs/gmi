# Repository Testing Guide

## Overview

This repo contains two related projects:
- **gmi-main**: The core GMI cognition engine (root level)
- **gmos**: The Glyph-Manifold Operating System (subdirectory)

## Testing gmi-main (root)

```bash
# From repository root
pip install -e .
pytest tests/ -v
```

## Testing gmos (subdirectory)

```bash
# From gmos subdirectory
cd gmos
pip install -e .
pytest -q tests/
```

## Install Order

1. First install gmi-main: `pip install -e .` (root)
2. Then install gmos: `cd gmos && pip install -e .`

Note: gmos is designed as a separate package that can be imported as `from gmos...`. The root pyproject.toml excludes gmos from its test discovery to avoid ambiguity.

## Current Invariants (must pass)

- Root GMI tests pass
- Stress tests pass (in experiments/)
- Reserve law blocks greedy leap
- Halt receipt appears when no lawful move exists

## Running Stress Tests

```bash
# Greed test - verifies ledger blocks catastrophic decisions
python -c "from experiments.stress_tests import run_greed_test; print(run_greed_test())"

# Pressure test - verifies anti-freeze under high pressure  
python -c "from experiments.stress_tests import run_pressure_test; print(run_pressure_test())"
```
