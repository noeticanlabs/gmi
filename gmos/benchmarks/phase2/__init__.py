"""
Phase 2 Benchmark Package

Provides shared utilities for Phase 2 evaluation.
"""

import os
from pathlib import Path


def get_results_dir() -> Path:
    """Get the results directory relative to this package."""
    return Path(__file__).resolve().parent


def get_results_path(filename: str) -> Path:
    """Get full path for a results file."""
    return get_results_dir() / filename
