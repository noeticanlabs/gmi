# Development Setup

This repository uses a **dual-package monorepo structure**. The GM-OS package is the canonical implementation, while the root-level packages are legacy archives.

## Quick Start

```bash
# 1. Create and activate a virtual environment (REQUIRED on Nix/Project IDX)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install BOTH packages in editable mode
pip install -e .           # Installs legacy packages (core, memory, ledger, runtime, adapters)
pip install -e ./gmos      # Installs the canonical GM-OS package

# 3. Run tests

# Activate the virtual environment first (REQUIRED)
source .venv/bin/activate

# Test all packages:
pytest tests/ -v

# Test specific modules:
pytest gmos/tests/kernel/test_kernel.py -v    # Kernel substrate tests
pytest gmos/tests/agents/gmi/test_gmi.py -v  # GMI agent tests
pytest tests/test_gmos_modules.py -v          # GMOS module imports

# Quick test summary:
pytest tests/ --tb=short
```

**Note:** A virtual environment is REQUIRED - the project uses numpy and other packages not available in system Python.

## Running Tests (Post-Setup)

After setting up the environment, always activate the venv first:

```bash
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Current test status: 133 passed, 21 skipped
# - 20/20 kernel tests passing
# - 10/10 GMI agent tests passing
# - 21 skipped = Layer 2 features (Memory/Sensory/Symbolic - intentionally pending)
```

### Quick Test Commands

```bash
# Activate venv
source .venv/bin/activate

# Run GMOS kernel tests (all should pass)
python -m pytest gmos/tests/kernel/test_kernel.py -v

# Run GMI agent tests (all should pass)
python -m pytest gmos/tests/agents/gmi/test_gmi.py -v

# Run full test suite
python -m pytest tests/ -v
```

## Why Dual-Install?

This repository contains two Python packages:

| Package | Location | Purpose |
|---------|----------|---------|
| `gmi` | Root (`/`) | Legacy prototype code (archive-only) |
| `gmos` | `gmos/` | Canonical implementation (active development) |

Both packages must be installed for:
- Import resolution to work correctly
- IDE language servers to detect all modules
- Test discovery to find all test files

## Project IDX (Google Cloud)

If using Google Project IDX, the environment automatically installs both packages on workspace creation.

If you encounter issues, rebuild the environment from the IDX console.

## Troubleshooting

### "ModuleNotFoundError: No module named 'gmos'"

Ensure both packages are installed:
```bash
pip install -e . && pip install -e ./gmos
```

### IDE shows import errors

1. Ensure both packages are installed: `pip list | grep -E "gmi|gmos"`
2. Try restarting the IDE/language server

### Tests not discovered

Run pytest with explicit paths:
```bash
pytest tests/ gmos/tests/
```
