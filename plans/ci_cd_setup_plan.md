# CI/CD Setup Plan for GMI

## Overview

This document outlines the CI/CD pipeline to be implemented for the GMI (Governed Metabolic Intelligence) project.

## Current State

- **Version**: 0.1.0 (Alpha)
- **Python**: 3.11, 3.12
- **Test Framework**: pytest (configured in pyproject.toml)
- **Linting**: ruff, black, mypy

## Proposed CI/CD Workflow

### GitHub Actions Workflow File

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
        pip install pytest-cov
    
    - name: Run tests with coverage
      run: |
        pytest --cov=core --cov=ledger --cov=runtime --cov=memory --cov-report=xml --cov-report=term-missing tests/
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install ruff black mypy
    
    - name: Run Ruff
      run: ruff check core/ ledger/ runtime/ memory/ adapters/
    
    - name: Run Black
      run: black --check core/ ledger/ runtime/ memory/ adapters/
    
    - name: Run MyPy
      run: mypy core/ ledger/ runtime/ memory/

  gmos-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    
    - name: Install GM-OS dependencies
      run: |
        python -m pip install --upgrade pip
        cd gmos && pip install -e ".[dev]" && cd ..
        pip install pytest
    
    - name: Run GM-OS tests
      run: cd gmos && pytest -q
```

## Implementation Steps

### Step 1: Create GitHub Actions Directory Structure

```bash
mkdir -p .github/workflows
```

### Step 2: Create CI Workflow File

Create `.github/workflows/ci.yml` with the YAML content above.

### Step 3: Add pytest-cov Dependency

Update `pyproject.toml` to add pytest-cov:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
]
```

### Step 4: Add Coverage Configuration

Update `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["core", "ledger", "runtime", "memory"]
omit = ["*/tests/*", "*/experiments/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

## Jobs Summary

| Job | Purpose | Timeout |
|-----|---------|---------|
| test | Run pytest with coverage on Python 3.11, 3.12 | 10 min |
| lint | Run ruff, black, mypy checks | 5 min |
| gmos-test | Run GM-OS subproject tests | 5 min |

## Codecov Integration

To enable Codecov:
1. Go to https://codecov.io and sign in with GitHub
2. Add the `gmi` repository
3. The workflow will automatically upload coverage on each run

## Verification Commands

Before pushing, verify locally:

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=core --cov=ledger --cov=runtime --cov=memory --cov-report=term-missing tests/

# Run linting
ruff check core/ ledger/ runtime/ memory/ adapters/
black --check core/ ledger/ runtime/ memory/ adapters/
mypy core/ ledger/ runtime/ memory/
```

## Next Steps

1. Switch to **Code mode** to implement the CI/CD configuration
2. Create `.github/workflows/ci.yml`
3. Update `pyproject.toml` with coverage configuration
4. Test locally before pushing
