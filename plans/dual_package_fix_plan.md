# Dual Package Fix Implementation Plan

## Current State Assessment

After reviewing the existing configuration, **most fixes are already implemented**:

| Item | Status | File |
|------|--------|------|
| Virtual environment creation | ✅ Implemented | `.idx/dev.nix` |
| Dual package installation | ✅ Implemented | `.idx/dev.nix` |
| Unified test discovery | ✅ Implemented | `pyproject.toml` |
| Setup documentation | ✅ Exists | `SETUP.md` |
| CI workflow | ✅ Exists | `.github/workflows/ci.yml` |

## Remaining Issues Identified

### Issue 1: CI Workflow Not Using Virtual Environment
The CI workflow installs packages directly without a venv:
```yaml
# Current (line 25-31)
pip install -e ".[dev]"
pip install -e "./gmos"
```

**Fix**: Use venv for consistency with IDX environment.

### Issue 2: Lint Job Missing GM-OS
The lint job only checks legacy directories:
```yaml
# Current (line 65-75)
ruff check core/ ledger/ runtime/ memory/ adapters/
```
Missing: `gmos/src/`

### Issue 3: Coverage Configuration Incomplete
Root pyproject.toml only tracks legacy packages:
```toml
# Current (line 68-70)
source = ["core", "ledger", "runtime", "memory"]
```
Missing: `gmos`

## Implementation Plan

### Phase 1: Fix CI Workflow

#### 1.1 Update `.github/workflows/ci.yml`
- Add venv creation step
- Add gmos to lint checks
- Add gmos to coverage

### Phase 2: Enhance Configuration

#### 2.1 Update Coverage Configuration
Add gmos to coverage sources in root pyproject.toml

#### 2.2 Add Unified Test Script
Create `scripts/run_all_tests.py` for convenience

---

## Files to Modify

| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | Add venv, fix lint, add gmos coverage |
| `pyproject.toml` | Add gmos to coverage sources |

---

## Success Criteria

1. CI runs with virtual environment
2. Lint checks both legacy and gmos code
3. Coverage reports include gmos
4. Single command runs all tests
