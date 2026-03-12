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
# Test legacy packages:
pytest tests/

# Test GM-OS:
cd gmos && pytest tests/

# Or test both from root:
pytest tests/ gmos/tests/
```

**Note:** A virtual environment is REQUIRED when using Nix or Project IDX because they block pip from modifying the system Python.

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
