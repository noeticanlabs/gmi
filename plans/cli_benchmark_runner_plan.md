# Plan: User-Friendly CLI and Benchmark Runner

## Problem
Currently running benchmarks requires complex commands:
```bash
source .venv/bin/activate && python gmos/tests/agents/gmi/benchmark_suite.py
```

Users need a simple, intuitive CLI interface.

## Solution

### 1. Create CLI Module (`gmos/src/gmos_cli.py`)

```python
# gmos/src/gmos_cli.py
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="GMI Benchmark Runner")
    parser.add_argument("benchmark", choices=["nav", "keydoor", "all"], 
                        help="Which benchmark to run")
    parser.add_argument("--trials", "-n", type=int, default=10,
                        help="Number of trials")
    parser.add_argument("--noise", "-nse", type=float, default=0.0,
                        help="Noise level σ")
    parser.add_argument("--stress", "-s", action="store_true",
                        help="Run stress test (100 trials)")
    args = parser.parse_args()
    # Run benchmark

if __name__ == "__main__":
    main()
```

### 2. Add Console Script Entry Point (`pyproject.toml`)

```toml
[project.scripts]
gmi-bench = "gmos_cli:main"
```

### 3. Create Makefile (`Makefile`)

```makefile
.PHONY: bench bench-nav bench-keydoor bench-all install test

install:
    python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

bench:
    .venv/bin/python gmos/tests/agents/gmi/benchmark_suite.py

bench-nav:
    .venv/bin/python -c "from gmos.tests.agents.gmi.benchmark_suite import run_navigation_trial; ..."

bench-keydoor:
    .venv/bin/python -c "from gmos.tests.agents.gmi.benchmark_suite import run_key_door_trial; ..."

test:
    .venv/bin/pytest gmos/tests/
```

### 4. Create Shell Script Wrapper (`scripts/gmi-bench`)

```bash
#!/bin/bash
# Simple wrapper that auto-activates venv and runs benchmarks
cd "$(dirname "$0")/.."
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
python gmos/tests/agents/gmi/benchmark_suite.py "$@"
```

## Implementation Steps

| Step | Description | Priority |
|------|-------------|----------|
| 1 | Create `scripts/gmi-bench` wrapper script | HIGH |
| 2 | Update `pyproject.toml` with console scripts | HIGH |
| 3 | Create `Makefile` with common commands | MEDIUM |
| 4 | Add CLI argument parser in `gmos_cli.py` | LOW |

## Expected Usage After

```bash
# Option 1: Direct run (after install)
python gmos/tests/agents/gmi/benchmark_suite.py

# Option 2: Using Makefile
make install
make bench

# Option 3: Using CLI (after pip install -e)
gmi-bench all --trials 10 --noise 0.5
gmi-bench nav --stress

# Option 4: Using shell script
./scripts/gmi-bench
```
