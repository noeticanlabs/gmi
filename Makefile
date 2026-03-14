# Makefile for GMI (Governed Metabolic Intelligence)
#
# Usage:
#   make install       # Create venv and install dependencies
#   make bench        # Run full benchmark suite
#   make bench-nav    # Run navigation benchmark only
#   make bench-keydoor # Run key-door benchmark only
#   make test         # Run all tests
#   make test-gmi     # Run GMI-specific tests
#   make clean        # Remove venv and cache files
#   make help         # Show this help

.PHONY: help install bench bench-nav bench-keydoor bench-stress test test-gmi clean

# Default target
.DEFAULT_GOAL := help

# Colors
GREEN := $(shell tput setaf 2 2>/dev/null || echo "")
BLUE := $(shell tput setaf 4 2>/dev/null || echo "")
YELLOW := $(shell tput setaf 3 2>/dev/null || echo "")
RESET := $(shell tput sgr0 2>/dev/null || echo "")

help:
	@echo "$(BLUE)============================================================$(RESET)"
	@echo "$(BLUE)GMI - Governed Metabolic Intelligence$(RESET)"
	@echo "$(BLUE)============================================================$(RESET)"
	@echo ""
	@echo "Available targets:"
	@echo "  $(GREEN)install$(RESET)       - Create venv and install dependencies"
	@echo "  $(GREEN)bench$(RESET)         - Run full benchmark suite"
	@echo "  $(GREEN)bench-nav$(RESET)     - Run navigation benchmark"
	@echo "  $(GREEN)bench-keydoor$(RESET) - Run key-door benchmark"
	@echo "  $(GREEN)bench-stress$(RESET)  - Run stress test (100 trials)"
	@echo "  $(GREEN)test$(RESET)          - Run all tests"
	@echo "  $(GREEN)test-gmi$(RESET)      - Run GMI-specific tests"
	@echo "  $(GREEN)clean$(RESET)         - Remove venv and cache files"
	@echo ""

install:
	@echo "$(YELLOW)Creating virtual environment...$(RESET)"
	@python3 -m venv .venv
	@echo "$(YELLOW)Installing dependencies...$(RESET)"
	@.venv/bin/pip install -q -e ".[dev]"
	@echo "$(GREEN)Done! Virtual environment created at .venv/$(RESET)"

bench: install
	@echo "$(YELLOW)Running GMI benchmark suite...$(RESET)"
	@.venv/bin/python gmos/tests/agents/gmi/benchmark_suite.py

bench-nav: install
	@echo "$(YELLOW)Running navigation benchmark...$(RESET)"
	@.venv/bin/python -c "
import sys
sys.path.insert(0, 'gmos/src')
from gmos.tests.agents.gmi.benchmark_suite import run_navigation_trial

successes = 0
for seed in range(10):
    result = run_navigation_trial(noise_level=0.0, seed=seed, max_steps=100)
    if result.success:
        successes += 1

print(f'Navigation: {successes}/10 ({100*successes//10}%)')
"

bench-keydoor: install
	@echo "$(YELLOW)Running key-door benchmark...$(RESET)"
	@.venv/bin/python -c "
import sys
sys.path.insert(0, 'gmos/src')
from gmos.tests.agents.gmi.benchmark_suite import run_key_door_trial

successes = 0
for seed in range(10):
    result = run_key_door_trial(noise_level=0.0, seed=seed, max_steps=100)
    if result.success:
        successes += 1

print(f'Key-Door: {successes}/10 ({100*successes//10}%)')
"

bench-stress: install
	@echo "$(YELLOW)Running stress test (100 trials)...$(RESET)"
	@.venv/bin/python -c "
import sys
sys.path.insert(0, 'gmos/src')
from gmos.tests.agents.gmi.benchmark_suite import run_navigation_trial

successes = 0
for seed in range(100):
    result = run_navigation_trial(noise_level=0.0, seed=seed, max_steps=100)
    if result.success:
        successes += 1
    if (seed + 1) % 20 == 0:
        print(f'  {seed+1}/100: {100*successes//(seed+1)}%')

print(f'Stress Test: {successes}/100 ({100*successes//100}%)')
"

test: install
	@echo "$(YELLOW)Running all tests...$(RESET)"
	@.venv/bin/pytest tests/ gmos/tests/ -v --tb=short

test-gmi: install
	@echo "$(YELLOW)Running GMI-specific tests...$(RESET)"
	@.venv/bin/pytest gmos/tests/agents/gmi/ -v --tb=short

clean:
	@echo "$(YELLOW)Cleaning up...$(RESET)"
	@rm -rf .venv
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleaned!$(RESET)"
